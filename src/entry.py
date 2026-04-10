import json
from js import fetch, Headers
from workers import WorkerEntrypoint, Response


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


async def get_all_tasks_title_from_tick_tick_list(env):
    headers = Headers.new()
    headers.set("Authorization", f"Bearer {env.TICK_TICK_API_TOKEN}")

    resp = await fetch(
        f"https://api.ticktick.com/open/v1/project/{env.TICK_TICK_LIST_ID}/data",
        headers=headers,
        method="GET",
    )

    data = json.loads(await resp.text())
    titles = [task["title"] for task in data.get("tasks", [])]
    return titles


async def get_playlist_items_to_add(env):
    all_videos = []
    page_token = None
    existing_titles = await get_all_tasks_title_from_tick_tick_list(env)

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
            if item["snippet"]["title"] in existing_titles:
                continue
            all_videos.append({
                "title": item["snippet"]["title"],
                "url": f"https://www.youtube.com/watch?v={item['snippet']['resourceId']['videoId']}",
            })

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    return all_videos


async def convert_videos_data_to_tasks(videos_data):
    tasks = []
    for video in videos_data:
        title = video["title"].split("||")[0].strip() if "||" in video["title"] else video["title"]
        tasks.append({
            "title": title,
            "content": f"Video Link: {video['url']}",
        })
    return tasks


class Default(WorkerEntrypoint):

    async def scheduled(self, controller, env, ctx):
        print(f"cron processed: {controller.cron}")

        videos = await get_playlist_items_to_add(env)
        print(f"{len(videos)} new video(s) to add")

        tasks = await convert_videos_data_to_tasks(videos)

        for task in tasks:
            await add_task_to_tick_tick(env, task["title"], task["content"])
            print(f"created task: {task['title']}")

        print(f"done. created {len(tasks)} task(s).")

    async def fetch(self, request, env, ctx):
        return Response.json({
            "status": "ok",
            "worker": "yt-ticktick-sync",
        })