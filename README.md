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
| Cloudflare API Token | [Cloudflare Dashboard → API Tokens](https://dash.cloudflare.com/profile/api-tokens) → use **Edit Cloudflare Workers** template |

## Setup

```bash
git clone https://github.com/praffq-dev/yt-playlist-ticktick-sync.git
cd yt-playlist-ticktick-sync
cp .env.example .env # fill in your values
```

### GitHub Actions (auto-deploy)

Add these secrets in your repo **Settings → Secrets → Actions**:

- `CLOUDFLARE_API_TOKEN`
- `YOUTUBE_API_KEY`
- `YOUTUBE_PLAYLIST_ID`
- `TICKTICK_ACCESS_TOKEN`
- `TICKTICK_LIST_ID`

Push to `main` and it deploys automatically.

### Manual deploy

```bash
npx wrangler deploy
```

## Local development

```bash
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

## License

MIT