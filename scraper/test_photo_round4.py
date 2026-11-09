#!/usr/bin/env python3
"""Photo round 4 (2026-11-09): Ario image_url, Pull-A-Part image-service
lookups, Fenix detail-photo checks, YardSmart thumbnails (expiry), and the
shared per-car lookup cache. Offline.
Run:  python3 scraper/test_photo_round4.py"""
import base64
import json
import re
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


PUB = js.published_photo_sources(js.load_photo_sources())


def build(code, which="card"):
    for k, s in PUB.items():
        for p in s["patterns"]:
            m = re.fullmatch(p["code"], code)
            if m:
                u = p[which]
                for i, g in enumerate(m.groups(), 1):
                    u = u.replace("{%d}" % i, g)
                return k, u
    return None, None


# --- Ario --------------------------------------------------------------------
YMS = "https://tlcgcwhkzwvdbdoceyse.supabase.co/storage/v1/object/public/yms-inventory-images/"
u = YMS + "foss-winston-salem/STK030774/1793970635534_0.jpg"
c = js._ario_photo_code(u + "," + YMS + "foss-winston-salem/STK030774/1793970635534_1.jpg", "foss-winston-salem")
check("Ario YMS: first URL -> code", c == "afoss-winston-salem/STK030774/1793970635534_0", c)
check("Ario YMS: credited to the tenant", build(c) == ("ario_foss", u), build(c))
check("Ario YMS: other yard's folder -> none", js._ario_photo_code(u, "ryans-pick-a-part-detroit") == "")
check("Ario Paul's CDN", js._ario_photo_code("https://d1vnbry5hm94g5.cloudfront.net/ADY/HZC/NJO/27E/I.jpg", "x")
      == "cADY/HZC/NJO/27E/I")
check("Ario Copart -> none", js._ario_photo_code(
    "https://cs.copart.com/v1/AUTH_svc.pdoc00001/lpp/0926/292f83de350341528436bc9b783a7db2_vhrs.jpg", "x") == "")
check("Ario empty -> none", js._ario_photo_code("", "x") == "" and js._ario_photo_code(None, "x") == "")

# --- Pull-A-Part -------------------------------------------------------------------
W = "https://papimages.blob.core.windows.net/carinventory/9/2026/11/20261107095043_9_1254173_1.png"
c = js._pap_photo_code_from_webpath(W, "9", "1254173", "1")
check("PAP webPath -> code", c == "q9/20261107095043/1254173/1", c)
check("PAP code -> same URL", build(c) == ("pap", W), build(c))
check("PAP: other car's path -> none", js._pap_photo_code_from_webpath(W, "9", "1254174", "1") == "")
check("PAP: folder month != name month -> none", js._pap_photo_code_from_webpath(
    W.replace("/2026/11/", "/2026/10/"), "9", "1254173", "1") == "")

# --- Fenix --------------------------------------------------------------------------
check("Fenix code -> URL", build("f202611203022216") ==
      ("fenix", "https://fenixupull.com/wp-content/uploads/2026/11/203022216_1.jpg"))


class H:
    def __init__(self, st, ct="image/jpeg"):
        self.status_code, self.headers = st, {"content-type": ct}


from unittest import mock  # noqa: E402
js.FENIX_DELAY_SEC = 0
with mock.patch.object(js.requests, "head", side_effect=[H(404), H(200)]) as h:
    r = js._fenix_lookup_photo("204015155|2026-09-30")
check("Fenix: next-month upload found", r == ("photo", "f202610204015155") and h.call_count == 2, r)
with mock.patch.object(js.requests, "head", side_effect=[H(404), H(404)]):
    check("Fenix: 404 twice -> none", js._fenix_lookup_photo("1|2026-12-15") == ("none", ""))
with mock.patch.object(js.requests, "head", return_value=H(503)):
    check("Fenix: server error -> unknown (retry)", js._fenix_lookup_photo("2|2026-11-01") is None)

# --- iPull-uPull (round 5) ----------------------------------------------------------
IC = "https://ipullupull.com/wp-content/uploads/ipullupull-catalog/"
check("iPull: API imageUrl -> code", js._ipull_photo_code(IC + "FRE118500/Photo-Oct-26-2026-3-25-23-PM.jpg", "FRE118500")
      == "iFRE118500/Photo-Oct-26-2026-3-25-23-PM")
check("iPull: code -> same URL", build("iSAC053156/SAC053156_1") == ("ipull", IC + "SAC053156/SAC053156_1.jpg"))
check("iPull: other stock's folder -> none", js._ipull_photo_code(IC + "SAC1/x.jpg", "SAC2") == "")
check("iPull: other host -> none", js._ipull_photo_code("https://evil.example/ipullupull-catalog/SAC1/x.jpg", "SAC1") == "")
with mock.patch.object(js, "_vinplus_search", return_value=[
        {"stock": "SAC053156", "imageUrl": IC + "SAC053156/SAC053156_1.jpg"}, {"stock": "SAC9", "imageUrl": ""}]):
    cars = [{"id": "ipull-sac053156", "make": "Honda"}, {"id": "ipull-sac9", "make": "Honda"}]
    js._ipull_apply_api_photos(cars)
check("iPull: API pass sets codes only where the API has a photo",
      cars[0].get("_photo") == "iSAC053156/SAC053156_1" and "_photo" not in cars[1], cars)

check("US Auto Supply: own photo -> code", js._vinplus_photo_code(
    "https://usautosupplymi.com/inventory-photos/STK187533.jpg", "STK187533", "US Auto Supply") == "mSTK187533")
check("US Auto Supply: code -> URL", build("mSTK187533") ==
      ("usautosupply", "https://usautosupplymi.com/inventory-photos/STK187533.jpg"))
check("US Auto Supply: other stock -> none", js._vinplus_photo_code(
    "https://usautosupplymi.com/inventory-photos/STK1.jpg", "STK2", "US Auto Supply") == "")

# --- YardSmart ----------------------------------------------------------------------
def blob(exp):
    raw = json.dumps({"_rails": {"message": "BAhpBA2Paw==", "exp": exp, "pur": "blob_id"}}, separators=(",", ":"))
    return base64.b64encode(raw.encode()).decode()


V1 = "b0c21fdd98391a3d8083f052f5b3fabb2e2c9079"
D = "a" * 40
NOW = datetime(2026, 11, 9, 0, 0, tzinfo=timezone.utc)


def rep(b, var=V1):
    return (f'<img src="https://api.yardsmartapp.com/rails/active_storage/representations/redirect/'
            f'{b}--{D}/eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaDd--{var}/IMG_1.jpeg">')


c = js._yardsmart_photo_code(rep(blob(None)), "ruperts", now=NOW)
check("YardSmart: non-expiring -> code", c.startswith("yru1") and c.endswith("--" + D), c)
k, url = build(c)
check("YardSmart: rebuilt URL has the full blob id",
      k == "ys_ruperts" and (blob(None) + "--" + D) in url and V1 in url, url)
check("YardSmart: 10 h left -> code",
      js._yardsmart_photo_code(rep(blob("2026-11-09T10:00:00.000Z")), "upullitne", now=NOW).startswith("yne1"))
check("YardSmart: 2 h left -> none",
      js._yardsmart_photo_code(rep(blob("2026-11-09T02:00:00.000Z")), "upullitne", now=NOW) == "")
check("YardSmart: unknown variation -> none",
      js._yardsmart_photo_code(rep(blob(None), var="f" * 40), "ruperts", now=NOW) == "")
check("YardSmart: unknown site -> none", js._yardsmart_photo_code(rep(blob(None)), "nosuchsite", now=NOW) == "")
check("YardSmart: JSON-escaped slashes",
      js._yardsmart_photo_code(rep(blob(None)).replace("/", "\\/"), "ruperts", now=NOW).startswith("yru1"))
bc = js._yardsmart_photo_code(
    "https://api.yardsmartapp.com/rails/active_storage/blobs/redirect/" + blob("2026-11-09T10:00:00.000Z")
    + "--" + D + "/IMG_0721.jpeg", sid="vl", now=NOW)
check("YardSmart blob (VinPlus) -> resized-thumbnail code", bc.startswith("yvl1"), bc)
k, url = build(bc)
check("YardSmart blob: credited per brand, rendered via representations (never the original)",
      k == "ys_vinplus_vl" and "/representations/redirect/" in url and "/blobs/" not in url, (k, url))
check("YardSmart blob: expired -> none", js._yardsmart_photo_code(
    "https://api.yardsmartapp.com/rails/active_storage/blobs/redirect/" + blob("2026-11-09T01:00:00.000Z")
    + "--" + D + "/a.jpg", sid="vl", now=NOW) == "")
check("Army's blob -> thumbnail code", js._yardsmart_photo_code(
    "https://api.yardsmartapp.com/rails/active_storage/blobs/redirect/" + blob(None) + "--" + D + "/a.jpg",
    "armys", now=NOW).startswith("yam1"))

# --- shared lookup cache -------------------------------------------------------------
with tempfile.TemporaryDirectory() as td:
    db.DB_FILE = Path(td) / "h.db"
    cars = [{"id": f"c{i}", "dateAdded": f"2026-11-0{i}"} for i in range(1, 6)]
    keyed = [(v, v["id"]) for v in cars]
    asked = []
    ans = {"c1": ("photo", "x1"), "c2": ("none", ""), "c3": None, "c4": ("photo", "x4"), "c5": ("photo", "x5")}

    def lk(k):
        asked.append(k)
        return ans[k]
    js.photo_lookup_pass("t", keyed, lk, cap=3, delay=0, now=NOW, sleep=lambda s: None)
    check("lookup: newest first, capped", asked == ["c5", "c4", "c3"], asked)
    check("lookup: codes set from cache", [v.get("_photo") for v in cars] == [None, None, None, "x4", "x5"])
    asked.clear()
    js.photo_lookup_pass("t", keyed, lk, cap=10, delay=0, now=NOW, sleep=lambda s: None)
    check("lookup: only the unknown/unasked next time", asked == ["c3", "c2", "c1"], asked)
    asked.clear()
    js.photo_lookup_pass("t", keyed, lk, cap=10, delay=0, now=NOW, sleep=lambda s: None)
    check("lookup: no repeats within the recheck window (except unknown)", asked == ["c3"], asked)
    check("lookup: sources kept apart", db.load_photo_lookups("other") == {})

if fails:
    print(f"\n{len(fails)} FAILED")
    sys.exit(1)
print("\nall passed")
