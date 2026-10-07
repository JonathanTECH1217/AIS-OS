# Monarc Edge

Built 2026-10-04 from an 18-answer interview (`brainstorms/2026-10-03-betting-market-agent.md`). It bets against
Kalshi's English Premier League match-winner prices when our own model's chance sits 7 points or more from the
price after fees, in busy markets, sized from the gap. Status: Phase 2, demo exchange, dry-run orders, approve mode.
Nothing is placed for real until the rehearsal checklist below is ticked and Jonathan flips `rehearsal_passed`.

## The idea, in one line

When Kalshi says 45 cents and our numbers say 55, buy the 45 at $60, write down why, and keep score until the score
earns the right to run by itself.

## The five stages

His words from Q1, and what each became.

1. **"Define the outcome the bet is for."** Premier League match winner on Kalshi: series `KXEPLGAME`, three Yes/No
   markets a match (home, away, Tie). All six sides tradable, one position a match (the largest green side, Q18).
2. **"Define the variables that influence the outcome. The data points have to be posted, proven legit."**
   API-Football Pro for fixtures, lineups and stats; football-data.co.uk for results and closing odds. Never an AI
   guess, never a second market. `scripts/edge_model.py`.
3. **"Build a win probability per test group."** The model service gives `p_home`, `p_draw`, `p_away` with its
   contributions and sources, once per fixture per pass (`model_runs`).
4. **"Observe if the win rate scales proportionally with the market's prediction."** The record: bands of the
   model's chance against what happened, Brier for us and for the market, CLV by hours-before-kickoff band, the
   equity line. `scripts/edge_ledger.py`.
5. **"Post the offset in the ratio as a green +% or red -% offset with the reasoning behind betting being the fair
   trade."** The cards: gap after fees, color, stake and count, the busy check, the second witness, and two to four
   plain sentences written by Claude from the numbers (never the number itself). `scripts/edge_cards.py`,
   `scripts/edge_reason.py`.

## Open it

- Desktop shortcut **Monarc Edge** (its own Edge window on http://127.0.0.1:8800/).
- `pythonw scripts/edge_boot.pyw` does the same; `--no-open` starts or refreshes the server with no window (what the
  Startup entry "Monarc Edge (background)" runs); `python scripts/edge_boot.pyw --install` writes the icon
  (`projects/edge/monarc-edge.ico`), the Desktop shortcut and the Startup entry.
- The boot script restarts an idle server when any `scripts/edge_*.py`, `kalshi_api.py`, `api_football.py` or
  `polymarket_read.py` changed; a server placing an order or running a backtest is left alone.
- Log: `~/.monarc/edge-server.log`. Started copy: `~/.monarc/edge-server.json`.
- By hand: `python scripts/edge_server.py [--port 8800] [--no-open]`. The API is in `API.md`.

## The window and the states

Markets appear about two weeks ahead. From listing the loop snapshots each market every 60 minutes; from 75 minutes
before kickoff every 5 minutes, and it polls the lineups. When both XIs post, the cards are re-priced with
`lineups_seen` and the flag "lineups posted". At 20 minutes with no lineups (and `decide_without_lineups` false) the
open cards go `no_edge` with the flag "no lineups". At 2 minutes resting orders are cancelled (`unfilled`) and
untouched cards `expired`; one last snapshot is taken first so the closing fair exists for CLV.

Card states: `watching` (priced, outside an approvable condition: a smaller green side, a halt, no price), `ready`
(green and busy, approvable), `no_edge` (amber or red, or the busy check failed), `approved`, `placed` (order
resting), `partial`, `filled`, `unfilled`, `passed`, `expired`, `delisted`, `halted`, `settled`, `error`.

Claude is called only when a card first turns `ready` or its side or gap band moves while ready. The words go to
`reasoning`, its flags are appended, `model_p` is written first and never touched.

## Money rules

- **Gap:** our chance minus the ask, minus the taker fee at that price (0.07 x price x (1 - price), rounded up per
  fill). Always the ask, never the mid. Green at 7 points or more, red under zero, amber between (shown, no trade).
- **Stake line:** 6% of the match day's opening bankroll at 7 points, a straight line to 8% at 17 points or more.
  Whole contracts, never zero once there is a stake. "Opening bankroll" is the ledger balance at the start of the
  fixture's UTC day (today's balance when that day has not begun).
- **Busy floor:** 10,000 contracts traded, a 2-cent spread or less, and depth at the touch for our count (a No buy
  fills against the Yes bidders).
- **No at-risk cap** (Q13: "only constrained by the amount of upsided bets we can take and the capital we have").
  Ten cards on one weekend can put $600 to $800 of $1,000 to work.
- **Drawdown stop:** when equity falls 25% under its peak the loop halts and mode goes back to approve. In auto
  mode only (`drawdown.auto_only`); his to turn off.
- **One position a match.** The largest green side is `ready`; other green sides wait as `watching` with
  "larger edge on ...". A second approve on the same match is refused.

## The gate

Auto mode is refused until all four lights are green:

1. **Count:** 200 settled cards. Paper (dry-run) cards count.
2. **Calibration:** in every 10-point band of the model's chance with 30 or more cards, the share that happened is
   within 5 points of what the model said; a band with fewer is grey and ignored; the pooled rate within 3 points.
3. **Profit:** return after fees above zero.
4. **CLV:** average closing line value 5 points or more (the price we paid against the last price before kickoff).
   Expect this light last.

A halt flips the mode back to approve. The auto pass then takes only `ready` cards whose band is green, inside the
lineup hour (or under 75 minutes to kickoff) or in an hours-band whose CLV record is positive over 30 settled cards.

## Halts

- **Delisting:** a market gone (404) or closed, settled, determined or paused before kickoff cancels any resting
  order and marks the card `delisted`. Not a halt by itself.
- **sports_gone:** two syncs in a row with no open `KXEPLGAME` market while fixtures sit in the next 7 days.
- **state_block:** an order refused with location, state, jurisdiction, restricted, eligible or geo in the message
  or body (Maryland v. Kalshi). The body is kept in the halt row.
- **drawdown:** the stop above.
- **Resume:** the page's Resume button (`POST /api/halt/clear`) clears the halt, parks nothing, and puts halted
  cards back to `watching` so the next pass re-prices them. Mode stays approve until he turns auto back on.

## Running without the paid key

Without `API_FOOTBALL_KEY` the football client raises on live calls and the loop carries on: fixtures come from the
Kalshi events themselves (home and away from the event title; kickoff from the markets' `expected_expiration_time`
minus 3 hours, which is Kalshi's settlement margin, checked 2026-10-04 on 19 events), then Polymarket's exact
`gameStartTime` replaces it when the same two clubs match within 36 hours (`kickoff_source: "polymarket"` on
`/api/fixtures`; "kalshi" and the flag "kickoff from Kalshi" only when Polymarket has no such match). The fixture
id is a stable negative hash of the event ticker, lineups are "not available", `decide_without_lineups` is treated
as true, and every card carries "no lineup feed". The model service prices from football-data.co.uk alone.

Prices always come from the **production** exchange's public feed (`Ctx.quotes`, a key-less `Kalshi(env="prod")`),
whatever `env` says: the demo exchange lists the same markets with empty books, and a card priced from demo would
show 0 and 1. Orders and the account use the configured `env`.

Without `ANTHROPIC_API_KEY`, with `claude.on` false, with `EDGE_NO_CLAUDE=1`, or past the daily cap
(`claude.max_usd_per_day`), the card's text is a template built from the same numbers. The model id is
`claude.model`, or the cheapest current Claude model (`claude-haiku-4-5`) when empty.

A dry-run Kalshi order (status `dry`) is treated as a paper fill at the limit price with the taker fee, flagged
"paper fill at the ask", so paper cards settle (from the market's own result) and count toward the gate.

**Paper mode runs by itself.** While `dry_run` is on and `paper_auto` is on (Jonathan, 2026-10-04: "run paper on an
account"), every card that turns `ready` is paper-filled at the ask on the next pass, one position a match, with
`mode: "paper"` on the card. No click, no order, no money. The page's top bar says "Paper, auto fills" and the
Bankroll panel shows the real Kalshi account beside the paper book. Once `dry_run` is off, `paper_auto` does nothing
and approve mode means his click.

**Yellow: a big gap is a warning, not a bigger bet** (review of the first card, 2026-10-04). At or past
`big_gap_points` (10) the card turns yellow instead of green with the flag "big gap: the model may be wrong, check the
news". On a league this heavily bet, a model that sits 10 or more points from every serious market has usually missed
something. Paper mode still logs the bet (that is exactly the data that tells us whether to trust the model), Jonathan
may still click it after a look at the news, and live auto mode never takes it. The Record tab splits settled bets by
gap size (7 to 10, 10 to 15, 15 and up) so the answer shows up as it comes in. The note under each card now says which
way each reason cuts for the bet, and says so plainly when most of the named reasons point the other way.

## Tests

- `python projects/edge/tests/run.py`: every `unit_*.py` (`unit_loop.py` is the loop: gate, mode lock, window,
  orders, delisting, settlement, drawdown, the reasoning guard, paper cards, no football), then `demo`, then `page`.
- `python projects/edge/tests/run.py loop`: one unit module.
- `python projects/edge/tests/run.py demo`: the real Kalshi demo exchange (balance, status, markets, a resting
  order and its cancel, a crossing order and its fill with the fee checked against `kalshi_fee_usd`). Skipped with
  a note without `KALSHI_DEMO_API_KEY_ID`.
- `python projects/edge/tests/run.py page`: a test server on 8801 (`EDGE_TEST=1`, temp data and config, the fakes,
  the clock frozen, no Claude), the health and tick smoke checks, then each `t-*.js` in headless Edge at 1536x780
  with a shot in `tests/shots/` and `tests/out/report.json`.
- `python scripts/edge_check.py`: keys (labels only), Kalshi demo and prod reachability, open market count, the
  API-Football quota, Polymarket, imports, the port, `teams.json`, the data folder.

## Rehearsal checklist

`rehearsal_passed` stays false until every box is ticked by Jonathan.

- [x] `python scripts/edge_check.py` clean from his own IP, Polymarket included (2026-10-04: all checks passed; the
      production key accepted, Polymarket answers from this machine).
- [ ] Two match days run in approve mode end to end on paper (dry-run fills, settled from the markets' own results).
- [ ] One settlement whose ledger rows match Kalshi to the cent. Needs a real fill: either a demo key (play money)
      or Jonathan's explicit go for one 1-contract order on the live exchange with dry-run off for that order only.
- [ ] A forced delisting and a forced state block handled live (the card delisted, the halt on, Resume works).
- [ ] The backtest report read together.
- [ ] The drawdown stop fired once in a dry run and the mode went back to approve.
- [x] The shortcut, the Startup entry, the log and the restart-on-change seen working (2026-10-04, installed and
      restarted twice on edits).

Key status 2026-10-04: Jonathan made a **production** key (saved as `KALSHI_API_KEY` in the repo `.env`; the private
key, an Ed25519 PEM, copied to `~/.monarc/kalshi.pem`). The live exchange accepts it (balance read); the demo
exchange refuses it, since demo keys are separate. There is no demo key. With `env: demo` the agent prices from the
production feed and places nothing; with `env: prod` and `dry_run` on it also reads the real balance and positions
and still places nothing. Only Jonathan flips `env`; the AIOS never turns `dry_run` off.

## What Jonathan does

- Kalshi account: done. Production key wired 2026-10-04 (`KALSHI_API_KEY` plus `~/.monarc/kalshi.pem`). A demo key
  (`KALSHI_DEMO_API_KEY_ID`, `KALSHI_DEMO_PRIVATE_KEY_PATH`, PEM at `~/.monarc/kalshi-demo.pem`) is still useful for
  rehearsing an order round trip with play money; optional (`references/credentials.md`).
- API-Football Pro ($19 a month) and `API_FOOTBALL_KEY`.
- Read the Kalshi fee PDF's sports row once and write the date in `config.json` `fees.schedule_checked`.
- Confirm EPL markets show in his Kalshi app from Maryland, and decide whether to trade sports contracts there while
  Maryland v. Kalshi is pending (his call, recorded when he funds the account).
- Fund the bankroll ($1,000) and tick the rehearsal checklist.

## Findings so far

- `backtest/2026-10-04.md`: the stats model lands 1 to 2 points of log loss behind Pinnacle's close and never ahead;
  the 7-point rule against the close lost 14.8% over 625 simulated bets, worse than random.
- `backtest/kalshi-vs-books-2026-10-04.md`: on Kalshi's first 50 settled Premier League matches, Kalshi's kickoff
  price sits within a point of the books (3% of sides 3+ points off, none 5+); the gap is 2 points on average six days
  out and 27% of sides are 3+ off then; Kalshi runs 1 to 2 points dear on favorites and about fair on draws.
- `backtest/replay-current-rules-2026-10-04.md`: the current rules replayed hour by hour over those 50 matches with
  the model fitted as of each date: 24 bets, won 42%, down 8.3% at 6 to 8% stakes with a 27% worst drop (the 25% stop
  would have fired); the same bets at 2% lose 0.8%; CLV negative on 71% of bets in every variant.
- `backtest/strategies-top5-2026-10-04.md`: 26 strategies on 19,763 matches across the top five leagues. Nothing
  reaches t 3. The sharp-against-soft family (a book's price 2+ points under Pinnacle fair) is positive at every
  threshold and in both halves of the decade (+5.4% on 1,905 bets, t 1.8) but needs the best price across many books;
  away favorites +4.1% (t 2.1) is the one rule that passes, barely; every model rule won big in 2019/20 and lost from
  2020 on; home teams lose since 2020.
- `backtest/stakes-and-the-million-2026-10-04.md`: stake share against strategy on the same data. The growth-best
  share is 3.4% for the best rule and under 1% for the model rule; 6 to 8% loses money on every strategy even with a
  real edge. From $2,500 to $1,000,000 with the best rule: 6,000 to 8,000 bets at the full measured edge (34 to 45
  years at the rule's rate in five leagues), 18,000 at a realistic +3%, never at +0.5%.
- `backtest/correlated-parlays-2026-10-04.md`: draw + under 2.5 on one match hits 1.57 times as often as
  independence predicts; at multiplied odds it would return +47% (t 14), every season. No book pays multiplied odds on
  same-match legs any more and Kalshi has no parlays, so it is a proof of the idea, not a trade. Favorite + over is
  the other positive pair (+8 to +15%). Draw + over and favorite + under lose 20 to 50%.
- `backtest/kalshi-combo-pricing-2026-10-04.md`: Kalshi's combined contracts (396 traded two-leg same-game sports
  combos, 879 trades) are priced at the product of their legs (median 1.01), with a markup by how unlikely the combo
  is, not by correlation. Over 356 settled combos buyers paid 31 for what came true 26% of the time. Soccer combos
  have barely traded (three); the draw + under test on Kalshi is untested and is the next step, with Jonathan's go.
- Stat power (ten seasons): strength from results (Elo) 0.44 correlation with goal difference, shots on target
  difference 0.40, goal difference 0.38, head to head 0.30 and useless once strength is in, cards, fouls, rest about 0.

## Not verified yet

- Nothing has run against the real demo exchange (no demo key on this machine): the order reply shapes, the fee per
  fill, and the settlement rows are coded from the `kalshi_api.py` contract and the fakes.
- Kalshi's `expected_expiration_time` sat exactly 3 hours after Polymarket's kickoff on all 19 events checked on
  2026-10-04; the fallback assumes that margin holds. Polymarket's kickoff is preferred whenever it links.
- `kalshi_api.create_order` receives `expires_at` as an ISO 8601 string.
- The Polymarket match link against real slugs and names, and its geoblock from Maryland.
- The real `ModelService` and `run_backtest` outputs through the server (coded against the stated interfaces; the
  page tests will exercise them once the page lands).
- The daily Claude cost estimate uses the model's list price from a table in `edge_reason.py`; the real usage
  numbers come back on every reply and are what is summed.
