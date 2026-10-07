# Replay of the current rules over Kalshi's settled Premier League markets (2026-10-04)

Jonathan's question: using our current logic, blindly replay the bets that should have been made and see whether we
would be in the green, sized as a percentage of bankroll. Data: every Premier League market Kalshi had settled by
2026-10-04 (50 matches, 21 August to 20 September 2026, 150 sides) with its hourly book from the public API. The
model was refitted as of each match date so it never saw the result. Rules as configured: six sides a match from the
model's chance against Kalshi's book after the taker fee, green at 7 points, yellow at 10, busy floor 10,000 contracts
and a 2 cent spread, one position a match (the largest green side the first hour it qualifies), stake 6% of the
running bankroll at 7 points rising to 8% at 17. Bets: `replay-current-rules-2026-10-04.csv`.

| Variant | Bets | Won | Staked | P&L | Bankroll | Worst drop | Mean CLV | CLV positive |
|---|---|---|---|---|---|---|---|---|
| Current rules (6 to 8% stakes) | 24 | 42% | $1,754 | -$83 | $1,000 to $917 (-8.3%) | 27.4% | -1.4 pts | 29% |
| Same, skipping yellow (10+) bets | 19 | 37% | $1,382 | +$56 | +5.6% | 26.8% | -1.1 pts | 26% |
| Same bets at a flat 2% of bankroll | 24 | 42% | $503 | -$8 | -0.8% | 8.6% | -1.4 pts | 29% |
| 3-point floor against the model, 2% | 38 | 45% | $773 | -$35 | -3.5% | -1.7 pts | 21% |

By gap size under the current rules: 7 to 10 points, 11 bets, -$182; 10 to 15, 10 bets, +$194; 15 and up, 3 bets,
-$95. By side: No 18 bets +$168, Yes 6 bets -$251. Median time of the bet: 147 hours (6 days) before kickoff, because
the gaps are widest when a market lists and the agent takes the first hour a side qualifies.

## Reading

- Not in the green. Down 8% on 24 bets, and the 27% drop from the high would have tripped the 25% stop in week three.
- The tell is CLV, not the P&L. On 71% of the bets Kalshi's price had moved against us by kickoff, by 1.4 points on
  average. A real edge shows the opposite. The one profitable variant (skipping yellow, +5.6%) still has negative CLV
  and a 37% hit rate: that is a coin that landed well, not a method.
- Size did what it was warned it would do: the same 24 bets at 2% of bankroll lose 0.8% with a 9% worst drop; at 6 to
  8% they lose 8% with a 27% worst drop.
- 24 bets is not 100. At Kalshi's current Premier League volume that takes about four more months, or a second
  league. The paper book keeps collecting either way.
- What the rules do today: bet early (6 days out) on what the model calls cheap, which is exactly where the market
  later disagrees most. The playbook's version (Pinnacle's fair price as the yardstick, 3-point floor, quarter Kelly
  under 2%) has not been replayed because Pinnacle's live prices are not on this machine.
