# API-Football

Wired 2026-10-04 for Monarc Edge (`projects/edge/`): the facts the match model is built from. Fixtures and kickoff times, confirmed lineups in the last hour, shots and possession after each match, player minutes and ratings, injuries, and bookmaker odds as a check on the model. Client: `scripts/api_football.py`. The key is pending Jonathan's Pro account ($19 a month, dashboard.api-football.com); until it lands every live call raises and the cache serves what it has. The docs site (`api-football.com/documentation-v3`) refused automated reads on 2026-10-04, so the field names below follow the published v3 shape and the first live read should be checked against them.

## What it gives us

- **Fixtures**: every Premier League match with its id, kickoff (UTC), status (`NS` not started, `1H`, `HT`, `2H`, `FT`, `PST` postponed), round, home and away ids and names, goals, venue. The fixture id is the key for everything else.
- **Lineups**: the starting eleven, formation, and bench per team, posted 20 to 40 minutes before kickoff. The agent polls from 75 minutes out every 5 minutes (`window.lineup_from_minutes`, `lineup_poll_minutes`) and will not decide without them unless `decide_without_lineups` is on.
- **Match statistics**: shots, shots on target, possession, corners, fouls, cards, saves, passes, expected goals per team. The model's inputs.
- **Player statistics per match**: minutes, rating, tackles, interceptions, dribbles, duels. Season totals per player (`/players`) for who matters when a name is missing from a lineup.
- **Injuries**: who is out and why, by league or by fixture.
- **Odds**: decimal Match Winner prices per bookmaker (`bet=1`), kept 7 days only. A sanity check on the model (`api_football.odds_witness`), not an input.
- **Head to head** and **teams** (ids, three-letter codes) for `teams.json`.

## Account and keys

- `API_FOOTBALL_KEY` in `%USERPROFILE%\.monarc\secrets.env` (`references/credentials.md`), sent as the header `x-apisports-key`. Direct API-Sports plan, not RapidAPI.
- Pro plan: 7,500 calls a day, 300 a minute. The day quota comes back in `x-ratelimit-requests-remaining`, the minute quota in `X-RateLimit-Remaining`; `Football.remaining` keeps the last day value seen.
- The client's own budget is lower: `api_football.daily_budget` (6,000) in the config, counted in `projects/edge/data/football-budget.json` as `{"day", "used"}`. A live call past it raises `FootballBudget`; cached answers still serve.
- Premier League is `league=39`; `season=2026` is 2026-27 (`league_id` and `season` in the config).

## Endpoints used

Base `https://v3.football.api-sports.io`. Every answer is `{"get", "parameters", "errors", "results", "paging": {"current", "total"}, "response": [...]}`. Errors often come with HTTP 200 and `errors` as a dict (`{"token": ...}`, `{"requests": ...}` when the day quota is spent, `{"rateLimit": ...}` for the minute); the client raises on any of them.

| Job | Endpoint and params | Response item | Cache |
|---|---|---|---|
| Fixtures | `GET /fixtures?league=39&season=2026&from=&to=` (also `ids=1-2-3`, `team`, `last`, `next`) | `fixture{id, date, timestamp, venue{name, city}, status{short, elapsed}}`, `league{round, season}`, `teams{home{id, name}, away{id, name}}`, `goals{home, away}` | 6 h |
| Lineups | `GET /fixtures/lineups?fixture=` | per team: `team{id, name}`, `formation`, `coach{name}`, `startXI[{player{id, name, number, pos, grid}}]`, `substitutes[...]` | none until both teams are in, then for good |
| Match statistics | `GET /fixtures/statistics?fixture=` | per team: `team{id}`, `statistics[{type, value}]` with types "Shots on Goal", "Shots off Goal", "Total Shots", "Blocked Shots", "Shots insidebox", "Shots outsidebox", "Fouls", "Corner Kicks", "Offsides", "Ball Possession" ("55%"), "Yellow Cards", "Red Cards", "Goalkeeper Saves", "Total passes", "Passes accurate", "Passes %", "expected_goals", "goals_prevented" | for good once non-empty |
| Player statistics | `GET /fixtures/players?fixture=` | per team: `players[{player{id, name}, statistics[{games{minutes, number, position, rating, substitute}, shots{total, on}, goals{total, assists}, passes{total, key}, tackles{total, blocks, interceptions}, duels{total, won}, dribbles{attempts, success}, fouls{drawn, committed}, cards{yellow, red}}]}]` | for good once non-empty |
| Injuries | `GET /injuries?league=39&season=2026` or `?fixture=` | `player{id, name, type, reason}`, `team{id, name}`, `fixture{id, date}` | 6 h |
| Season players | `GET /players?team=&league=39&season=2026&page=` | `player{id, name, injured}`, `statistics[{league{id}, games{appearences, lineups, minutes, position, rating}}]` (the API spells it "appearences") | 24 h, every page |
| Odds | `GET /odds?fixture=&bet=1` | `bookmakers[{id, name, bets[{id, name: "Match Winner", values[{value: Home/Draw/Away, odd}]}]}]` | 3 h |
| Head to head | `GET /fixtures/headtohead?h2h=A-B&last=10` | fixture items | 168 h |
| Teams | `GET /teams?league=39&season=2026` | `team{id, name, code, country}`, `venue{name}` | 168 h |

Cache: `projects/edge/data/cache/football/<sha1 of path and params>.json` as `{"t", "path", "params", "body"}`. A hit costs nothing and needs no key. The hours per kind are `api_football.cache_hours` in the config.

## The scripts

- `python scripts/api_football.py check`: where the key comes from (label only), the budget used today, and with a key the plan and calls used from `/status`.
- `fixtures --from 2026-10-10 --to 2026-10-12`: the fixtures in a window with ids and status.
- `lineups FIXTURE`: both elevens or "not posted yet".
- `stats FIXTURE`: the parsed statistics per team id.
- `teams`: this season's clubs with their ids and codes, for `teams.json` (`api_id`).
- In code: `Football()` then `fixtures`, `lineups`, `fixture_stats`, `fixture_players`, `injuries`, `players`, `odds`, `h2h`, `teams`, or `get(path, ttl_hours, **params)` for anything else. `FootballError` on a refused call, `FootballBudget` (a `FootballError`) when the day's budget is spent.

## Limits and traps

- 7,500 a day, 300 a minute on Pro. The client keeps a 0.25 s floor between live calls and waits 2 s once on a 429 or a `rateLimit` error. Past the day quota the API answers 200 with `errors.requests`; the client raises `FootballBudget`.
- Odds are kept 7 days only. Fetch them inside the week before the match or they are gone; never plan a backtest on API-Football odds (football-data.co.uk has the closing lines).
- Lineups post 20 to 40 minutes before kickoff and sometimes later. `lineups()` returns None until both teams are present and caches nothing until then, so polling costs one call every 5 minutes per match in that window.
- `fixture_stats` and `fixture_players` keep the first non-empty answer for good. Call them after full time; a call during the match would freeze half a game's numbers.
- `ids` cannot be mixed with `league` and `season`; the client sends `ids` alone. Combining `from`/`to` needs `league` and `season`.
- "Ball Possession" and "Passes %" come as strings with a percent sign; `expected_goals` as a string; null counts (often "Red Cards") read as 0 in the parser, null floats stay None.
- `status.short` values worth knowing: `TBD`, `NS`, `1H`, `HT`, `2H`, `ET`, `P`, `FT`, `AET`, `PEN`, `PST` (postponed), `CANC`, `ABD`, `AWD`, `WO`. Only `FT` (and `AET`, `PEN` in cups) is a finished league match.
- Team ids are stable across seasons; names can change spelling (Nottingham Forest, Man United vs Manchester United). Map by id into `teams.json` once `teams` has run.
