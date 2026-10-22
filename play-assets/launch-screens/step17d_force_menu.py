import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    els = page.query_selector_all("text=more_vert")
    print("more_vert elements:", len(els))
    info = page.eval_on_selector_all("*",
        """els => els.filter(e => e.childElementCount===0 && (e.textContent||'').trim()==='more_vert')
            .map(e => {
              let p = e, chain=[];
              for (let i=0;i<4 && p;i++){ chain.push(p.tagName + (p.getAttribute('aria-label')?('['+p.getAttribute('aria-label')+']'):'')); p=p.parentElement; }
              return chain.join(' < ');
            })""")
    for x in info: print(x)
    if els:
        els[-1].click(force=True)
        page.wait_for_timeout(2500)
        shot(page, "17d-menu-open")
        items = page.eval_on_selector_all("[role=menuitem], [role=menu] button, [role=menu] a, [role=listbox] *",
            "els => els.map(e => (e.innerText||'').trim()).filter(Boolean)")
        print("MENU ITEMS:", items)
        print("BODY TAIL:\n", page.inner_text("body")[-1200:])
