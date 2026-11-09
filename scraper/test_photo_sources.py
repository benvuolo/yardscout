#!/usr/bin/env python3
"""Photo sources = the remote kill switch (scraper/photo_sources.json):
patterns, URL rebuilds, filtering of disabled/unknown codes, the published
map in vehicle_extras.json and the shard manifest, Pick-n-Pull "n" codes.
Run:  python3 scraper/test_photo_sources.py   (offline; uses node if present
to check the patterns behave the same in JavaScript)"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f" — {detail}"))
    if not ok:
        fails.append(name)


SRC = js.load_photo_sources()
PUB = js.published_photo_sources(SRC)


def rebuild(code, which="card"):
    import re
    for key, s in PUB.items():
        for p in s["patterns"]:
            m = re.fullmatch(p["code"], code)
            if m:
                out = p[which]
                for i, g in enumerate(m.groups(), 1):
                    out = out.replace("{%d}" % i, g)
                return key, out
    return None, None


# --- the file ---------------------------------------------------------------
check("photo_sources.json loads", isinstance(SRC, dict) and SRC)
check("enabled set includes every passing chain",
      {"pyp", "pnp", "wap", "weller", "ezpullit", "kikers", "papva", "upullitwa", "aesop", "midwayupull",
       "byot", "wilberts", "nvpap", "pns", "pap", "fenix", "paulsautoyard", "ario_foss", "ario_ryans",
       "ys_ruperts", "ys_upickitaz"} <= set(PUB), sorted(PUB))
check("army's is listed but OFF", "armys" in SRC and "armys" not in PUB)
check("sturtevant published as heavy (tap to load, ~3.8 MB)",
      PUB.get("sturtevant", {}).get("heavy") is True and PUB["sturtevant"].get("approxKB") == 3800
      and PUB["sturtevant"]["onCards"] is False, PUB.get("sturtevant"))
check("only sturtevant is heavy", [k for k, s in PUB.items() if s.get("heavy")] == ["sturtevant"])
check("every published source has a label and patterns",
      all(s["label"].startswith("Photo: ") and s["patterns"] for s in PUB.values()))
check("every published URL is https on the source's host",
      all(p[w].startswith("https://" + s["host"] + "/") or p[w] == "{1}"
          for s in PUB.values() for p in s["patterns"] for w in ("card", "large")))
check("onCards published as a bool on every source", all(isinstance(s.get("onCards"), bool) for s in PUB.values()))
# 2026-11-09 owner ("do what you think, it needs to be free"): sources up to
# ~300 KB per image (Ario tenants, Fenix) show on list cards, lazy-loaded;
# 400 KB+ sources stay car-screen only.
check("heavy sources are off list cards",
      {"byot", "papva", "upullitwa", "aesop", "midwayupull", "kikers", "pap"}
      <= {k for k, s in PUB.items() if not s["onCards"]},
      sorted(k for k, s in PUB.items() if not s["onCards"]))
check("onCards defaults to true", js.published_photo_sources({"x": {"enabled": True, "label": "Photo: X", "host": "h",
      "patterns": [{"code": "^x$", "card": "https://h/a", "large": "https://h/a"}]}})["x"]["onCards"] is True)
check("LKQ card is not cropped (mode=max, not mode=crop)",
      "mode=max" in PUB["pyp"]["patterns"][0]["card"] and "mode=crop" not in PUB["pyp"]["patterns"][0]["card"])

# --- codes -> URLs ----------------------------------------------------------
CASES = {
    "p26140235": ("pyp", "https://cdn.pypapps.com/carbuy/CAR-FRONT-LEFT_26140235_front_left_corner.jpg?quality=70&w=640&h=427&mode=max&format=webp"),
    "n054e0d16d12847daa3f888e2ee3b8c39": ("pnp", "https://cdn.row52.com/images/054e0d16-d128-47da-a3f8-88e2ee3b8c39.JPG"),
    "w2/1C3CCCAB3FN712637/1793896869292.j": ("wap", "https://storage.googleapis.com/wrench-car-photos/v1%2F2%2F1C3CCCAB3FN712637%2F1793896869292-front_driver-thumb.jpg"),
    "w3/1GC4KXBG8AF136387/1788281660820.p": ("wap", "https://storage.googleapis.com/wrench-car-photos/v1%2F3%2F1GC4KXBG8AF136387%2F1788281660820.png"),
    "https://ik.imagekit.io/rm8xun1iy5t/ZFBHRFBB4M6T24102/291966_01.jpg": ("weller", "https://ik.imagekit.io/rm8xun1iy5t/ZFBHRFBB4M6T24102/291966_01.jpg"),
    "https://cdn.shopify.com/s/files/1/0731/9250/5650/files/users_2FzTcvQAepjoYI1lHMoZFeD8THq9O2_2Fuploads_2F1793723763603000.jpg?v=1793893783": ("ezpullit", None),
    "https://www.kikersupullit.com/inventory-feed/photos/27347fde-eebf-4320-be22-7bffe11ea702_8fffc11b3f82528a.jpg": ("kikers", None),
    "utt87/PAP175750/PAP175750-1-HDDN5D_1": ("papva", "https://da8h1v3w8q6n5.cloudfront.net/tt87/images/PAP175750/PAP175750-1-HDDN5D_1.jpg"),
    "ujj65/2L2756/2L2756_1": ("upullitwa", "https://da8h1v3w8q6n5.cloudfront.net/jj65/images/2L2756/2L2756_1.jpg"),
    "uoo95/STK031489/STK031489-1-BOAAD1_1": ("aesop", "https://da8h1v3w8q6n5.cloudfront.net/oo95/images/STK031489/STK031489-1-BOAAD1_1.jpg"),
    "umo06/2604445/2604445_0": ("midwayupull", "https://da8h1v3w8q6n5.cloudfront.net/mo06/images/2604445/2604445_0.jpg"),
    "b8e86-e286-5094-248f": ("byot", "https://storage.googleapis.com/byotautoparts.appspot.com/yard_inventory/8e86-e286-5094-248f"),
    "l1G1JC6SH6C4172184/179380681910558733016406597819920261104_104113": ("wilberts", "https://buyingtoolrg.blob.core.windows.net/vehicleimagesresized/1G1JC6SH6C4172184/179380681910558733016406597819920261104_104113.jpg"),
    "vH065291_left": ("nvpap", "https://www.nvpap.com/photos/preview_photos/H065291_left.JPG"),
    "sSTK134723-1": ("pns", "https://app.pullnsaveapp.com/v1/Vehicles/Images/StockId/STK134723-1/OrderId/1"),
}
for code, (want_key, want_url) in CASES.items():
    key, url = rebuild(code)
    check(f"{want_key}: {code[:40]}", key == want_key and url == (want_url or code), (key, url))
check("wap .j large is the full shot",
      rebuild("w2/1C3CCCAB3FN712637/1793896869292.j", "large")[1].endswith("1793896869292-front_driver.jpg"))

REJECT = [
    "r12345", "rabc",  # old Row52 codes: never
    "https://cdn.row52.com/images/054e0d16-d128-47da-a3f8-88e2ee3b8c39.JPG",  # raw Row52 URL
    "https://api.yardsmartapp.com/rails/active_storage/blobs/redirect/eyJ--0123456789abcdef0123456789abcdef01234567/IMG_1.jpeg",
    "https://app.pullnsaveapp.com/v1/Vehicles/Images/StockId/STK1-1/OrderId/1",
    "https://ik.imagekit.io/someoneelse/A/1.jpg",
    "https://cdn.shopify.com/s/files/1/9999/9999/9999/files/x.jpg",
    "https://evil.example/p.jpg", "p", "pabc", "N054E0D16D12847DAA3F888E2EE3B8C39",
    "https://www.kikersupullit.com.evil.example/inventory-feed/photos/a.jpg",
    "javascript:alert(1)",
    "uzz99/A1/A1_1",         # URG folder no enabled source owns
    "sSTK134723",            # Pull-N-Save without the -n suffix
]
for code in REJECT:
    check(f"rejected: {code[:50]}", js.photo_source_for(code, SRC) is None)

# --- filtering ----------------------------------------------------------------
ex = {
    "a": ["p1", "Red"],
    "b": ["r999"],
    "c": ["https://api.yardsmartapp.com/rails/active_storage/blobs/redirect/eyJ--0123456789abcdef0123456789abcdef01234567/IMG_1.jpeg", "Blue", "", "Manual", "vin"],
    "d": ["", "Green"],
    "e": ["n054e0d16d12847daa3f888e2ee3b8c39"],
}
dropped = js.filter_photo_codes(ex, SRC)
check("filter drops disabled/unknown codes", dropped == 2, dropped)
check("filter keeps enabled codes", ex["a"] == ["p1", "Red"] and ex["e"] == ["n054e0d16d12847daa3f888e2ee3b8c39"])
check("filter removes a row left empty", "b" not in ex)
check("filter keeps the rest of the row", ex["c"] == ["", "Blue", "", "Manual", "vin"], ex.get("c"))
check("filter leaves photo-less rows alone", ex["d"] == ["", "Green"])

off = json.loads(json.dumps(SRC))
off["pnp"]["enabled"] = False
ex2 = {"x": ["n054e0d16d12847daa3f888e2ee3b8c39", "White"]}
js.filter_photo_codes(ex2, off)
check("kill switch: pnp off -> its codes dropped", ex2 == {"x": ["", "White"]}, ex2)
check("kill switch: pnp off -> not published", "pnp" not in js.published_photo_sources(off))
check("enabled must be literally true", "pyp" not in js.published_photo_sources({"pyp": {**SRC["pyp"], "enabled": "yes"}}))

with tempfile.TemporaryDirectory() as td:
    bad = Path(td) / "photo_sources.json"
    bad.write_text("{not json")
    check("unreadable file fails closed", js.load_photo_sources(bad) == {})
    check("missing file fails closed", js.load_photo_sources(Path(td) / "nope.json") == {})

# --- Pick-n-Pull code from the API's own field --------------------------------
check("pnp code from imageName",
      js._pnp_photo_code({"imageName": "https://cdn.row52.com/images/054e0d16-d128-47da-b3f8-88e2ee3b8c39.JPG"})
      == "n054e0d16d12847dab3f888e2ee3b8c39")
check("pnp: no image -> empty", js._pnp_photo_code({"imageName": None}) == "")
check("pnp: other host -> empty",
      js._pnp_photo_code({"imageName": "https://evil.example/images/054e0d16-d128-47da-b3f8-88e2ee3b8c39.JPG"}) == "")
grp = {"location": {"name": "PICK-n-PULL Newark", "city": "Newark", "state": "CA"},
       "vehicles": [{"id": "1", "imageName": "https://cdn.row52.com/images/054e0d16-d128-47da-b3f8-88e2ee3b8c39.JPG"},
                    {"id": "2", "imageName": None}]}
out = []
js._pnp_ingest_group(grp, out)
check("pnp ingest sets _photo", out[0].get("_photo") == "n054e0d16d12847dab3f888e2ee3b8c39")
check("pnp ingest: no photo -> no _photo", "_photo" not in out[1])

# --- published with the extras file and the shard manifest -------------------
payload = {"schemaVersion": 2, "scrapedAt": "2026-11-06T00:00:00Z",
           "fields": ["id", "vin", "year", "make", "model", "row", "dateAdded", "yard", "partSet", "maxValue", "premium"],
           "yardFields": ["location", "city", "state", "lat", "lng", "radius", "kind"],
           "yards": [["Y - A", "A", "CA", 37.5, -122.0, 100, "yard"]], "partSets": [], "vpic": {},
           "vehicles": [[1, "", 2010, "Honda", "Civic", "1", "2026-11-01", 0, -1, 0, 0],
                        [2, "", 2011, "Honda", "Fit", "2", "2026-11-01", 0, -1, 0, 0]]}
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    old_extras, old_data = js.EXTRAS_FILE, js.DATA_DIR
    js.EXTRAS_FILE, js.DATA_DIR = td / "vehicle_extras.json", td
    try:
        js._write_extras_and_shards(payload, {"1": ["p5"], "2": ["r7", "Red"]})
        written = json.loads(js.EXTRAS_FILE.read_text())
        man_p = td / "inv" / "manifest.json"
        man = json.loads(man_p.read_text()) if man_p.exists() else {}
    finally:
        js.EXTRAS_FILE, js.DATA_DIR = old_extras, old_data
check("extras file publishes photoSources", set(written.get("photoSources", {})) == set(PUB))
check("extras file: r code dropped, color kept", written["extras"] == {"1": ["p5"], "2": ["", "Red"]}, written["extras"])
check("shard manifest publishes photoSources", set(man.get("photoSources", {})) == set(PUB), sorted(man))

# --- same behaviour in JavaScript ---------------------------------------------
node = shutil.which("node")
if node:
    script = """
const pub = JSON.parse(process.argv[1]), cases = JSON.parse(process.argv[2]);
const out = {};
for (const code of cases) {
  let hit = null;
  for (const [k, s] of Object.entries(pub)) for (const p of s.patterns) {
    const m = new RegExp(p.code).exec(code);
    if (!hit && m && m[0] === code) hit = [k, p.card.replace(/\\{(\\d)\\}/g, (_, i) => m[+i])];
  }
  out[code] = hit;
}
console.log(JSON.stringify(out));
"""
    allc = list(CASES) + REJECT
    res = json.loads(subprocess.run([node, "-e", script, json.dumps(PUB), json.dumps(allc)],
                                    capture_output=True, text=True, check=True).stdout)
    for code in allc:
        py = rebuild(code)
        jsr = res[code]
        check(f"JS matches Python: {code[:40]}", (list(py) if py[0] else None) == jsr, (py, jsr))
else:
    print("SKIP  JavaScript parity (node not installed)")

if fails:
    print(f"\n{len(fails)} FAILED")
    sys.exit(1)
print("\nall passed")
