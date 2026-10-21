"""Re-add the 5 shots in the owner's new order using each tile's dedicated
select-button overlay (debug-id='select-button'), verifying tile state via its
aria-label ('Selected asset ...')."""
from playwright.sync_api import sync_playwright
from _cdp import shot

NEW_ORDER = ["screen_1_live.png", "screen_3_yards.png", "screen_5_pro.png",
             "screen_2_search.png", "screen_4_alerts.png"]

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next((pg for pg in ctx.pages if "store-listings/default/edit" in pg.url), None)

    def tag_section():
        return page.evaluate("""() => {
            document.querySelectorAll('[data-ys-shots]').forEach(e =>
                e.removeAttribute('data-ys-shots'));
            const head = [...document.querySelectorAll('*')].find(e =>
                e.children.length === 0 && /^Phone screenshots/.test(e.textContent.trim()));
            if (!head) return false;
            let s = head;
            for (let i = 0; i < 14 && s; i++) {
                if (s.querySelector("button[debug-id='delete-button']")
                    || s.textContent.includes('Add assets')) break;
                s = s.parentElement;
            }
            if (!s) return false;
            s.setAttribute('data-ys-shots', '1');
            return true;
        }""")

    def thumbs():
        tag_section()
        return page.evaluate("""() =>
            [...document.querySelector("[data-ys-shots='1']")
                .querySelectorAll("button[debug-id='delete-button']")]
            .map(b => b.getAttribute('aria-label'))""")

    def open_panel():
        if page.locator(".asset-library-container").count() == 0:
            tag_section()
            page.locator("[data-ys-shots='1']").get_by_text("Add assets").first.click()
            page.wait_for_timeout(2500)

    def tag_select_btn(name):
        """Tag the select-button of the 1080x2160 tile for `name`; return the
        tile's current aria-label (Selected/Deselected)."""
        return page.evaluate("""(name) => {
            document.querySelectorAll('[data-ys-sel]').forEach(e =>
                e.removeAttribute('data-ys-sel'));
            const c = document.querySelector('.asset-library-container');
            const tiles = [...c.querySelectorAll("[debug-id='tile-container']")]
                .filter(t => (t.getAttribute('aria-label') || '').endsWith(' ' + name));
            for (const t of tiles) {
                let row = t;
                for (let i = 0; i < 10 && row; i++) {
                    if (row.classList?.contains('list-row-container')) break;
                    row = row.parentElement;
                }
                if (!row || !row.textContent.includes('1080x2160')) continue;
                const btn = t.querySelector("[debug-id='select-button']");
                if (!btn) continue;
                btn.setAttribute('data-ys-sel', '1');
                return t.getAttribute('aria-label');
            }
            return null;
        }""", name)

    def tile_state(name):
        return page.evaluate("""(name) => {
            const c = document.querySelector('.asset-library-container');
            const tiles = [...c.querySelectorAll("[debug-id='tile-container']")]
                .filter(t => (t.getAttribute('aria-label') || '').endsWith(' ' + name));
            return tiles.map(t => t.getAttribute('aria-label'));
        }""", name)

    print("start:", thumbs())
    for i, name in enumerate(NEW_ORDER):
        open_panel()
        state = tag_select_btn(name)
        assert state, f"tile not found for {name}"
        print(f"{name}: tile state before: {state}")
        if state.startswith("Deselected"):
            # The select overlay only shows on hover: hover the tile first.
            tile = page.locator(".asset-library-container [debug-id='tile-container']",
                                has=page.locator("[data-ys-sel='1']"))
            tile.first.scroll_into_view_if_needed()
            tile.first.hover()
            page.wait_for_timeout(600)
            btn = page.locator("[data-ys-sel='1']")
            try:
                btn.click(timeout=5000)
            except Exception:
                page.evaluate(
                    "document.querySelector(\"[data-ys-sel='1']\").click()")
            page.wait_for_timeout(1200)
        print(f"  state after: {tile_state(name)}")
        add = page.locator(".asset-library-container").get_by_role(
            "button", name="Add", exact=True)
        assert add.count(), "no exact 'Add' button (selection may have failed)"
        add.first.click()
        for _ in range(20):
            page.wait_for_timeout(1000)
            if len(thumbs()) >= i + 1:
                break
        t = thumbs()
        assert t == [f"Remove {n}" for n in NEW_ORDER[:i + 1]], \
            f"unexpected slot after {name}: {t}"
        print(f"  added -> {t}", flush=True)

    print("final:", thumbs())
    # Close panel and screenshot the reordered section.
    page.evaluate("""() => {
        const c = document.querySelector('.asset-library-container');
        if (!c) return;
        const x = [...c.parentElement.querySelectorAll('button')]
            .find(b => /close/i.test(b.getAttribute('aria-label') || ''));
        if (x) x.click();
    }""")
    page.wait_for_timeout(1500)
    tag_section()
    page.locator("[data-ys-shots='1']").scroll_into_view_if_needed()
    page.wait_for_timeout(800)
    shot(page, "20-after-reorder")
