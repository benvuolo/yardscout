import json, sys, collections
sys.path.insert(0, 'scraper/oem_fitment')
import policy
d = json.load(open('scraper/oem_fitment/groups/_report/held_exterior.json'))
pair_names = {}
rows = []
for x in d['groups']:
    names = {}
    for mk, md, y0, y1 in x['apps']:
        k = policy.base_model(mk, md)
        names.setdefault(k, f"{mk} {md}")
    pk = ' + '.join(' '.join(k) for k in sorted(names))
    pair_names.setdefault(pk, ' / '.join(names[k] for k in sorted(names)))
    gid = f"{x['ns']}~{x['cat']}~{x['pn'][0]}"
    rows.append({'id': gid, 'ns': x['ns'], 'cat': x['cat'], 'pn': x['pn'], 'apps': x['apps'],
                 'note': x['note'], 'reason': x['reason'], 'urls': x['urls'], 'pk': pk})
cnt = collections.Counter(r['pk'] for r in rows)
order = sorted(cnt, key=lambda k: (-cnt[k], k))
rank = {k: i for i, k in enumerate(order)}
rows.sort(key=lambda r: (rank[r['pk']], r['cat'], min(a[2] for a in r['apps']), r['pn'][0]))
assert len({r['id'] for r in rows}) == len(rows) == d['count']
out = {'pairs': [{'k': k, 'label': pair_names[k], 'n': cnt[k]} for k in order], 'groups': rows}
sys.stdout.write(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
