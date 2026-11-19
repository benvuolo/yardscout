#!/usr/bin/env python3
"""VIN model mismatch (2026-11-19): _vpic_mismatch_msg flags a car whose VIN
decodes as another model only when the hand-sorted table
(scraper/vin_model_names.json) says the pair is 'different'.
Run:  python3 scraper/test_vin_model_mismatch.py   (offline)"""
import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js  # noqa: E402

fails = []
passes = 0


def check(name, ok, detail=""):
    global passes
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f" — {detail}"))
    if ok:
        passes += 1
    else:
        fails.append(name)


def dec(make, model, year=0, **kw):
    return {"make": make, "model": model, "modelYear": str(year or ""), **kw}


def msg(make, model, year, dmake, dmodel, dyear=None, **kw):
    js._VIN_MODEL_TABLE = None if kw.pop("reload", False) else js._VIN_MODEL_TABLE
    return js._vpic_mismatch_msg({"make": make, "model": model, "year": year},
                                 dec(dmake, dmodel, dyear if dyear is not None else year), **kw)


# ---- the table itself ----
data = json.loads(js.VIN_MODEL_NAMES_FILE.read_text())
buckets = ("same", "different", "unsure", "decode_wrong")
check("table: four lists", all(isinstance(data.get(b), list) for b in buckets))
check("table: every entry has make, listed, decoded, cars, basis",
      all(all(k in e and e[k] not in (None, "") for k in ("make", "listed", "decoded", "cars", "basis"))
          for b in buckets for e in data[b]))
keys = [js._vin_model_key(e["make"], e["listed"], e["decoded"]) for b in buckets for e in data[b]]
check("table: no pair in two lists", len(keys) == len(set(keys)), str(len(keys) - len(set(keys))))
check("table: every pair really shares no word (else it would never be looked up)",
      all(js._model_words_disjoint(e["listed"], js.normalize_model(e["decoded"], e["make"]))
          for b in buckets for e in data[b]))

# ---- naming pairs: never flagged ----
for mk, li, dm, y in [("Chevrolet", "K1500", "GMT-400", 1995), ("Subaru", "Outback", "Legacy", 2002),
                      ("Volkswagen", "CC", "Passat", 2012), ("Mercedes-Benz", "ML350", "M-Class", 2008),
                      ("Ram", "1500", "Ram", 2011), ("Chevrolet", "C/K 1500", "GMT-400", 1994),
                      ("MINI", "Cooper", "Hardtop", 2012), ("Infiniti", "FX", "FX35", 2007)]:
    m = msg(mk, li, y, mk.upper(), dm)
    check(f"naming pair not flagged: {mk} {li} / {dm}", m is None, str(m))

# ---- different pairs: flagged with the year/make wording family ----
for mk, li, dm, y, want in [
        ("Infiniti", "QX80", "QX60", 2017, "VIN decodes as Infiniti QX60 (listed QX80)"),
        ("Subaru", "Outback", "Impreza", 2006, "VIN decodes as Subaru Impreza (listed Outback)"),
        ("Fiat", "500", "500L", 2014, "VIN decodes as Fiat 500L (listed 500)"),
        ("Lexus", "GS 300", "RX", 2003, "VIN decodes as Lexus RX (listed GS 300)"),
        ("Chevrolet", "Silverado 1500", "Suburban", 2000, "VIN decodes as Chevrolet Suburban (listed Silverado 1500)")]:
    m = msg(mk, li, y, mk.upper(), dm)
    check(f"different pair flagged: {mk} {li} / {dm}", m == want, str(m))

# ---- the pairs the hub expected different but the VIN says otherwise ----
for mk, li, dm, y in [("Chevrolet", "Silverado 1500", "S-10", 2001), ("Hyundai", "Genesis", "Equus", 2014)]:
    m = msg(mk, li, y, mk.upper(), dm)
    check(f"decode_wrong pair not flagged: {mk} {li} / {dm}", m is None, str(m))
check("decode_wrong lists Silverado / S-10 and Genesis / Equus",
      {(e["listed"], e["decoded"]) for e in data["decode_wrong"]} >= {("Silverado 1500", "S-10"), ("Genesis", "Equus")})

# ---- unsure and unknown pairs: not flagged ----
check("unsure pair not flagged (Legacy / Outback)", msg("Subaru", "Legacy", 2012, "SUBARU", "Outback") is None)
check("pair in no list not flagged", msg("Toyota", "Corolla", 2010, "TOYOTA", "Hilux") is None)
check("names sharing a word not looked up", msg("Ford", "F-150 XL", 2010, "FORD", "F-150") is None)
check("names equal once punctuation drops not looked up", msg("Honda", "CRV", 2010, "HONDA", "CR-V") is None)
check("decoded model blank: not flagged", msg("Infiniti", "QX80", 2017, "INFINITI", "") is None)

# ---- year and make behaviour unchanged ----
check("year only", msg("Honda", "Civic", 2005, "HONDA", "Civic", 2006) == "VIN decodes as 2006 (listed 2005)")
check("make only (no model check across makes)",
      msg("Acura", "ILX", 2014, "CHEVROLET", "Cruze") == "VIN decodes as Chevrolet (listed Acura)",
      msg("Acura", "ILX", 2014, "CHEVROLET", "Cruze"))
check("brand family still not a make mismatch", msg("Scion", "tC", 2008, "TOYOTA", "tC") is None)
check("year + model joined like year + make",
      msg("Infiniti", "QX80", 2016, "INFINITI", "QX60", 2017)
      == "VIN decodes as 2017 (listed 2016); VIN decodes as Infiniti QX60 (listed QX80)")
check("check_model=False keeps year/make only", msg("Infiniti", "QX80", 2017, "INFINITI", "QX60", check_model=False) is None)
check("_trans_make_conflict: a model-only mismatch is not a make conflict",
      js._trans_make_conflict({"make": "Infiniti", "model": "QX80", "year": 2017}, dec("INFINITI", "QX60", 2017)) is False)
check("no decode: None", js._vpic_mismatch_msg({"make": "Honda", "model": "Civic", "year": 2005}, None) is None)

# ---- stats for the scan log ----
js.MODEL_MISMATCH_STATS.clear()
js.MODEL_MISMATCH_UNCLASSIFIED.clear()
msg("Infiniti", "QX80", 2017, "INFINITI", "QX60", stats=True)
msg("Chevrolet", "K1500", 1995, "CHEVROLET", "GMT-400", stats=True)
msg("Toyota", "Corolla", 2010, "TOYOTA", "Hilux", stats=True)
msg("Toyota", "Corolla", 2011, "TOYOTA", "Hilux", stats=True)
check("stats count verdicts", js.MODEL_MISMATCH_STATS == {"different": 1, "same": 1, "unclassified": 2}, str(js.MODEL_MISMATCH_STATS))
err = io.StringIO()
with contextlib.redirect_stderr(err):
    js._log_model_mismatch_stats()
line = err.getvalue()
check("log: one line, flagged count and top unclassified pair",
      line.count("\n") == 1 and "1 car(s) flagged" in line and "Toyota Corolla / Hilux 2" in line, line)

# ---- end to end through enrich_vehicles' call (stats=True) on a QX80 with a QX60 VIN ----
v = {"make": "Infiniti", "model": "QX80", "year": 2017}
check("enrich-style call sets the flag", js._vpic_mismatch_msg(v, dec("INFINITI", "QX60", 2017), stats=True)
      == "VIN decodes as Infiniti QX60 (listed QX80)")

# ---- a malformed table never fails the scan ----
real = js.VIN_MODEL_NAMES_FILE
with tempfile.TemporaryDirectory() as td:
    for name, text in [("not json", "{not json"), ("missing list", json.dumps({"same": []})),
                       ("bad entry", json.dumps({"same": [], "different": [{"make": "Infiniti", "listed": 5}],
                                                 "unsure": [], "decode_wrong": []})),
                       ("missing file", None)]:
        f = Path(td) / "t.json"
        if text is None:
            f = Path(td) / "nope.json"
        else:
            f.write_text(text)
        js.VIN_MODEL_NAMES_FILE = f
        js._VIN_MODEL_TABLE = None
        err = io.StringIO()
        raised = None
        try:
            with contextlib.redirect_stderr(err):
                m1 = js._vpic_mismatch_msg({"make": "Infiniti", "model": "QX80", "year": 2016}, dec("INFINITI", "QX60", 2017))
                m2 = js._vpic_mismatch_msg({"make": "Acura", "model": "ILX", "year": 2014}, dec("CHEVROLET", "Cruze", 2014))
        except Exception as e:  # noqa: BLE001
            raised = e
        check(f"malformed table ({name}): no exception", raised is None, repr(raised))
        check(f"malformed table ({name}): falls back to year/make only",
              raised is None and m1 == "VIN decodes as 2017 (listed 2016)" and m2 == "VIN decodes as Chevrolet (listed Acura)",
              f"{m1!r} {m2!r}")
        check(f"malformed table ({name}): one warning", err.getvalue().count("WARNING") == 1, err.getvalue())
js.VIN_MODEL_NAMES_FILE = real
js._VIN_MODEL_TABLE = None
check("real table reloads after the fallback", msg("Infiniti", "QX80", 2017, "INFINITI", "QX60") is not None)

print(f"\n{passes} passed, {len(fails)} failed")
if fails:
    print("FAILED:", ", ".join(fails))
    sys.exit(1)
