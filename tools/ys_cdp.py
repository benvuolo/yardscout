"""Shared helper for driving the CDP Chrome (port 9222) with Playwright.

Each step script connects over CDP (async API — the sync API crashes on the
free-threaded Python 3.14 build), acts on the existing page, screenshots,
and exits. Chrome keeps all state between invocations.
"""
import os
from playwright.async_api import async_playwright

SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/vc4-screens"


async def get_page(p, url_substr=None):
    browser = await p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    if url_substr:
        for pg in ctx.pages:
            if url_substr in pg.url:
                return browser, pg
    if ctx.pages:
        return browser, ctx.pages[-1]
    return browser, await ctx.new_page()


async def shot(page, name):
    os.makedirs(SHOTS, exist_ok=True)
    path = f"{SHOTS}/{name}.png"
    await page.screenshot(path=path)
    print(f"SHOT {path}")
    return path
