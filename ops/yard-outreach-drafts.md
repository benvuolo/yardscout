# Yard outreach — send from hello@yardscout.io

Four emails, one per blocked source. Pull-N-Save is the one that matters most (8 yards, ~11,000 cars, and their own search is broken for 6 stores — they'll want to know).

---

## 1. Pull-N-Save (8 yards, AZ/UT/CA)

**To:** info@pullnsave.com
**Subject:** Your online inventory search shows no cars for 6 of your stores

Hi,

I run YardScout (yardscout.io), a free app that helps DIY mechanics find cars in self-service yards near them and sends them to your stores. Two things you'd probably want to know:

1. Since Friday Oct 31, your website's inventory search returns "no matching vehicles" for Glendale, Gilbert, Phoenix North, Tucson, Springville and Riverside. Salt Lake City and Phoenix South still work. Glendale alone showed about 1,500 cars the day before, so it looks like a sync problem on the inventory side rather than empty lots.

2. Our app has listed all 8 of your yards since October, reading the same public inventory your site shows, at the pace your robots.txt asks for (one request every 10 seconds, a few times a day). About half of our checks now get a "please wait" page instead of the inventory, so your stores are going stale in the app. If you're OK with us listing you, could you allow our scanner through? It identifies itself as "YardScout/1.12 (+https://yardscout.io)". If you'd rather we didn't list you, just say so and we'll take you out.

Every car we show links back to your site and your store.

Thanks,
Ben
hello@yardscout.io

---

## 2. Budget U-Pull-It (Winter Garden + Bartow, FL)

**To:** sales@budgetupullit.com (cc Craig@budgetfl.com)
**Subject:** Listing Budget U-Pull-It's inventory in YardScout

Hi,

I run YardScout (yardscout.io), a free app that helps DIY mechanics find cars in self-service yards near them. We list both your yards and send people to your inventory pages and your lots.

Two things on our end:

1. About half of our checks of budgetupullit.com/current-inventory/ now come back empty, so Winter Garden goes stale in the app between successful checks. We read the public inventory page at a slow pace (about 1.5 seconds between requests, a few times a day). If you're OK with being listed, could you allow our scanner? It identifies itself as "YardScout/1.12 (+https://yardscout.io)".

2. Bartow's inventory page (budgetupullit.s3softwaresolutions.com) has shown the same 927 cars since Oct 23. If that system moved, let me know where and we'll point at the new one.

If you'd prefer not to be listed, say the word and we'll remove you.

Thanks,
Ben
hello@yardscout.io

---

## 3. Route 34 U-Pull-M (Auburn, NY)

**To:** route34upullm@gmail.com
**Subject:** Listing Route 34's inventory in YardScout

Hi,

I run YardScout (yardscout.io), a free app that helps DIY mechanics find cars in self-service yards near them. We've listed your Auburn yard since October, reading the inventory table on route34upullm.com/inventory/ a few times a day, and every car links back to your site.

About half of our checks now get blocked, so your lot goes stale in the app between the ones that work. If you're OK with being listed, could you allow our scanner through? It identifies itself as "YardScout/1.12 (+https://yardscout.io)" and reads one page per visit.

If you'd rather not be listed, just say so and we'll take you out.

Thanks,
Ben
hello@yardscout.io

---

## 4. U-Pull-R Parts (Rosemount + East Bethel MN, Toledo OH)

Their site lists no email, only a contact form at upullrparts.com/contact/ and phones (651-322-1800 MN, 419-724-5503 Toledo). Paste this into the form:

**Subject:** Listing U-Pull-R's inventory in YardScout

Hi,

I run YardScout (yardscout.io), a free app that helps DIY mechanics find cars in self-service yards near them. We listed your Rosemount, East Bethel and Toledo yards until about Oct 21, when your site started blocking our requests, so they've dropped out of the app.

We only read the public inventory your site already shows, slowly (one request every couple of seconds, a few times a day), and every car links back to your site. If you're OK with that, could you allow our server through? It identifies itself as "YardScout/1.12 (+https://yardscout.io)". Or if you'd rather send a daily file, any format works.

If you'd prefer we don't list you, just say so and we'll leave it off.

Thanks,
Ben
hello@yardscout.io

---

## Not emailing

**Sunshine Auto Salvage (Orangeburg, SC):** their whole website is returning errors right now (every page, not just inventory), so there's nothing to ask them to allow. The app keeps showing their last good list. If it's still down in a week I'll flag it.

---

## 5. Harry's U-Pull-It (Hazle Township, Allentown, Pennsburg PA) — added 2026-11-02, reworded 2026-11-16

Owner, 2026-11-16: "give me harrys, the form never sent". So nothing went to
Harry's on 11-02 and there is nothing to correct; this is the first note.
Contact: the form at wegotused.com/contact (no email published); paste the
text below as the message.

Reworded 2026-11-16 so every sentence is checkable against the reader
(`scrape_harrys` in `scraper/junkyard_scraper.py`): a scan every four hours,
about 290 pages a pass (15 cars a page), one page a second
(`HARRYS_DELAY_SEC`), the scanner's own name (true from the first scan after
the reader change is on main), and that the reader answers the Sucuri check
itself today. The 11-02 wording said the screen "sometimes stops our
scanner", which was not what happens, and "a few times a day", which
understated six. **Send only after the hub confirms a scan ran with the
YardScout name.**

Hi,

I run YardScout (yardscout.io), a website and app, free to use, that helps DIY mechanics find cars in self-service yards near them. We list all three Harry's yards (Hazle Township, Allentown and Pennsburg), and every car links back to wegotused.com.

I would like your OK for that. Our scanner reads your public inventory pages about every four hours: roughly 290 pages a pass, one page a second. It identifies itself as "YardScout/1.12 (+https://yardscout.io)". Your site has a Sucuri security check in front of it, and today our scanner answers that check itself to get the pages. I would rather have your permission than rely on that. Could you allow the scanner by name, or send a daily file instead? Any format works.

If you would rather not be listed, tell me and I will take your yards out.

Thanks,
Ben
YardScout, hello@yardscout.io

---

## Corrections, 2026-11-16 (owner: "Yes draft the corrections for all three")

The 11-02 / 11-03 notes said the scanner "identifies itself as YardScout/1.12
(+https://yardscout.io)". For Pull-N-Save, Budget, U-Pull-R and Harry's the
inventory readers were sending a generic browser name until 2026-11-16 (table
in `ops/yards.md`, same date). Each correction is true only once the reader
change is on main and a scan has run with it; the owner sends after the hub
confirms that scan.

- **Pull-N-Save**: the correction is one paragraph inside the photo note,
  Gmail draft in thread `1a1e52cb8accbc08`.
- **U-Pull-R**: Gmail draft, a reply to Glenn Wear (CTO) in thread
  `1a1b2b1b2f24f262`. This is the one that matters: on 11-03 and 11-06 he
  was told "every request identified itself as YardScout" and "same
  identity" for the home-connection pull, and neither was so. The draft
  says exactly that, says what does hold (only the inventory JSON, about 110
  small requests a scan 2 s apart, no images, never past the human check,
  yards still off the app) and that the reader sends the name now.
- **Budget**: Gmail draft, a reply in thread `1a19e455f0efaf97` to
  sales@budgetupullit.com (the 11-02 CC to Craig@budgetfl.com bounced; it is
  not on the reply).
- **Harry's**: none needed. The owner confirmed on 2026-11-16 that the 11-02
  form note never went out, so section 5 above (reworded the same day) is
  the first and only note.
