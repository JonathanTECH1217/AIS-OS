# Stake size against strategy, and the road from $2,500 to $1,000,000 (2026-10-04)

Jonathan's questions: with "buy where the best book's price is 2+ points under Pinnacle's fair chance", how many bets
does it take $2,500 to reach $1,000,000; and simulate betting different percentages of bankroll across the strategies.
Method: each strategy's real bet-by-bet returns (top five leagues, 2015/16 to 2025/26, best closing price across books;
the model rule on England) drawn at random in sequence, compounded at a fixed share of the bankroll, 400 runs of 1,000
bets per share. The growth-best share (Kelly) is the share that maximises average log growth over the rule's own
returns. Script in the session scratchpad.

## Share of bankroll, by strategy (median bankroll multiple after 1,000 bets; worst drop; how often the pot halved)

| Strategy (edge per $1, hit rate, Kelly share) | 1% | 2% | 3% | 5% | 8% | 10% |
|---|---|---|---|---|---|---|
| Best price 2+ under Pinnacle fair (+5.4%, 49%, Kelly 3.4%) | 1.61x, 26%, halved 2% | 2.24x, 46%, 39% | 2.64x, 63%, 83% | 2.38x, 85%, 99% | 0.71x, 97% | 0.16x, 99% |
| Best price 1+ (+3.4%, 44%, Kelly 1.7%) | 1.26x, 34%, 11% | 1.30x, 58%, 74% | 1.09x, 75%, 98% | 0.46x | 0.04x | 0.00x |
| Best price 3+ (+5.0%, 53%, Kelly 3.9%) | 1.59x, 24%, 0% | 2.20x, 44%, 33% | 2.70x, 60%, 78% | 2.76x, 82%, 100% | 1.13x, 96% | 0.34x |
| Away favorites (+4.1%, 63%, Kelly 6.0%) | 1.45x, 17%, 0% | 1.96x, 33%, 7% | 2.48x, 46%, 38% | 3.23x, 66%, 91% | 2.86x, 86% | 1.87x, 93% |
| Big favorites 65%+ (+1.7%, 74%, Kelly 4.5%) | 1.18x, 15% | 1.35x, 29%, 6% | 1.49x, 40%, 26% | 1.61x, 60%, 77% | 1.33x, 81% | 0.95x |
| Always the draw (+1.1%, 25%, Kelly 0.3%) | 0.89x, 49% | 0.59x, 78% | 0.29x | 0.03x | 0 | 0 |
| Always the home team (-2.1%, 43%, none) | 0.72x | 0.43x | 0.21x | 0.03x | 0 | 0 |
| Model 7+ over best price, England (+4.7%, 24%, Kelly 0.9%) | 1.17x, 49%, 47% | 0.87x, 78%, 99% | 0.44x | 0.04x | 0 | 0 |

Readings:
- The right share depends on the edge AND the odds. A rule that wins 63% of the time at short odds (away favorites)
  can carry 5 to 6%; a rule that wins 24% at long odds (the model) cannot carry 2% even with a positive edge, because
  the swings wipe it out. "Growth per bet" turns negative above Kelly for every rule.
- Betting above the growth-best share turns a winning rule into a losing one. The best rule at 8% of bankroll loses
  29% of the pot over 1,000 bets despite a real +5.4% edge; at 10% it loses 84%.
- Jonathan's 6 to 8% sits above Kelly for every strategy on this list. On the best rule it is the losing side of the
  curve.
- Halving the pot at some point is normal at 3% and up, even with an edge. That is why the 25% stop rule exists.
- Draws and home teams have no positive share: every size loses.

## From $2,500 to $1,000,000 with the best rule

The rule fires about 173 times a season across five leagues (1,905 bets in 11 seasons). Edge shaved as a flat haircut
per $1 staked (a worse price on every bet), which is how the real world shaves it: limits, slower prices, one account.

| Edge you really get | Share | Median bets | 10% to 90% | Years at 173 bets a season |
|---|---|---|---|---|
| +5.4% as measured | 1% | 12,900 | 9,400 to 16,700 | 74 |
| +5.4% as measured | 2% | 7,800 | 4,600 to 12,600 | 45 |
| +5.4% as measured | 3% | 6,000 | 3,200 to 11,500 | 34 |
| +5.4% as measured | 5% | 5,500 | 2,200 to 16,100 | 32 |
| about +3% | 2% | 18,200 | 8,400 to 40,200 | 105 |
| about +3% | 5% | mostly never (83% of runs) | | |
| about +1.5% | 2% | 52,000, and 57% never | | 300 |
| about +0.5% | any | never | | |

Readings:
- Even at the full measured edge and the growth-best share, it is 6,000 to 8,000 bets. Five leagues supply 173 a
  year. Every league and sport with a sharp line might supply ten times that; then it is 4 to 5 years at the full
  edge, and the full edge is the optimistic in-sample number that assumes the best price across every book at close.
- At a realistic retail edge of 1.5 to 3%, the million is 18,000 to 50,000 bets: a lifetime, or never.
- Compounding is slow because both numbers are small: 2% of the pot at a 5% edge grows the pot about 0.08% a bet. The
  money in this game is made by volume and survival, not by any one bet.

## Away favorites at 5% of bankroll (Jonathan's pick), stressed

- The +4.1% exists only at the best price across every book. The same bets at Bet365: -1.2%. At Pinnacle: +0.2%.
  At the average book: 0.0%. The "away favorite edge" is line shopping, not the away favorite.
- By league: Italy +13.7% carries it; England -0.9%, France +1.0%, Germany +2.2%, Spain +2.4%. By season: 6 of 7
  positive, 2022/23 -2.4%. By size: favorites over 80% lose (-3.2%).
- On Kalshi, which runs about 1.7 points dear on favorites and charges the taker fee, the same rule is worth about
  +0.7% at best.

| Edge you really get | 2% | 3% | 5% |
|---|---|---|---|
| +4.1% as measured (best price) | 1.98x, worst drop 32%, 6% of runs halve | 2.52x, 45%, 35% halve | 3.33x, 66%, 89% halve, every run hits the 25% stop |
| +2% (shaved for picking the best of 26) | 1.31x, 40% | 1.36x, 55% | 1.17x, 77%, 98% halve |
| +1% (what Pinnacle's own close implies) | 1.07x | 1.01x | 0.72x, 80% drop |
| +0.7% (Kalshi: dear on favorites, plus fee) | 1.01x | 0.92x | 0.62x, 80% drop, all runs halve |

At 5% the growth-best share is already behind you unless the full in-sample edge is real, and even then every run
hits the 25% stop and nine in ten halve the pot. At the honest edge, 5% loses money.
