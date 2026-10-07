# Which betting rule prints cash and which one is luck (2026-10-04)

Jonathan's question: take a thousand or more past outcomes and test different strategies to see which one, when it
places bets, negates luck and prints cash. Football.

Data: the top five leagues (England, Spain, Germany, Italy, France), 2015/16 to 2025/26, from football-data.co.uk:
19,763 matches, 59,289 outcomes, with closing prices from Pinnacle (the sharp book, 18,907 matches), Bet365 (a soft
book, 12,458) and the best price across every listed book ("Max", 12,459). The model's chances are the England
walk-forward predictions from `2026-10-04-predictions.csv` (2,660 matches, 2019/20 on, never seeing the result).
Every strategy is scored the same way: $1 a bet at the book's price (its fee is inside the price), hit rate, return,
closing line value against Pinnacle's fair chance (power method), a t-test on the per-bet returns, a 2,000-draw
bootstrap for the 5% to 95% band, the two halves of the decade separately, and the bankroll at quarter Kelly under a
2% cap from $1,000. Table: `strategies-top5-2026-10-04.csv`. "Prints cash" needs t at or above 2, a bootstrap band
above zero, and a positive return in both halves.

## The result

| Strategy | Bets | Return per $1 | t | Both halves positive | Verdict |
|---|---|---|---|---|---|
| Best book price 2+ pts under Pinnacle fair (closing) | 1,905 | +5.4% | 1.8 | yes (+12.5%, +3.8%) | positive, not proven |
| Best book price 1+ pts under Pinnacle fair (closing) | 5,801 | +3.4% | 1.8 | yes | positive, not proven |
| Best book price 3+ pts under Pinnacle fair | 706 | +5.0% | 1.1 | yes | positive, not proven |
| Same, no longshots under 20 | 1,812 | +4.6% | 1.6 | yes | positive, not proven |
| Away favorites at the best price | 1,832 | +4.1% | 2.1 | yes (+3.7%, +4.1%) | the one that passes, barely |
| Big favorites, 65%+ | 2,424 | +1.7% | 1.4 | yes | positive, not proven |
| Always the draw | 12,459 | +1.1% | 0.7 | no | luck or nothing |
| Always the away team | 12,459 | +0.8% | 0.4 | yes | luck or nothing |
| Bet365 price 1+ under Pinnacle fair (closing) | 129 | -2.4% | -0.2 | | nothing: Bet365's close is the sharp close |
| Always the home team | 12,459 | -2.1% | -1.6 | no (2020 on: -3.2%, t -2.4) | loses since 2020 |
| Longshots, 15% or less | 3,644 | -1.2% | -0.2 | no | luck or nothing |
| Model 3+ pts over Pinnacle closing (England) | 1,865 | -4.9% | -1.0 | no (2019/20 +14%, then -8.8%) | luck or nothing |
| Model 7+ pts over Pinnacle fair (our old rule) | 842 | -5.8% | -0.8 | no (then -10.8%) | luck or nothing |
| Model 7+ pts over the best price | 894 | +4.7% | 0.6 | no (+41.7% one season, then -2.8%) | luck or nothing |
| Model and Pinnacle both call the best price cheap | 401 | -2.7% | -0.3 | no | luck or nothing |

## Reading

- **Nothing here negates luck outright.** With 26 strategies tested, one t near 2 is what chance alone produces. The
  honest bar is t of 3 or more, or a rule that holds out of sample for years. None reaches it.
- **The only structural edge is the sharp-against-soft family**: buy where some book's price is 2 or more points
  under Pinnacle's fair chance. It is positive at every threshold, positive in both halves of the decade, and its
  closing line value is positive by construction. It is "not proven" only because the per-bet noise is large. The
  catch: it needs the best price across many books at closing time, which one retail account cannot get, and the
  single soft book (Bet365) shows no such gaps at the close. On Kalshi this is exactly the playbook's rule, and it can
  only be tested live with Pinnacle's price on the card.
- **Away favorites** is the one rule that passes the test, barely: +4.1% over 1,832 bets, t 2.1, positive in both
  halves. Its closing line value is only +0.8, so the sharp market does not fully agree there is an edge. A known
  public bias (the crowd overbets home teams), worth a column in the record, not a strategy by itself.
- **The model family is the lesson in luck.** Every model rule shows a big win in its first season (2019/20: +14% to
  +42%) and loses from 2020 on (-3% to -16%). Anyone who had stopped after season one would have believed it. That
  is what "a hundred bets" cannot tell you and a thousand can.
- **Home teams lose money since 2020** (-3.2%, t -2.4): the home advantage shrank with empty grounds and the books
  overcorrected for a while. The draw is priced fairly. Longshots lose, as always.
- **Size still decides survival.** At quarter Kelly under a 2% cap the best rule turns $1,000 into about $3,000 to
  $4,000 over ten seasons with a 40% worst drop; "always home" turns it into $53.

## What this means for Monarc Edge

The number on the card should be Pinnacle's fair chance, not the model's; the floor 2 to 3 points, not 7; the size
quarter Kelly under 2%; longshots under 20 cents out; and the record should carry an "away favorite" column. The one
input missing is Pinnacle's live price (the Odds API key).
