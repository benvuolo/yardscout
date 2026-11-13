# Reddit replies — playbook (hub, 2026-11-13)

The owner posts weekly "what landed" lists as u/YardScout and answers every
comment personally. A session drafts the replies; the owner copies and posts
them. Never post, and never send email.

To use it: in a session with the Gmail connector, say "check Reddit". The
session follows the steps below.

## Steps

1. **Find new replies.** Gmail search
   `from:noreply@redditmail.com newer_than:3d -label:reddit-drafted`, minimal
   view (subject + snippet). The subject says who replied and where; the
   snippet starts with the comment. Do not open full bodies by default (a
   Reddit email is thousands of tokens of tracking links); open one only when
   its snippet is cut off. A reply with no text is an image or GIF: no draft.
2. **Look up facts** in `docs/data/inventory_live.json` with a short script
   (never print the file). `vehicles` rows use the columns in `fields`; `yards`
   uses `yardFields`; `vpic` is keyed by the vehicle's ROW INDEX as a string:
   [trim, quality, series, driveType, mismatch]. Drive containing "4WD" or
   "4x4" = 4x4; "4x2" = 2WD; empty = "drive unknown".
3. **Draft** each reply between two horizontal rules, rendered as normal chat
   text (not a code block) so bold, bullets and links copy into Reddit.
   - Voice: first person, casual, short, one owner to another. No sales pitch,
     no emoji, no em dashes, nothing that reads as written by AI.
   - Car lists: newest first, at most 10, as
     `* 2008 **4x4**, Pick-n-Pull Springfield, row 25, set out 11/10`.
   - At most one link, to the model near the reader:
     `https://yardscout.io/?utm_source=reddit&utm_medium=comment&utm_campaign=<model>#cars=Make|Model`
     (posts use `utm_medium=post`).
   - Only what the data supports. Never invent a car, yard, fitment, price,
     feature or date. Not covered = say so and ask which yard they use.
   - Hostile, off-topic or moderation comments: no draft, flag for the owner.
4. **Mark handled:** add the Gmail label `reddit-drafted` to every thread
   looked at. Nothing else in the mailbox changes.
5. End with "Worth knowing" when a comment holds a feature request, a bug, a
   missing yard, or a sign the post is landing badly.

## Lessons so far (r/XTerra, 2026-11-12)

- Group lists by state first, then generation: people look for their state.
- "Is there any in <state>?" usually means the post had them further down.
- Feature requests from comments led to the Cars-tab search box.

## Scheduled task

`trig_01PQWZukG51yQNZQ4zbm1956` "Reddit reply drafts": hourly 6:42–21:42
America/Denver, a fresh session each run, push notification when it has
drafts. The owner added the Gmail connector in the Claude app on 2026-11-13 (a
session cannot attach one through the API here); enabled since 16:58 UTC.
