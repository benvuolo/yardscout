"""Add the 5 uploaded shots from the asset-library panel to the phone
screenshots slot, one at a time, in iOS order."""
from playwright.sync_api import sync_playwright
from _cdp import shot

ORDER = ["screen_1_live.png", "screen_2_search.png", "screen_3_yards.png",
         "screen_4_alerts.png", "screen_5_pro.png"]

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next((pg for pg in ctx.pages if "store-listings/default/edit" in pg.url), None)

    def panel_open():
        return page.get_by_text("Search assets").count() > 0

    def open_panel():
        if not panel_open():
            page.get_by_text("Add assets").first.click()
            page.wait_for_timeout(2500)

    def thumbs():
        return page.evaluate("""() => {
            const head = [...document.querySelectorAll('*')].find(e =>
                e.children.length === 0 && /^Phone screenshots/.test(e.textContent.trim()));
            let s = head;
            for (let i = 0; i < 14 && s; i++) {
                if (s.querySelector("button[debug-id='delete-button']")
                    || s.textContent.includes('Add assets')) break;
                s = s.parentElement;
            }
            return [...s.querySelectorAll("button[debug-id='delete-button']")]
                .map(b => b.getAttribute('aria-label'));
        }""")

    def deselect_all():
        # Uncheck any pre-selected tiles in the panel.
        n = page.evaluate("""() => {
            const checked = [...document.querySelectorAll(
                "[aria-checked='true'], input[type=checkbox]:checked")];
            checked.forEach(c => c.click());
            return checked.length;
        }""")
        page.wait_for_timeout(800)
        return n

    print("start thumbs:", thumbs())
    open_panel()
    print("deselected:", deselect_all())

    for name in ORDER:
        open_panel()
        # Click the row/tile for this asset (click its thumbnail area).
        row = page.locator(f"text={name}").first
        row.scroll_into_view_if_needed()
        row.click()
        page.wait_for_timeout(1000)
        # 'Add' button at the bottom of the panel.
        add_btn = page.get_by_role("button", name="Add", exact=True)
        if add_btn.count() == 0:
            add_btn = page.locator("button:has-text('Add')").last
        add_btn.first.click()
        page.wait_for_timeout(3000)
        t = thumbs()
        print(f"after adding {name}: {t}", flush=True)

    final = thumbs()
    print("final:", final)
    print("ORDER OK:", final == [f"Remove {n}" for n in ORDER])
    shot(page, "10-after-add")
