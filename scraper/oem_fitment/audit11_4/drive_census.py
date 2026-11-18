"""drive_census.py NS RAW INVENTORY DECODES GROUPS_JSON: every shippable Likely
group of GROUPS_JSON (e.g. the file as it is on main) whose app vehicle-years
the §5.16 drive rule (curate.Curation.drive_of) limits to one drive family or
leaves out, with the evidence class:
  split     - T's own pages in the category also show the other drive family
  unread    - the number sits on one drive's page / row only, and nothing on
              T's own pages in that category names the other drive (that page
              was not read for this category)
  ambiguous - the drive evidence is ambiguous or contradicts itself
Prints counts per category and one line per app vehicle-year. Read-only."""
import collections
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scraper" / "oem_fitment"))
sys.path.insert(0, str(REPO / "scraper"))
import adapters as A  # noqa: E402
import curate as C  # noqa: E402
import model_map as MM  # noqa: E402
import junkyard_scraper as js  # noqa: E402


def page_families(cur, T, cat):
    fam = set()
    gm = cur._gm_page_letters(T) if cur.ns == "gm" else None
    for lr in cur.t_list_rows.get((T, cat), []):
        d = C._row_drive(lr.notes, lr.site, gm, lr.variant)
        if d and d != C.DRIVE_AMBIGUOUS:
            fam |= {"4" if x in C._FOUR else "2" for x in d}
    for r in cur.t_seed_records.get((T, cat), []):
        d = C._row_drive(r.note_texts, r.site, gm, C._catalog_of(r.list_url))
        if d and d != C.DRIVE_AMBIGUOUS:
            fam |= {"4" if x in C._FOUR else "2" for x in d}
    return fam


def main(argv):
    ns, raw, invp, decp, gpath = argv[1:6]
    mm = MM.ModelMap(MM.load(str(MM.MODEL_MAP_PATH)))
    inv = MM.load_inventory(invp)
    cur, _doc = C.curate(ns, A.RawSource(ref=raw), C.Options(
        model_map=mm, model_map_path=MM.MODEL_MAP_PATH, inventory=inv, js=js,
        model_bodies=C.model_bodies(inv, js, decp), body_counts=C.model_body_counts(inv, js, decp)))
    hold = set(js.GROUP_HOLD_CATS)
    live = [g for g in json.loads(Path(gpath).read_text())["likely"] if g["cat"] not in hold]
    byk = {(cat, tuple(sorted(c.pns))): c for (_k, cat), c in cur.classes.items()}
    cnt, ts, groups = collections.Counter(), set(), 0
    for g in live:
        c = byk.get((g["cat"], tuple(sorted(g["pn"]))))
        if c is None:
            continue
        hit = False
        for a in g["apps"]:
            for y in range(a[2], a[3] + 1):
                T = (a[0], a[1], y)
                d = cur.drive_of(c, g["cat"], T)
                if d is None:
                    continue
                if d == C.DRIVE_AMBIGUOUS:
                    cls, lab = "ambiguous", "?"
                else:
                    mine = {"4" if x in C._FOUR else "2" for x in d}
                    cls, lab = ("split" if page_families(cur, T, g["cat"]) - mine else "unread"), C._drive_label(d)
                hit = True
                ts.add(T)
                cnt[(g["cat"], cls)] += 1
                print(f"{ns}\t{g['cat']}\t{g['pn'][0]}\t{T[0]} {T[1]} {T[2]}\t{lab}\t{cls}\t"
                      f"lot cars {cur.inv_counts.get(T, 0)}")
        groups += hit
    print(f"# {ns}: {len(live)} live groups, {groups} with an app vehicle-year limited to one drive; "
          f"{len(ts)} distinct vehicle-years, {sum(cur.inv_counts.get(T, 0) for T in ts)} lot cars")
    for k, v in sorted(cnt.items()):
        print(f"#   {k[0]} {k[1]}: {v} app-years")


if __name__ == "__main__":
    main(sys.argv)
