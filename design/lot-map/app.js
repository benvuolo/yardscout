/* Direction B — Lot Map. Static prototype; real yards/cars from the 2026-11-06 scan. */
const SCREENS = ['home', 'results', 'car', 'part', 'watches', 'pro'];
const ME = [-121.885, 37.345]; // zip 95112
const SJN = D.yards[0];
const WATER = [
  [[-122.40, 37.93], [-122.33, 37.90], [-122.30, 37.83], [-122.26, 37.76], [-122.20, 37.70], [-122.14, 37.62], [-122.10, 37.55], [-122.05, 37.48], [-121.98, 37.45], [-122.10, 37.46], [-122.20, 37.52], [-122.30, 37.60], [-122.37, 37.70], [-122.38, 37.80], [-122.47, 37.86]],
  [[-122.40, 37.93], [-122.45, 38.08], [-122.30, 38.10], [-122.18, 38.07], [-122.30, 37.98]],
  [[-123.2, 38.2], [-122.98, 38.0], [-122.51, 37.78], [-122.50, 37.60], [-122.42, 37.25], [-122.30, 37.10], [-122.05, 36.96], [-121.95, 36.97], [-121.80, 36.90], [-121.79, 36.80], [-121.85, 36.50], [-123.2, 36.4]],
];
const ROADS = [
  [[-121.57, 37.0], [-121.80, 37.25], [-121.89, 37.34], [-122.05, 37.40], [-122.20, 37.48], [-122.39, 37.60], [-122.40, 37.77]],
  [[-121.89, 37.34], [-121.93, 37.45], [-122.05, 37.55], [-122.12, 37.65], [-122.20, 37.75], [-122.29, 37.82]],
  [[-121.89, 37.34], [-121.85, 37.50], [-121.92, 37.70], [-122.05, 37.90]],
  [[-122.29, 37.82], [-122.32, 37.92], [-122.35, 38.05]],
  [[-121.80, 36.70], [-121.78, 36.80], [-121.85, 36.95], [-122.02, 36.97]],
  [[-121.89, 37.34], [-121.97, 37.10], [-122.02, 36.98]],
];
const CITIES = [['SAN JOSE', -121.86, 37.30], ['OAKLAND', -122.22, 37.84], ['SAN FRANCISCO', -122.47, 37.73], ['MONTEREY BAY', -122.10, 36.86]];

function map({ center = [-122.0, 37.37], ky = 205, pins = D.yards.map(y => ({ y, n: y.newWeek, lbl: yardShort(y.name) })), sel, radius = 50 } = {}) {
  const desk = innerWidth >= 960;
  const W = desk ? innerWidth - 420 : innerWidth, H = desk ? innerHeight : Math.round(innerHeight * .62);
  if (desk) ky *= 1.45;
  const cy = desk ? H / 2 : (84 + innerHeight * .52) / 2, kx = ky * Math.cos(center[1] * Math.PI / 180);
  const P = ([lng, lat]) => [(W / 2 + (lng - center[0]) * kx).toFixed(1), (cy - (lat - center[1]) * ky).toFixed(1)];
  const poly = pts => pts.map(P).join(' ');
  const me = P(ME), rpx = radius / 69 * ky;
  const pin = p => { const [x, y] = P([p.y.lng, p.y.lat]); const lbl = p.lbl, nw = String(p.n).length * 8 + 16; const w = nw + 22 + lbl.length * 7.6;
    const isSel = sel && p.y.name === sel, left = /Newark/.test(p.y.name) ? -w + 22 : -w / 2;
    return `<a href="${go('results')}" aria-label="${esc(p.y.name)}, ${p.n} ${p.unit || 'new this week'}"><g transform="translate(${x},${y})">
      <line x1="0" y1="0" x2="0" y2="-9" stroke="var(--text)" stroke-width="3"/>
      <rect x="${left}" y="-43" width="${w}" height="34" rx="17" fill="${isSel ? 'var(--text)' : 'var(--surface)'}" stroke="var(--text)" stroke-width="2"/>
      <rect x="${left + 4}" y="-39" width="${nw}" height="26" rx="13" fill="var(--brand)"/>
      <text x="${left + 4 + nw / 2}" y="-21.5" text-anchor="middle" style="font:700 12px var(--font-mono)" fill="#1C1C1A">${p.n}</text>
      <text x="${left + nw + 12}" y="-21" style="font:700 13px var(--font-ui)" fill="${isSel ? 'var(--bg)' : 'var(--text)'}">${esc(lbl)}</text></g></a>`; };
  return `<div class="mapwrap" aria-label="Map of yards near 95112"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Illustrative map">
    <rect class="map-land" width="${W}" height="${H}"/>
    ${WATER.map(w => `<polygon class="map-water" points="${poly(w)}"/>`).join('')}
    ${ROADS.map(r => `<polyline class="map-road" points="${poly(r)}"/><polyline class="map-road2" points="${poly(r)}"/>`).join('')}
    ${CITIES.map(([n, lng, lat]) => { const [x, y] = P([lng, lat]); return `<text class="map-label" x="${x}" y="${y}" text-anchor="middle">${n}</text>`; }).join('')}
    <circle class="map-radius" cx="${me[0]}" cy="${me[1]}" r="${rpx}"/>
    <circle cx="${me[0]}" cy="${me[1]}" r="14" fill="rgba(47,111,222,.2)"/><circle cx="${me[0]}" cy="${me[1]}" r="7" fill="#2F6FDE" stroke="#fff" stroke-width="3"/>
    ${pins.map(pin).join('')}</svg>
    <div class="mapnote">Illustrative map · pins = cars set out this week</div></div>`;
}
const floattop = (back) => `<div class="floattop">${back ? `<a class="roundbtn" href="${back}" aria-label="Back">${icon('back')}</a>` : ''}
  <a class="searchpill" href="${go('part')}">${back ? '' : '<span class="mark" aria-hidden="true"></span>'}${icon('search')}<span>Search a part or car</span></a>
  <a class="roundbtn" href="#" aria-label="Location 95112 within 50 miles">${icon('locate')}</a></div>`;
const nav = cur => `<nav class="nav" aria-label="Main">${[['home', 'map', 'Map'], ['part', 'wrench', 'Find a part'], ['watches', 'bell', 'Watches']].map(([s, i, l]) => `<a href="${go(s)}"${s === cur ? ' aria-current="page"' : ''}>${icon(i)}${l}</a>`).join('')}</nav>`;
const deskBrand = `<div class="desk-brand"><span class="mark"></span><span class="wordmark">YARD<b>SCOUT</b></span></div>`;
function stayPill(c) { const s = stay(c); return `<span class="pill ${s.pct > .75 ? 'late' : s.pct > .34 ? 'mid' : 'fresh'}">${s.label} · day ${c.day}/~${c.typical}</span>`; }

function home() {
  const total = D.yards.reduce((a, y) => a + y.newWeek, 0);
  return `${map()}${floattop()}<section class="sheet"><div class="grab"></div><div class="scroll">${deskBrand}
    <div class="sh-head"><div><h1>${total} cars set out this week</h1><p>5 self-service yards within 50 mi of 95112 · scanned 6:02 AM</p></div></div>
    ${D.yards.map(y => { const on = Math.round(y.newWeek / y.cars * 40); return `<a class="yard" href="${go('results')}"><div><h3>${esc(yardShort(y.name))}</h3>
      <div class="m">${y.mi} mi · ${y.cars.toLocaleString()} cars · stay ~${y.typical} days</div></div>
      <div class="n"><b class="num">${y.newWeek}</b><span>new</span></div>
      <div class="freshbar" role="img" aria-label="${Math.round(y.newWeek / y.cars * 100)}% of the lot is new this week">${Array.from({ length: 20 }, (_, i) => `<i class="${i < on ? 'on' : ''}"></i>`).join('')}</div></a>`; }).join('')}
  </div></section>${nav('home')}`;
}

function results() {
  const cars = [...D.civics.filter(c => c.yard === SJN.name), ...D.cars.filter(c => c.yard === SJN.name)].sort((a, b) => +a.row - +b.row);
  const rows = {}; cars.forEach(c => (rows[c.row] = rows[c.row] || []).push(c));
  return `${map({ center: [-121.93, 37.40], ky: 700, sel: SJN.name, pins: [{ y: SJN, n: SJN.newWeek, lbl: 'San Jose North' }] })}${floattop(go('home'))}<section class="sheet tall"><div class="grab"></div><div class="scroll">${deskBrand}
    <div class="sh-head"><div><h1>San Jose North</h1><p>Pick-n-Pull · 1 mi · ${SJN.cars} cars · <b style="color:var(--accent)">${SJN.newWeek} new this week</b></p></div>
    <a class="btn sq" href="#" aria-label="Directions">${icon('pin')}</a></div>
    <div class="seg" role="tablist"><a aria-current="true">Walk by row</a><a>Newest</a><a>Leaving soon</a></div>
    <p class="note" style="margin-top:0">Filtered: Toyota &amp; Honda · showing ${cars.length} of ${SJN.cars}</p>
    ${Object.entries(rows).map(([r, list]) => `<div class="rowgroup"><div class="rowtag"><i>${icon('pin')}</i>ROW ${esc(r)} <span>· ${list.length} car${list.length > 1 ? 's' : ''}</span></div>
      ${list.map(c => { const v = value(c); return `<a class="carc" href="${go('car', '&id=' + c.id)}"><div class="t"><h3>${c.year} ${esc(c.make)} ${esc(c.model)}</h3>${c.day <= 3 ? '<span class="pill new">New</span>' : ''}</div>
        <div class="s">${[c.engine, transShort(c.trans)].filter(Boolean).map(esc).join(' · ')}</div>
        <div class="b">${stayPill(c)}<span>${v.conf.length} parts · best <b>${money(v.best.high)}</b></span></div></a>`; }).join('')}</div>`).join('')}
  </div></section>${nav('home')}`;
}

function carScreen() {
  const c = car(qs.get('id') || 8000716), v = value(c), s = stay(c);
  const lanes = 14, here = Math.min(lanes - 1, Math.round(+c.row / 140 * lanes));
  return `<div class="app-car" style="padding-bottom:96px">
  <div class="lotstrip" role="img" aria-label="${esc(c.yard)}, row ${esc(c.row)}"><div class="cap"><a href="${go('results')}" style="color:inherit;display:flex;align-items:center;gap:4px;text-decoration:none;min-height:32px">${icon('back')} ${esc(yardShort(c.yard))}</a><span>${c.mi} mi · lot sketch</span></div>
    <div class="lanes">${Array.from({ length: lanes }, (_, i) => `<i class="${i === here ? 'here' : ''}"></i>`).join('')}</div>
    <div class="big"><small>ROW</small><b>${esc(c.row)}</b></div></div>
  <div style="padding:var(--s4)">
    <div class="sh-head" style="padding-top:0"><div><h1>${c.year} ${esc(c.make)} ${esc(c.model)}</h1>
      <p>${[c.engine, c.trans].filter(Boolean).map(esc).join(' · ')} · set out ${setOut(c)}</p></div></div>
    <div style="display:flex;gap:8px;flex-wrap:wrap">${stayPill(c)}${isManual(c) ? '<span class="pill man">Manual (VIN)</span>' : ''}<span class="pill man">${v.conf.length} parts</span></div>
    <div class="cartabs" role="tablist" style="margin-top:var(--s4)"><a aria-current="true">Parts</a><a>Car &amp; VIN</a><a>Yard</a></div>
    <table class="tbl"><thead><tr><th>Part</th><th>Yard</th><th>Used online</th></tr></thead><tbody>
    ${v.conf.map(p => `<tr><td><b>${esc(cleanPart(p.name))}</b>${partNote(p.name) ? `<small>${esc(partNote(p.name))}</small>` : ''}${p.speed === 'Fast' ? '<small style="color:var(--accent2);font-weight:600">Sells fast</small>' : ''}</td><td class="num">${yardPrice(p)}</td><td class="num">${money(p.low)}–${money(p.high)}</td></tr>`).join('')}
    ${v.opt.length ? `<tr class="optsep"><td colspan="3">If equipped — check the car · not in value</td></tr>${v.opt.map(p => `<tr class="opt"><td><b>${esc(cleanPart(p.name))}</b>${p.verify ? `<small>${esc(p.verify.split('—')[0])}</small>` : ''}</td><td class="num">${yardPrice(p)}</td><td class="num">${money(p.low)}–${money(p.high)}</td></tr>`).join('')}` : ''}
    </tbody></table>
    <p class="note">Parts this model shipped with; some may already be pulled. ${s.txt} days at a yard where cars stay ~${c.typical} days (median of departed cars) — an estimate, not a schedule.</p>
  </div></div>
  <div class="dock"><a class="btn primary" href="#">${icon('pin')}Directions to row ${esc(c.row)}</a><a class="btn sq" href="#" aria-label="Save">${icon('heart')}</a><a class="btn sq" href="${go('watches')}" aria-label="Watch model">${icon('bell')}</a></div>`;
}

function part() {
  const by = {}; D.civics.forEach(c => (by[c.yard] = by[c.yard] || []).push(c));
  const pins = Object.entries(by).map(([n, l]) => ({ y: D.yards.find(y => y.name === n), n: l.length, lbl: yardShort(n), unit: 'donors' }));
  return `${map({ pins, center: [-122.05, 37.62], ky: 270 })}${floattop(go('home'))}<section class="sheet"><div class="grab"></div><div class="scroll">${deskBrand}
    <div class="sh-head"><div><h1>Alternator · 2006–11 Civic</h1><p>${D.civics.length} donors at 3 yards · Pick-n-Pull $42.98 incl. core · online $30–$70</p></div></div>
    ${Object.entries(by).sort((a, b) => a[1][0].mi - b[1][0].mi).map(([n, l]) => `<p class="label">${esc(yardShort(n))} · ${l[0].mi} mi</p>${l.map(c => `<a class="carc" href="${go('car', '&id=' + c.id)}"><div class="t"><h3>${c.year} Honda Civic</h3><span class="mono" style="font-weight:700">ROW ${esc(c.row)}</span></div><div class="b">${stayPill(c)}</div></a>`).join('')}`).join('')}
  </div></section>${nav('part')}`;
}

function watches() {
  const W = [
    { t: 'Toyota Tacoma', c: '1995–2004 · Manual', zone: '50 mi of 95112', on: true, hits: [['San Jose North', 1], ['Moss Landing', 1]] },
    { t: 'Mazda MX-5 Miata', c: 'Any year', zone: '100 mi of 95112', on: true, hits: [['Richmond', 1]] },
    { t: 'Honda Civic', c: '2006–2011', zone: '50 mi of 95112', on: false, hits: [['San Jose North', 3], ['Richmond', 2], ['Newark', 1]] },
  ];
  return `${map({ radius: 50, pins: [] })}${floattop()}<section class="sheet tall"><div class="grab"></div><div class="scroll">${deskBrand}
    <div class="sh-head"><div><h1>Watches</h1><p>We check every yard in your zone about every 4 hours.</p></div><a class="btn sq" href="#" aria-label="New watch">${icon('plus')}</a></div>
    ${W.map(w => `<article class="wz"><div class="t"><div><h3>${w.t}</h3><div class="c">${w.c} · within ${w.zone}</div></div><span class="tog ${w.on ? '' : 'off'}" role="switch" aria-checked="${w.on}" aria-label="Alerts for ${w.t}"></span></div>
      <div class="dots">${w.hits.map(([y, n]) => `<span><i></i>${n} at ${y}</span>`).join('')}</div></article>`).join('')}
    <p class="note">Free: weekly recap. Pro: a push within hours of a set-out, plus same-day email.</p>
  </div></section>${nav('watches')}`;
}

function pro() {
  const rows = [['Cars &amp; yards near you', 1, 1], ['Watches + weekly recap', 1, 1], ['Push within hours of a set-out', 0, 1], ['Every part, yard price vs online', 0, 1], ['Leaving-soon sort', 0, 1], ['Nationwide, trim &amp; 4WD filters', 0, 1]];
  const ck = v => v ? icon('check') : '<span aria-label="No" style="color:var(--text-dim)">—</span>';
  return `${home()}<div class="scrim"></div><section class="pro" role="dialog" aria-modal="true" aria-labelledby="ph"><div class="grab"></div>
    <h2 id="ph">YardScout Pro</h2><p class="lede">Finding cars stays free. Pro tells you first, and what it’s worth.</p>
    <table class="cmp"><thead><tr><th></th><th>Free</th><th class="p">Pro</th></tr></thead><tbody>${rows.map(([l, f, p]) => `<tr><td>${l}</td><td>${ck(f)}</td><td class="p">${ck(p)}</td></tr>`).join('')}</tbody></table>
    <a class="btn orange" style="width:100%" href="#">Get Pro · $8.99/month</a>
    <p class="fine">Cancel anytime · secure checkout by Stripe</p>
    <div class="alt"><a href="#">Already have Pro?<br><span style="font-weight:400;color:var(--text-dim)">Restore by email</span></a><a href="#">Prefer the app?<br><span style="font-weight:400;color:var(--text-dim)">App Store</span></a></div></section>`;
}

document.getElementById('app').innerHTML = `<div class="app">${({ home, results, car: carScreen, part, watches, pro }[SCREEN] || home)()}</div>`;
protoNav(SCREENS);
