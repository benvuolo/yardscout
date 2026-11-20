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

## The weekly "what landed" post

`tools/landed_post.py <Make> <Model>` writes the whole post in the form
above (state first, then generation with `--gens`, newest first, one tagged
link) from `docs/data/inventory_live.json`. `git pull` first so it reads the
newest scan, and run it right before the owner posts: the list goes stale
with every scan. Example:

    python3 tools/landed_post.py Toyota 4Runner \
      --gens "1989:1st gen,1995:2nd gen,2002:3rd gen,2009:4th gen,2024:5th gen,9999:6th gen"

It posts nothing. The owner reads the draft, checks the subreddit's rules on
self-promotion (or asks its moderators first), and posts it themselves.

## Lessons so far (r/XTerra, 2026-11-12)

- Group lists by state first, then generation: people look for their state.
- "Is there any in <state>?" usually means the post had them further down.
- Feature requests from comments led to the Cars-tab search box.

## Scheduled task

`trig_01PQWZukG51yQNZQ4zbm1956` "Reddit reply drafts": hourly 6:42–21:42
America/Denver, a fresh session each run, push notification when it has
drafts. The owner added the Gmail connector in the Claude app on 2026-11-13 (a
session cannot attach one through the API here); enabled since 16:58 UTC.

## One-generation posts (owner, 2026-11-20: "this would be for just 3rd gens")

The owner posts in generation-specific subreddits too. `tools/landed_post.py`
has no year filter yet; on 11-20 the hub cut the 3rd gen list (1996 to 2002)
out of the tool's full output by script and recounted (38 cars, 15 states, 9
confirmed 4x4, from the 13:40 UTC scan). To do: a `--years 1996-2002` option
on the tool (title and counts for that range, no generation sub-headings),
and a year range on the public landed page so the link can match the post.
Link form for posts since 11-20: the visible text
`yardscout.io/landed/<make>/<model>`, linked to the same address with
`?s=reddit` (the landed pages count views and sources since 11-20).
Correction the same day (owner: the landed page shows every generation):
for a one-generation post the link is the app's own year-filtered list,
`https://yardscout.io/?utm_source=reddit&utm_medium=post&utm_campaign=<model>-<gen>#cars=Make%7CModel%7C1996-2002`
(the `#cars=` link takes `<make>|<model>|<years>`), put behind the visible
text `yardscout.io` as a hyperlink. Checked live 11-20: near 90001 it
opened the Cars tab with 33 cars, 1997 to 2002 only. One closing sentence
names the iPhone and Android apps without store links.
Apps in a post (owner asked 11-20 whether to link the stores or spell them
out): neither. Use the existing say-it-out-loud address `yardscout.io/app`
(phones go straight to their own store, everything else to the site; made
11-02 because people who searched the store by name sometimes landed on
another app). Visible text `yardscout.io/app`, linked to the same address
with the post's `utm_*` tags (Play receives them as the install referrer).

Done 11-20 (hub): `tools/landed_post.py` takes `--years 1996-2002 --label
"3rd gen"` (only those model years; title, counts and link for that range),
and every post it writes now ends with the two agreed lines: the visible
`yardscout.io` linked to the tagged, filtered list, and the apps through
`yardscout.io/app`. Example:

    python3 tools/landed_post.py Toyota 4Runner --years 1996-2002 --label "3rd gen"

Still to do: a year range on the public landed page.
