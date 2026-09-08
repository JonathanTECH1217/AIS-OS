# Decisions Log

Append-only record of meaningful decisions and why they were made. `/level-up` Phase 2 (Method interview) writes scoped automation specs here. You can also append manually whenever you decide something worth remembering.

**Format per entry:**

```
## YYYY-MM-DD — Short title

**Decision:** what was decided.

**Why:** the reasoning, constraints, and what would change your mind.

**Alternatives considered:** what else was on the table.

**Owner:** who's accountable.
```

Keep it terse. Future-you will thank present-you for capturing the *why*, not just the *what*.

---

## 2026-09-06 - Audit evidence and routing maintenance

**Decision:** Ship audit rubric v2 and a small /link skill. Audit scores working evidence across the Four Cs, checks operating-manual routing and freshness, and passes one concrete gap into /level-up. A selected repair can improve an existing workflow instead of creating another skill.

**Why:** File counts, configured keys, named rituals, and recent edits do not prove an operational AIOS. Source findability and freshness need explicit checks.

**Alternatives considered:** Keeping presence-based scoring or requiring a hot cache. Neither reliably establishes retrieval quality or successful execution.

## 2026-09-06 - Portable skills and automatic audit history

**Decision:** Ship all four skills for Claude Code and Codex, with bundled resources, matching operating manuals, and a script for regenerating Codex copies. Audit reports are saved automatically, preserve previous runs, and track findings across comparable inspections.

**Why:** Students need the same shared guidance when switching assistants and evidence of actual improvements over time. Intentional runtime adaptations, unknown verification, and confirmed defects are reported separately.

## 2026-09-06 - Portable 3D Brain skill

**Decision:** Add `/3d-brain` for Claude Code and Codex. Ask for a name and categories, map selected local folders, and scaffold a bundled, configurable application with spherical placement, Cinema, and interactive growth replay.

**Why:** Shipping the working renderer preserves the intended appearance and interactions across AIOS installations. A prose-only prompt would produce inconsistent recreations. User config and graph data remain local; the public package includes only code, documentation, dependency notices, and fictional test inputs.

## 2026-09-06 - Add ongoing context interviews

**Decision:** Adapt Herk-2's grill-me skill for the student kit and ship matching Claude/Codex packages. Save every answer to brainstorms/, preserve resumable Q&A history, and update canonical context only with confirmed facts during requested context-building sessions.

**Why:** Onboarding is an initial snapshot. Ongoing interviews capture changing priorities, decisions, and preferences while keeping tentative ideas distinct from current business facts.

## 2026-09-07 - Two-tier offer, B2B outreach dropped

**Decision:** Monarc Build sells two tiers. Level 1 at $2,500/mo (site, landing pages per service and area, managed Google Ads, SEO, weekly PDF report, monthly meeting) with a 60 day pilot, no setup fee, $1,000 matched ad spend, then a 6 month term. Level 2 at $4,500/mo adds First Responder, a human who calls leads within 5 minutes during 9am to 7pm Eastern weekdays and books into the client's calendar; month to month, never sold alone. B2B referral-partner outreach is off the offer.

**Why:** B2B outreach is too much overhead to deliver as a standard tier. First Responder depends on Monarc managing the site and forms, so it can't stand alone. The pilot lowers the barrier for the first 5 clients (due December 1, 2026); the 6 month term protects the retainer after proof.

**Alternatives considered:** Three-tier stack with B2B spine and permit monitoring (the earlier proposal structure). Selling First Responder standalone at $2,000/mo.

**Owner:** Jonathan Beach. Full offer in `context/offer.md`; interview in `brainstorms/2026-09-07-offer-doc.md`.

## 2026-09-08 - Landing page moves to the two-tier offer

**Decision:** Rebuild the monarcbuild.com homepage around nine sections (hero, problem, solution, benefits, proof, FAQ, pricing, final CTA, footer). Problem: integrators want predictable high ticket work but have no time to run top of funnel. Solution: sign with Monarc. Primary CTA "Apply now" to /book. Amended same day: the two tiers and their contents are on the page, but the dollar amounts are not. Prices are quoted on the call and on the offer doc. Permit intelligence and territory exclusivity come off the homepage.

**Why:** The page was selling the B2B permit offer that was scratched on 2026-09-07, with no prices and no First Responder. A prospect reading the site and hearing the offer on a call would hear two different companies.

**Alternatives considered:** Keep the territory story and quote the offer verbally.

**Owner:** Jonathan Beach. Draft lives in the local mirror until approved; site state in `context/website.md`.
