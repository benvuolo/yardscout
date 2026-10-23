"""Resume step46: add the remaining library scenes (yards, pro, alerts) to
the slot. Fixes over step46's add_from_library: selection is verified via the
tile's own aria-live flipping to 'Selected asset ...', and the Add button is
matched exactly (never 'Add from Drive')."""
import re
from playwright.sync_api import sync_playwright
from _cdp import shot

REMAINING = ["screen_3_yards.png", "screen_5_pro.png", "screen_4_alerts.png"]
FULL_ORDER = ["screen_1_live.png", "screen_2_search.png", "screen_7_fitment.png",
              "screen_6_compare.png", "screen_3_yards.png", "screen_5_pro.png",
              "screen_4_alerts.png"]

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next(pg for pg in ctx.pages if "store-listings/default/edit" in pg.url)

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

    def tag_tile(name):
        """Tag the newest 1080x2160 library tile for `name` and report its
        aria-live selection state."""
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
                const sel = row.querySelector("a[debug-id='select-button']");
                const tc = row.querySelector("[debug-id='tile-container']");
                if (!sel || !tc) continue;
                tc.setAttribute('data-ys-tile', name);
                sel.setAttribute('data-ys-select', name);
                return { ok: true, live: tc.getAttribute('aria-label') || '' };
            }
            return { ok: false };
        }""", name)

    start = thumbs()
    print("slot at start:", start)
    assert start == [f"Remove {n}" for n in FULL_ORDER[:len(start)]], \
        f"slot prefix unexpected: {start}"

    for name in REMAINING:
        i = len(thumbs())
        assert FULL_ORDER[i] == name, f"resume mismatch: slot has {i}, next={name}"
        added = False
        for attempt in range(4):
            open_panel()
            # select the tile; verify via its aria-live text
            st = tag_tile(name)
            assert st["ok"], f"tile not found: {name}"
            tile = page.locator(f"[data-ys-tile='{name}']")
            tile.scroll_into_view_if_needed()
            page.wait_for_timeout(400)
            if "Selected asset" not in st["live"]:
                # the select control only renders on hover; hover then click it
                tile.hover()
                page.wait_for_timeout(500)
                sel = page.locator(f"[data-ys-select='{name}']")
                if sel.is_visible():
                    sel.click()
                else:  # fall back to a JS dispatch on the anchor
                    page.evaluate(
                        "n => document.querySelector(`[data-ys-select='${n}']`).click()",
                        name)
                page.wait_for_timeout(1000)
                st = tag_tile(name)
            print(f"{name} attempt {attempt}: live={st['live']!r}", flush=True)
            if "Selected asset" not in st.get("live", ""):
                continue
            # exact Add button (e.g. 'Add' or 'Add 1 asset'), never 'Add from Drive'
            add_btns = page.evaluate("""() =>
                [...document.querySelectorAll('.asset-library-container button')]
                .filter(b => b.offsetParent)
                .map(b => b.textContent.replace(/\\s+/g, ' ').trim())""")
            label = next((t for t in add_btns
                          if re.fullmatch(r"(add_photo_alternate)?Add( \d+ assets?)?", t)), None)
            print(f"  visible buttons: {add_btns} -> clicking {label!r}", flush=True)
            assert label, f"no exact Add button; buttons: {add_btns}"
            page.locator(".asset-library-container button").filter(
                has_text=re.compile(rf"^{re.escape(label)}$")).first.click()
            for _ in range(20):
                page.wait_for_timeout(1000)
                if len(thumbs()) >= i + 1:
                    added = True
                    break
            if added:
                break
        assert added, f"could not add {name}"
        t = thumbs()
        assert t == [f"Remove {n}" for n in FULL_ORDER[:i + 1]], \
            f"unexpected slot state after {name}: {t}"
        print(f"added {name}: {len(t)} in slot", flush=True)

    final = thumbs()
    print("final:", final)
    print("ORDER OK:", final == [f"Remove {n}" for n in FULL_ORDER])
    page.keyboard.press("Escape")
    page.wait_for_timeout(1500)
    tag_section()
    page.locator("[data-ys-shots='1']").scroll_into_view_if_needed()
    page.wait_for_timeout(800)
    shot(page, "46c-after-full-order")
