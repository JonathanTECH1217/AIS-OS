# Instagram: the feed pull and the numbers

Jonathan, 2026-10-05: "let's work on the instagram feed pull. This should give access to analytics as well." Earlier the same day: "I want to pull Instagram photos and put them on the our work section in the website."

Status: the script is written and not yet run against a real account. No Meta app exists and no token is on file.

## What it is

Meta's own route, the Instagram API with Instagram Login. The owner of an Instagram account signs in once to Monarc's Meta app and a token comes back. With that token the AIOS reads, and only reads:

- **The feed:** each post's picture (a reel's cover), caption, date, link, likes, and comments. Posts have a caption and no title.
- **The numbers:** per post (reach, views, likes, comments, shares, saves, total interactions) and for the account (reach, views, accounts engaged, profile views, followers). Meta renames these often; the script asks for each by itself and lists the ones an account does not have.

## Two kinds of read (Jonathan, 2026-10-05: "I only pull analytics for my personal and I pull meta data on theirs")

- **Monarc's own account: the feed and the numbers.** Jonathan's account signs in once; the token is `INSTAGRAM_TOKEN`.
- **Anyone else's: the public profile and posts, no sign-in from them.** Meta's Business Discovery: with Monarc's own token, any business or creator account can be read by its handle: bio, website, follower count, post count, and the posts with captions, pictures, dates, links, likes, and comments. Not their numbers; Meta never hands out another account's analytics. A personal or private account comes back as not found. Meta caps how much can be read this way per week.

Monarc's account must be a professional account (business or creator). Switching is free and takes a minute in the Instagram app. A client whose own numbers Monarc should read connects the same way as Monarc (`INSTAGRAM_TOKEN_<SLUG>`); for pictures and captions alone, nobody but Monarc has to connect.

Whether Business Discovery answers on this login route (graph.instagram.com) is not confirmed until the first run; Meta's pages show it on the older Facebook Login route for certain. If it refuses, the fallback is that route: the same Meta app with Facebook Login and a Facebook Page linked to Monarc's Instagram.

## Limits Meta sets

- Some numbers are missing on an account with fewer than 100 followers.
- Account numbers are kept for about 90 days.
- A token lives 60 days. `python scripts/instagram_api.py refresh` trades it for a fresh one; run it monthly.
- A reel with copyrighted music may come back with no picture address.
- While Monarc's Meta app is in development mode, only accounts added to the app as Instagram testers can connect. That is enough for Monarc and a handful of clients. Serving any account without adding it by hand needs Meta's App Review and business verification, which takes weeks.

## Setup, his to do (about 20 minutes, once)

1. developers.facebook.com, signed in with the Facebook login that owns Monarc's pages. Create an app, type Business. Name it "Monarc Build".
2. In the app, add the product **Instagram**, then **API setup with Instagram login**.
3. Under roles, add the Instagram account as an **Instagram tester**. In the Instagram app on the phone: Settings, Website permissions (or Apps and websites), Tester invites, accept.
4. Back in the app's Instagram setup page, press **Generate token** beside the account and sign in as that account. Allow the two permissions: `instagram_business_basic` and `instagram_business_manage_insights`.
5. Put the token in `%USERPROFILE%\.monarc\secrets.env` as `INSTAGRAM_TOKEN=...` for Monarc's own account, or `INSTAGRAM_TOKEN_<SLUG>=...` for a client's (`INSTAGRAM_TOKEN_PHA`). Never in chat, never in a tracked file.
6. Tell the clone. It runs `python scripts/instagram_api.py check` and reports whose token it is.

For a client: steps 3 to 6 again with their account. They accept the tester invite on their phone and sign in once when the token is made.

## Commands

```
python scripts/instagram_api.py check
python scripts/instagram_api.py feed     [--limit 12] [--save]
python scripts/instagram_api.py insights [--limit 12]
python scripts/instagram_api.py discover <handle> [--limit 12] [--save] [--name slug]
python scripts/instagram_api.py refresh
```

`feed --save` and `discover --save` put the pictures in `projects/research/<slug>/instagram/` and write `instagram.json`; `insights` writes `instagram-insights.json`. `--account <slug>` on any of them uses a client's token instead of Monarc's.

## Rules for the clone

- Read only. The script cannot post, comment, or message, and the two permissions asked for do not allow it.
- A client's pictures and numbers are the client's. They go on that client's page and in that client's report, nowhere else, without their say.
- The first run on any new account is `check`, to prove whose token it is, before anything is saved.
- Another company's pictures and captions, read through Business Discovery, are theirs: for a render they see, a page they approve, or a message to them, not for Monarc's own posts.
- Not verified yet, to settle on the first real run: the exact names of the numbers Meta returns today, whether the token from the dashboard is the 60-day kind, and whether Business Discovery answers on this login route.

## Checklist

- [ ] Meta app made, Instagram product added
- [ ] Monarc's own Instagram connected, `INSTAGRAM_TOKEN` in `secrets.env`
- [ ] `check`, `feed --save`, and `insights` run once on Monarc's account
- [ ] `discover` run once on a business account that is not Monarc's
- [ ] First client account connected, if its numbers are wanted

Last checked: 2026-10-05.
