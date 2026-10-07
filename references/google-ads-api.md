# Google Ads API

Wired 2026-09-28 for the Ads screen in the CRM, where Jonathan approves each campaign's spend, keywords, negatives, and ad, then publishes it. Scripts: `scripts/google_ads_api.py` (login, reads, changes), `scripts/ads_publish.py` (the rules and the publish), `scripts/ads_pull.py` (the morning read-back). Campaign files: `projects/google-ads/campaigns/NN-<service>.json`.

## What changed in 2026

- **Developer tokens are gone** (2026-09-09). API access comes from the Google Cloud project that holds the OAuth client. No Google Ads manager account is needed.
- **Access levels**, per Cloud project ([access levels](https://developers.google.com/google-ads/api/docs/api-policy/access-levels)):
  - **Test:** automatic, test accounts only.
  - **Explorer:** apply in the Cloud Console, and Google may grant it on its own. Real accounts, 2,880 actions a day. It can build campaigns, budgets, ad groups, keywords, negatives, shared lists, and ads. It **cannot** use Keyword Planner, billing, or user management.
  - **Basic:** brand verification plus an application, about 10 business days. 15,000 actions a day, everything unlocked, including Keyword Planner.
- **Current version: v25** (v25.2 on 2026-09-23), pinned as `VERSION` in `google_ads_api.py`.

## Setup (Jonathan, about 20 minutes, once)

1. At console.cloud.google.com, signed in as jonathan@monarcbuild.com: make a project named "Monarc AIOS".
2. APIs and Services, Library: turn on **Google Ads API**.
3. On the Google Ads API page, press **Apply for access** and ask for Explorer.
4. APIs and Services, OAuth consent screen: External, app name "Monarc AIOS", your email. Add yourself as a test user.
5. Credentials, Create credentials, OAuth client ID, type **Desktop app**. Copy the client ID and secret into `%USERPROFILE%\.monarc\secrets.env`:
   ```
   GOOGLE_ADS_CLIENT_ID=...
   GOOGLE_ADS_CLIENT_SECRET=...
   ```
6. Run `python scripts/google_ads_api.py --login`. A browser opens; sign in with the Google account that is admin on the Ads account (418-577-4900). The refresh token is saved to `secrets.env` and never printed.
7. Run `python scripts/google_ads_api.py --check`. It lists the accounts this login reaches, the auto-tagging and final URL suffix settings, and any campaigns already there.

If a call is ever refused for a missing developer token, add `GOOGLE_ADS_DEVELOPER_TOKEN` to `secrets.env` and it is sent. The Google reference page still lists the header, but the September change says it is ignored. Also optional: `GOOGLE_ADS_CUSTOMER_ID` (otherwise read from `projects/google-ads/account.md`) and `GOOGLE_ADS_LOGIN_CUSTOMER_ID` (only if a manager account is ever added).

## How the calls look (REST)

- Token: `POST https://oauth2.googleapis.com/token` with `grant_type=refresh_token`, `client_id`, `client_secret`, `refresh_token`. Scope `https://www.googleapis.com/auth/adwords`.
- Headers: `Authorization: Bearer <token>`, plus `developer-token` and `login-customer-id` only when set.
- Read: `POST https://googleads.googleapis.com/v25/customers/<id>/googleAds:search` with `{"query": "<GAQL>"}`, then follow `nextPageToken`.
- Change: `POST .../customers/<id>/googleAds:mutate` with `{"mutateOperations": [...], "validateOnly": bool, "partialFailure": false}`. It is all or nothing. Temporary ids (`customers/<id>/campaigns/-2`) link new objects inside one call. Every publish sends `validateOnly: true` first: Google checks every step and builds nothing, then the real call follows.
- Place names to location ids: `POST .../v25/geoTargetConstants:suggest` with `{"locale": "en", "countryCode": "US", "locationNames": {"names": [...]}}`, cached in `projects/google-ads/geo-target-ids.json`.
- Account switches (the Fix buttons): `POST .../customers/<id>:mutate` (auto-tagging, final URL suffix) and `POST .../customers/<id>/conversionActions:mutate` (`primaryForGoal`).
- Errors come back as `error.details[].errors[]` with an `errorCode` and a `message`. The client turns them into plain lines on the screen.

## What a publish builds

In one call, in this order:
1. One shared negative list per group in `projects/google-ads/negatives/shared-lists.md` ("Monarc: <name>"), created once for the account and brought up to date after that.
2. The budget.
3. The campaign, **PAUSED**. Search only; Maximize clicks with the CPC cap; locations set to "Presence" only; `containsEuPoliticalAdvertising: DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING`.
4. The 213 locations and English.
5. The campaign's own negatives.
6. Links to the shared lists.
7. One ad group, holding each keyword as exact and as phrase.
8. The responsive search ad.

The ids Google returns are written back into the campaign file (`google`) and `projects/google-ads/shared-sets.json`. Publishing again sends only the differences.

**Action budget on Explorer.** A first publish of 01 with every shared list is about 1,080 actions, and the rehearsal doubles that. Publish one new campaign a day until Basic access comes through. `python scripts/ads_publish.py plan 01` prints the count offline.
