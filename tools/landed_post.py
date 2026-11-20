#!/usr/bin/env python3
"""A "what landed" list for one model, in the form ops/reddit.md asks for:
every car of that make and model set out in the last N days, grouped by
state (most cars first), then generation when --gens is given, newest first.

    python3 tools/landed_post.py Toyota 4Runner \\
        --gens "1989:1st gen,1995:2nd gen,2002:3rd gen,2009:4th gen,2024:5th gen,9999:6th gen"
    python3 tools/landed_post.py Nissan Xterra --days 7 --out /tmp/xterra.md

Reads docs/data/inventory_live.json (run `git pull` first so it is the
newest scan) and prints nothing from it but the list. Every line is a row of
that file: nothing is invented, and a car with no VIN-decoded drive shows
neither 4x4 nor 2WD. The model must match exactly (ignoring case, spaces and
hyphens), so "Cherokee" does not pull in "Grand Cherokee"; --contains loosens
that. --gens is "<last model year>:<label>" pairs, in order.

The text is a draft for the owner to read and post. This script posts
nothing and contacts nothing.
"""
import argparse
import collections
import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATES = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California', 'CO': 'Colorado',
    'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
    'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana',
    'ME': 'Maine', 'MD': 'Maryland', 'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota',
    'MS': 'Mississippi', 'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
    'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina',
    'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania',
    'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas',
    'UT': 'Utah', 'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
    'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'Washington DC',
    'AB': 'Alberta', 'BC': 'British Columbia', 'MB': 'Manitoba', 'NB': 'New Brunswick', 'NS': 'Nova Scotia',
    'ON': 'Ontario', 'QC': 'Quebec', 'SK': 'Saskatchewan',
}


def norm(s):
    return re.sub(r'[\s-]+', '', str(s or '')).casefold()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('make')
    ap.add_argument('model')
    ap.add_argument('--days', type=int, default=7)
    ap.add_argument('--gens', default='', help='"<last model year>:<label>,..." in order, e.g. "2004:1st gen,2015:2nd gen"')
    ap.add_argument('--contains', action='store_true', help='match models that contain the name')
    ap.add_argument('--years', default='', help='only these model years, e.g. "1996-2002" (a one-generation post)')
    ap.add_argument('--label', default='', help='what to call that range in the title and text, e.g. "3rd gen"')
    ap.add_argument('--campaign', default='', help='utm_campaign for the link (default: the model, lower case)')
    ap.add_argument('--data', type=Path, default=ROOT / 'docs/data/inventory_live.json')
    ap.add_argument('--out', type=Path, help='write the draft here instead of printing it')
    args = ap.parse_args()

    d = json.load(open(args.data, encoding='utf8'))
    F = {n: i for i, n in enumerate(d['fields'])}
    YF = {n: i for i, n in enumerate(d['yardFields'])}
    yards, vpic = d['yards'], d.get('vpic', {})
    scraped = datetime.datetime.fromisoformat(str(d['scrapedAt']).replace('Z', '+00:00'))
    today = scraped.date()
    since = today - datetime.timedelta(days=args.days)

    gens = []
    for part in filter(None, (p.strip() for p in args.gens.split(','))):
        top, label = part.split(':', 1)
        gens.append((int(top), label.strip()))

    def gen(year):
        return next((label for top, label in gens if year <= top), '') if gens else ''

    yr_lo = yr_hi = None
    if args.years.strip():
        m = re.fullmatch(r'\s*(\d{4})\s*-\s*(\d{4})\s*', args.years)
        if not m or int(m.group(1)) > int(m.group(2)):
            ap.error('--years wants "<first>-<last>", e.g. 1996-2002')
        yr_lo, yr_hi = int(m.group(1)), int(m.group(2))
    label = ' '.join(args.label.split())

    want_make, want_model = norm(args.make), norm(args.model)
    rows = []
    for idx, v in enumerate(d['vehicles']):
        if norm(v[F['make']]) != want_make:
            continue
        m = norm(v[F['model']])
        if not (want_model in m if args.contains else m == want_model):
            continue
        try:
            day = datetime.date.fromisoformat(str(v[F['dateAdded']])[:10])
            year = int(v[F['year']])
        except (TypeError, ValueError):
            continue   # no set-out date or year: not listed
        if day < since or day > today:
            continue
        if yr_lo is not None and not (yr_lo <= year <= yr_hi):
            continue
        y = yards[v[F['yard']]]
        vp = vpic.get(str(idx)) or []
        drive = (vp[3] if len(vp) > 3 else '') or ''
        dr = '4x4' if ('4WD' in drive or '4x4' in drive.lower()) else '2WD' if '4x2' in drive.lower() else ''
        rows.append(dict(year=year, yard=' '.join(str(y[YF['location']]).replace(' - ', ' ').split()), state=y[YF['state']] or '',
                         row=v[F['row']], day=day, drive=dr))

    name = f'{args.make} {args.model}'
    short = args.model   # "4Runner", "Xterra": the title says "4Runners", "Xterras"
    what = f'{label} {short}' if label else short            # "3rd gen 4Runner"
    span = f' ({yr_lo} to {yr_hi})' if yr_lo is not None else ''
    by_state = collections.defaultdict(list)
    for r in rows:
        by_state[r['state']].append(r)
    n4 = sum(1 for r in rows if r['drive'] == '4x4')
    has_drive = any(r['drive'] for r in rows)
    L = [f'**Title:** {what}s set out at u-pull yards this week ({since.month}/{since.day} to {today.month}/{today.day}), by state', '']
    if not rows:
        L.append(f'No {what if label else name}{span} was set out in the last {args.days} days at the yards I track.')
    else:
        places = 'states and provinces' if any(s in ('AB', 'BC', 'MB', 'NB', 'NS', 'ON', 'QC', 'SK') for s in by_state) else 'states'
        lead = (f'I keep track of what self-service yards put out each day. Here is every {what}{span} that was set out in the last '
                f'{args.days} days: {len(rows)} of them in {len(by_state)} {places}')
        L.append(lead + (f', {n4} confirmed 4x4.' if has_drive else '.'))
        L.append('')
        how = 'Sorted by state, then generation, newest first.' if gens else 'Sorted by state, newest first.'
        tail = ' 4x4 or 2WD comes from the VIN. If neither is shown, I could not tell.' if has_drive else ''
        L.append(f'{how} The row is whatever the yard posted, so check the board when you get there.{tail}')
        for st in sorted(by_state, key=lambda s: (-len(by_state[s]), STATES.get(s, s))):
            L += ['', f'**{STATES.get(st, st or "State not listed")}**']
            cars = sorted(by_state[st], key=lambda r: (gen(r['year']), -r['day'].toordinal(), -r['year']))
            last = None
            for r in cars:
                g = gen(r['year'])
                if g != last:
                    L += ['', f'{g}:', ''] if g else ['']
                    last = g
                dr = ' **4x4**' if r['drive'] == '4x4' else (' 2WD' if r['drive'] else '')
                row = f', row {r["row"]}' if r['row'] not in (None, '') else ''
                L.append(f'* {r["year"]}{dr}, {r["yard"]}{row}, set out {r["day"].month}/{r["day"].day}')
        L += ['', 'If your state is not here, either nothing landed this week or I do not track your yard yet. '
                  'Tell me which yard you use and I will look at adding it.']
    campaign = args.campaign or (re.sub(r'[^a-z0-9]+', '', args.model.lower())
                                 + ('-' + re.sub(r'[^a-z0-9]+', '', label.lower()) if label else ''))
    make_q = args.make.replace(' ', '%20')
    model_q = args.model.replace(' ', '%20')
    years_q = f'%7C{yr_lo}-{yr_hi}' if yr_lo is not None else ''
    tags = f'utm_source=reddit&utm_medium=post&utm_campaign={campaign}'
    # Owner, 2026-11-20: a clean visible address with the tagged link behind
    # it; the apps through yardscout.io/app (phones go to their own store),
    # never store links.
    L += ['', f'To see the {what}s near you, with photos where the yard posts them: '
              f'[yardscout.io](https://yardscout.io/?{tags}#cars={make_q}%7C{model_q}{years_q})',
          '', 'It is free and needs no account. The iPhone and Android apps are at '
              f'[yardscout.io/app](https://yardscout.io/app?{tags}) if you want an alert when the next one lands.']
    text = '\n'.join(L) + '\n'
    note = (f'data as of {scraped:%Y-%m-%d %H:%M} UTC | {len(rows)} cars, {len(by_state)} states/provinces, '
            f'{n4} confirmed 4x4')
    if args.out:
        args.out.write_text(text, encoding='utf8')
        print(note, '| wrote', args.out, file=sys.stderr)
    else:
        sys.stdout.write(text)
        print(note, file=sys.stderr)


if __name__ == '__main__':
    main()
