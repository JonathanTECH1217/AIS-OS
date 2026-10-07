# projects/edge/data

Monarc Edge's working data. Git tracks only this README.

- `edge.sqlite`: fixtures, features, model runs, market snapshots, cards, orders, fills, settlements, the ledger,
  halts, backtests (schema in `scripts/edge_common.py`).
- `cache/`: raw API responses (football, polymarket, kalshi), one JSON per request.
- `fd/`: football-data.co.uk season CSVs (`E0-2526.csv` and so on).
- `dry-run.jsonl`: every order the agent would have sent while `dry_run` is on.
- `football-budget.json`: API-Football calls used today.

`EDGE_DATA` points the scripts at another folder (the tests use a temp copy).
