"""Trusted-click version: tag each 1080x2160 tile via JS, click it with a real
Playwright click, confirm the 'Selected asset' announcement, then Add."""
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

    def open_panel():
        if page.locator(".asset-library-container").count() == 0:
            page.get_by_text("Add assets").first.click()
            page.wait_for_timeout(2500)

    def tag_tile(name):
        return page.evaluate("""(name) => {
            document.querySelectorAll('[data-ys-tile]').forEach(e =>
                e.removeAttribute('data-ys-tile'));
            const c = document.querySelector('.asset-library-container');
            const crops = [...c.querySelectorAll("button[debug-id='crop-button']")]
                .filter(b => b.getAttribute('aria-label') === 'Crop ' + name);
            for (const b of crops) {
                let row = b;
                for (let i = 0; i < 10 && row; i++) {
                    if (row.textContent.includes('1080x2160')
                        && row.textContent.includes(name)) break;
                    row = row.parentElement;
                }
                if (!row || !row.textContent.includes('1080x2160')) continue;
                const img = row.querySelector('img');
                if (!img) continue;
                img.setAttribute('data-ys-tile', name);
                return true;
            }
            return false;
        }""", name)

    def selected_names():
        return page.evaluate("""() =>
            [...document.querySelectorAll('.asset-library-container [aria-live]')]
            .map(e => e.textContent.trim()).filter(t => /Selected asset/.test(t))""")

    for name in ORDER:
        open_panel()
        assert tag_tile(name), f"tile not found: {name}"
        img = page.locator(f"[data-ys-tile='{name}']")
        img.scroll_into_view_if_needed()
        img.click(force=True)
        page.wait_for_timeout(1000)
        sel = selected_names()
        print(f"{name}: selected={sel}", flush=True)

        # Footer buttons in the panel right now:
        foot = page.evaluate("""() =>
            [...document.querySelectorAll('.asset-library-container button')]
            .map(b => (b.getAttribute('aria-label') || b.textContent.replace(/\\s+/g,' ').trim()))
            .slice(-6)""")
        print("  footer buttons:", foot, flush=True)
        add = page.locator(".asset-library-container button").filter(has_text="Add").last
        add.click()
        want = ORDER.index(name) + 1
        for _ in range(30):
            page.wait_for_timeout(1000)
            if len(thumbs()) >= want:
                break
        print(f"  after add: {thumbs()}", flush=True)

    final = thumbs()
    print("final:", final)
    print("ORDER OK:", final == [f"Remove {n}" for n in ORDER])
    page.keyboard.press("Escape")
    page.wait_for_timeout(1000)
    shot(page, "13-after-add")
