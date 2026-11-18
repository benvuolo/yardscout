"""Compact per-item summary of a sample dossier: names, positions, fitment rows,
and per vehicle-year: own-page variant + notes, lot mix, same-part competitors."""
import sys, re
path, items = sys.argv[1], set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
cur = None
out = []
for line in open(path):
    line = line.rstrip('\n')
    m = re.match(r'=== (\S+) ', line)
    if m:
        cur = m.group(1)
        if items is None or cur in items:
            print('\n' + line[:300])
        continue
    if cur is None or (items is not None and cur not in items):
        continue
    s = line.strip()
    if s.startswith('apps=') or s.startswith('note='):
        continue
    if s.startswith('RECORD'):
        mm = re.search(r"seed=(\(.*?\)) pn=(\S+) name='(.*?)' aux='(.*?)'", s)
        print(f"  REC {mm.group(1) if mm else ''} {mm.group(2) if mm else ''} name={mm.group(3) if mm else s[:120]!r} aux={mm.group(4) if mm else ''!r}")
    elif s.startswith('description='):
        print('    ' + s[:200])
    elif s.startswith('seed-page notes='):
        print('    ' + s[:220])
    elif s.startswith('[option]') or s.startswith('[trim]'):
        r = re.search(r"raw='(.*)'$", s) or re.search(r'raw="(.*)"$', s)
        print('      fit: ' + (r.group(1) if r else s)[:200])
    elif s.startswith('OWN PAGE'):
        mm = re.match(r"OWN PAGE (\(.*?\)) on_page=(\S+) via=(\S+) notes=(\[.*?\]) pointers", s)
        print(f"  T {mm.group(1)} on={mm.group(2)} via={mm.group(3)} notes={mm.group(4)[:160]}" if mm else '  ' + s[:200])
    elif s.startswith('lot body mix'):
        print('     ' + s[:120])
    elif s.startswith('row '):
        mm = re.search(r"catalog/variant='(.*?)' .*?main='(.*?)'.*?notes=(\[.*?\]) loc=(\[.*?\]) matched=(\S+)", s)
        if mm:
            print(f"     row var={mm.group(1)!r} main={mm.group(2)!r} notes={mm.group(3)[:150]} loc={mm.group(4)} m={mm.group(5)}")
    elif s.startswith('same-part numbers'):
        print('     ' + s)
    elif s.startswith('- '):
        print('       ' + s[:170])
    elif s.startswith('reason=') or s.startswith('packaging='):
        print('  ' + s[:120])
