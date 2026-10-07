# Kalshi against the books: every settled Premier League market so far (2026-10-04)

Question from Jonathan: are there common gaps between Pinnacle and Kalshi? Data: the 150 sides (50 matches, home,
away, Tie) Kalshi had settled in series `KXEPLGAME` by 2026-10-04, with their hourly price history from the public
API, against football-data.co.uk's closing odds for the same matches with the fee removed (the market average,
`AvgC`; Pinnacle is not in the 2026/27 file). Rows: `kalshi-vs-books-2026-10-04.csv`. Script kept in the session
scratchpad; rerun it when more matches have settled.

## The gap shrinks as kickoff comes

Kalshi's price minus the books' fair chance, in points. Positive means Kalshi is dearer.

| When | Sides | Mean gap | Mean size of gap | Gaps of 3+ points | Gaps of 5+ |
|---|---|---|---|---|---|
| At kickoff | 150 | +0.5 | 0.9 | 3% | 0% |
| 1 hour before | 150 | +0.5 | 1.2 | 5% | 1% |
| 6 hours before | 150 | +0.5 | 1.4 | 11% | 3% |
| 24 hours before | 150 | +0.4 | 1.8 | 18% | 7% |
| 3 days before | 150 | +0.4 | 1.8 | 14% | 6% |
| 6 days before | 150 | +0.1 | 2.1 | 27% | 10% |

At kickoff Kalshi is the books, within a point. Its kickoff price is almost as well calibrated as theirs (log loss
0.619 against 0.614 over 150 sides). The first price appears about 13 days before kickoff.

## Where Kalshi leans (at kickoff)

| Books' fair chance | Sides | Kalshi minus books |
|---|---|---|
| Under 20 | 26 | -0.6 (Kalshi slightly cheap on longshots) |
| 20 to 35 | 72 | +0.3 |
| 35 to 50 | 29 | +0.8 |
| 50 to 65 | 16 | +1.7 |
| Over 65 | 7 | +2.2 (Kalshi dear on favorites) |

By outcome: home +0.7, draw +0.5, away +0.3. Draws are priced about right (mean size 0.6), so the "retail blind spot
on the draw" idea does not show up on Kalshi.

## Did the cheap sides pay?

Buy every side Kalshi priced 3 or more points under the books' closing fair chance, $1 a contract, taker fee:
6 days out 17 sides +25%, 3 days out 7 sides +78%, 24 h out 8 sides +42%. The dear sides (3+ over), bought anyway:
24 sides -21%, 14 sides -15%, 19 sides -24%. Right direction, tiny samples, and it uses the closing price as the
yardstick, which nobody knows days ahead. A real signal needs the sharp price at the same moment (the Odds API key).

## What it means for the agent

- A 7-point gap against a sharp price does not exist on Kalshi at kickoff. The big gaps the model showed were the
  model being wrong. The playbook's 3-point floor is the realistic one.
- The soft window is days out, not the lineup hour: by an hour before kickoff the two prices agree. Part of the early
  gap is news that moved both prices later, so the test is Kalshi against Pinnacle at the same time, not against the
  close.
- Kalshi runs about half a point dear overall and 1 to 2 points dear on favorites. Buying favorites on Kalshi pays a
  tax; longshots and the No side of favorites are where the price is fair or slightly cheap.
- These are 50 matches from the first five weeks of Kalshi's Premier League markets. Rerun after each month.
