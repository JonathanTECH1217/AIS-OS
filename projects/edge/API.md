# Monarc Edge: the contract between the server and the page

Server `scripts/edge_server.py` on http://127.0.0.1:8800/ (tests on 8801). Every route under `/api/` answers JSON;
errors are `{"errors": ["..."]}` with a 4xx or 500. Static files come from `projects/edge/`. Money and prices are
dollars as floats (0.26 = 26 cents); points are percentage points (7.0); times are ISO 8601 UTC with a `Z`.
The page shows times in America/New_York.

## Routes

| Method and path | Returns |
|---|---|
| `GET /api/health` | `{app:"Monarc Edge", version, env, mode, dry_run, halted, keys:{kalshi_demo, kalshi, football, anthropic}, football_remaining, busy, rev, clock}`. `keys.*` are source labels or null, never values. |
| `GET /api/state?since=N` | Long-poll: answers at once when `rev > N`, else waits up to 25 s. Body: the **state bundle** below. |
| `GET /api/config` | The full config (see `scripts/edge_common.py` DEFAULTS). |
| `PUT /api/config` | Body: a partial config, deep-merged. 409 `{errors, gate}` when `mode: "auto"` is asked for and the gate has not passed; 409 when `env: "prod"` with `dry_run: false` and `rehearsal_passed` is false; 400 on an unknown key or a wrong type. Returns the saved config. |
| `GET /api/cards?day=YYYY-MM-DD&state=a,b` | Cards. Default: every card whose fixture kicks off from now minus 3 h to the listing lookahead (16 days, the whole early market), plus any card in a live-order or position state. |
| `GET /api/cards/{id}` | One card plus `snapshots` (latest 24) and `order`. |
| `POST /api/cards/{id}/approve` | Re-prices from a fresh book, places (or dry-runs) the order. 200 the card; 409 `{errors, card}` when the gap fell under the floor, the busy check fails, a halt is on, or the state does not allow it. |
| `POST /api/cards/{id}/pass` | The card, state `passed`. |
| `POST /api/cards/{id}/cancel` | Cancels a resting order; the card, state `unfilled`. |
| `GET /api/record` | The **record** below. |
| `GET /api/gate` | The **gate** below. |
| `POST /api/backtest` | Body `{seasons:["2122","2223",...]}` (football-data codes), starts a run in the background. 409 if one is running. |
| `GET /api/backtest` | `{status:"idle"|"running"|"done"|"error", started, finished, report_md, report_path, metrics, error}`. |
| `POST /api/tick` | Runs one loop pass now. `{ran:true, took_ms, did:[...]}`. |
| `POST /api/halt/clear` | `{halted:false}`. |
| `GET /api/fixtures` | `[{id, home, away, kickoff_utc, kalshi_event, poly_slug, linked, status, unlinked_names}]` for the next 16 days. |
| `GET /api/clock`, `POST /api/clock {iso|null}` | Only with `EDGE_TEST=1`. Freezes or releases the server's clock. |
| `POST /api/fake/{kalshi|football|poly}` | Only with `EDGE_TEST=1`. Replaces the fake client's scripted data (see the test fakes). |

## Card

```
{ id, fixture_id, event_ticker, ticker, outcome: "home"|"draw"|"away", outcome_name: "Arsenal"|"Tie",
  home, away, kickoff_utc, side: "yes"|"no"|null, state, created, decided_at, expires_at,
  model_version, model_p, p_home, p_draw, p_away,
  market_yes_bid, market_yes_ask, market_price, market_mid, poly_mid,
  fee_points, break_even, gap_points, color: "green"|"yellow"|"amber"|"red"   (yellow = at or past config big_gap_points: a warning, paper-filled and approvable, never taken by live auto mode),
  stake_usd, count, limit_price, band: "30-40", hours_band: "0-1h"|"1-3h"|"3-12h"|"12-24h"|"1-3d"|"3d+",
  mode, can_approve, approved_at, passed_at, order_id, fill_count, avg_fill, fees_paid,
  result: "yes"|"no"|null, pnl_usd, clv_points, closing_fair, reasoning, flags: [string],
  lineups_seen: 0|1, busy_ok: 0|1, busy_reason, sources: [string], paper: 0|1, updated }
```

States: `watching` (priced, outside an approvable condition), `ready` (green and busy, approvable), `no_edge`
(amber or red, or busy check failed), `approved`, `placed` (order resting), `partial`, `filled`, `unfilled`
(cancelled at kickoff), `passed`, `expired`, `delisted`, `halted`, `settled`, `error`.

`can_approve` is true only for `ready` cards while no halt is on and the kickoff is in the future.

## State bundle (`GET /api/state`)

```
{ rev, now, config: <full config>, halted: bool, halts: [{id, ts, reason, detail, cleared_at}],
  cards: [card], record: <record summary>, gate: <gate>,
  sync: {fixtures_at, markets_at, open_markets, football_remaining, poly_ok, last_error},
  account: {env, balance_usd, positions, read_at, error} | null   (the Kalshi account behind the configured env, read every 5 minutes when a key is accepted; null with no key),
  unlinked: [{fixture_id|null, kalshi_event|null, poly_slug|null, names:[...]}],
  version }
```

## Record (`GET /api/record`)

```
{ settled, bets, hit_rate, pnl_usd, return_pct, staked_usd,
  bankroll: {start, balance, equity, peak, drawdown_pct},
  equity: [{ts, balance}], ledger: [{id, ts, kind, card_id, amount_usd, balance_after, note}]  (latest 100),
  bands: [{band, n, model_mean, hit_rate, lo, hi, within, light: "green"|"red"|"grey"}],
  market_bands: [{band, n, market_mean, hit_rate}],
  clv: {mean, n, positive_share, by_hours: [{band, n, mean}]},
  brier: {model, market, n},
  by_side: [{side, n, pnl_usd}], by_outcome: [{outcome, n, pnl_usd}],
  by_gap: [{gap: "7 to 10"|"10 to 15"|"15 and up", n, hit_rate, pnl_usd}] }
```

`record summary` in the state bundle is the same object without `equity`, `ledger`, `market_bands`.

## Gate (`GET /api/gate`)

```
{ settled,
  lights: { count:       {ok, value, need},
            calibration: {ok, bands:[{band, n, model_mean, hit_rate, within, light}], pooled:{n, model_mean, hit_rate, within}},
            profit:      {ok, value},
            clv:         {ok, value, need, n} },
  passed: bool, reasons: [string] }
```

`passed` is true only when all four lights are ok.
