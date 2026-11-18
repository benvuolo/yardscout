"""Diff two groups/<ns>.json files by (cat, pn): apps added/removed per class."""
import json, sys
a = json.load(open(sys.argv[1]))
b = json.load(open(sys.argv[2]))
verbose = '-v' in sys.argv


def idx(d):
    out = {}
    for g in d['likely'] + d.get('groups', []):
        out[(g['cat'], tuple(g['pn']))] = g
    return out


def yrs(g):
    s = set()
    for ap in g['apps']:
        for y in range(ap[2], ap[3] + 1):
            s.add((ap[0], ap[1], y))
    return s


A, B = idx(a), idx(b)
for k in sorted(set(A) | set(B)):
    ga, gb = A.get(k), B.get(k)
    if ga and not gb:
        print('REMOVED', k, ga['apps'], ga['note'][-60:] if verbose else '')
    elif gb and not ga:
        print('ADDED  ', k, gb['apps'], gb['note'][-60:] if verbose else '')
    elif ga['apps'] != gb['apps'] or ga['note'] != gb['note']:
        ya, yb = yrs(ga), yrs(gb)
        print('CHANGED', k, 'lost', sorted(ya - yb)[:8], 'gained', sorted(yb - ya)[:8],
              'note' if ga['note'] != gb['note'] else '')
