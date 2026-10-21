"""Owner request: Pro F-150 card must be slide 3.
New order: live, yards, pro, search, alerts.
Delete all 5 from the slot, re-add from the asset library in the new order
(drag-reorder is unreliable; assets persist in the library)."""
from playwright.sync_api import sync_playwright
from _cdp import get_page, goto_listing, shot

EDIT = ("https://play.google.com/console/u/0/developers/9052149026359320771"
        "/app/4975171430765358175/store-listings/default/edit")
NEW_ORDER = ["screen_1_live.png", "screen_3_yards.png", "screen_5_pro.png",
             "screen_2_search.png", "screen_4_alerts.png"]

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next((pg for pg in ctx.pages
                 if "play.google.com/console" in pg.url
                 and "submission-activity" not in pg.url), None)
    if "store-listings/default/edit" not in page.url:
        page.goto(EDIT, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(8000)
    print("URL:", page.url)

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

    assert tag_section(), "phone screenshots section not found"
    sec = page.locator("[data-ys-shots='1']")
    sec.scroll_into_view_if_needed()
    page.wait_for_timeout(800)
    print("before:", thumbs())
    shot(page, "19-before-reorder")

    # ---- delete all current shots from the slot (library keeps the files) ---
    for _ in range(8):
        tag_section()
        btns = page.locator("[data-ys-shots='1'] button[debug-id='delete-button']")
        if btns.count() == 0:
            break
        name = btns.first.get_attribute("aria-label")
        btns.first.click()
        page.wait_for_timeout(1200)
        for txt in ("Delete", "Remove", "Confirm"):
            dlg = page.locator(f"[role='dialog'] button:has-text('{txt}')")
            if dlg.count():
                dlg.first.click()
                page.wait_for_timeout(1000)
                break
        print(f"removed from slot: {name}", flush=True)
    print("after-delete:", thumbs())

    # ---- re-add from the asset library in the new order ----
    def open_panel():
        if page.locator(".asset-library-container").count() == 0:
            tag_section()
            page.locator("[data-ys-shots='1']").get_by_text("Add assets").first.click()
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

    for i, name in enumerate(NEW_ORDER):
        added = False
        for attempt in range(3):
            open_panel()
            ds = page.get_by_role("button", name="Deselect all")
            if ds.count() and ds.first.is_enabled():
                ds.first.click()
                page.wait_for_timeout(600)
            assert tag_tile(name), f"tile not found: {name}"
            img = page.locator(f"[data-ys-tile='{name}']")
            img.scroll_into_view_if_needed()
            img.click(force=True)
            page.wait_for_timeout(1200)
            sel = page.evaluate("""() =>
                [...document.querySelectorAll('.asset-library-container [aria-live]')]
                .map(e => e.textContent.trim()).filter(t => /Selected asset/.test(t))""")
            print(f"  attempt {attempt}: selected={sel}", flush=True)
            add = page.locator(".asset-library-container button").filter(has_text="Add")
            if add.count() == 0:
                continue  # nothing selected -> no Add button; retry click
            add.last.click()
            for _ in range(20):
                page.wait_for_timeout(1000)
                if len(thumbs()) >= i + 1:
                    added = True
                    break
            if added:
                break
        assert added, f"could not add {name}"
        # Guard: exactly one asset must have been added, and it must be `name`.
        t = thumbs()
        assert t == [f"Remove {n}" for n in NEW_ORDER[:i + 1]], \
            f"unexpected slot state after {name}: {t}"
        print(f"added {name}: {t}", flush=True)

    final = thumbs()
    print("final:", final)
    print("ORDER OK:", final == [f"Remove {n}" for n in NEW_ORDER])
    # Close panel.
    page.evaluate("""() => {
        const c = document.querySelector('.asset-library-container');
        if (!c) return;
        const x = [...c.parentElement.querySelectorAll('button')]
            .find(b => /close/i.test(b.getAttribute('aria-label') || ''));
        if (x) x.click();
    }""")
    page.wait_for_timeout(1500)
    sec = page.locator("[data-ys-shots='1']")
    sec.scroll_into_view_if_needed()
    page.wait_for_timeout(800)
    shot(page, "19-after-reorder")
