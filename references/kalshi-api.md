# Kalshi API

Wired 2026-10-04 for Monarc Edge (`projects/edge/`), the Premier League betting agent: Kalshi is the market the agent prices against and the account that holds the bets. Client: `scripts/kalshi_api.py` (public reads, request signing, V2 orders, dry run). The read-only second witness, Polymarket, is `scripts/polymarket_read.py` (last section). Interview behind the agent: `brainstorms/2026-10-03-betting-market-agent.md`; the numbers it set: `projects/edge/config.json`.

## What it gives us

- **Match-winner markets** for every Premier League game, series `KXEPLGAME`. One event a match, event ticker `KXEPLGAME-26OCT18NFOARS` = series, `YYMMMDD`, home code, away code; title "Nottingham Forest vs Arsenal" (home first), sub title "NFO vs ARS (Oct 18)". Three binary markets under it, `-NFO`, `-ARS`, `-TIE`, each with `yes_sub_title` the club name or "Tie". Settles on 90 minutes plus stoppage, no extra time or penalties; a game moved more than 48 hours settles at a fair price. Listed about two weeks out (19 events on 2026-10-04, Oct 10 to Oct 18).
- **Prices as dollar strings**, 0.0100 to 0.9900 in cent steps: `yes_bid_dollars`, `yes_ask_dollars`, `no_bid_dollars`, `no_ask_dollars`, `last_price_dollars`; sizes and volumes as fixed-point contract strings `yes_bid_size_fp`, `yes_ask_size_fp`, `volume_fp`, `volume_24h_fp`, `open_interest_fp`. The old integer cent fields (`yes_bid`, `volume`) may still appear; the client prefers the new ones and falls back.
- **The order book**, bids only on each side (`orderbook_fp.yes_dollars`, `no_dollars`, each `[price, count]`). The yes ask is 1 minus the best no bid; a yes buy fills against the no bidders, so the depth for a yes buy is the size at the best no bid.
- **The account**: balance, positions, fills, settlements, resting orders. Demo is a separate exchange with play money and separate keys; on 2026-10-04 it listed the same EPL events but with empty books (every ask 1.0000, volume 0), so a demo rehearsal proves the plumbing, not the prices.

## Account and keys

- Two environments, two key pairs, both made on the site under Account, API keys. Kalshi shows the key id and hands the private key as a PEM file once.
- Demo (`demo.kalshi.co`): `KALSHI_DEMO_API_KEY_ID` and `KALSHI_DEMO_PRIVATE_KEY_PATH` in `%USERPROFILE%\.monarc\secrets.env`; the PEM at `~/.monarc/kalshi-demo.pem`, beside `secrets.env`, never inside it.
- Prod (`kalshi.com`): `KALSHI_API_KEY_ID` and `KALSHI_PRIVATE_KEY_PATH`; PEM at `~/.monarc/kalshi-prod.pem`. Only after the rehearsal checklist in `projects/edge/README.md`; the client refuses `env="prod"` with `dry_run=False` unless `allow_prod=True` is passed, which the server does only once the config says `rehearsal_passed`.
- Public reads need no key. Without one, `Kalshi.has_key` is false and any account call raises `KalshiError` naming the missing key. No key id, PEM path content, or signature is ever printed or logged; the dry-run log writes `<key id>` and `<signed>` in their place.
- Signing: headers `KALSHI-ACCESS-KEY` (the key id), `KALSHI-ACCESS-TIMESTAMP` (Unix milliseconds as a string), `KALSHI-ACCESS-SIGNATURE` (base64). The string signed is `timestamp + METHOD + path`, the path from the host root including `/trade-api/v2` and without the query string. RSA-PSS, SHA-256, MGF1 SHA-256, salt length equal to the digest length. Kalshi also accepts Ed25519 keys; the client only loads RSA PEMs.

## Endpoints used

Base: prod `https://api.elections.kalshi.com/trade-api/v2` (`https://external-api.kalshi.com/trade-api/v2` as the fallback host on a connection error); demo `https://demo-api.kalshi.co/trade-api/v2` (`https://external-api.demo.kalshi.co/trade-api/v2`). All verified live 2026-10-04 except where marked.

| Job | Endpoint | Notes |
|---|---|---|
| Open EPL markets | `GET /markets?series_ticker=KXEPLGAME&status=open&limit=200` | Cursor paginated; an empty `cursor` is the last page. The filter takes `open`, the object says `active`. |
| One market | `GET /markets/{ticker}` | `{"market": {...}}`; 404 when unknown. |
| Order book | `GET /markets/{ticker}/orderbook?depth=5` | `orderbook_fp.yes_dollars` and `no_dollars`, bids as `[price, count]` strings. |
| Open events with markets | `GET /events?series_ticker=KXEPLGAME&status=open&with_nested_markets=true` | Each event carries `markets`. |
| One event | `GET /events/{event_ticker}?with_nested_markets=true` | `{"event": {... "markets": [...]}, "markets": []}`. |
| Series | `GET /series/KXEPLGAME` | Rules text, settlement sources (ESPN, Fox Sports). |
| Exchange open? | `GET /exchange/status` | `exchange_active`, `trading_active`, plus one status per `exchange_index`. |
| Balance | `GET /portfolio/balance` | `balance` cents, `balance_dollars` string (docs). Needs a key. |
| Positions | `GET /portfolio/positions?settlement_status=unsettled` | `market_positions[]`: `ticker`, `position_fp` (+ yes, - no), `market_exposure_dollars`, `realized_pnl_dollars`, `fees_paid_dollars` (docs). |
| Fills | `GET /portfolio/fills?ticker&min_ts` | `fill_id`, `trade_id`, `order_id`, `ticker`, `outcome_side` yes/no, `book_side` bid/ask, `count_fp`, `yes_price_dollars`, `no_price_dollars`, `is_taker`, `fee_cost` (dollars string), `created_time` (docs). |
| Settlements | `GET /portfolio/settlements?ticker&min_ts` | `ticker`, `market_result` yes/no, `yes_count_fp`, `no_count_fp`, `revenue` (cents int), `fee_cost` (dollars string), `settled_time` (docs). |
| One order | `GET /portfolio/orders/{order_id}` | `status` resting, canceled, executed; `fill_count_fp`, `remaining_count_fp`, `taker_fees_dollars`, `maker_fees_dollars`, `taker_fill_cost_dollars`, `maker_fill_cost_dollars` (docs). |
| Place (V2) | `POST /portfolio/events/orders` | Body `{ticker, side: bid or ask, count: "20", price: "0.2600", time_in_force, self_trade_prevention_type: taker_at_cross, client_order_id, expiration_time (Unix s, optional), post_only}`. Answer `order_id, client_order_id, fill_count, remaining_count, average_fill_price, average_fee_paid, ts_ms` (docs). |
| Cancel (V2) | `DELETE /portfolio/events/orders/{order_id}?market_ticker=...` | `market_ticker` routes the cancel when `exchange_index` is not given. Answer `order_id, reduced_by, ts_ms` (docs). |

V2 speaks in YES terms. `side: bid` buys YES at `price`; `side: ask` sells YES, which opens a NO position. `Kalshi.create_order(ticker, side, price, count, ...)` takes the side you want to buy and that side's price and maps it: buy No at 0.77 becomes `ask` at `0.2300`, buy Yes at 0.26 becomes `bid` at `0.2600`.

## Fees

- Taker: `0.07 x count x price x (1 - price)`, rounded up to the cent per fill (`edge_common.kalshi_fee_usd`). Worst at 50 cents: 1.75 cents a contract. 100 contracts at 0.55 cost $1.74 in fees.
- Maker: about a quarter of that (rate 0.0175). The agent assumes taker on every card (`fees.assume_taker`), so the gap it shows is after the worse fee.
- The fee shows up per fill (`fee_cost`) and on the order (`taker_fees_dollars`, `maker_fees_dollars`). `fees.schedule_checked` in the config is the date Jonathan last read Kalshi's fee PDF; the rate is his to change there.

## The scripts

- `python scripts/kalshi_api.py check [--prod]`: env, which key names resolve and from where (labels only), exchange status, balance when a key is usable.
- `events [SERIES]`, `markets [SERIES]`, `event TICKER`, `book TICKER`: public reads, default series from the config.
- `order TICKER yes|no PRICE COUNT [--prod] --really`: the one way to place from the command line. Without `--really` it dry-runs and writes the line to `projects/edge/data/dry-run.jsonl`. `--prod --really` is refused until `rehearsal_passed` is true.
- `cancel ORDER_ID TICKER --really`, `fills`, `settlements [--since YYYY-MM-DD]`.
- In code: `Kalshi(env, dry_run, allow_prod=...)`; `markets`, `market`, `events`, `event`, `orderbook`, `exchange_status`, `balance`, `positions`, `fills`, `settlements`, `order`, `create_order`, `cancel`. Normalized dicts carry floats in dollars and contracts, plus `raw`.

## Limits and traps

- Rate limits are token buckets per second by tier (Basic: 200 reads, 100 writes a second). Over the limit answers `429 {"error": "too many requests"}` with no Retry-After header; the client sleeps 0.5, 1, 2 s and retries three times, retries a 5xx once, and tries the other host once on a connection error.
- Prices come as strings. Keep them as dollars (floats 0..1) everywhere inside the agent; never mix the cent fields in.
- `status=open` in the filter, `"active"` in the object. A market that closed early (`can_close_early`, after the result) drops out of the open list.
- The order book lists bids only. Compute the asks (1 minus the other side's best bid); never read a "yes ask" off the yes list.
- Demo books were empty on 2026-10-04. Rehearse the plumbing there; prices only mean something on prod.
- Orders: V2 only; the old `POST /portfolio/orders` is not used. `count` and `price` are strings; `price` is the YES price in every case. Set `client_order_id` so a lost answer can be matched; `expiration_time` is Unix seconds.
- Maryland note: sports event contracts are contested in *Maryland v. Kalshi* (Fourth Circuit, argued 2026-05-07); enforcement is paused pending the ruling. `legal_watch` in the config holds the note and the date Jonathan last checked it. A ruling against Kalshi could close these markets in Maryland with little notice; open positions would settle under Kalshi's rules.
- Kalshi's rules bar current players, coaches, and staff of the league from trading these markets (`series.additional_prohibitions`).

## Polymarket, read-only

The second witness: a second market's price next to Kalshi's, so a card can say when the two disagree by more than `polymarket.disagree_points`. No account, no key, nothing sent. `scripts/polymarket_read.py`.

- Gamma `https://gamma-api.polymarket.com`: `GET /events?tag_slug=epl&active=true&closed=false&limit=100&offset=N&end_date_min=<iso>&end_date_max=<iso>` lists EPL events. A match event has slug `epl-cry-not-2026-10-11` (home code, away code, date), title "Crystal Palace FC vs. Nottingham Forest FC", and three `markets` with `sportsMarketType` "moneyline" whose slugs end in the home code, `-draw`, and the away code. Each market: `question`, `outcomes` (a JSON string `["Yes","No"]`), `outcomePrices` (JSON string), `bestBid`, `bestAsk`, `clobTokenIds` (JSON string, index 0 the Yes token), `gameStartTime` ("2026-10-17 11:30:00+00"), `liquidity`, `volume`. The event's `endDate` equals the kickoff, which is why the listing filters by end date; `startDate` is the day Polymarket listed it, so `start_date_min` is no use for kickoff. `GET /events?slug=<slug>` fetches one. Verified live 2026-10-04 (15 match events, Oct 10 to Oct 17).
- CLOB `https://clob.polymarket.com`: `GET /midpoint?token_id=<yes token>` answers `{"mid": "0.345"}`. One call per market, cached 2 minutes; the listing is cached 5 minutes under `projects/edge/data/cache/polymarket/`.
- Codes differ from Kalshi's (`ast` for Aston Villa, `mac` for Man City, `che`, `liv`, `not`); `projects/edge/teams.json` carries both, and `find_match` matches by club names and kickoff within 10 minutes, never by code.
- Polymarket blocks some US users. If Gamma or the CLOB answers 403 or 451 from this machine, `reachable()` is false, `LAST_ERROR` says why, and the agent runs with no witness. Both answered from here on 2026-10-04.
