"""Owner UI feedback 2026-10-24: before/after shots + overflow audit.

Shoots all four tabs at 390x844 and 360x800 in chromium + webkit against a
given base URL (prod or local). Pre-seeds zip 84101 / 250 mi so the Yards and
Live tabs render real content, dismisses first-run + promo banners. Full-page
screenshots (footer included), plus a per-tab horizontal-overflow assert that
reports any element wider than the viewport.

Usage: python3 tools/_owner_ui_shots.py <base_url> <out_dir>
"""
import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://yardscout.io/"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "tools/_owner_ui_shots")

SEED = """
localStorage.setItem('jh_zip', '84101');
localStorage.setItem('jh_zip_coords', JSON.stringify({'84101': {lat: 40.7608, lng: -111.891}}));
localStorage.setItem('jh_radius', '250');
localStorage.setItem('jh_honesty_ack', '1');
localStorage.setItem('ys_app_promo', '1');
"""

TABS = ["live", "yards", "parts", "alerts"]
SIZES = [(390, 844), (360, 800)]

OVERFLOW_JS = """
() => {
  const vw = document.documentElement.clientWidth;
  const bad = [];
  if (document.documentElement.scrollWidth > vw)
    bad.push(`PAGE scrollWidth ${document.documentElement.scrollWidth} > ${vw}`);
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (r.width > 0 && (r.right > vw + 1 || r.left < -1)) {
      const s = getComputedStyle(el);
      if (s.visibility === 'hidden' || s.display === 'none') continue;
      // scroll containers that intentionally clip are fine; flag their kids only
      bad.push(`${el.tagName.toLowerCase()}#${el.id || ''}.${(el.className && el.className.baseVal === undefined ? el.className : '')} right=${Math.round(r.right)} left=${Math.round(r.left)}`);
      if (bad.length > 12) break;
    }
  }
  return bad;
}
"""


async def shoot(p, engine_name):
    browser = await getattr(p, engine_name).launch()
    for (w, h) in SIZES:
        ctx = await browser.new_context(viewport={"width": w, "height": h})
        await ctx.add_init_script(SEED)
        page = await ctx.new_page()
        await page.goto(BASE, wait_until="domcontentloaded")
        try:
            await page.wait_for_selector("#live-grid .car-card", timeout=45000)
        except Exception:
            print(f"  [{engine_name} {w}] live grid never rendered cards")
        await page.wait_for_timeout(800)
        for tab in TABS:
            await page.click(f".tab[data-tab='{tab}']")
            await page.wait_for_timeout(1200)
            name = f"{engine_name}_{w}x{h}_{tab}.png"
            await page.screenshot(path=str(OUT / name), full_page=True)
            bad = await page.evaluate(OVERFLOW_JS)
            status = "OK" if not bad else "OVERFLOW"
            print(f"  [{engine_name} {w}x{h}] {tab}: {status}")
            for b in bad[:12]:
                print(f"      {b}")
        await ctx.close()
    await browser.close()


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        for engine in ("chromium", "webkit"):
            print(f"== {engine} @ {BASE}")
            await shoot(p, engine)


asyncio.run(main())
