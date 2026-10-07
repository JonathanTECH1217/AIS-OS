# YouTube Data API v3: the Monarc Build channel

Written 2026-10-05 for the lead review pipeline (`.claude/skills/social-content/workflows/lead-review-long-form.md`). Script: `scripts/youtube_api.py`. Not connected yet: no `YOUTUBE_REFRESH_TOKEN` in `secrets.env` (checked 2026-10-05).

## What it does

Uploads a long-form review to the Monarc Build channel as **private**, on his go. Sets it **public**, on his second go. Reads a video's state. Nothing else: no comments, no captions upload (he drops the `.srt` in YouTube Studio), no deletes.

## His part, once, in the Monarc Build Cloud project (console.cloud.google.com)

1. **APIs and Services, Library**: enable **YouTube Data API v3**. The project already has the Google Ads and Calendar APIs on; this is one more.
2. **OAuth consent screen**: it is External with him as a test user (`references/google-ads-api.md`), which Google calls **Testing**. In Testing a refresh token dies after 7 days. Press **Publish app** to move it to **In production**. Google then shows an "unverified app" warning on sign-in for sensitive scopes; for his own account that is a click through, not a block. (The same 7-day rule has been hitting the Calendar and Ads tokens; production fixes those too.)
3. **Scopes** on the consent screen: add `youtube.upload` and `youtube` so the sign-in screen does not list them as unexpected. Optional for a Desktop client.
4. Then: `python scripts/youtube_api.py --login`, pick jonathan@monarcbuild.com, and if Google asks which channel, pick Monarc Build's. The script prints the channel name as the check and refuses any other account.
5. **File the API Services compliance audit the same day** (Cloud console, YouTube Data API, "API Services Audit"; the form takes a short description of the use: uploading the company's own videos). It can take weeks. Until it passes, see the caveat below.

## The caveats, plainly

- **Private until the audit passes.** A project that has not passed YouTube's API Services audit uploads every video as private, and `videos.update` to public is refused or does not take. `publish` says so when it happens. The fallback is YouTube Studio: he opens the video and sets Public by hand. The upload itself, the title, the description and the tags all land either way.
- **Quota**: 10,000 units a day. One upload is 1,600 units; a status read is 1; a publish is 50. Six uploads a day at most.
- **Channel eligibility** is the channel's, not the API's: videos over 15 minutes and custom thumbnails need the channel's phone verification, done once in YouTube Studio.
- **Token expiry**: 7 days while the consent screen is in Testing (see step 2); none once in production, unless he revokes it.

## The metadata (`<name>.youtube.json`, written by `social_content.py long-form`)

| Field | Rule |
|---|---|
| `title` | His words, under 100 characters, no `<` or `>`. Never the prospect's name. |
| `description` | First line says who it is for. Two or three general lines. The booking link with UTM: `https://monarcbuild.com/av_marketing/?utm_source=youtube&utm_medium=video&utm_campaign=lead-review&utm_content=<slug>`. |
| `tags` | The fixed list in the workflow file plus the trade. Under 500 characters in all. |
| `category` | 27, Education (his to change; 22 is People and Blogs). |
| `privacy` | `private` on upload. `publish` flips it. |
| `made_for_kids` | false. |
| `company_key` | The lead's domain. `check-meta` refuses a title or description that carries its name. |
| `video_id`, `url`, `uploaded_on`, `published_on` | Written by the script. |

`python scripts/youtube_api.py check-meta <json>` runs the checks with no network.

## Where it is recorded

`projects/crm/creative.json`, through `scripts/creative_record.py`: the piece's `posts` get `{"platform": "youtube", "id", "url", "on", "state"}`; the Creative tab shows a tag ("YouTube private" until public). A piece with only a private upload stays in the unpublished list.

## The two gos

| Step | Command | Who says go |
|---|---|---|
| Upload, private | `python scripts/youtube_api.py upload media/looms/<set>/<name>.mp4 --meta media/looms/<set>/<name>.youtube.json` | Jonathan, per video |
| Publish | `python scripts/youtube_api.py publish <video-id>` | Jonathan, per video |

The clone runs neither on its own. `status <video-id>` is free to run.
