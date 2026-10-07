# Does Kalshi price the correlation into its combined contracts? (2026-10-04)

Kalshi's combos are "multivariate event collections": a collection per game (winner, spread, total, props; for soccer
winner, spread, total, both teams to score) and a combined contract created when someone picks two or more legs. It
resolves Yes only if every leg does. Test: every two-leg, same-game sports combo that has ever traded (396 combos,
879 trades; the first pass with crypto and index pairs removed, since hourly prices mean nothing for 15-minute
markets), each trade's price against the product of the two legs' prices in the same hour (leg candles, the hour's
mid when the book was tight, else its last trade), the legs labeled favorite or underdog by the leg's own price and
over or under by the side taken on the total. Rows: `kalshi-combo-pricing-2026-10-04.csv`.

## Answer: no. It prices near the product, with a markup that follows how unlikely the combo is, not the correlation.

| Winner or spread + total | Combos | Trades | Combo price over product (median) | Settled | Came true | Product said | Price said |
|---|---|---|---|---|---|---|---|
| Favorite + over (legs move together) | 42 | 64 | 0.97 | 36 | 22% | 44% | 41% |
| Favorite + under (move apart) | 33 | 66 | 0.97 | 22 | 64% | 46% | 47% |
| Underdog + over (move apart) | 43 | 71 | 1.12 | 33 | 6% | 16% | 18% |
| Underdog + under (move together) | 28 | 52 | 1.09 | 19 | 0% | 16% | 15% |

If the correlation were priced, favorite + over and underdog + under would sit above the product and the other two
below. Instead both favorite combos sit 3% under the product and both underdog combos 9 to 12% over it, whichever way
the legs move. That is a longshot markup, not a correlation model.

All 396 combos together: median ratio 1.01 (quarter to three-quarter range 0.98 to 1.28). Over the 356 settled ones:
came true 26% of the time, the product said 29%, the combo price said 31%. Buyers paid about five points more than
reality on average. Most volume is baseball (two-player home-run pairs, spread + total) and NBA.

## What it means

- The engine treats legs as independent. On paper that is the opening the five-league study found: draw + under 2.5
  hits 1.57 times as often as independence predicts, favorite + over 1.15 to 1.18 times.
- In US sports the opening has not paid in this sample: favorite + over came true 22% of the time against 44% implied
  (36 combos; small, and the opposite sign). Nothing to bet on there yet.
- In soccer nobody has traded the combos: three in the whole record. The draw + under test on Kalshi has never been
  run because the contract has never been quoted and bought in size. Combo markets trade thinly (879 trades in
  months) and quotes come from market makers who may not quote at all ("active_quoters" is empty on the open
  collections).

## The next step, which needs Jonathan's go (his key, no order)

Look up or create the "Tie and under 2.5 goals" combo on one Premier League match through the collections API
(`KXMVESPORTSMULTIGAMEEXTENDED` lists `KXEPLGAME`, `KXEPLSPREAD`, `KXEPLTOTAL`, `KXEPLBTTS` legs), read the quote and
its size, and compare it with the product of the Tie price and the under price. Near the product, with size, at
fees that leave room: that is the trade this whole thread has been looking for, and it would be the first one with a
structural reason behind it rather than a model's opinion. Creating the market is not an order; buying it would be.
