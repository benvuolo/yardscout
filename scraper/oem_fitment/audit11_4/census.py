"""Census of every shippable Likely group of one namespace for the failure
classes found in the nissan §11.4 rounds: per app vehicle-year, its own-page
matched rows' option column is read for engine codes (Infiniti displacement),
body codes vs the car's bodies, cab codes vs the note, production windows,
and the class's fitment rows for that model/year. Prints suspects only."""
import sys, json, re, collections
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'scraper' / 'oem_fitment'))
sys.path.insert(0, str(REPO / 'scraper'))
import curate as C, adapters as A, model_map as MM, policy  # noqa: E401,E402
import junkyard_scraper as js  # noqa: E402
ns, raw, invp, decp = sys.argv[1:5]
mm = MM.ModelMap(MM.load(str(MM.MODEL_MAP_PATH)))
inv = MM.load_inventory(invp)
cur, doc = C.curate(ns, A.RawSource(ref=raw), C.Options(
    model_map=mm, model_map_path=MM.MODEL_MAP_PATH, inventory=inv, js=js,
    model_bodies=C.model_bodies(inv, js, decp), body_counts=C.model_body_counts(inv, js, decp)))
HOLD = set(js.GROUP_HOLD_CATS)
FVO = re.compile(r'^\s*fitting\s+vehicle\s+options\s*:\s*(.*)$', re.I)
groups = [g for g in doc['likely'] if g['cat'] not in HOLD]
sus = collections.Counter()
out = []
for g in groups:
    c = next(c for (k, cat), c in cur.classes.items() if cat == g['cat'] and sorted(c.pns) == sorted(g['pn']))
    for a in g['apps']:
        for y in range(a[2], a[3] + 1):
            T = (a[0], a[1], y)
            rows = [lr for lr in cur.t_list_rows.get((T, g['cat']), []) if policy.pn_key(ns, lr.pn) == c.key and lr.matched]
            notes = [n for lr in rows for n in lr.notes] if rows else \
                [n for r in cur.t_seed_records.get((T, g['cat']), []) if r.key == c.key for n in r.note_texts]
            need = cur.body_need(T)
            fv = [FVO.match(n).group(1) for n in notes if FVO.match(n)]
            flags = []
            # leading codes of every alternative
            leads = set()
            for f in fv:
                for alt in C._split_top_plus(f, ','):
                    for part in C._split_top_plus(alt, '+'):
                        p = C._NISSAN_PREFIX_RE.sub('', part.strip().lstrip('*').lstrip('(').strip())
                        t = re.match(r'^([A-Za-z0-9/]+)', p)
                        leads.add(t.group(1).upper() if t else '?')
            body_leads = {C._NISSAN_BODY_CODES[x] for x in leads if x in C._NISSAN_BODY_CODES}
            if body_leads and need and not (body_leads <= need) and len(need) == 1:
                flags.append(f'body-code {sorted(body_leads)} vs car {sorted(need)}')
            if any(re.search(r'\bfrom\s+\d', n, re.I) or re.search(r'production', n, re.I) for n in notes):
                if C._production_excludes(notes, y):
                    flags.append('production window misses year')
            disp = C._INFINITI_DISP.get(re.sub(r'\s+', '', a[1]).upper()) if a[0] == 'Infiniti' else None
            if disp:
                codes = {int(d) for f in fv for d in C._NISSAN_ENGINE_CODE_RE.findall(f)}
                if codes and disp not in codes:
                    flags.append(f'engine codes {sorted(codes)} vs {disp}')
            cabs = C._fvo_cab_codes(notes)
            if cabs and len(cabs) == 1 and 'cab only' not in g['note']:
                flags.append(f'single cab {cabs} but no cab note')
            unknown = sorted(x for x in leads if x not in C._NISSAN_BODY_CODES and x not in ('KC', 'CC', '?'))
            if flags:
                out.append((g['cat'], g['pn'][0], T, flags, fv[:2]))
                for fl in flags:
                    sus[fl.split(' ')[0]] += 1
print(f"{ns}: {len(groups)} shippable groups; suspect app-years by class: {dict(sus)}")
for x in out[:60]:
    print('  ', x[0], x[1], x[2], x[3], [f[:90] for f in x[4]])
