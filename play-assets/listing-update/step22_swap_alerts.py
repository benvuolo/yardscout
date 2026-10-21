"""Swap slide 5 (screen_4_alerts.png) for the re-captured honest version:
remove it from the slot, upload the new file (auto-selected on upload), Add —
it appends at position 5."""
from playwright.sync_api import sync_playwright
from _cdp import shot

EDIT = ("https://play.google.com/console/u/0/developers/9052149026359320771"
        "/app/4975171430765358175/store-listings/default/edit")
NEW_FILE = ("/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter"
            "/play-assets/screenshots/screen_4_alerts.png")
WANT = ["Remove screen_1_live.png", "Remove screen_3_yards.png",
        "Remove screen_5_pro.png", "Remove screen_2_search.png",
        "Remove screen_4_alerts.png"]

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next((pg for pg in ctx.pages
                 if "play.google.com/console" in pg.url
                 and "submission-activity" not in pg.url), None)
    if "store-listings/default/edit" not in page.url:
        page.goto(EDIT, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(9000)

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
    t = thumbs()
    print("before:", t)
    assert t == WANT, f"unexpected starting order: {t}"
    page.locator("[data-ys-shots='1']").scroll_into_view_if_needed()
    page.wait_for_timeout(800)
    shot(page, "22-before-alerts-swap")

    # Remove the old alerts slide (position 5).
    page.locator("[data-ys-shots='1'] "
                 "button[aria-label='Remove screen_4_alerts.png']").click()
    page.wait_for_timeout(1500)
    print("after remove:", thumbs())

    # Open the asset panel and upload the new file (upload auto-selects it).
    tag_section()
    page.locator("[data-ys-shots='1']").get_by_text("Add assets").first.click()
    page.wait_for_timeout(2500)
    page.locator("input[type=file]").first.set_input_files(NEW_FILE)
    sel = []
    for _ in range(60):
        page.wait_for_timeout(1000)
        sel = page.evaluate("""() =>
            [...document.querySelectorAll(
                ".asset-library-container [debug-id='tile-container']")]
            .map(t => t.getAttribute('aria-label'))
            .filter(l => /^Selected asset/.test(l || ''))""")
        if sel:
            break
    print("auto-selected:", sel)
    assert sel == ["Selected asset screen_4_alerts.png"], f"bad selection: {sel}"

    page.locator(".asset-library-container").get_by_role(
        "button", name="Add", exact=True).first.click()
    for _ in range(30):
        page.wait_for_timeout(1000)
        if len(thumbs()) == 5:
            break
    final = thumbs()
    print("final:", final)
    print("ORDER OK:", final == WANT)
    assert final == WANT, "order broken after swap"

    # Close panel, screenshot the section.
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
    shot(page, "22-after-alerts-swap")
