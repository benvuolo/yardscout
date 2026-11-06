#!/usr/bin/env python3
"""Round-3 photo capture (2026-11-06): URG/iis-pro-upull cards, BYOT,
Wilbert's, Nevada Pic-A-Part, Sturtevant, and the Pull-N-Save
check-once placeholder logic (no network; fake responses + temp DB).
Run:  python3 scraper/test_photo_capture.py   (offline)"""
import hashlib
import io
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import db  # noqa: E402
import junkyard_scraper as js  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f" — {detail}"))
    if not ok:
        fails.append(name)


# --- URG / iis-pro-upull -----------------------------------------------------
CF = "https://da8h1v3w8q6n5.cloudfront.net"
PAGE = f'''
<div class="card-img " data-vstock-no="PAP175750"> <a href="{CF}/tt87/images/PAP175750/PAP175750-1-HDDN5D_1.jpg" data-lightbox="x">
<div class="card-img " data-vstock-no="PAP016029"> <a href="/wp-content/uploads/2025/10/Pick-A-Part-logo-placeholder-1.png" data-lightbox="y">
<div class="card-img " data-vstock-no="PAP1"> <a href="{CF}/tt87/images/PAP2/PAP2-1-X_1.jpg">
<div class="card-img " data-vstock-no="PAP3"> <a href="https://evil.example/tt87/images/PAP3/PAP3_1.jpg">
'''
codes = js._iis_upull_photo_codes(PAGE)
check("URG: photo card -> code", codes.get("PAP175750") == "utt87/PAP175750/PAP175750-1-HDDN5D_1", codes)
check("URG: logo placeholder -> no code", "PAP016029" not in codes)
check("URG: image of another stock -> no code", "PAP1" not in codes)
check("URG: other host -> no code", "PAP3" not in codes)

# --- BYOT ----------------------------------------------------------------------
B = "https://storage.googleapis.com/byotautoparts.appspot.com/yard_inventory/"
check("BYOT: first image -> code", js._byot_photo_code({"images": [B + "8e86-e286-5094-248f", B + "f885-478a-35ab-45ab"]}) == "b8e86-e286-5094-248f")
check("BYOT: none -> empty", js._byot_photo_code({"images": []}) == "" and js._byot_photo_code({}) == "")
check("BYOT: other bucket -> empty", js._byot_photo_code({"images": ["https://storage.googleapis.com/other/yard_inventory/8e86-e286-5094-248f"]}) == "")

# --- Wilbert's -----------------------------------------------------------------
W = "https://buyingtoolrg.blob.core.windows.net/vehicleimagesresized/1G1JC6SH6C4172184/179380681910558733016406597819920261104_104113.jpg"
check("Wilbert's: first URL -> code", js._wilberts_photo_code({"ImageURLs": [W]}) == "l1G1JC6SH6C4172184/179380681910558733016406597819920261104_104113")
check("Wilbert's: none -> empty", js._wilberts_photo_code({"ImageURLs": []}) == "")
check("Wilbert's: other container -> empty", js._wilberts_photo_code({"ImageURLs": [W.replace("vehicleimagesresized", "raw")]}) == "")

# --- Nevada Pic-A-Part / Sturtevant ---------------------------------------------
NB = '<img src="https://www.nvpap.com/photos/preview_photos/H065291_left.JPG" loading="lazy">'
check("NVPAP: preview -> code", js._nvpap_photo_code(NB, "H065291") == "vH065291_left")
check("NVPAP: other stock -> empty", js._nvpap_photo_code(NB, "H000001") == "")
SB = '<td><a href="../InventoryPhotos/STK049735.JPG"><img src="../InventoryPhotos/STK049735.JPG" width="80" /></a></td>'
check("Sturtevant: row img -> code", js._sturtevant_photo_code(SB, "STK049735") == "tSTK049735")
check("Sturtevant: no img -> empty", js._sturtevant_photo_code("<td></td>", "STK049735") == "")

# --- Pull-N-Save ------------------------------------------------------------------
cell = "<img width='100' src='https://app.pullnsaveapp.com/v1/Vehicles/Images/StockId/STK134723-1/OrderId/1'>"
check("PNS key from the row's img", js._pns_photo_key(cell, "STK134723") == "STK134723-1")
check("PNS key: other stock -> empty", js._pns_photo_key(cell, "STK999") == "")

PLACEHOLDER = b"x" * 3474
js.PNS_PLACEHOLDER_SHA256 = hashlib.sha256(PLACEHOLDER).hexdigest()


class FakeResp:
    def __init__(self, status=200, ctype="image/png", length=None, body=b""):
        self.status_code = status
        self.headers = {"content-type": ctype}
        if length is not None:
            self.headers["content-length"] = str(length)
        buf = io.BytesIO(body)

        class Raw:
            def read(self, n, decode_content=True):
                return buf.read(n)
        self.raw = Raw()


check("classify: big image -> photo", js._pns_classify_photo(FakeResp(length=110004)) == "photo")
check("classify: placeholder -> none", js._pns_classify_photo(FakeResp(length=3474, body=PLACEHOLDER)) == "none")
check("classify: unknown small image -> none (fail closed)", js._pns_classify_photo(FakeResp(length=500, body=b"y" * 500)) == "none")
check("classify: 404 -> unknown", js._pns_classify_photo(FakeResp(status=404, length=10)) is None)
check("classify: html -> unknown", js._pns_classify_photo(FakeResp(ctype="text/html", length=99999)) is None)
check("classify: no length -> unknown", js._pns_classify_photo(FakeResp()) is None)

with tempfile.TemporaryDirectory() as td:
    db.DB_FILE = Path(td) / "h.db"
    now = datetime(2026, 11, 6, 12, tzinfo=timezone.utc)
    cars = [{"id": f"pns-stk{i}", "dateAdded": f"2026-11-0{i}", "_pns_photo_key": f"STK{i}00-1"} for i in range(1, 6)]
    cars.append({"id": "pns-x", "dateAdded": "2026-11-06", "_pns_photo_key": ""})
    asked = []
    answers = {"STK100-1": "photo", "STK200-1": "none", "STK300-1": "photo", "STK400-1": None, "STK500-1": "photo"}

    def fake(k):
        asked.append(k)
        return answers[k]
    js.PNS_PHOTO_CHECK_MAX = 3
    r = js._pns_apply_photo_checks(cars, check=fake, now=now, sleep=lambda s: None)
    check("PNS: newest first, capped", asked == ["STK500-1", "STK400-1", "STK300-1"], asked)
    check("PNS: only checked photos get codes",
          {c["id"]: c.get("_photo") for c in cars if c.get("_photo")} == {"pns-stk5": "sSTK500-1", "pns-stk3": "sSTK300-1"},
          [c.get("_photo") for c in cars])
    check("PNS: error is not stored (retried next scan)", "STK400-1" not in db.load_pns_photo_checks())
    asked.clear()
    for c in cars:
        c.pop("_photo", None)
    js._pns_apply_photo_checks(cars, check=fake, now=now, sleep=lambda s: None)
    check("PNS: second scan checks only the rest", asked == ["STK400-1", "STK200-1", "STK100-1"], asked)
    asked.clear()
    js._pns_apply_photo_checks(cars, check=fake, now=now, sleep=lambda s: None)
    check("PNS: nothing re-checked within 3 days except the error", asked == ["STK400-1"], asked)
    asked.clear()
    later = datetime(2026, 11, 10, tzinfo=timezone.utc)
    answers["STK200-1"] = "photo"
    for c in cars:
        c.pop("_photo", None)
    js._pns_apply_photo_checks(cars, check=fake, now=later, sleep=lambda s: None)
    check("PNS: 'none' re-checked after 3 days and upgraded", "STK200-1" in asked and cars[1].get("_photo") == "sSTK200-1", (asked, cars[1]))
    db.store_pns_photo_checks({"STK100-1": "none"}, "2026-11-11T00:00:00Z")
    check("PNS: a 'photo' is never downgraded", db.load_pns_photo_checks()["STK100-1"][0] == "photo")
    errs = []
    js.PNS_PHOTO_CHECK_MAX = 50
    many = [{"id": f"e{i}", "dateAdded": "2026-11-06", "_pns_photo_key": f"STK9{i:02d}-1"} for i in range(20)]
    js._pns_apply_photo_checks(many, check=lambda k: errs.append(k), now=later, sleep=lambda s: None)
    check("PNS: stops after 5 consecutive errors", len(errs) == 5, len(errs))

if fails:
    print(f"\n{len(fails)} FAILED")
    sys.exit(1)
print("\nall passed")
