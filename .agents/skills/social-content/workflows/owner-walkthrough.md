# Owner's walkthrough

Workflow of the social content skill. Status: first cut made 2026-10-05 (Momentum, 4:25 from 6:48 of recording), not approved; not sent.

One line: Cuts his page review down to a video made for the company's owner to watch.

Jonathan, 2026-10-05: "I want one variation of this video to be sent directly to the owner, but take out the part where it talks about them being my prospect and just talk about the changes that I'm going to make to the website."

## Objective

The owner gets one video, wide, that only talks about their page and what changes: no line about them being a prospect, nothing untrue, no dead weight.

## What sets it off

A review he recorded for a company with a meeting booked or just missed. One Loom, or two (the review and the after).

## What he gives

The Loom link or links, and the owner's name if it is not on the company's file.

## Procedure

1. Fetch each Loom: `python scripts/social_content.py fetch <link> --name <company>-<review|after>`.
2. Read the transcripts (`words <folder>`) and the rules (`references/content-rules.md`).
3. Mark the cuts, each with its reason:
   - any line that calls them a prospect, or speaks to an audience that is not them (rule 2)
   - anything not true of what is on screen or on file, and any guess about them stated as fact (rule 1)
   - repeats, false starts, lines that trail off, talk about the making of the video (rule 1)
   - dead air at the start or the end
4. Mark `keep_whole` over any stretch where the screen is the point: a form being filled in, a scroll through the new page.
5. Write the plan in `projects/social-content/plans/<date>-<company>-owner-cut.json` and run `cut <plan>`. Fillers and long pauses come out by themselves.
6. Transcribe the result and read it: the cut lines are gone, the order holds, no half word is left at a cut.
7. Tell him it is on the Creative tab, with its length and the log of what was cut.

## Getting it to the owner

The cut is a file on this laptop. To be sent it needs a link.

- He uploads the file to Loom and pastes the link, or says which Loom link to use as it is.
- The email is drafted into Proton Drafts in his copy (`references/mycopy.md`): first name, the point, the link, how long it runs, and the meeting time or a rebook line. The clone never sends it.
- The owner's name comes from the company's file in the CRM. With no name on file, ask; do not send to "Hi".

## Criteria for passing

Before he sees it:
- [ ] No line calls them a prospect.
- [ ] Nothing said is untrue of what is on screen.
- [ ] The log lists every cut with its reason.
- [ ] Sound and picture are there for the whole length.

Before it is sent:
- [ ] He watched it.
- [ ] The link in the draft opens the cut he approved.

## What it never does without a go

Send the email. Upload the video anywhere.

## Open, his to answer

- Whether the owner's version always gets the after joined on, or only when a rebuild exists.
- How long is too long for an owner to watch.
