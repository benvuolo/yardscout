"""Select each NEW (1080x2160) asset tile in the library panel and Add it to
the phone-screenshots slot, one at a time, in iOS order."""
from playwright.sync_api import sync_playwright
from _cdp import shot

ORDER = ["screen_1_live.png", "screen_2_search.png", "screen_3_yards.png",
         "screen_4_alerts.png", "screen_5_pro.png"]

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next((pg for pg in ctx.pages if "store-listings/default/edit" in pg.url), None)

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

    def panel():
        return page.locator(".asset-library-container")

    def open_panel():
        if panel().count() == 0:
            page.get_by_text("Add assets").first.click()
            page.wait_for_timeout(2500)

    def select_tile(name):
        """Click the thumbnail of the 1080x2160 tile for `name`. Returns the
        aria-live announcement."""
        return page.evaluate("""(name) => {
            const c = document.querySelector('.asset-library-container');
            const crop = [...c.querySelectorAll("button[debug-id='crop-button']")]
                .filter(b => b.getAttribute('aria-label') === 'Crop ' + name);
            for (const b of crop) {
                let row = b;
                for (let i = 0; i < 10 && row; i++) {
                    if (row.textContent.includes('1080x2160')
                        && row.textContent.includes(name)) break;
                    row = row.parentElement;
                }
                if (!row || !row.textContent.includes('1080x2160')) continue;
                const img = row.querySelector('img');
                (img || row).dispatchEvent(new MouseEvent('click',
                    {bubbles: true, cancelable: true, view: window}));
                return 'clicked ' + name;
            }
            return 'NOT FOUND ' + name;
        }""", name)

    def live_msg():
        return page.evaluate("""() =>
            [...document.querySelectorAll('[aria-live]')]
            .map(e => e.textContent.trim()).filter(Boolean).join(' | ')""")

    print("start thumbs:", thumbs())
    for name in ORDER:
        open_panel()
        # Clear any stray selection so Add only adds this one asset.
        ds = page.get_by_role("button", name="Deselect all")
        if ds.count() and ds.first.is_enabled():
            ds.first.click()
            page.wait_for_timeout(600)
        r = select_tile(name)
        page.wait_for_timeout(800)
        print(r, "|", live_msg(), flush=True)
        add = panel().get_by_role("button", name="Add", exact=True)
        add.first.click()
        want = ORDER.index(name) + 1
        for _ in range(30):
            page.wait_for_timeout(1000)
            if len(thumbs()) >= want:
                break
        print(f"after {name}: {thumbs()}", flush=True)

    final = thumbs()
    print("final:", final)
    print("ORDER OK:", final == [f"Remove {n}" for n in ORDER])
    # Close the panel if still open.
    x = page.locator(".asset-library-container button[aria-label*='lose']")
    page.keyboard.press("Escape")
    page.wait_for_timeout(1000)
    shot(page, "12-after-add")
