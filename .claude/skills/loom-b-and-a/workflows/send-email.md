# Send email

Workflow of the Loom B and A skill. Status: written 2026-10-06; the copy (three subject lines, two bodies) is drafted and not approved; no send yet.

One line: The Proton draft that carries the video's link, with one of the subject lines and one of the bodies under test, and the record that makes the test readable.

Jonathan, 2026-10-06: "This then gets packaged into an email draft where we'll test different subject lines and brief amounts of copy that get them to open the link and watch the video more frequently."

## Objective

They open the email and watch the video. Over sends, the subject line and the body that get the most watches win.

## What sets it off

His go on a piece from the steps cut or the trailer cut.

## Procedure

1. Read `templates/loom-ba-email.md`: the subject lines S1 to S3, the bodies B1 and B2, and which is on test now.
2. Pick the next subject line in the rotation (the one with the fewest sends in `projects/loom-b-and-a/sends.json`) and the body on test. Change one thing at a time: while the subject lines are on test, every send uses B1.
3. Fill the blanks: first name, the service the page is for, the Loom link (the share link of the cut once he has put it on Loom, or the Monarc link he gives), and the sign-off ("My Best, Jonathan" on a first touch; "Jonathan." after).
4. Write the spec (To, Subject, a blank line, the body) and place it: `python scripts/proton_mail.py draft <spec.txt>`. It refuses when a draft or a sent mail to that address with that subject exists inside 7 days. It never sends.
5. Record it: `python scripts/loom_ba.py record --company <key> --loom <url> --cut A --subject S1 --body B1`.
6. Tell him the draft is in Proton Drafts, with the subject line and body used. He sends.
7. When Loom's view email comes or they write back: `record ... --watched yes` or `--replied yes`. The `record` command prints the table by subject line.

## What is measured

Watched (Loom's view email; his to mark) and replied. Proton gives no open count, so "opened" is not read; a watch stands in for it. About 20 sends a subject line before a difference is read, the same bar as the Loom brief variations.

## Where it sits

Open, his to answer: the cold sequence's Email 1 (his word 2026-10-06: "Email 1 carries the rebuilt page's link once the first batch of rebuilds exists") or a touch of its own after the hero-check lead's review. Until he says, the draft goes from his own mailbox, to the company's owner, as a first touch.

## What it never does

Send. Place the same draft twice. Name a price. Call them a prospect. Add a line he did not say.
