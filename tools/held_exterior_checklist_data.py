"""Build the Held Parts Checklist page data from held_exterior.json.

Usage (repo root): python3 tools/held_exterior_checklist_data.py [held.json] [previous_checklist_data.json]
With a previous data file, groups that were in it but are no longer held are
kept with "sup": true (superseded: no longer held by the current curation).
"""
import json, sys, collections
sys.path.insert(0, 'scraper/oem_fitment')
import policy
src = sys.argv[1] if len(sys.argv) > 1 else 'scraper/oem_fitment/groups/_report/held_exterior.json'
prev = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else None
d = json.load(open(src))

def pair_of(apps):
    names = {}
    for mk, md, y0, y1 in apps:
        k = policy.base_model(mk, md)
        names.setdefault(k, f"{mk} {md}")
    pk = ' + '.join(' '.join(k) for k in sorted(names))
    return pk, ' / '.join(names[k] for k in sorted(names))

pair_names, rows = {}, []
for x in d['groups']:
    pk, label = pair_of(x['apps'])
    pair_names.setdefault(pk, label)
    gid = f"{x['ns']}~{x['cat']}~{x['pn'][0]}"
    rows.append({'id': gid, 'ns': x['ns'], 'cat': x['cat'], 'pn': x['pn'], 'apps': x['apps'],
                 'note': x['note'], 'reason': x['reason'], 'urls': x['urls'], 'pk': pk})
assert len({r['id'] for r in rows}) == len(rows) == d['count']
cnt = collections.Counter(r['pk'] for r in rows)
order = sorted(cnt, key=lambda k: (-cnt[k], k))
rank = {k: i for i, k in enumerate(order)}
rows.sort(key=lambda r: (rank[r['pk']], r['cat'], min(a[2] for a in r['apps']), r['pn'][0]))
pairs = [{'k': k, 'label': pair_names[k], 'n': cnt[k]} for k in order]
if prev:
    live = {r['id'] for r in rows}
    sup = [dict(g, sup=True) for g in prev['groups'] if g['id'] not in live and not g.get('sup')]
    sup += [g for g in prev['groups'] if g.get('sup') and g['id'] not in live]
    sup.sort(key=lambda r: (r['pk'], r['cat'], r['pn'][0]))
    rows += sup
out = {'pairs': pairs, 'groups': rows}
sys.stdout.write(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
