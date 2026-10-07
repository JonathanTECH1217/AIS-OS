"""Monarc Books: the money book in Airtable, run from the command line.

  python scripts/books.py --check                      key source, base reachable, row counts
  python scripts/books.py stripe-sync [--since DATE]   charges, refunds, fees, payouts -> Transactions (dedupe on id)
  python scripts/books.py import-bank <csv> [--account "Business checking"] [--write]
                                                       bank export -> Transactions; proposes a label per row; --write saves
  python scripts/books.py month-end YYYY-MM [--write]  the fifteen-minute tally; --write saves the Months row
  python scripts/books.py spend-sync [--days 30] [--write]
                                                       money out the AIOS can read itself -> Transactions: Google Ads
                                                       spend by campaign and day (the Ads API), and the known charges in
                                                       projects/books/known-spend.json; dedupe on External id; --write saves
                                                       (Jonathan, 2026-10-06: "update my spend in the CRM to reflect any
                                                       money out or in"). A bank row for Google Ads is then skipped by
                                                       import-bank in a month that has these daily rows, so it is not counted twice.

Base id: projects/crm/config.json -> "books_base_id" (or --base). Tables by name: Accounts, Transactions, Invoices, Months.
Keys through outreach_common.load_env: AIRTABLE_PAT (must have access to the Books base), STRIPE_SECRET_KEY (optional,
for stripe-sync; without it the command explains what to add). Money rules: config.json -> "books" -> {"salary": n,
"invest_pct": n}; until set, the tally says so instead of guessing.

bike-method-phase: 1 (run by hand, watch everything). Nothing is written without --write except stripe-sync rows,
which carry the Stripe id and can never double.
"""
import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from outreach_common import ROOT, get_secret, load_env  # noqa: E402
from crm_server import Airtable, AirtableError  # noqa: E402

CONFIG = ROOT / "projects" / "crm" / "config.json"

# counterparty keyword -> account name. First match wins. Extend as the bank rows teach you.
LABEL_RULES = [
    (r"stripe", "Stripe balance"),
    (r"google.*ads|adwords", "Advertising"),
    (r"meta|facebook|instagram|linkedin", "Advertising"),
    (r"airtable|proton|hostinger|docuseal|anthropic|openai|google (workspace|cloud)|adobe|zoom|notion", "Software"),
    (r"upwork|fiverr|contractor|freelanc", "Contractors"),
    (r"united|delta|american air|southwest|amtrak|uber|lyft|hotel|marriott|hilton", "Travel"),
    (r"restaurant|cafe|coffee|starbucks|chipotle|grill|pizza|doordash", "Meals"),
    (r"fee|service charge|wire", "Fees"),
    (r"transfer to .*savings|owner|draw", "Owner draw"),
]


def load_config():
    return json.loads(CONFIG.read_text(encoding="utf-8")) if CONFIG.exists() else {}


def client(base_id):
    token = get_secret("AIRTABLE_PAT", required=True, hint="Add it to %USERPROFILE%\\.monarc\\secrets.env.")
    return Airtable(token, base_id)


def rows(air, table, formula=None):
    recs, _ = air.list_all(table, formula=formula)
    return [dict(r["fields"], id=r["id"]) for r in recs]


def money(v):
    return f"${v:,.2f}"


# ---------------------------------------------------------------- commands

def cmd_check(air, base_id):
    env, src = load_env()
    print(f"AIRTABLE_PAT: found in {src['AIRTABLE_PAT']}" if env.get("AIRTABLE_PAT") else "AIRTABLE_PAT: MISSING")
    print(f"STRIPE_SECRET_KEY: {'found in ' + src['STRIPE_SECRET_KEY'] if env.get('STRIPE_SECRET_KEY') else 'not set (stripe-sync will explain)'}")
    print(f"Books base: {base_id}")
    try:
        meta = air.meta()
    except AirtableError as e:
        sys.exit(f"Cannot read the Books base: {e}. Add the base to the token's access list at airtable.com/create/tokens.")
    names = [t["name"] for t in meta.get("tables", [])]
    print(f"Tables: {', '.join(names)}")
    for t in ("Accounts", "Transactions", "Invoices", "Months"):
        if t in names:
            print(f"  {t}: {len(rows(air, t))} rows")
    cfg = load_config().get("books", {})
    print(f"Money rules: salary {cfg.get('salary') if cfg.get('salary') is not None else 'not set'}, "
          f"invest {str(cfg.get('invest_pct')) + '%' if cfg.get('invest_pct') is not None else 'not set'}")


def propose_label(counterparty, amount, accounts):
    text = (counterparty or "").lower()
    names = {a.get("Name"): a for a in accounts}
    for pat, name in LABEL_RULES:
        if re.search(pat, text) and name in names:
            return name
    if amount > 0:
        return "Management fees" if "Management fees" in names else None
    return None


def cmd_import_bank(air, path, account, write):
    p = Path(path)
    if not p.exists():
        sys.exit(f"No file at {p}")
    accounts = rows(air, "Accounts")
    existing = {t.get("External id") for t in rows(air, "Transactions") if t.get("External id")}
    with open(p, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        cols = {c.lower().strip(): c for c in reader.fieldnames or []}
        date_col = next((cols[c] for c in cols if c in ("date", "posted date", "transaction date", "posting date")), None)
        desc_col = next((cols[c] for c in cols if c in ("description", "memo", "payee", "name", "details")), None)
        amt_col = next((cols[c] for c in cols if c in ("amount", "transaction amount")), None)
        debit_col = next((cols[c] for c in cols if c in ("debit", "withdrawal", "withdrawals", "money out")), None)
        credit_col = next((cols[c] for c in cols if c in ("credit", "deposit", "deposits", "money in")), None)
        if not date_col or not desc_col or not (amt_col or (debit_col and credit_col)):
            sys.exit(f"Could not find date, description, and amount columns. Header: {reader.fieldnames}")
        new, skipped = [], 0
        for r in reader:
            d = r[date_col].strip()
            for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m/%d/%y", "%d/%m/%Y"):
                try:
                    d = datetime.strptime(d, fmt).date().isoformat()
                    break
                except ValueError:
                    continue
            desc = r[desc_col].strip()
            if amt_col:
                amt = float(str(r[amt_col]).replace("$", "").replace(",", "").replace("(", "-").replace(")", "") or 0)
            else:
                deb = float(str(r.get(debit_col) or "0").replace("$", "").replace(",", "") or 0)
                cre = float(str(r.get(credit_col) or "0").replace("$", "").replace(",", "") or 0)
                amt = cre - deb
            ext = "bank:" + hashlib.sha1(f"{d}|{desc}|{amt:.2f}".encode("utf-8")).hexdigest()[:16]
            if ext in existing:
                skipped += 1
                continue
            # the Ads API already put this month's Google Ads spend in the book day by day (spend-sync): the card
            # charge for it is the same money and is not counted twice
            if re.search(r"google.*ads|adwords", desc.lower()) and any(x.startswith("gads:") and f":{d[:7]}-" in x for x in existing):
                print(f"  {d}  {amt:>10,.2f}  {desc[:40]:40}  -> skipped: Google Ads spend for {d[:7]} is already in the book by day")
                skipped += 1
                continue
            label = propose_label(desc, amt, accounts)
            new.append({"Date": d, "Memo": desc[:120], "Counterparty": desc[:80], "Amount": round(amt, 2),
                        "Source": "Bank CSV", "External id": ext, "_label": label})
    print(f"{len(new)} new rows, {skipped} already in the book.")
    for t in new:
        print(f"  {t['Date']}  {t['Amount']:>10,.2f}  {t['Counterparty'][:40]:40}  -> {t['_label'] or 'NO LABEL, pick one'}")
    if not write:
        print("Dry run. Add --write to save these rows. Rows without a label are saved unlabeled for you to pick in Airtable.")
        return
    acct_ids = {a.get("Name"): a["id"] for a in accounts}
    payload = []
    for t in new:
        f = {k: v for k, v in t.items() if not k.startswith("_")}
        if t["_label"] and t["_label"] in acct_ids:
            f["Account"] = [acct_ids[t["_label"]]]
        payload.append(f)
    created = air.create("Transactions", payload) if payload else []
    print(f"saved {len(created)} rows.")


def cmd_stripe_sync(air, since):
    key = get_secret("STRIPE_SECRET_KEY")
    if not key:
        sys.exit("STRIPE_SECRET_KEY is not in secrets.env. Stripe, Developers, API keys: a restricted key with read on "
                 "Charges, Balance transactions, Payouts, Invoices is enough. Until then, stripe-sync has nothing to read.")
    H = {"Authorization": f"Bearer {key}"}
    existing = {t.get("External id") for t in rows(air, "Transactions") if t.get("External id")}
    accounts = {a.get("Name"): a["id"] for a in rows(air, "Accounts")}
    params = {"limit": 100}
    if since:
        params["created[gte]"] = int(datetime.fromisoformat(since).timestamp())
    new = []
    url = "https://api.stripe.com/v1/balance_transactions"
    while url:
        r = requests.get(url, headers=H, params=params, timeout=30)
        if r.status_code != 200:
            sys.exit(f"Stripe {r.status_code}: {r.text[:200]}")
        data = r.json()
        for bt in data.get("data", []):
            ext = "stripe:" + bt["id"]
            if ext in existing:
                continue
            amt = bt["amount"] / 100.0
            fee = bt.get("fee", 0) / 100.0
            d = date.fromtimestamp(bt["created"]).isoformat()
            kind = bt.get("type", "")
            label = "Management fees" if kind == "charge" else ("Fees" if kind in ("stripe_fee",) else ("Stripe balance" if kind == "payout" else None))
            row = {"Date": d, "Memo": f"Stripe {kind}: {bt.get('description') or bt['id']}"[:120], "Counterparty": "Stripe",
                   "Amount": round(amt, 2), "Source": "Stripe", "External id": ext}
            if label in accounts:
                row["Account"] = [accounts[label]]
            new.append(row)
            if fee and kind == "charge":
                new.append({"Date": d, "Memo": f"Stripe fee on {bt['id']}", "Counterparty": "Stripe", "Amount": round(-fee, 2),
                            "Source": "Stripe", "External id": ext + ":fee", **({"Account": [accounts["Fees"]]} if "Fees" in accounts else {})})
        url = None
        if data.get("has_more") and data.get("data"):
            params["starting_after"] = data["data"][-1]["id"]
            url = "https://api.stripe.com/v1/balance_transactions"
    print(f"{len(new)} new Stripe rows.")
    if new:
        air.create("Transactions", new)
        print("saved.")


def cmd_month_end(air, month, write):
    if not re.fullmatch(r"\d{4}-\d{2}", month):
        sys.exit("month looks like 2026-09")
    accounts = {a["id"]: a for a in rows(air, "Accounts")}
    txs = [t for t in rows(air, "Transactions") if (t.get("Date") or "").startswith(month)]
    rev = cost = 0.0
    by_acct = {}
    unlabeled = 0
    for t in txs:
        amt = float(t.get("Amount") or 0)
        aid = (t.get("Account") or [None])[0]
        a = accounts.get(aid)
        if not a:
            unlabeled += 1
            continue
        by_acct[a["Name"]] = by_acct.get(a["Name"], 0.0) + amt
        if a.get("Type") == "Revenue":
            rev += amt
        elif a.get("Type") == "Cost":
            cost += -amt
    profit = rev - cost
    cfg = load_config().get("books", {})
    salary = cfg.get("salary")
    invest_pct = cfg.get("invest_pct")
    invested = round(profit * invest_pct / 100.0, 2) if invest_pct is not None and profit > 0 else 0.0
    open_inv = [i for i in rows(air, "Invoices") if i.get("Status") in ("Sent", "Late")]
    print(f"Month end {month}")
    print(f"  Revenue   {money(rev)}")
    print(f"  Costs     {money(cost)}")
    print(f"  Profit    {money(profit)}")
    print(f"  Salary    {money(salary) if salary is not None else 'rule not set (config.json books.salary)'}")
    print(f"  Invest    {money(invested) + f' ({invest_pct}% of profit)' if invest_pct is not None else 'rule not set (config.json books.invest_pct)'}")
    print(f"  Open invoices: {len(open_inv)} for {money(sum(float(i.get('Amount') or 0) for i in open_inv))}")
    print(f"  Rows: {len(txs)} this month, {unlabeled} without a label, "
          f"{sum(1 for t in txs if not t.get('Reconciled'))} not yet matched to the statement")
    for name, v in sorted(by_acct.items(), key=lambda kv: kv[1]):
        print(f"    {name:24} {v:>12,.2f}")
    if not write:
        print("Dry run. Add --write to save the Months row.")
        return
    existing = next((m for m in rows(air, "Months") if m.get("Month") == month), None)
    fields = {"Month": month, "Revenue": round(rev, 2), "Costs": round(cost, 2), "Profit": round(profit, 2),
              "Salary paid": float(salary) if salary is not None else None, "Invested": invested, "Tally done": True}
    fields = {k: v for k, v in fields.items() if v is not None}
    if existing:
        air.update("Months", [(existing["id"], fields)])
        print("Months row updated.")
    else:
        air.create("Months", [fields])
        print("Months row created.")


KNOWN_SPEND = ROOT / "projects" / "books" / "known-spend.json"


def google_ads_spend(days):
    """Google Ads spend by campaign and day from the Ads API, money out, over the last N days. [] when nothing is
    published or the login is missing; the reason is printed."""
    try:
        import ads_publish as ap
    except Exception as e:  # noqa: BLE001
        print(f"  Google Ads: not read ({type(e).__name__}: {str(e)[:120]})")
        return []
    docs = [d for d in ap.all_campaigns() if (d.get("google") or {}).get("campaign")]
    if not docs:
        print("  Google Ads: nothing published yet, no spend to read.")
        return []
    try:
        g = ap._google()
        rows_ = g.search("SELECT campaign.id, campaign.name, segments.date, metrics.cost_micros FROM campaign "
                         f"WHERE segments.date DURING LAST_{days}_DAYS AND metrics.cost_micros > 0")
    except Exception as e:  # noqa: BLE001
        print(f"  Google Ads: not read ({type(e).__name__}: {str(e)[:160]})")
        return []
    out = []
    for r in rows_:
        cid, d = str(r["campaign"]["id"]), r["segments"]["date"]
        cost = round(int(r.get("metrics", {}).get("costMicros", 0) or 0) / 1e6, 2)
        if cost <= 0:
            continue
        out.append({"Date": d, "Memo": f"Google Ads, {r['campaign'].get('name', cid)}, {d}"[:120], "Counterparty": "Google Ads",
                    "Amount": -cost, "Source": "Manual", "External id": f"gads:{cid}:{d}", "_label": "Advertising",
                    "Notes": "From the Ads API by day (spend-sync). The card charge for this month is skipped by import-bank."})
    print(f"  Google Ads: {len(out)} campaign-days with spend in the last {days} days, {money(sum(-x['Amount'] for x in out))}.")
    return out


def cmd_spend_sync(air, days, write):
    """Money out the AIOS can read itself, into Transactions. Dry run unless --write."""
    known = json.loads(KNOWN_SPEND.read_text(encoding="utf-8")).get("rows", []) if KNOWN_SPEND.exists() else []
    for k in known:
        k.setdefault("Source", "Manual")
        k["_label"] = k.pop("Account", None)
    print(f"  Known charges on file (projects/books/known-spend.json): {len(known)}, {money(sum(-float(k['Amount']) for k in known))}.")
    candidates = google_ads_spend(days) + known
    try:
        existing = {t.get("External id") for t in rows(air, "Transactions") if t.get("External id")}
        accounts = {a.get("Name"): a["id"] for a in rows(air, "Accounts")}
        reachable = True
    except AirtableError as e:
        existing, accounts, reachable = set(), {}, False
        print(f"  The Books base cannot be read ({str(e)[:80]}...). Add \"Monarc Books\" to the token at airtable.com/create/tokens. "
              "Dry run only; nothing can be saved.")
    new = [c for c in candidates if c["External id"] not in existing]
    print(f"{len(new)} new rows, {len(candidates) - len(new)} already in the book.")
    for t in sorted(new, key=lambda x: x["Date"]):
        print(f"  {t['Date']}  {t['Amount']:>10,.2f}  {t['Counterparty'][:24]:24}  {t['Memo'][:50]:50}  -> {t.get('_label') or 'NO LABEL'}")
    if not write or not reachable:
        if reachable:
            print("Dry run. Add --write to save these rows.")
        return
    payload = []
    for t in new:
        f = {k: v for k, v in t.items() if not k.startswith("_")}
        if t.get("_label") in accounts:
            f["Account"] = [accounts[t["_label"]]]
        payload.append(f)
    created = air.create("Transactions", payload) if payload else []
    print(f"saved {len(created)} rows.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", nargs="?", default="check", choices=["check", "stripe-sync", "import-bank", "month-end", "spend-sync"])
    ap.add_argument("--days", type=int, default=30, help="spend-sync: how far back the Ads API is read")
    ap.add_argument("arg", nargs="?", help="csv path for import-bank, YYYY-MM for month-end")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--base")
    ap.add_argument("--since")
    ap.add_argument("--account", default="Business checking")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    base_id = args.base or load_config().get("books_base_id")
    if not base_id:
        sys.exit("No Books base id. Set books_base_id in projects/crm/config.json or pass --base.")
    air = client(base_id)
    cmd = "check" if args.check else args.command
    if cmd == "check":
        cmd_check(air, base_id)
    elif cmd == "stripe-sync":
        cmd_stripe_sync(air, args.since)
    elif cmd == "import-bank":
        if not args.arg:
            sys.exit("import-bank needs the csv path")
        cmd_import_bank(air, args.arg, args.account, args.write)
    elif cmd == "month-end":
        if not args.arg:
            sys.exit("month-end needs YYYY-MM")
        cmd_month_end(air, args.arg, args.write)
    elif cmd == "spend-sync":
        cmd_spend_sync(air, args.days, args.write)


if __name__ == "__main__":
    main()
