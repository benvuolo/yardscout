"""Raw-CDP helper for the YardScout Android WebView (Playwright's
connect_over_cdp refuses WebView targets — no browser context management).

Usage:  _ys_webview_cdp.py eval  '<js expression>'     (awaits promises)
        _ys_webview_cdp.py port <n> eval '<js>'        (non-default forward)
Prints the JSON-serialized result.
"""
import asyncio
import json
import sys
import urllib.request

import websockets


def page_ws(port):
    tabs = json.load(urllib.request.urlopen(f"http://localhost:{port}/json"))
    pages = [t for t in tabs if t.get("type") == "page"]
    if not pages:
        raise SystemExit("no page target on :" + str(port))
    return pages[0]["webSocketDebuggerUrl"]


async def cdp_eval(port, expr):
    async with websockets.connect(page_ws(port), max_size=50 * 1024 * 1024) as ws:
        await ws.send(json.dumps({
            "id": 1, "method": "Runtime.evaluate",
            "params": {"expression": expr, "awaitPromise": True,
                       "returnByValue": True},
        }))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get("id") == 1:
                res = msg.get("result", {})
                if "exceptionDetails" in res:
                    print("JS ERROR:", json.dumps(res["exceptionDetails"])[:500])
                    raise SystemExit(1)
                print(json.dumps(res.get("result", {}).get("value")))
                return


args = sys.argv[1:]
port = 9223
if args and args[0] == "port":
    port = int(args[1]); args = args[2:]
assert args and args[0] == "eval"
asyncio.run(cdp_eval(port, args[1]))
