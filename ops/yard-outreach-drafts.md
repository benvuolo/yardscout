# Yard outreach — send from hello@yardscout.io


> **Gmail connector rewrites links (found 2026-11-18).** Any web address or
> bare domain written into a draft through the Gmail tool (create_draft /
> update_draft), even "yardscout.io" in plain text, is stored as a Google
> redirect link (`google.com/url?q=...&source=gmail&ust=...`). Five emails
> the owner sent on 11-18 at ~17:28 UTC went out that way (Kenny U-Pull,
> Carolina Pick N Pull, Express Pull-N-Save, Andersen; the Glenn reply quotes
> them). Drafts written by the hub carry NO web addresses from now on; the
> owner adds a link by hand in Gmail if one is wanted. Check a draft with
> get_draft RAW, not the plain-text view.
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
understated six. Confirmed 2026-11-16: scan 43923253337 read all three yards under the
YardScout name (4,259 cars), so the note can go. The Sucuri sentence is
conditional on purpose: the reader does not record whether the check came
up on a given scan (one test request with the new name got the list with no
check at all), so "when that check stops our scanner" is what can be said.

Hi,

I run YardScout (yardscout.io), a website and app, free to use, that helps DIY mechanics find cars in self-service yards near them. We list all three Harry's yards (Hazle Township, Allentown and Pennsburg), and every car links back to wegotused.com.

I would like your OK for that. Our scanner reads your public inventory pages about every four hours: roughly 290 pages a pass, one page a second. It identifies itself as "YardScout/1.12 (+https://yardscout.io)". Your site has a Sucuri security check in front of it. When that check stops our scanner, the scanner answers it by itself and carries on. I would rather have your permission than rely on that. Could you allow the scanner by name, or send a daily file instead? Any format works.

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

---

# 2026-11-17 drafts (yards breadth pass). None sent; the owner sends.

Each yard below was checked with the scanner's own name
("YardScout/1.12 (+https://yardscout.io)") and was NOT added, for the reason
given. Nothing was worked around. What was read is listed so each note can be
checked: `ops/yards.md`, "2026-11-17 breadth pass".

## 6. Carolina Pick N Pull (Wilmington NC, Fayetteville NC, Conway SC; about 4,300 cars)

**Why a note and not a reader:** their Terms of Service (last updated
2026-08-11) list as a prohibited use "Using any robot, spider or other similar
automatic technology, process or means to access or use the Website for any
purpose, including monitoring or copying any of the material on this Website".
robots.txt allows everything (Crawl-delay 10) and the inventory page answered
our scanner normally, but the terms say no, so we ask.
**Read from their site on 2026-11-17:** robots.txt, the inventory page once
(the search form only, no search run), the terms page.
**To:** mvanoverpnp@gmail.com (Marc, the contact their terms page names;
phone 910-332-1824)
**Subject:** May YardScout list Carolina Pick N Pull's inventory?

Hi Marc,

I run YardScout (yardscout.io), a website and app, free to use, that helps DIY mechanics find cars in self-service yards near them. People in Wilmington, Fayetteville and Myrtle Beach ask it where a car is, and today we cannot send them to you.

Your terms of service do not allow automated reading of your site, so I am asking first. With your OK we would read your public vehicle inventory for Cape Fear, Sandhills and Grand Strand (year, make, model, row, date), no faster than the 10 seconds between requests your site asks for, and show each car with your yard's name and a link back to carolinapicknpull.com. Our scanner identifies itself as "YardScout/1.12 (+https://yardscout.io)". If a daily file or feed is easier for you, any format works and we would read that instead.

We have not read your inventory. If the answer is no, we will leave you off.

Thanks,
Ben
YardScout, hello@yardscout.io

---

## 7. Kenny U-Pull (about 25 yards in Quebec, Ontario, New Brunswick, Nova Scotia)

**Why:** kennyupull.com answered our scanner with a Cloudflare block page
("Sorry, you have been blocked", HTTP 403) on the home page; robots.txt is a
404. One request each, nothing else tried. This is the largest Canadian
self-service chain and the one the Canadian store listings would gain most
from.
**To:** not found without reading their site. Use the contact form on
kennyupull.com, or the owner finds a marketing or web contact at Kenny U-Pull
/ AIM Recycling.
**Subject:** May YardScout list Kenny U-Pull's inventory?

Hi,

I run YardScout (yardscout.io), a website and app, free to use, that helps DIY mechanics find cars in self-service yards near them. It covers Canada (postal codes work, and both app stores offer it there), but only five Canadian yards so far, none of them yours.

Your site blocks our scanner, so we have not read anything and will not. I am asking instead: may we list your yards' vehicle inventory (year, make, model, row, date listed), each car shown with the branch name and a link back to kennyupull.com? If yes, the simplest way is a daily file or feed in any format. Or you could allow our scanner, which identifies itself as "YardScout/1.12 (+https://yardscout.io)", at whatever pace you set.

If you would rather not be listed, tell me and that is the end of it.

Thanks,
Ben
YardScout, hello@yardscout.io

---

## 8. Express Pull-N-Save (La Vergne, Lebanon, Nashville TN)

**Why:** every page of expresspullnsave.com carries "Downloading,
republication, retransmission or reproduction of content on this website is
strictly prohibited", and the Terms of Use it links are served from the site
builder's host (thryv.com), which answered our scanner HTTP 403, so the terms
could not be read. robots.txt itself allows everything. A Reddit user asked
for these yards on 2026-10-28; an unmerged reader exists on the old branch
`yards/express-pull-n-save` (their public kiosk search, about 900 requests a
pass) and can be finished with a test in about an hour once they say yes.
**Read on 2026-11-17:** robots.txt, the home page, /inventory, the terms page
shell; the kiosk host's robots.txt (404). The kiosk itself was not opened.
**To:** info@expresspullnsave.com (terms questions go to tspelta@ergtn.com
per their site)
**Subject:** May YardScout list Express Pull-N-Save's inventory?

Hi,

I run YardScout (yardscout.io), a website and app, free to use, that helps DIY mechanics find cars in self-service yards near them. People around Nashville have asked us for your three yards.

Your website says its content may not be reproduced, so I am asking before we list anything. With your OK we would read the public vehicle search on kiosk.expresspullnsave.com for La Vergne, Lebanon and Nashville (stock number, year, make, model, row, days on lot), about 900 page requests a pass at one a second, a few times a day, and show each car with your yard's name and a link back to your site. No photos unless you say so. Our scanner identifies itself as "YardScout/1.12 (+https://yardscout.io)". A daily file would also work and would mean far fewer requests.

If you would rather not be listed, tell me and we will leave you off.

Thanks,
Ben
YardScout, hello@yardscout.io

---

## 9. U Pull It Davie (Davie FL; the site says over 2,000 vehicles, updated daily)

**Why:** its robots.txt allows search crawlers ("search=yes") but turns away
AI agents by name (ClaudeBot, Claude-Web, anthropic-ai, GPTBot and others).
The builder in this session is such an agent, so it read robots.txt and
nothing else, and did not look at the pages under the scanner's name
instead. A person can open upullitdavie.com and see how the inventory is
shown; if it is a plain page or feed the reader is small.
**To:** not read. Their site's contact page.
**Subject:** May YardScout list U Pull It Davie's inventory?

Hi,

I run YardScout (yardscout.io), a website and app, free to use, that helps DIY mechanics find cars in self-service yards near them. We list many South Florida yards and people ask about yours.

May we list your vehicle inventory (year, make, model, row, date), each car shown with your yard's name and a link back to upullitdavie.com? We would read only the public inventory, slowly, a few times a day, and our scanner identifies itself as "YardScout/1.12 (+https://yardscout.io)". A daily file or feed in any format is just as good.

If you would rather not be listed, tell me and we will leave you off.

Thanks,
Ben
YardScout, hello@yardscout.io

---

## 10. Ario / autorecycler.io (the platform behind about 45,000 cars we already list)

**Why this is on the list (owner decision, not a new yard):**
`ario.autorecycler.io/robots.txt` now says, for every crawler, `Disallow:
/yard/` with the comment "Paid Website Search / embed product — not for
organic indexing", and the same host now serves Ario's own consumer search
site, "U-Pull Yards" (upullyards.com), which makes Ario a competitor as well
as a vendor. Our reader does not fetch `/yard/` pages; it calls the search
function behind them on another host, with the page's public key and a
browser name. No new Ario yard was added in this pass for that reason. The
existing reader was left as it is.
**To:** not found. Ario / ari (Auto PARTnered Solutions), via its website.
**Subject:** YardScout and the yards that use Ario's website search

Hi,

I run YardScout (yardscout.io), a website and app, free to use, that helps DIY mechanics find cars in self-service yards near them. Since October we have listed about 45 yards whose own websites embed your inventory search (EZ Pull N Pay, Foss, UAPI, Paul's and others), reading the same search those pages use, a few times a day, and linking every car back to the yard.

Your robots.txt now marks the yard search as a paid embed product that crawlers should leave alone, so I would rather ask than assume. Is there a way you would be comfortable with us listing these yards' cars: an official feed, a partner key, or terms we should follow? If the answer is that we should stop, tell me and we will.

Thanks,
Ben
YardScout, hello@yardscout.io

---

## 11. Pull N' Go Self Service Auto Parts (Bradenton FL)

**Why:** pullngo.net answered both of our requests (robots.txt and
/inventory.php) with "503 Service Unavailable", 23 bytes. That may be an
outage or a filter; either way nothing more was tried. Re-check once with
the same name in a week or two. If it still answers 503 while the site
opens in a browser, send the Davie note above with the names changed.

## 12. Andersen Self-Service (Kearney NE; 1,721 vehicles on its page). Not blocked: a heads-up

**Why not added:** the page reads fine (robots.txt allows it, one request
returns the whole yard), but its newest set date is 08/22/2026: 60 to 120
cars a month from mid-2025 to July 2026, six in August, none since. That
looks like an inventory export that stopped, so the list may no longer match
the lot. Add it when new set dates appear (registry: candidate).
**To:** not read. Phone on their site: 308-236-7661.

Hi,

I run YardScout (yardscout.io), a website and app, free to use, that helps DIY mechanics find cars in self-service yards near them. I would like to list your Kearney yard.

One thing you may want to know first: the inventory on andersenselfservice.com shows no vehicle set after August 22, 2026. If the yard has set cars since then, the website is not getting them. Once it is current we will list it, each car with your name and a link back to your site. Our scanner identifies itself as "YardScout/1.12 (+https://yardscout.io)" and would read that one page a few times a day.

Thanks,
Ben
YardScout, hello@yardscout.io

## Gmail drafts as of 2026-11-18 16:50 UTC (owner: "ensure they're filled out with an address/proper destination. Make follow up drafts where needed, and make them sound non ai")

All rewritten in the owner's own plain voice (short, first person, no lists
or dashes, no pasted Google redirect links). None sent; the owner sends.

| Draft | To | Kind |
|---|---|---|
| U-Pull-R correction | glennw@aaaparts.com (thread with Glenn) | correction + reader switched off since Nov 18 |
| Budget | sales@budgetupullit.com (Nov 2 thread) | follow-up + correction |
| Pull-N-Save | info@pullnsave.com (reply to the Nov 2 email) | follow-up + correction + photo question; the old stand-alone photo draft was deleted |
| Route 34 | route34upullm@gmail.com (Nov 2 thread) | follow-up (reads fine now) |
| Kenny U-Pull | info@kennyupull.com (Oct 27 thread, no reply, no bounce) | follow-up (site blocks us) |
| Carolina Pick N Pull | mvanoverpnp@gmail.com (Marc, named on their terms page) | first note |
| Express Pull-N-Save | info@expresspullnsave.com | first note (their site: terms questions to tspelta@ergtn.com) |
| Andersen Self-Service | info@andersenselfservice.com (on their own home page, read once 11-18) | heads-up: no car set after Aug 22 |
| 1A Auto | NO ADDRESS (no verified email found; their site errored our crawler, so not read) | permission request; owner adds the address from 1aauto.com's contact page |

Not in Gmail (no email address): Harry's (form at wegotused.com/contact),
U Pull It Davie (its robots.txt turns AI agents away, so not read; owner
opens upullitdavie.com), Ario (no address found: "ari.app" is an unrelated
auto-repair software company; autopartneredsolutions.com turns AI agents
away; owner decision on Ario still open). Form texts for Harry's and Davie
were given to the owner in chat.
