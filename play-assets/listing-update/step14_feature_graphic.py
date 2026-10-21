"""Replace the stale '165 yards' feature graphic with the refreshed 210+ one
(repo play-assets/feature_graphic.png, committed today)."""
from playwright.sync_api import sync_playwright
from _cdp import shot

FG = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/feature_graphic.png"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next((pg for pg in ctx.pages if "store-listings/default/edit" in pg.url), None)

    # Close the asset panel if open (X button top-right of panel).
    page.evaluate("""() => {
        const c = document.querySelector('.asset-library-container');
        if (!c) return;
        const x = [...c.parentElement.querySelectorAll('button')]
            .find(b => /close/i.test(b.getAttribute('aria-label') || ''));
        if (x) x.click();
    }""")
    page.wait_for_timeout(1500)

    # Tag the Feature graphic section.
    ok = page.evaluate("""() => {
        const head = [...document.querySelectorAll('*')].find(e =>
            e.children.length === 0 && /^Feature graphic/.test(e.textContent.trim()));
        if (!head) return 'no-head';
        let s = head;
        for (let i = 0; i < 14 && s; i++) {
            if (s.querySelector("button[debug-id='delete-button']")
                || (s.textContent.includes('Add assets') && !/Phone screenshots/.test(s.textContent)))
                break;
            s = s.parentElement;
        }
        document.querySelectorAll('[data-ys-fg]').forEach(e => e.removeAttribute('data-ys-fg'));
        s.setAttribute('data-ys-fg', '1');
        return [...s.querySelectorAll('button')].map(b =>
            b.getAttribute('aria-label') || b.textContent.trim()).slice(0, 8);
    }""")
    print("feature section buttons:", ok)
    sec = page.locator("[data-ys-fg='1']")
    sec.scroll_into_view_if_needed()
    page.wait_for_timeout(800)
    shot(page, "14-before-feature-graphic")

    # Remove the old graphic from the slot.
    rm = sec.locator("button[debug-id='delete-button']")
    if rm.count():
        print("removing:", rm.first.get_attribute("aria-label"))
        rm.first.click()
        page.wait_for_timeout(1500)

    # Open this section's asset panel and upload the new file.
    sec.get_by_text("Add assets").first.click()
    page.wait_for_timeout(2500)
    page.locator("input[type=file]").first.set_input_files(FG)
    # Wait for upload + auto-selection of the new asset.
    sel = []
    for _ in range(60):
        page.wait_for_timeout(1000)
        sel = page.evaluate("""() =>
            [...document.querySelectorAll('.asset-library-container [aria-live]')]
            .map(e => e.textContent.trim()).filter(t => /Selected asset/.test(t))""")
        if sel:
            break
    print("selected after upload:", sel)
    add = page.locator(".asset-library-container button").filter(has_text="Add").last
    add.click()
    page.wait_for_timeout(3000)

    # Verify the slot now holds one graphic.
    state = page.evaluate("""() => {
        const s = document.querySelector("[data-ys-fg='1']");
        return {
            removes: [...s.querySelectorAll("button[debug-id='delete-button']")]
                .map(b => b.getAttribute('aria-label')),
            counter: (s.textContent.match(/(\\d+) \\/ 1/) || ['?'])[0],
        };
    }""")
    print("slot state:", state)
    page.keyboard.press("Escape")
    page.wait_for_timeout(1000)
    sec.scroll_into_view_if_needed()
    page.wait_for_timeout(800)
    shot(page, "14-after-feature-graphic")
