# yt-playlist-ticktick-sync

Cloudflare Python Worker that runs daily, checks a YouTube playlist for new videos, and creates tasks in your TickTick list. Deduplicates by comparing video titles against existing tasks.

## How it works

```
Cloudflare Cron (daily)
    │
    ├──▶ Fetch videos from YouTube playlist
    ├──▶ Fetch existing tasks from TickTick list
    ├──▶ Find new videos not yet in TickTick
    └──▶ Create a task for each new video
```

## Prerequisites

You'll need these credentials before setting up:

| Credential | Where to get it |
|------------|----------------|
| YouTube Data API Key | [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials) (enable [YouTube Data API v3](https://console.cloud.google.com/apis/library/youtube.googleapis.com)) |
| YouTube Playlist ID | From the playlist URL: `youtube.com/playlist?list=<THIS_PART>` |
| TickTick Access Token | Create an app at [developer.ticktick.com](https://developer.ticktick.com/), then follow the [OAuth flow](#ticktick-oauth-flow) below |
| TickTick List ID | `curl "https://api.ticktick.com/open/v1/project" -H "Authorization: Bearer <TOKEN>"` |

## Deploy

### 1. Fork/clone the repo

```bash
git clone https://github.com/praffq-dev/yt-playlist-ticktick-sync.git
cd yt-playlist-ticktick-sync
```

### 2. Connect to Cloudflare

Go to [Cloudflare Dashboard → Workers & Pages](https://dash.cloudflare.com/?to=/:account/workers-and-pages) → **Create** → **Import a repository** → select this repo. Cloudflare will auto-detect the config and deploy on every push to `main`.

Alternatively, deploy manually:

```bash
npx wrangler deploy
```

### 3. Add secrets

After the first deploy, go to [Cloudflare Dashboard](https://dash.cloudflare.com) → **Workers & Pages** → click your Worker → **Settings** → **Variables and Secrets** → add these as type **Secret**:

| Name | Value |
|------|-------|
| `YT_API_KEY` | Your YouTube Data API key |
| `PLAYLIST_ID` | Your YouTube playlist ID |
| `TICK_TICK_API_TOKEN` | Your TickTick OAuth access token |
| `TICK_TICK_LIST_ID` | Your TickTick list/project ID |

Click **Deploy**. The cron will now run automatically on schedule.

## Local development

```bash
cp .env.example .env  # fill in your values
uv sync
uv run pywrangler dev --test-scheduled

# Test cron handler
curl "http://localhost:8787/cdn-cgi/handler/scheduled?cron=*+*+*+*+*"
```

## Cron schedule

Default: `30 18 * * *` (18:30 UTC = 12:00 AM IST). Edit in `wrangler.toml`.

| IST | Cron |
|-----|------|
| 12:00 AM | `30 18 * * *` |
| 8:00 AM | `30 2 * * *` |
| 6:00 PM | `30 12 * * *` |

## TickTick OAuth flow

1. Register an app at [developer.ticktick.com](https://developer.ticktick.com/) — set both App Service URL and OAuth Redirect URL to `http://localhost`

2. Authorize in browser:
```
https://ticktick.com/oauth/authorize?scope=tasks:read%20tasks:write&client_id=<CLIENT_ID>&redirect_uri=http://localhost&response_type=code
```

3. Copy the `code` from the redirect URL, then exchange it:
```bash
curl -X POST https://ticktick.com/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "code=<CODE>&grant_type=authorization_code&redirect_uri=http://localhost" \
  -u "<CLIENT_ID>:<CLIENT_SECRET>"
```

The `access_token` in the response expires in ~180 days.

## Notes

- YouTube API free tier: 10,000 units/day. Each playlist fetch costs 1 unit.
- TickTick token expires in ~180 days — re-authorize and update the secret when it does.
- Deduplication is title-based: if a video title matches an existing task title, it's skipped.
- Secrets are set in the Cloudflare dashboard and persist across deployments.

## License

MIT