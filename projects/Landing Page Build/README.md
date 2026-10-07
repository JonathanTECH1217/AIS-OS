# Landing Page Build

The SOP for monarcbuild.com. Run it with `/landing-page` (skill at `.claude/skills/landing-page/SKILL.md`, Codex mirror at `.agents/skills/landing-page/`).

- `Style Guide.md`: palette with roles, type, layout, copy, and media rules. Checkable rules are what the drift check tests. Read first.
- `Section Spec.md`: the seven blocks in order, each with its copy source, media source, and draft headlines. Read second.
- `variants/`: `build_variants.py` generates three alignment variations of the full page (A, B, C) as standalone HTML for review. Not the deploy path.
- `renders/YYYY-MM-DD/`: PNG renders at 1440 and 390 wide for Jonathan's approval.
- Live editing (added 2026-09-19): `/landing-page live`. Claude starts `scripts/site_preview.py`, which hands out the mirror at http://127.0.0.1:8790 and reloads the browser window after every file change. Jonathan prompts, Claude edits, the window refreshes, Claude posts one line. Page-level CSS goes in `public_html/assets/site.css`.
- Ad landing pages (Style Guide section 6): first one is `public_html/avmarketing/index.html`, the LinkedIn destination, built 2026-09-13. Drift-check with `--type ad` (auto-detected from the page's `mb-page-type` meta).

Decisions and the interview that produced these files: `decisions/log.md` (2026-09-13) and `brainstorms/2026-09-13-landing-page-sop.md` (paused at Q23, resume there).

The live site's source of truth is `projects/monarcbuild-site/public_html/` (Hostinger mirror). Nothing moves from here to there without Jonathan approving a render, and nothing is pushed without him saying so. Push goes through `scripts/site_sync.py`.
