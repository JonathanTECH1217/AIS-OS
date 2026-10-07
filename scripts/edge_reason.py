"""Monarc Edge reasoning writer (2026-10-04): the two to four sentences under a green card.

Claude writes the words, never the number. The card's model_p, prices, gap and stake are set before the call and the
reply can only fill `reasoning` and add `flags`; nothing here touches model_p. The prompt hands over the fixture, our
three chances, the ratings, the top five contributions, both prices, the fee, the break-even, the gap, the stake and
count, the Polymarket mid and how it reads, the lineup status and the settlement rule. The model may cite only those.

Model id: config `claude.model`; when empty, the cheapest current Claude model, `claude-haiku-4-5` ($1 in, $5 out per
million tokens, checked against the claude-api skill's model table on 2026-10-04; references/anthropic-api.md names
only Opus 5, so the id was not confirmed there). max_tokens 300, no thinking. Spend is summed per UTC day in kv
`claude.cost.<date>` from the usage tokens at the model's price and held under `claude.max_usd_per_day`. Past the cap,
with EDGE_NO_CLAUDE=1, with `claude.on` false, without a key, or on any error, the card gets a template built from the
same numbers, so a card always has text.

  python scripts/edge_reason.py        print the template for a sample card (no model call)
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import edge_common as ec  # noqa: E402

MODEL_DEFAULT = "claude-haiku-4-5"
PRICES = {"claude-haiku-4-5": (1.0, 5.0), "claude-sonnet-5": (2.0, 10.0), "claude-sonnet-4-6": (3.0, 15.0),
          "claude-opus-5": (5.0, 25.0), "claude-opus-4-8": (5.0, 25.0)}   # $ per million tokens, in and out
MAX_TOKENS = 300
EST_COST = 0.01       # the room one call needs under the daily cap before it is tried

SCHEMA = {"type": "object",
          "properties": {"reasoning": {"type": "string"},
                         "flags": {"type": "array", "items": {"type": "string"}}},
          "required": ["reasoning", "flags"], "additionalProperties": False}

SYSTEM = """You finish the note under a betting card for its owner, Jonathan. The opening (what we think, what Kalshi's \
price says, the gap, the risk and the win) is already written by code and given to you as "lead". You add the rest. \
Never repeat, restate or change a number from the lead. He asked for a sixth grader's view: short sentences, everyday \
words, no trade words. Never write "break-even", "mid", "ask", "bid", "contracts", "second witness", "model", \
"probability", "edge" or "stake". No em dashes.

Write two to four short sentences:
1. "Why we think so: ..." with one to three plain reasons from "contributions" (each has a name and an effect in \
points; a positive effect helps the home team). For each reason say which way it cuts for THIS bet ("bet_words"), like \
"Chelsea's defense is a bit weaker than Bournemouth's attack, which helps this bet" or "playing at home helps \
Chelsea, which goes against this bet". If the reasons mostly go against the bet, add: "Most of what we can name \
points the other way; the number comes from both teams' results over the season, so treat it with care." If the \
contributions are empty, write "Why we think so: each team's strength from this season's and last season's results."
2. One sentence on Polymarket from "poly_reading": "Polymarket's price agrees with us." or "Polymarket's price agrees \
with Kalshi, not with us." or "Polymarket's price sits in between." Skip it when poly_reading is empty.
3. One sentence on lineups from "lineups": "Lineups are not out yet." or "Lineups are out." and, when \
"missing_regulars" has names, "Missing: ...".

Rules. Use only the facts you are given. Never invent a chance, a price, motivation, momentum, weather, a referee or an \
injury that is not in the data. Return JSON: {"reasoning": "<your sentences only, without the lead>", "flags": [...]} \
where flags are up to three short plain warnings (for example "Lineups not out yet", "Polymarket agrees with Kalshi, \
not with us"), or an empty list."""


def _pct(x, nd=0):
    return f"{100.0 * float(x):.{nd}f}"


def lead(card, context):
    """The opening sentences from the numbers alone: what we think, what Kalshi's price says, the gap, the risk and
    the win. Always written by code, never by the model, so a number can never drift."""
    c = context or {}
    name = c.get("outcome_name") or card.get("outcome_name") or card.get("outcome") or "this side"
    side = card.get("side") or "yes"
    draw = card.get("outcome") == "draw"
    bet_words = c.get("bet_words") or (("it does not end in a draw" if draw else f"{name} does not win") if side == "no"
                                       else ("it ends in a draw" if draw else f"{name} wins"))
    p = card.get("model_p")
    p_side = c.get("p_side")
    if p_side is None and p is not None:
        p_side = 1.0 - float(p) if side == "no" else float(p)
    price = c.get("price_side") if c.get("price_side") is not None else card.get("market_price")
    parts = []
    if p_side is not None:
        parts.append(f"We think {bet_words} about {round(100 * float(p_side))} times out of 100.")
    if price is not None:
        parts.append(f"Kalshi's price says {bet_words} {round(100 * float(price))} times out of 100.")
    gap = card.get("gap_points")
    if gap is not None:
        color = card.get("color") or ("green" if gap >= 7 else "amber" if gap >= 0 else "red")
        if color == "green":
            risk, win = float(c.get("risk_usd") or card.get("stake_usd") or 0), float(c.get("win_usd") or 0)
            paper = "Paper: " if c.get("paper") else ""
            parts.append(f"After Kalshi's fee that is {round(float(gap))} points in our favor, so this is a green card: "
                         f"{paper}risk ${risk:,.0f} to win ${win:,.0f}.")
        elif color == "amber":
            parts.append(f"That is only {round(float(gap))} points in our favor, and we need 7, so no bet.")
        else:
            parts.append("Kalshi's price is better than ours here, so no bet.")
    return " ".join(parts)


def tail_template(card, context):
    """The rest of the note without a model call: the reasons, Polymarket's reading, the lineups."""
    c = context or {}
    parts = []
    # only the reasons that moved the number (the form rows carry effect 0 until they are in the model)
    contribs = [x for x in (c.get("contributions") or []) if x and x.get("in_model", True)
                and isinstance(x.get("effect"), (int, float)) and abs(float(x["effect"])) >= 0.5]
    contribs.sort(key=lambda x: -abs(float(x["effect"])))
    if contribs:
        bits = [f"{str(x.get('name') or '').replace('_', ' ')} ({float(x['effect']):+.0f} points)" for x in contribs[:3]]
        parts.append("Why we think so: " + ", ".join(bits) + ".")
    pr = (c.get("poly_reading") or "").lower()
    if pr:
        if "agree" in pr and "kalshi" not in pr:
            parts.append("Polymarket's price agrees with us.")
        elif "kalshi" in pr:
            parts.append("Polymarket's price agrees with Kalshi, not with us.")
        else:
            parts.append("Polymarket's price sits in between.")
    lu = (c.get("lineups") or "").lower()
    if lu:
        parts.append("Lineups are out." if "posted" in lu and "not" not in lu else "Lineups are not out yet.")
    if c.get("missing_regulars"):
        parts.append("Missing regulars: " + ", ".join(c["missing_regulars"][:4]) + ".")
    return " ".join(parts)


def template(card, context):
    """The whole note from the numbers alone."""
    return (lead(card, context) + " " + tail_template(card, context)).strip()


class Reasoner:
    def __init__(self, cfg):
        self.cfg = cfg
        self.last_error = None

    @property
    def model(self):
        return (self.cfg.get("claude") or {}).get("model") or MODEL_DEFAULT

    def enabled(self):
        if os.environ.get("EDGE_NO_CLAUDE") == "1":
            return False, "EDGE_NO_CLAUDE"
        if not (self.cfg.get("claude") or {}).get("on", True):
            return False, "claude.on is off"
        cap = float((self.cfg.get("claude") or {}).get("max_usd_per_day") or 0)
        if self.spent_today() + EST_COST > cap:
            return False, "daily Claude cap reached"
        return True, ""

    @staticmethod
    def _day():
        return ec.iso(ec.now())[:10]

    def spent_today(self):
        return float(ec.kv_get(f"claude.cost.{self._day()}") or 0)

    def _charge(self, usage):
        pin, pout = PRICES.get(self.model, (5.0, 25.0))
        cost = (getattr(usage, "input_tokens", 0) or 0) * pin / 1e6 + (getattr(usage, "output_tokens", 0) or 0) * pout / 1e6
        key = f"claude.cost.{self._day()}"
        ec.kv_set(key, round(float(ec.kv_get(key) or 0) + cost, 6))
        return cost

    def _ask(self, card, context, head):
        import anthropic
        from outreach_common import get_secret
        key = get_secret("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY not found")
        client = anthropic.Anthropic(api_key=key)
        c = context or {}
        payload = {"lead": head,
                   "card": {k: card.get(k) for k in ("outcome", "outcome_name", "side", "color", "band", "hours_band")},
                   "home": c.get("home"), "away": c.get("away"), "bet_words": c.get("bet_words"),
                   "contributions": c.get("contributions") or [], "poly_reading": c.get("poly_reading") or "",
                   "lineups": c.get("lineups") or "", "missing_regulars": c.get("missing_regulars") or []}
        msg = client.messages.create(model=self.model, max_tokens=MAX_TOKENS, system=SYSTEM,
                                     messages=[{"role": "user", "content": json.dumps(payload, default=str)}],
                                     output_config={"format": {"type": "json_schema", "schema": SCHEMA}})
        self._charge(getattr(msg, "usage", None))
        if msg.stop_reason == "refusal":
            raise RuntimeError("Claude declined")
        text = next((b.text for b in msg.content if getattr(b, "type", "") == "text"), "")
        data = json.loads(text)
        reasoning = str(data.get("reasoning") or "").strip()
        flags = [str(f)[:80] for f in (data.get("flags") or []) if str(f).strip()][:3]
        if not reasoning:
            raise RuntimeError("empty reasoning")
        return reasoning, flags

    def write(self, card, context):
        """{"reasoning", "flags"}. Never anything else, so a reply can never move model_p. The numbers (the lead)
        are always code's; the model only adds the why, the witness and the lineups."""
        head = lead(card, context)
        fallback = (head + " " + tail_template(card, context)).strip()
        ok, why = self.enabled()
        if not ok:
            return {"reasoning": fallback, "flags": []}
        try:
            tail, flags = self._ask(card, context, head)
            return {"reasoning": (head + " " + tail).strip(), "flags": flags}
        except Exception as e:  # noqa: BLE001  (the card must still have text)
            self.last_error = f"{type(e).__name__}: {e}"[:300]
            ec.log("reasoning: template used,", self.last_error)
            return {"reasoning": fallback, "flags": ["reasoning: template (Claude unavailable)"]}


if __name__ == "__main__":
    sample = {"outcome": "away", "outcome_name": "Arsenal", "side": "yes", "model_p": 0.55, "limit_price": 0.45,
              "fee_points": 1.73, "break_even": 0.4673, "gap_points": 8.27, "color": "green", "stake_usd": 60.76,
              "count": 135}
    ctx_ = {"outcome_name": "Arsenal", "contributions": [{"name": "away form (10)", "effect": 0.06},
                                                        {"name": "shots on target", "effect": 0.03}],
            "poly_reading": "Polymarket mid 53 cents sides with us", "lineups": "lineups not posted yet",
            "rule": "settles Yes if Arsenal win in 90 minutes plus stoppage"}
    print(template(sample, ctx_))
