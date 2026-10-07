# Correlated two-leg parlays on one match (2026-10-04)

Jonathan's question: what about parlay strategies with correlated bets. Test: match winner x over/under 2.5 goals on
the same match, paid at the multiplied odds a book pays when it treats the legs as independent. Top five leagues,
2015/16 to 2025/26, 11,537 matches with both prices at Pinnacle closing, 12,459 at the best closing price across
books. "Correlation" is how often both legs hit divided by what independence predicts (1.0 = none).

| Parlay | Both hit | Multiplied price implies | Correlation | Return per $1 (Pinnacle) | Return (best price) | t |
|---|---|---|---|---|---|---|
| Draw + under 2.5 | 18.7% | 13.1% | 1.57 | +46.9% | +58.1% | 14 to 17 |
| Home win + over 2.5 | 26.9% | 24.6% | 1.18 | +7.9% | +14.8% | 4 to 7 |
| Away win + over 2.5 | 19.4% | 17.3% | 1.15 | +6.6% | +12.6% | 3 to 5 |
| Away win + under 2.5 | 12.4% | 15.9% | 0.83 | -18.2% | -10.6% | |
| Home win + under 2.5 | 16.0% | 21.4% | 0.79 | -26.6% | -21.2% | |
| Draw + over 2.5 | 6.7% | 13.5% | 0.50 | -50.9% | -47.9% | |

Draw + under 2.5 at multiplied Pinnacle odds is positive in every season (+36% to +61%) and in every strength band
(+38% to +79%; biggest when one side is a huge favorite, because a draw there is almost always 0-0 or 1-1). The single
legs on their own all lose the fee (-2% to -5%).

## Why this does not print cash today

- No book pays multiplied odds on two legs of the same match any more, for exactly this reason. Pinnacle does not
  offer same-match parlays at all. The books that do (the US "same game parlay" engines) price the correlation into
  the combined odds, and they limit or close accounts that win.
- Kalshi has no parlays. Buying "Tie" and, if it existed, "under 2.5" as two contracts pays each at its own price. The
  correlation adds no edge; it only makes the two positions win and lose together.
- Where a residue survives, by the published accounts and practitioners: same-game-parlay engines on player props and
  less common combinations, where the correlation model is weaker, at small limits, until the account is restricted.

## What Kalshi actually lists (checked 2026-10-04, 3,958 sports series on the public API)

- Combined-outcome contracts exist, but not for soccer: `KXNCAAMBSGP` (College Basketball Same Game Parlay),
  `KXNFLCOMBO` (NFL Combo), `KXNBAPREPACK3ML` (3-leg basketball combo), `KXNCAAFPREPACKSGP` (college football
  pre-pack). Whether Kalshi prices those at the product of the legs or with the correlation inside is the next
  question to answer with data, in American sports, when there is time for it.
- Premier League has more than the match winner: `KXEPLTOTAL` (total goals), `KXEPLSPREAD`, `KXEPLTEAMTOTAL`,
  `KXSOCCERBTTS` and `KXEPL1HBTTS` (both teams to score), `KXEPLCORNERS`, `KXEPL1HSCORE` (first-half correct score),
  `KXEPL1HTOTAL`, `KXEPL2HTOTAL`, `KXEPL2HSPREAD`. Separate contracts, each paid at its own price: holding Tie and
  under 2.5 together gives no multiplied payout and no correlation edge, only two positions that move together.

## The one actionable version

If a venue ever lists a single combined contract ("draw and under 2.5", "team wins and over") priced near the product
of the two single prices, that contract is worth about 1.5 times its price on the draw-under pair and 1.15 to 1.2
times on the favorite-over pairs. Check the price against the product; if it is near the product, buy it.
