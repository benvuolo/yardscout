"""§11.4 sample builder for OEM Likely groups (scratch; not committed).

Runs curate in-process for one namespace with the given pins, draws a seeded
sample of shippable Likely groups (stratified: every category represented,
proportional otherwise, cross-make / cross-base-model first within a
category) and donor pairs (seeker T, donor T' of another feed model inside a
shippable group not already sampled), and writes one dossier per item with
the raw evidence: the class's product-page records (fitment rows, notes,
evidence lines) and every app vehicle-year's own-page list rows, plus the
lot's vPIC body mix per app (body-variant trap check).

usage: sample.py NS RAW_SHA INVENTORY DECODES SEED OUTDIR [N_GROUPS N_PAIRS]
"""
import sys, json, random, gzip, collections, re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'scraper' / 'oem_fitment'))
sys.path.insert(0, str(REPO / 'scraper'))
import curate as C  # noqa: E402
import adapters as A  # noqa: E402
import model_map as MM  # noqa: E402
import policy  # noqa: E402
import junkyard_scraper as js  # noqa: E402

HOLD = set(js.GROUP_HOLD_CATS)

ns, raw, invp, decp, seed, outdir = sys.argv[1:7]
NG = int(sys.argv[7]) if len(sys.argv) > 7 else 30
NP = int(sys.argv[8]) if len(sys.argv) > 8 else 30
out = Path(outdir)
out.mkdir(parents=True, exist_ok=True)
mm = MM.ModelMap(MM.load(str(MM.MODEL_MAP_PATH)))
inv = MM.load_inventory(invp)
src = A.RawSource(ref=raw)
bodies = C.model_bodies(inv, js, decp)
opts = C.Options(model_map=mm, model_map_path=MM.MODEL_MAP_PATH, inventory=inv, js=js, model_bodies=bodies,
                 body_counts=C.model_body_counts(inv, js, decp))
cur, doc = C.curate(ns, src, opts)

# lot body mix per (make, model, year) from vPIC decodes (live inventory pin)
dec = json.loads(gzip.open(decp).read())
f = inv['fields']
iv, imk, imd, iy = f.index('vin'), f.index('make'), f.index('model'), f.index('year')
bmix = collections.defaultdict(collections.Counter)
for r in inv['vehicles']:
    b = js.body_style_from_vpic(dec.get(r[iv]), r[imk]) or 'unknown'
    bmix[(r[imk], r[imd], r[iy])][b] += 1

groups = [g for g in doc['likely'] if g['cat'] not in HOLD]
rng = random.Random(int(seed))


def cls_of(g):
    for (key, cat), c in cur.classes.items():
        if cat == g['cat'] and sorted(c.pns) == sorted(g['pn']):
            return c
    raise KeyError(g['id'])


def Ts_of(g):
    ts = []
    for a in g['apps']:
        for mk in str(a[0]).split('|'):
            for y in range(a[2], a[3] + 1):
                ts.append((mk, a[1], y))
    return ts


def rec_text(r):
    rows = []
    for fr in r.rows:
        rows.append(f"      [{fr.layout}] {fr.lo}-{fr.hi} {fr.make} {fr.model} | trims={fr.trims} | "
                    f"engines={fr.engines} | options={fr.options} | raw={fr.raw!r}")
    ev = r.evidence_lines or []
    lines = [f"  RECORD {r.pointer} site={r.site} seed={r.seed} pn={r.pn} name={r.name!r} aux={r.aux!r}",
             f"    description={r.description!r} position={r.position!r} list_location={r.list_location}",
             f"    seed-page notes={r.note_texts} replaces={r.replaces} replaced_by={r.replaced_by} "
             f"list_replaced_by={r.list_replaced_by} reman={r.reman_flag} flags={r.flags} problems={r.problems}",
             f"    list_url={r.list_url}", f"    product_url={r.product_url}", f"    retrieved={r.retrieved}",
             f"    fitment rows ({len(r.rows)}):"] + rows
    lines.append(f"    evidence_lines: {len(ev)} (rendered={r.rendered} total={r.total}; structured rows above re-checked by ci_audit)")
    return lines


def _same_part(a, b):
    w = lambda x: [t for t in re.split(r"[^a-z0-9]+", (x or "").lower()) if t][:6]
    return w(a) == w(b)


def own_text(T, cat, c):
    on, notes, srcs, ptrs, kind = cur.own_page(T, cat, c)
    rows = [lr for lr in cur.t_list_rows.get((T, cat), []) if policy.pn_key(cur.ns, lr.pn) == c.key]
    lines = [f"  OWN PAGE {T} on_page={on} via={kind} notes={notes} pointers={ptrs}",
             f"    lot body mix: {dict(bmix.get(T, {}))}  lot cars: {cur.inv_counts.get(T, 0)}"]
    for lr in rows:
        lines.append(f"    row {lr.pointer} catalog/variant={lr.variant!r} section={lr.section} main={lr.main!r} "
                     f"aux={lr.aux!r} group={lr.group!r} remark={lr.remark!r} notes={lr.notes} "
                     f"loc={lr.locations} matched={lr.matched} excl={lr.excluded_by} replace={lr.replace}")
        lines.append(f"        {lr.list_url.split('/parts-list/')[-1][:90]} {lr.retrieved[:10]}")
    # other numbers in the same category on T's own pages (split check)
    myname = (rows[0].main or rows[0].group) if rows else (c.records[0].name if c.records else "")
    others = sorted({(lr.pn, lr.main or lr.group, tuple(lr.notes)) for lr in cur.t_list_rows.get((T, cat), [])
                     if policy.pn_key(cur.ns, lr.pn) != c.key and lr.matched and _same_part(lr.main or lr.group, myname)})
    if others:
        lines.append(f"    same-part numbers on this page ({len(others)}):")
        lines += [f"      - {pn} {nm!r} notes={list(nt)}" for pn, nm, nt in others[:40]]
    if kind == 'seed':
        recs = [r for r in cur.t_seed_records.get((T, cat), []) if r.key == c.key]
        lines.append(f"    seed-proxy records: {[r.pointer for r in recs]}")
    return lines


# stratified group draw
bycat = collections.defaultdict(list)
for g in groups:
    bycat[g['cat']].append(g)
cats = sorted(bycat)
quota = {c: 1 for c in cats}
rest = NG - len(cats)
tot = len(groups)
for c in cats:
    quota[c] += int(rest * len(bycat[c]) / tot)
while sum(quota.values()) < NG:
    c = max(cats, key=lambda c: len(bycat[c]) / quota[c])
    quota[c] += 1
picked = []
for c in cats:
    pool = list(bycat[c])
    rng.shuffle(pool)
    # cross-make / cross-base-model first
    pool.sort(key=lambda g: -len({policy.base_model(a[0].split('|')[0], a[1]) for a in g['apps']}))
    picked += pool[:min(quota[c], len(pool))]
picked_ids = {g['id'] for g in picked}

# pairs: from groups not sampled, one pair per group, random seeker/donor of different feed models
pair_pool = [g for g in groups if g['id'] not in picked_ids]
rng.shuffle(pair_pool)
pairs = []
for g in pair_pool:
    ts = Ts_of(g)
    models = sorted({(t[0], t[1]) for t in ts})
    if len(models) < 2:
        continue
    m1, m2 = rng.sample(models, 2)
    s = rng.choice([t for t in ts if (t[0], t[1]) == m1])
    d = rng.choice([t for t in ts if (t[0], t[1]) == m2])
    pairs.append((g, s, d))
    if len(pairs) >= NP:
        break

lines = [f"# §11.4 sample, ns={ns}, raw={raw}, seed={seed}, inventory={invp}, decodes={decp}",
         f"# shippable groups {len(groups)} (held cats excluded: {sorted(HOLD)}); categories {dict(collections.Counter(g['cat'] for g in groups))}",
         f"# sampled groups {len(picked)} quota {quota}; pairs {len(pairs)}", ""]
index = []
for i, g in enumerate(picked, 1):
    c = cls_of(g)
    tag = f"G{i:02d}"
    index.append({"item": tag, "id": g['id'], "cat": g['cat'], "pn": g['pn'], "apps": g['apps'], "note": g['note'],
                  "cars": g.get('cars')})
    lines += [f"=== {tag} {g['id']} cat={g['cat']} pn={g['pn']} cars={g.get('cars')}",
              f"  apps={g['apps']}", f"  note={g['note']!r}", f"  reason={g['reason']} packaging={c.packaging!r}"]
    for r in c.records:
        lines += rec_text(r)
    for T in Ts_of(g):
        lines += own_text(T, g['cat'], c)
    lines.append("")
for j, (g, s, d) in enumerate(pairs, 1):
    c = cls_of(g)
    tag = f"P{j:02d}"
    index.append({"item": tag, "id": g['id'], "cat": g['cat'], "pn": g['pn'], "seeker": s, "donor": d,
                  "note": g['note'], "apps": g['apps']})
    lines += [f"=== {tag} seeker={s} donor={d} via {g['id']} cat={g['cat']} pn={g['pn']}",
              f"  apps={g['apps']}", f"  note={g['note']!r}", f"  packaging={c.packaging!r}"]
    for r in c.records:
        lines += rec_text(r)
    lines += own_text(s, g['cat'], c)
    lines += own_text(d, g['cat'], c)
    lines.append("")
(out / f"{ns}_sample_{seed}.txt").write_text("\n".join(lines))
(out / f"{ns}_sample_{seed}.json").write_text(json.dumps(index, indent=1))
print(f"{ns}: {len(groups)} shippable; wrote {len(picked)} groups + {len(pairs)} pairs to {out}")
