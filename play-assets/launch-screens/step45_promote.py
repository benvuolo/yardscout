import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

APP = "https://play.google.com/console/u/0/developers/9052149026359320771/app/4975171430765358175"

with sync_playwright() as p:
    browser, page = get_page(p, prefer="subscriptions/s/yardscout_pro_monthly")
    page.goto(APP + "/tracks/internal-testing", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(9000)
    shot(page, "45a-internal-track")
    page.click("button:has-text('Promote release')", timeout=15000)
    page.wait_for_timeout(3000)
    shot(page, "45b-promote-menu")
    items = page.eval_on_selector_all("[role=menuitem], [role=menu] *",
        "els => els.map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,20)")
    print("MENU:", items)
