"""Upload the 5 new shots. Try the hidden file input in the phone-screenshots
dropzone first; fall back to the filechooser event on 'Add assets'."""
from playwright.sync_api import sync_playwright
from _cdp import shot

NEW = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/screenshots"
ORDER = ["screen_1_live.png", "screen_2_search.png", "screen_3_yards.png",
         "screen_4_alerts.png", "screen_5_pro.png"]

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next((pg for pg in ctx.pages if "store-listings/default/edit" in pg.url), None)

    # Re-tag the phone screenshots section (empty state re-rendered it).
    ok = page.evaluate("""() => {
        document.querySelectorAll('[data-ys-shots]').forEach(e => e.removeAttribute('data-ys-shots'));
        const head = [...document.querySelectorAll('*')].find(e =>
            e.children.length === 0 && /^Phone screenshots/.test(e.textContent.trim()));
        if (!head) return 'no-head';
        let s = head;
        for (let i = 0; i < 14 && s; i++) {
            if (s.textContent.includes('Add assets')) break;
            s = s.parentElement;
        }
        if (!s) return 'no-sec';
        s.setAttribute('data-ys-shots', '1');
        return {
            fileInputs: s.querySelectorAll('input[type=file]').length,
            text: s.textContent.slice(0, 120),
        };
    }""")
    print("section:", ok)
    sec = page.locator("[data-ys-shots='1']")
    sec.scroll_into_view_if_needed()
    page.wait_for_timeout(500)

    def count_thumbs():
        return sec.locator("button[debug-id='delete-button']").count()

    for i, name in enumerate(ORDER):
        inp = sec.locator("input[type=file]")
        if inp.count():
            inp.first.set_input_files(f"{NEW}/{name}")
        else:
            add = sec.get_by_text("Add assets").first
            try:
                with page.expect_file_chooser(timeout=8000) as fc:
                    add.click()
                fc.value.set_files(f"{NEW}/{name}")
            except Exception as e:
                # Maybe the click opened an upload dialog with its own input.
                page.wait_for_timeout(1500)
                dlg_inp = page.locator("[role='dialog'] input[type=file]")
                glob_inp = page.locator("input[type=file]")
                tgt = dlg_inp if dlg_inp.count() else glob_inp
                print(f"fallback: dialog inputs={dlg_inp.count()} global={glob_inp.count()}")
                assert tgt.count(), f"no file input anywhere: {e}"
                tgt.first.set_input_files(f"{NEW}/{name}")
        for _ in range(90):
            page.wait_for_timeout(1000)
            if count_thumbs() >= i + 1:
                break
        print(f"uploaded {name} -> thumbs={count_thumbs()}", flush=True)
        page.wait_for_timeout(1500)

    labels = page.evaluate("""() =>
        [...document.querySelector("[data-ys-shots='1']")
            .querySelectorAll("button[debug-id='delete-button']")]
        .map(b => b.getAttribute('aria-label'))""")
    print("final:", labels)
    print("ORDER OK:", labels == [f"Remove {n}" for n in ORDER])
    errs = page.evaluate("""() => {
        const sec = document.querySelector("[data-ys-shots='1']");
        return [...sec.querySelectorAll("[role='alert'], [debug-id*='error']")]
            .map(e => e.textContent.trim()).filter(Boolean);
    }""")
    print("errors:", errs)
    shot(page, "09-after-upload")
