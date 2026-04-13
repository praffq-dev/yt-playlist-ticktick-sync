import json
from js import fetch, Headers
from workers import WorkerEntrypoint, Response


async def get_processed_video_ids(env):
    raw = await env.YT_SYNC_KV.get("processed_ids")
    return set(json.loads(raw)) if raw else set()


async def save_processed_video_ids(env, ids):
    await env.YT_SYNC_KV.put("processed_ids", json.dumps(list(ids)))


async def add_task_to_tick_tick(env, task_title, task_content):
    task_body = {
        "title": task_title,
        "content": task_content,
        "projectId": env.TICK_TICK_LIST_ID,
    }

    headers = Headers.new()
    headers.set("Authorization", f"Bearer {env.TICK_TICK_API_TOKEN}")
    headers.set("Content-Type", "application/json")

    await fetch(
        "https://api.ticktick.com/open/v1/task",
        method="POST",
        headers=headers,
        body=json.dumps(task_body),
    )


async def get_playlist_items_to_add(env):
    all_videos = []
    page_token = None
    processed_ids = await get_processed_video_ids(env)

    while True:
        url = (
            f"https://www.googleapis.com/youtube/v3/playlistItems"
            f"?part=snippet,contentDetails"
            f"&maxResults=50"
            f"&playlistId={env.PLAYLIST_ID}"
            f"&key={env.YT_API_KEY}"
        )
        if page_token:
            url += f"&pageToken={page_token}"

        resp = await fetch(url)
        data = json.loads(await resp.text())

        for item in data.get("items", []):
            video_id = item["snippet"]["resourceId"]["videoId"]
            if video_id in processed_ids:
                continue

            raw_title = item["snippet"]["title"]
            clean_title = raw_title.split("||")[0].strip() if "||" in raw_title else raw_title

            all_videos.append({
                "video_id": video_id,
                "title": clean_title,
                "url": f"https://www.youtube.com/watch?v={video_id}",
            })

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    return all_videos


class Default(WorkerEntrypoint):

    async def scheduled(self, controller, env, ctx):
        e = self.env
        print(f"cron processed: {controller.cron}")

        videos = await get_playlist_items_to_add(e)
        print(f"{len(videos)} new video(s) to add")

        for video in videos:
            await add_task_to_tick_tick(e, video["title"], f"Video Link: {video['url']}")
            print(f"created task: {video['title']}")

        # Save processed video IDs to KV
        processed_ids = await get_processed_video_ids(e)
        for video in videos:
            processed_ids.add(video["video_id"])
        await save_processed_video_ids(e, processed_ids)

        print(f"done. created {len(videos)} task(s).")

    async def fetch(self, request, env, ctx):
        e = self.env
        url = str(request.url)
        if "/trigger" in url:
            videos = await get_playlist_items_to_add(e)
            for video in videos:
                await add_task_to_tick_tick(e, video["title"], f"Video Link: {video['url']}")

            processed_ids = await get_processed_video_ids(e)
            for video in videos:
                processed_ids.add(video["video_id"])
            await save_processed_video_ids(e, processed_ids)

            return Response.json({"status": "done", "tasks_created": len(videos)})
        return Response.json({"status": "ok", "worker": "yt-ticktick-sync"})