"""Delete the 4 stale phone screenshots, then upload the 5 new 1080x2160
shots ONE AT A TIME (guarantees left-to-right order matches the iOS set)."""
from playwright.sync_api import sync_playwright
from _cdp import shot

NEW = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/screenshots"
ORDER = ["screen_1_live.png", "screen_2_search.png", "screen_3_yards.png",
         "screen_4_alerts.png", "screen_5_pro.png"]

def section(page):
    return page.locator("[data-ys-shots='1']")

def dump_state(page, tag):
    labels = page.evaluate("""() =>
        [...document.querySelector("[data-ys-shots='1']")
            .querySelectorAll("button[debug-id='delete-button']")]
        .map(b => b.getAttribute('aria-label'))""")
    counter = page.evaluate("""() => {
        const sec = document.querySelector("[data-ys-shots='1']");
        const m = sec.textContent.match(/(\\d+) \\/ 8/);
        return m ? m[0] : '?';
    }""")
    print(f"{tag}: {counter} | {labels}", flush=True)
    return labels

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next((pg for pg in ctx.pages if "store-listings/default/edit" in pg.url), None)
    sec = section(page)
    if sec.count() == 0:
        # Marker lost (e.g. section re-rendered) — re-tag it.
        page.evaluate("""() => {
            const head = [...document.querySelectorAll('*')].find(e =>
                e.children.length === 0 && /^Phone screenshots$/.test(e.textContent.trim()));
            let s = head;
            for (let i = 0; i < 12 && s; i++) {
                if (s.querySelector("button[debug-id='delete-button']")) break;
                s = s.parentElement;
            }
            s.setAttribute('data-ys-shots', '1');
        }""")
        sec = section(page)
    sec.scroll_into_view_if_needed()
    page.wait_for_timeout(800)
    dump_state(page, "before")
    shot(page, "08-before-swap")

    # ---- delete the 4 old shots ----
    for _ in range(10):
        btns = sec.locator("button[debug-id='delete-button']")
        if btns.count() == 0:
            break
        name = btns.first.get_attribute("aria-label")
        btns.first.click()
        page.wait_for_timeout(1200)
        # confirm dialog, if any
        for txt in ("Delete", "Remove", "Confirm"):
            dlg = page.locator(f"[role='dialog'] button:has-text('{txt}')")
            if dlg.count():
                dlg.first.click()
                page.wait_for_timeout(1000)
                break
        print(f"deleted: {name}", flush=True)
    dump_state(page, "after-delete")
    shot(page, "08-after-delete")

    # ---- upload the 5 new shots, one at a time, in iOS order ----
    for name in ORDER:
        add = sec.locator("button:has-text('Add assets')")
        if add.count() == 0:
            add = sec.get_by_text("Add assets")
        with page.expect_file_chooser() as fc:
            add.first.click()
        fc.value.set_files(f"{NEW}/{name}")
        # wait for the thumbnail to land (delete-button count grows)
        want = ORDER.index(name) + 1
        for _ in range(60):
            page.wait_for_timeout(1000)
            if sec.locator("button[debug-id='delete-button']").count() >= want:
                break
        print(f"uploaded: {name}", flush=True)
        page.wait_for_timeout(1500)

    labels = dump_state(page, "after-upload")
    shot(page, "08-after-upload")
    expect = [f"Remove {n}" for n in ORDER]
    print("ORDER OK:", labels == expect)

    # surface any validation errors near the section
    errs = page.evaluate("""() => {
        const sec = document.querySelector("[data-ys-shots='1']");
        return [...sec.querySelectorAll("[role='alert'], .error, [debug-id*='error']")]
            .map(e => e.textContent.trim()).filter(Boolean);
    }""")
    print("errors:", errs)
