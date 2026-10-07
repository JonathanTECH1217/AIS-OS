# Anthropic API: Opus 5 website qualification

Domain 5 and 11, `connections.md`. Started 2026-09-13. Goal: read every prospect website once and answer, in
fixed JSON, whether it is a residential integrator, what it offers, which ICP brands it names, and how thin the site
is. `scripts/qualify_sites.py` runs it; platform detection (Wix, Squarespace, WordPress, GoDaddy, Shopify) is
deterministic and happens before the model is involved.

## The short version

Model `claude-opus-5` ($5 in / $25 out per million tokens; thinking on by default, `effort: low` for classification).
Structured outputs pin the answer to a JSON schema (`output_config.format`, type `json_schema`), so the parser is
`json.loads` on the first text block. Bulk runs go through the **Message Batches API** at half price
($2.50 / $12.50), results usually within an hour, always within 24. The shared system prompt (ICP brand map from
`context/icp-brands.md`) carries `cache_control` so it is billed once and read from cache after that.

SDK: `anthropic` 1.5.0 (upgraded 2026-09-13 from 0.105; 1.x is built on `httpx2`). `pip install -U anthropic`.

## Setup, in order

1. **Key.** `ANTHROPIC_API_KEY` in `%USERPROFILE%\.monarc\secrets.env` (`references/credentials.md`). Set a monthly
   spend limit on the workspace in console.anthropic.com as the backstop.
2. **Fetch only, no spend:** `python scripts/qualify_sites.py --dry-run --limit 25` prints platform counts and the
   Opus estimate for those sites.
3. **Smoke test, synchronous:** `python scripts/qualify_sites.py --limit 25 --no-batch`. Read the 25 model reasons in
   `qualified-seed-<DATE>.xlsx` (All scored sheet) before spending on the full list.
4. **Full run:** `python scripts/qualify_sites.py`. Submits batches of 1,000, polls every 60 s, writes each result to
   `projects/outreach/site-cache-<DATE>.jsonl`. `--no-wait` submits and exits; rerun later to collect. Batch ids
   live in `projects/outreach/qualify-batches-<DATE>.json`.
5. **Rebuild outputs without the model:** `--build-only`.

## Request shape (per website)

```python
client.messages.create(
    model="claude-opus-5", max_tokens=3000,
    system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
    messages=[{"role": "user", "content": extracted_pages}],
    output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
)
```

Batch form: `client.messages.batches.create(requests=[{"custom_id": "d000001", "params": <same dict>}])`, then
`batches.retrieve(id).processing_status == "ended"`, then iterate `batches.results(id)` keyed by `custom_id`
(results arrive in any order). Custom ids are `d<index>`; the id-to-domain map is in the batches JSON.

Schema fields: `is_integrator`, `market_focus` (residential / mixed_residential_lead / mixed_commercial_lead /
commercial / unclear), `offerings` (8 booleans), `brands`, `high_end_signals`, `site_quality` (5 booleans),
`confidence`, `reason`. All required, `additionalProperties: false`.

Always check `stop_reason` before reading content: `refusal` (with `stop_details.category`) and `max_tokens` are
recorded as errors and the domain lands in Unverified for a rerun.

## Cost

Per site about 2,500 input tokens (homepage 5,000 chars plus two subpages at 2,000) and up to 1,000 output tokens
including thinking. Batch: about $0.02 per site, so 5,000 sites is roughly $90 to $110; synchronous doubles it. The
script estimates before submitting and refuses to cross `SEED_BUDGET_USD` (default $200) minus what
`places_seed.py` spent the same date. Real usage from each response is written to the cache and summed in the
Method sheet.

## Fallbacks

- `--no-batch` when a result is needed now (small `--limit` only).
- Monarc OS has an older Haiku-based qualifier, `Operations\Marketing\tools\qualify_icp.py`, that scores against
  `ICP.txt`. Different rubric, same key.

## Rules (Intern Rule)

- The model reads only text the script extracted; it never browses. Brands are reported only if on the page.
- Key stays in `secrets.env`. Cost estimate printed before every spend; cap enforced by `CostMeter`.
- Output is a scoring aid. Tier C and Unverified are for Jonathan's eyes, not the upload.

## Status

- [x] Script written; fetch, fingerprints, scoring, and output writer verified without the model (2026-09-13)
- [x] Key in `secrets.env` (2026-09-13)
- [x] 25-site synchronous smoke test: 23 reads, $0.62, reasons read and approved by Jonathan (2026-09-13)
- [x] Full batch run: 6,461 sites in 7 batches, all ended within about 40 minutes, zero errors or refusals, $75.58. Measured about $0.012 per site with the cached system prompt, well under the $0.02 planning figure. Output tokens averaged about 270 per site at effort low (2026-09-13).

## Studio: Find moments (2026-09-29)

Monarc Studio's "Find moments" button (`scripts/studio_moments.py`, guide `references/studio.md`) sends one
recording's transcript to `claude-opus-5` and gets back the calls and the best moments for shorts.

- **Request:** one streamed call (`client.beta.messages.stream`), `max_tokens` 128000 (Opus 5's ceiling; raised
  from 64000 on 2026-09-30 so moments, voice labels and thinking fit), adaptive thinking, effort high, structured output
  (`output_config.format` JSON schema), server-side fallbacks (`server-side-fallback-2026-07-01`,
  `fallbacks: "default"` in the body). `stop_reason` is checked for `refusal` and `max_tokens` first.
- **Voice labels (2026-09-30):** once the laptop has split the voices, the lines carry inline tags
  (`412|01:12:34|[S2] yeah… [S1] okay…`) and a table of tags goes on top (seconds, pitch, voiceprint match). The schema
  adds `jonathan_tags` and `voices` (`tag`, `gender`, `name`, `role`, `same_as`); the answer lands in
  `speaker-labels.json` and colors the captions. `--speakers-only` (or "Label voices with Claude…" in the bin) sends
  the same tagged transcript with its own short prompt and schema and leaves the moments alone. Labels are tied to the
  split they were asked about (its `rev`) and refused if it changed meanwhile.
- **Find calls, and running by itself (2026-10-01):** the button is now "Find calls" (same single call). Call labels
  ask for the first name and company when said ("Sean, C3 Electrical"); the outcome stays its own field. When a new
  recording finishes preparing, the server counts tokens (free) and runs the call only if the estimate's top is under
  `autoFindMax` in `projects/studio/config.json` (3.00, about 50,000 input tokens); otherwise it waits for a click.
  Logged as `kind: "auto"` in `moments-log.jsonl`. Never under test media or `STUDIO_NO_CLAUDE`.
- **Trailer headlines (2026-09-30):** Make trailer asks `claude-opus-5` (effort low, JSON schema) for three thumbnail
  headlines from the peak's words and the moment's title. The first real call cost $0.004. It is logged under
  `kind: "headlines"` in `moments-log.jsonl`.
- **Voice label cost, measured 2026-09-30:** the labels-only run on the 4 h 03 m session (426 voice groups, 1,823
  lines) took 58,416 input and 57,068 output tokens (nearly all adaptive thinking at effort high), 664 s, **$1.72**,
  against a first estimate of $0.54 to $1.04 (it assumed 10-30k output). `OUT_TOKENS_VOICES` is now 40-70k.
- **No made-up times:** the transcript goes out as numbered lines (`412|01:12:34|text`). Claude answers with line
  numbers only; the script maps them to times (first word -0.3 s, last word +0.4 s).
- **Only text leaves the laptop,** never the audio. The transcript itself is made on the laptop (Parakeet).
- **Cost:** `count_tokens` gives a free estimate first, and the button shows the dollar range before anything is
  spent. Prices checked on the pricing page 2026-09-29: Opus 5 $5 / $25 per million tokens. First real run: a
  4 h 03 m session, 1,823 lines, 42,567 input tokens, estimate $0.59 to $1.21, **actual $0.355** (62 s,
  32 calls, 31 moments). Every run is logged to `media/.studio/<asset>/moments-log.jsonl`.
