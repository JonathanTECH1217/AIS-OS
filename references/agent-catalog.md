# Agent catalog: 50 names, 12 groups, and where each sits

The agents Monarc builds, hands off, and checks each month. Two kinds of thing are listed (Jonathan, 2026-10-05: "There should be skills and then workflows which are the deliverables like outreach, follow up, appointment setting and so on"): **workflows** are the deliverables a company gets, and **skills** are the parts a workflow is built from. Made 2026-10-05 from the list Jonathan pasted (50 AI services with a market price each). Interview: `brainstorms/2026-10-05-agent-skills.md`. Decision: `decisions/log.md`, 2026-10-05, "The tool list".

## How it is laid out now (Jonathan, 2026-10-05, his latest word)

"This would be an SDR role, because they do outbound and follow-up and appointment setting... one agent or one skill is the SDR skill... workflows would live underneath of skills. The SDR is not auditing the copy. That is a coach skill that we will bake in. But the SDR is the real build right now."

- A **skill** is a role. A **workflow** is one thing that role does, kept as a file under the skill: `.claude/skills/<skill>/workflows/<name>.md`.
- The pass for the SDR: "we go through each function and I approve that the copy matches what I would typically sound like."

| Skill | What it is | Its workflows | State |
|---|---|---|---|
| `sdr` | The outbound, the follow-up, the appointment setting, and the replies in its own mailbox (patrick@monarcbuild.com at Monarc) | Cold outreach; lead form submission follow-up; stale proposal follow-up; appointment booking; inbox replies; no-show | the build now. Written 2026-10-05; cold outreach's copy v2 waits for his approval, the other four are not drafted |
| `coach` | Audits the copy the SDR sends | not named yet | later; not written |
| `social-content` | The editor: he records and gives notes, the clone cuts, captions, checks, and shows the piece (group 7's Content Repurposer) | The before-and-after short; the owner's walkthrough | written 2026-10-05 from the video he named and his rules of that day (`.claude/skills/social-content/SKILL.md`). One cut of each made for Momentum; neither watched or approved yet. Not there: animations, sound, posting |
| `loom-b-and-a` | The before and after of a rebuild he talks over: each change shows on their page the second he names it, then the email that carries the link (Jonathan, 2026-10-06) | Steps cut (A); trailer cut (B); send email | written 2026-10-06 (`.claude/skills/loom-b-and-a/SKILL.md`, `scripts/loom_ba.py`). Two cuts made on the PHA review, not watched. The step up, HyperFrames, waits on Node (`references/hyperframes.md`) |
| `research` | The researcher: reads a company once and saves it for the other skills | Site read; Google profile pull; Instagram feed pull | written 2026-10-05 (`.claude/skills/research/SKILL.md`). The first two work and were run that day. Instagram is written and not run: it waits on a Meta app and a connected account (`references/instagram-api.md`) |
| `list-building` | The list cold outreach runs on | none | written 2026-10-05; the Clay hookup and four site checks are not built |

The table of 12 below is the fold of his list of 50. Groups 1 to 3 are now the SDR's workflows. The other nine are not placed under a skill yet, and the `workflow-` names there are only labels for the groups. Where this page says "workflow" below this line, it was written before the SDR word and means one of those 12 groups.

## The rules (Jonathan, 2026-10-05)

- The buyer is any business with the problem, not one trade: "I am basically just handing off an agent that fixes a universal problem."
- Nothing high ticket is cut. Only the doubles go: the 50 names fold into 12 problems, one workflow per problem. The industry is a setting inside the workflow.
- A workflow's job: build the agent in the company's own tools, hand it off, then check it each month. Selling stays with Jonathan on the call.
- Each workflow works inside Monarc first, then ships into a client's business by the same steps.
- Price rule (same day): "We go off of what people pay on the market for the tools." The prices below are the list's. The final number on any quote is his.

## The three parts every workflow and skill has

Taken one at a time. The AIOS drafts, Jonathan marks up.

1. **Primary objective.** One line: what is true for the company once the agent runs.
2. **Procedure.** The steps that put it in place, the same at Monarc and at a client: intake, build, test, hand off, monthly check.
3. **Criteria for passing.** A checklist of things that can be counted or checked. Three stops: before the first real run, after the first 30 days, at the hand-off.

(Written before the SDR word; the layout at the top of this page is the one that holds.) A skill's page and each workflow file carry, in this order: primary objective; covers (the names below, each a setting); what the company must give (access and facts, never passwords); procedure; criteria for passing; what it never does without a go (send, spend, push live). A folder is made when its turn comes, not before: an empty one would still show in the clone's list and fire.

Each install leaves a record with the pass checklist ticked: `projects/clients/<slug>/workflow-<name>.md`. Monarc's own run is the first record, in `projects/clients/monarc-build/`.

## Workflows: the deliverables

States: not written, drafted, approved, passed at Monarc, shipped to a client.

| # | Workflow | The problem it fixes | Names | State |
|---|---|---|---|---|
| 1 | `workflow-outreach` | Not enough new conversations with buyers | 5 | now the SDR's cold outreach, `.claude/skills/sdr/workflows/cold-outreach.md`. Monarc run: `projects/clients/monarc-build/sdr.md` |
| 2 | `workflow-follow-up` | Leads and customers go cold | 4 | now two of the SDR's workflows: lead form submission follow-up and stale proposal follow-up. The first cut in the capture is replaced by them |
| 3 | `workflow-appointment-setting` | Meetings not booked, people not showing | 4 | now the SDR's appointment booking |
| 4 | `workflow-sales-desk` | Proposals, deals, and the forecast done late | 4 | not written |
| 5 | `workflow-ops` | The same admin every week | 5 | not written |
| 6 | `workflow-web-build` | No page that turns a visit into a lead | 7 | not written |
| 7 | `workflow-content` | Nothing published, nothing found | 6 | not written |
| 8 | `workflow-support` | The same questions answered by hand | 4 | not written |
| 9 | `workflow-documents` | Paper read and typed by hand | 5 | not written |
| 10 | `workflow-analytics` | Numbers nobody reads | 2 | not written |
| 11 | `workflow-finance` | The books and the spend watched by hand | 3 | not written |
| 12 | `workflow-caller` | Calls nobody has time to make | 1 | not written |

The order is the order we take them. Outreach first is Jonathan's pick; the rest is the AIOS's order, his to change.

## Skills: the parts

Parts the workflows use. Not on the list of 50 and not sold by themselves. Same three parts, same loop.

| Skill | What it does | Used by | State |
|---|---|---|---|
| `list-building` | A big pull from the Google Maps API, a Clay hookup for email, owner name, and LinkedIn URL, then a few checks on reviews and the website that show which of five things a company could use: a new site, a receptionist, email follow-up, an appointment setter, a proposal builder (Jonathan's words, 2026-10-05) | `workflow-outreach` | written 2026-10-05 from his spec (`.claude/skills/list-building/SKILL.md`). Not built yet: the Clay hookup, and four of the five site checks |

The five things the list checks for point at five workflows: a new site (`workflow-web-build`), email follow-up (`workflow-follow-up`), an appointment setter (`workflow-appointment-setting`), a proposal builder (`workflow-sales-desk`), and a receptionist. No name on the list of 50 is a receptionist; the nearest are `workflow-caller` (the phone) and `workflow-support` (chat). Open, his: where the receptionist sits, and whether these five go next in the order.

## The 50 names, by workflow

The four numbers are from the paste. The AIOS reads them as market price, cost to deliver, profit, and margin; Jonathan has not confirmed the last three. The code's last two letters look like the industry the listing was written for (HE health care, LE legal, RE real estate or recruiting, FI finance, SU support, SA sales, EC online stores); that is a reading, not a fact on file.

### 1. `workflow-outreach`

| Code | Name | Price | Cost | Profit | Margin |
|---|---|---|---|---|---|
| CORE | AI Candidate Outreach | $5,038 | $399 | $4,639 | 92.1% |
| AOOU | AI Account-Based Outbound | $4,859 | $473 | $4,386 | 90.3% |
| RCRE | AI Recruiter Copilot | $4,731 | $437 | $4,294 | 90.8% |
| SFRE | AI Seller Finder | $3,516 | $295 | $3,221 | 91.6% |
| LNKAGT | AI LinkedIn Agent | $3,473 | $240 | $3,233 | 93.1% |

### 2. `workflow-follow-up`

| Code | Name | Price | Cost | Profit | Margin |
|---|---|---|---|---|---|
| FEAU | AI Follow-Up Engine | $5,716 | $388 | $5,328 | 93.2% |
| RMOU | AI Reply Manager | $4,798 | $420 | $4,378 | 91.2% |
| UEEC | AI Upsell Engine | $4,061 | $378 | $3,683 | 90.7% |
| FERE | AI Follow-Up Engine (the double) | $3,740 | $263 | $3,477 | 93.0% |

### 3. `workflow-appointment-setting`

| Code | Name | Price | Cost | Profit | Margin |
|---|---|---|---|---|---|
| NRHE | AI No-Show Reducer | $5,664 | $398 | $5,266 | 93.0% |
| ISRE | AI Interview Scheduler | $4,997 | $348 | $4,649 | 93.0% |
| TSRE | AI Tour Scheduler | $3,961 | $350 | $3,611 | 91.2% |
| SBRE | AI Showing Booker | $3,472 | $309 | $3,163 | 91.1% |

### 4. `workflow-sales-desk`

| Code | Name | Price | Cost | Profit | Margin |
|---|---|---|---|---|---|
| PESA | AI Proposal Engine | $4,512 | $419 | $4,093 | 90.7% |
| DDSA | AI Deal Desk | $4,371 | $397 | $3,974 | 90.9% |
| FASA | AI Forecast Assistant | $4,162 | $359 | $3,803 | 91.4% |
| SLSMGR | AI Sales Manager | $4,036 | $287 | $3,749 | 92.9% |

### 5. `workflow-ops`

| Code | Name | Price | Cost | Profit | Margin |
|---|---|---|---|---|---|
| WBAU | AI Workflow Build | $6,922 | $364 | $6,558 | 94.7% |
| OAAU1 | AI Onboarding Automation | $5,935 | $389 | $5,546 | 93.4% |
| AUTOMATE | AI Automation Systems | $5,601 | $477 | $5,124 | 91.5% |
| OAAU | AI Ops Automation | $4,744 | $461 | $4,283 | 90.3% |
| PRJMGR | AI Project Manager | $3,171 | $215 | $2,956 | 93.2% |

### 6. `workflow-web-build`

| Code | Name | Price | Cost | Profit | Margin |
|---|---|---|---|---|---|
| LPBBU | AI Landing Page Build | $8,643 | $698 | $7,945 | 91.9% |
| MSBU | AI Membership Site | $7,792 | $525 | $7,267 | 93.3% |
| WEBGEN | AI Web Design | $6,905 | $507 | $6,398 | 92.7% |
| FBBU | AI Funnel Build | $6,826 | $449 | $6,377 | 93.4% |
| PBBU | AI Portal Build | $6,740 | $516 | $6,224 | 92.3% |
| WMBU | AI Webapp MVP | $5,741 | $512 | $5,229 | 91.1% |
| MBBU | AI Microsite Build | $5,111 | $429 | $4,682 | 91.6% |

### 7. `workflow-content`

| Code | Name | Price | Cost | Profit | Margin |
|---|---|---|---|---|---|
| PODAI | AI Podcast Studio | $6,053 | $432 | $5,621 | 92.9% |
| AVSCR | AI Avatar Video Studio | $4,726 | $409 | $4,317 | 91.3% |
| TABMA | AI Topical Authority Build | $4,515 | $316 | $4,199 | 93.0% |
| REEC | AI Review Engine | $4,363 | $365 | $3,998 | 91.6% |
| CRMA | AI Content Repurposer | $3,217 | $247 | $2,970 | 92.3% |
| LOCALSEO | AI Local SEO / GBP | $2,544 | $238 | $2,306 | 90.6% |

**The Content Repurposer at Monarc first (Jonathan, 2026-10-05).** His words: "The inputs for my organic social... broken down Loom videos showing a prospect's website that I look at, talk through a few changes that they could put together, and then show the after product right after with the difference. This would then be... CRMA, the content repurposer. We'll just break this down and then distribute it across my organic platforms, write captions, do the editing, keyframing and motion graphics, through the best tool in the industry right now."

- Input: the Loom website reviews he already records for booked meetings (`projects/crm/looms.json`), each with the before, the changes talked through, and the after.
- Its job: cut each review into shorts, write the captions, do the edit, the keyframes, and the motion graphics, and put them out on his organic platforms (the CRM's Organic social channel).
- **The tool is OpusClip (Jonathan, 2026-10-05: "We want to do testing first, I guess, but let's just get the tool put in place. Let's use OpusClip.").** Wired in `.mcp.json`; guide and the test plan in `references/opusclip.md`; `connections.md` row 23. Waiting on his account and sign-in.
- A prospect's public site may be shown without asking them (Jonathan, 2026-10-05; his words and the AIOS's cautions are in `references/opusclip.md`).
- Not decided: which platforms. Nothing posts without his go on each short.
- The tool comparison (web research, 2026-10-05; read from the vendors' pages, nothing tried or bought): **Tella** is the pick for this footage, a screen recording with a voice over it. Its API and MCP zoom onto a chosen point of the screen (up to 3.5x), set the frame to 1080x1920, burn in word-by-word captions, add text callouts, and hand back a file; $13 to $19 a month billed yearly. It has no "find the clips" step, so the clone picks the moments and the zoom points from the transcript. Runner-up **OpusClip** ($29 a month): picks moments, captions, and schedules to all five platforms, but only stacks the screen over the speaker, with no zoom onto a part of the page. Higgsfield's Shorts Studio is the wrong fit (a July 2026 review says it restyles the footage and cuts it into 10-second pieces). Posting on a schedule: **Zernio** (was Late), about $18 a month for five accounts. Not checked: which Tella plan includes the API, and whether its overlays move. The risk: a Loom file holds no click data and the face bubble is baked into the picture, so every zoom is a point the clone picks from frames; recording in Tella itself keeps the clicks. Next step, his go: one review on Tella's trial.
- This is a different rule from Monarc Studio, where every edit is by hand (G16, G17, G37). Here the repurposer makes the edit and he approves the result. His to confirm that Studio's own rule stays as it is.

### 8. `workflow-support`

| Code | Name | Price | Cost | Profit | Margin |
|---|---|---|---|---|---|
| LCASU | AI Live Chat Agent | $3,357 | $240 | $3,117 | 92.9% |
| FASU | AI FAQ Assistant | $3,307 | $266 | $3,041 | 92.0% |
| TDSU | AI Ticket Deflector | $3,271 | $311 | $2,960 | 90.5% |
| KBBSU | AI Knowledge Base Bot | $2,885 | $219 | $2,666 | 92.4% |

### 9. `workflow-documents`

| Code | Name | Price | Cost | Profit | Margin |
|---|---|---|---|---|---|
| PGLE | AI Policy Generator | $6,763 | $474 | $6,289 | 93.0% |
| PAHE | AI Prior-Auth Assistant | $5,300 | $368 | $4,932 | 93.1% |
| DEBAU | AI Data Entry Bot | $5,002 | $456 | $4,546 | 90.9% |
| DPAU | AI Document Processor | $4,923 | $407 | $4,516 | 91.7% |
| CRLE | AI Contract Review | $4,620 | $385 | $4,235 | 91.7% |

### 10. `workflow-analytics`

| Code | Name | Price | Cost | Profit | Margin |
|---|---|---|---|---|---|
| ACDA | AI Analytics Copilot | $6,091 | $388 | $5,703 | 93.6% |
| IEDA | AI Insight Engine | $5,859 | $444 | $5,415 | 92.4% |

### 11. `workflow-finance`

| Code | Name | Price | Cost | Profit | Margin |
|---|---|---|---|---|---|
| SCFI | AI Spend Controls | $5,407 | $493 | $4,914 | 90.9% |
| FRFI | AI Financial Reporting | $5,310 | $412 | $4,898 | 92.2% |
| RBFI | AI Reconciliation Bot | $5,149 | $404 | $4,745 | 92.2% |

### 12. `workflow-caller`

| Code | Name | Price | Cost | Profit | Margin |
|---|---|---|---|---|---|
| CCVO | AI Collections Caller | $4,991 | $404 | $4,587 | 91.9% |

The check: 5 + 4 + 4 + 4 + 5 + 7 + 6 + 4 + 5 + 2 + 3 + 1 = 50, each name once.

## Open, Jonathan's to answer

- Where the list came from, and whether the three numbers after the price are cost, profit, and margin.
- Whether each price is one-time or per month. The goal is $3k+ a month per client.
- The order after Outreach.
- Whose Google Maps key and Clay account a client's list is pulled on (Monarc's, or the client's own), the review band, and the kinds of business Monarc's own first pull searches for.
