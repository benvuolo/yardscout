"""Owner UI feedback 2026-10-24: element close-ups for the report.

Clips the Live/Yards stats bars, Parts where-row, and the footer (collapsed +
expanded) so the before/after is readable. Also sanity-checks the footer
accordion actually toggles.

Usage: python3 tools/_owner_ui_details.py <base_url> <out_dir> [engine] [width]
"""
import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

BASE = sys.argv[1]
OUT = Path(sys.argv[2])
ENGINES = [sys.argv[3]] if len(sys.argv) > 3 else ["webkit", "chromium"]
WIDTHS = [int(sys.argv[4])] if len(sys.argv) > 4 else [360, 390]

SEED = """
localStorage.setItem('jh_zip', '84101');
localStorage.setItem('jh_zip_coords', JSON.stringify({'84101': {lat: 40.7608, lng: -111.891}}));
localStorage.setItem('jh_radius', '250');
localStorage.setItem('jh_honesty_ack', '1');
localStorage.setItem('ys_app_promo', '1');
"""


async def clip(page, selector, path):
    el = page.locator(selector).first
    try:
        await el.scroll_into_view_if_needed()
        await page.wait_for_timeout(250)
        await el.screenshot(path=str(path))
        print(f"  wrote {path.name}")
    except Exception as e:
        print(f"  FAILED {path.name}: {e}")


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        for engine in ENGINES:
            browser = await getattr(p, engine).launch()
            for w in WIDTHS:
                h = 844 if w == 390 else 800
                ctx = await browser.new_context(viewport={"width": w, "height": h})
                await ctx.add_init_script(SEED)
                page = await ctx.new_page()
                await page.goto(BASE, wait_until="domcontentloaded")
                try:
                    await page.wait_for_selector("#live-grid .car-card", timeout=45000)
                except Exception:
                    print(f"  [{engine} {w}] live grid never rendered")
                await page.wait_for_timeout(600)
                pre = f"{engine}_{w}"
                await clip(page, "#live-stats-bar", OUT / f"{pre}_live_stats.png")
                # footer collapsed, then expanded (and assert toggle works)
                await clip(page, ".app-footer", OUT / f"{pre}_footer_collapsed.png")
                folds = page.locator(".app-footer .footer-fold")
                if await folds.count():
                    await folds.first.locator("summary").click()
                    opened = await folds.first.get_attribute("open")
                    print(f"  [{engine} {w}] footer fold toggles: {'yes' if opened is not None else 'NO'}")
                    await clip(page, ".app-footer", OUT / f"{pre}_footer_expanded.png")
                    await folds.first.locator("summary").click()
                else:
                    print(f"  [{engine} {w}] no .footer-fold found (before build?)")
                    await clip(page, ".app-footer", OUT / f"{pre}_footer_expanded.png")
                await page.click(".tab[data-tab='yards']")
                await page.wait_for_timeout(900)
                await clip(page, "#yards-stats-bar", OUT / f"{pre}_yards_stats.png")
                await page.click(".tab[data-tab='parts']")
                await page.wait_for_timeout(900)
                await clip(page, "#pf-body", OUT / f"{pre}_parts_form.png")
                await ctx.close()
            await browser.close()


asyncio.run(main())
