"""Replace short + full description with the refreshed LISTING.md copy."""
from playwright.sync_api import sync_playwright
from _cdp import shot

SHORT = ("Live inventory from 210+ self-service junkyards. "
         "Find the car before you drive.")

FULL = """YardScout tracks the live inventory of self-service salvage yards across the country, so you stop driving to yards on a maybe.

FIND THE CAR BEFORE YOU DRIVE
\u2022 Live inventory from 210+ self-serve yards \u2014 every major chain (Pick-n-Pull, LKQ Pick Your Part, Pull-A-Part) plus a growing set of independents \u2014 refreshed throughout the day
\u2022 Search by make, model, and year range around your ZIP
\u2022 See the row number, arrival date, and VIN before you leave the house
\u2022 Model search understands yard naming quirks \u2014 searching WRX finds every spelling

KNOW THE YARDS
\u2022 Every tracked yard near you with distance, car counts, and what arrived this week
\u2022 Each yard's own published pull-price list, right in the app \u2014 no digging through junkyard websites
\u2022 Tool rules per yard (sawzalls, compressors) so you bring the right gear

WATCH FOR THE RIGHT CAR
\u2022 Build a watchlist of makes, models, and years \u2014 picked from vehicles that actually cycle through yards, so no typos
\u2022 Watched cars light up in the app the moment they arrive at a yard in your radius

YARDSCOUT PRO
\u2022 Resale value ranges and demand speed on nearly every car
\u2022 Cross-yard price compare \u2014 find the cheapest alternator near you
\u2022 In-app arrival alerts within hours of a watched car hitting a yard in your radius \u2014 before the weekend crowd strips it (push notifications coming soon)
\u2022 Sale-day alerts when a yard near you runs a half-off sale

NO ACCOUNT, NO EMAIL
\u2022 The whole app works without signing up
\u2022 We never ask who you are

YardScout Pro is $8.99/month through your Google Play account, auto-renews monthly, cancel anytime in Play Store \u2192 Subscriptions. Finding cars is free forever.

Privacy policy: https://yardscout.io/privacy.html
Terms of use: https://yardscout.io/terms.html"""

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next((pg for pg in ctx.pages if "store-listings/default/edit" in pg.url), None)
    assert page, "editor tab lost"

    # Identify short/full description fields by their CURRENT stale values.
    boxes = page.locator("textarea, input[type=text]")
    n = boxes.count()
    short_i = full_i = None
    for i in range(n):
        v = boxes.nth(i).input_value()
        if v.startswith("Live inventory from 165"):
            short_i = i
        elif v.startswith("YardScout tracks the live inventory"):
            full_i = i
    assert short_i is not None and full_i is not None, f"fields not found ({n} boxes)"

    # 'Before' shot of the stale copy in place.
    boxes.nth(short_i).scroll_into_view_if_needed()
    page.wait_for_timeout(800)
    shot(page, "06-before-text")

    boxes.nth(short_i).fill(SHORT)
    page.wait_for_timeout(500)
    boxes.nth(full_i).fill(FULL)
    page.wait_for_timeout(1000)

    # Verify what the form now holds.
    sv = boxes.nth(short_i).input_value()
    fv = boxes.nth(full_i).input_value()
    print("short ok:", sv == SHORT, f"({len(sv)} chars)")
    print("full ok:", fv == FULL, f"({len(fv)} chars)")
    print("stale '165' gone:", "165" not in sv and "165" not in fv)
    print("stale 'coming to Android soon' PRO header gone:",
          "PRO (coming to Android soon)" not in fv)

    boxes.nth(short_i).scroll_into_view_if_needed()
    page.wait_for_timeout(800)
    shot(page, "06-after-text-short")
