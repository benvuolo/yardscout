/* Direction C — My Garage. Static prototype; donors/parts are real rows from the 2026-11-06 scan. */
const SCREENS = ['home', 'results', 'car', 'part', 'watches', 'pro'];
const CIV = D.civics, TACO = car(8000716), FOUR = car(8000860), MIATA = car(7997774);
const silhouette = `<svg class="silhouette" viewBox="0 0 130 60" aria-hidden="true"><path fill="currentColor" d="M16 46V32q0-3 3-3h16l11-14.5q1-1 3-1h30q2 0 3 1l10 13.5 18 2q4 .5 4 3V46q0 3-3 3h-5a10 10 0 0 0-20 0H44a10 10 0 0 0-20 0h-5q-3 0-3-3Z"/></svg>`;

function hdr(title, back) {
  if (back) return `<header class="hdr sub"><a class="ib" style="display:grid" href="${back}" aria-label="Back">${icon('back')}</a><h1>${title}</h1><a class="ib" href="#" aria-label="Share">${icon('share')}</a></header>`;
  return `<header class="hdr"><span class="brand"><span class="mark"></span><span class="wordmark">YARD<b>SCOUT</b></span></span><span class="sp"></span>
    <a class="ib" href="#" aria-label="Location 95112">${icon('pin')}</a></header>`;
}
const tabs = (cur, cls = '') => `<nav class="tabs ${cls}" aria-label="Main"><span class="tbrand"><span class="mark"></span><span class="wordmark">YARD<b>SCOUT</b></span></span>${[['home', 'garage', 'Garage'], ['results', 'search', 'Search'], ['yards', 'map', 'Yards'], ['watches', 'bell', 'Alerts']].map(([s, i, l]) => `<a href="${go(s)}"${s === cur ? ' aria-current="page"' : ''}>${icon(i)}${l}</a>`).join('')}</nav>`;

function home() {
  const newCiv = CIV.filter(c => c.day <= 4).length;
  return `${hdr()}<main><div class="dgrid"><section>
    <h1 class="title">Your garage</h1>
    <a class="gcar primary" href="${go('results')}">${silhouette}<div class="yr">2008 · 1.8L 4-cyl · 5-spd auto</div><h2>Honda Civic</h2>
      <div class="big"><b>${CIV.length}</b><span>donors within 50 mi</span></div><div class="sub">${newCiv} set out this week · closest 1 mi, San Jose North</div>
      <div class="needs"><span class="need"><i class="d"></i>Alternator · ${CIV.length} cars</span><span class="need">Window regulator · ${CIV.length} cars</span></div>
      <span class="go" aria-hidden="true">${icon('chev')}</span></a>
    <a class="gcar" href="${go('results')}">${silhouette}<div class="yr">2000 · 2.7L 4-cyl</div><h2>Toyota Tacoma</h2>
      <div class="big"><b style="color:var(--accent)">2</b><span>donors within 50 mi</span></div><div class="sub" style="color:var(--text-dim)">Tacoma row 17 · 4Runner row 18 — both at San Jose North</div>
      <div class="needs"><span class="need">Tailgate</span><span class="need">Climate control unit</span></div></a>
    <a class="add" href="#">${icon('plus')}<span>Add a car<small>Scan or type a VIN, or pick year · make · model</small></span></a>
    </section><section>
    <p class="kicker">Everything near 95112 <a href="${go('results')}">Browse</a></p>
    <a class="searchbar" href="${go('part')}">${icon('search')}Any part, car or yard</a>
    <div class="browse" style="margin-top:var(--s3)">
      <a href="${go('results')}"><b>${D.carsNear.toLocaleString()}</b><span>cars on 5 lots</span></a>
      <a href="${go('results')}"><b style="color:var(--accent)">${D.yards.reduce((a, y) => a + y.newWeek, 0)}</b><span>set out this week</span></a>
      <a href="${go('yards')}"><b>5</b><span>yards in range</span></a>
      <a href="${go('yards')}"><b>6:02</b><span>last scan today</span></a></div>
    <p class="kicker">Lately</p>
    <ul class="feed">
      <li><span class="ic">${icon('car')}</span><div><b>${CIV[3].year} Civic at San Jose North, row ${CIV[3].row}</b><span>Donor for your Civic · set out ${setOut(CIV[3])}</span></div></li>
      <li><span class="ic">${icon('car')}</span><div><b>2000 Tacoma at San Jose North, row ${TACO.row}</b><span>Your Tacoma · set out ${setOut(TACO)}</span></div></li>
      <li><span class="ic">${icon('bell')}</span><div><b>2006 MX-5 Miata at Richmond, row ${MIATA.row}</b><span>Watch: Miata, any year · set out ${setOut(MIATA)}</span></div></li></ul>
    </section></div></main>${tabs('home')}`;
}

function donor(c, hasPart = 'Alternator') {
  const s = stay(c);
  return `<a class="donor" href="${go('car', '&id=' + c.id)}"><h3>${c.year} ${esc(c.make)} ${esc(c.model)}</h3>
    <div class="meta">${esc(yardShort(c.yard))} · ${c.mi} mi · set out ${setOut(c)}</div>
    <div class="rw"><small>ROW</small><b>${esc(c.row)}</b></div>
    <div class="foot"><span class="has">${icon('check')}${hasPart}</span>${c.day <= 3 ? '<span class="lbl new">New</span>' : ''}<span class="lbl${s.pct > .75 ? ' late' : ''}">${s.txt}</span></div></a>`;
}
function results() {
  const near = CIV.slice().sort((a, b) => a.mi - b.mi);
  return `${hdr('Donors for your Civic', go('home'))}<main>
    <div class="ctx">${icon('car')}<div><b>2008 Honda Civic · 1.8L</b>Same generation, 2006–2011 · within 50 mi</div><a class="sw" href="#">Change</a></div>
    <div style="display:flex;gap:8px;overflow-x:auto;padding-bottom:4px"><a class="fchip on" href="#">Nearest</a><a class="fchip" href="#">Newest</a><a class="fchip" href="#">Leaving soon</a><a class="fchip" href="#">All cars instead</a></div>
    <p class="grp">${near.length} donor cars <span>sorted by distance</span></p>
    <div class="cards3">${near.map(c => donor(c)).join('')}</div>
    <p class="small" style="margin-top:var(--s4)">“Same generation” uses the model-year range the parts table already carries for this model. Confirm part numbers on the car.</p>
  </main>${tabs('results')}`;
}

function carScreen() {
  const c = car(qs.get('id') || CIV[3].id), v = value(c), s = stay(c);
  const mine = v.conf.filter(p => /^Alternator|^Window Regulator/.test(p.name)), rest = v.conf.filter(p => !mine.includes(p));
  const li = p => `<li><span class="n">${esc(cleanPart(p.name))}</span><span class="x">${[partNote(p.name), p.speed === 'Fast' ? 'sells fast' : ''].filter(Boolean).join(' · ') || '&nbsp;'}</span><span class="v"><b>${money(p.low)}–${money(p.high)}</b><span>yard ${yardPrice(p)}</span></span></li>`;
  return `${hdr('', go('results'))}<main>
    <section class="hero"><div class="small mono" style="letter-spacing:.08em">DONOR FOR YOUR 2008 CIVIC</div><h1>${c.year} ${esc(c.make)} ${esc(c.model)}</h1>
      <div class="m">${esc(c.yard)} · ${c.mi} mi · ${[c.engine, c.trans].filter(Boolean).map(esc).join(' · ')}</div>
      <div class="facts"><div><small>Row</small><b>${esc(c.row)}</b></div><div class="${s.pct < .34 ? 'ok' : ''}"><small>On lot</small><b>${c.day}<span style="font-size:var(--t-sm)">/~${c.typical}d</span></b></div><div><small>Set out</small><b style="font-size:var(--t-md)">${setOut(c)}</b></div></div></section>
    <p class="kicker">On your list</p><ul class="plist mine">${mine.map(li).join('')}</ul>
    <p class="kicker">Also on this car <span>${rest.length} parts</span></p><ul class="plist">${rest.map(li).join('')}</ul>
    ${v.opt.length ? `<p class="kicker">Check on the car <span>not counted</span></p><ul class="plist opt">${v.opt.map(li).join('')}</ul>` : ''}
    <p class="small mono" style="margin:var(--s5) 0">VIN ${esc(c.vin)}</p><p class="small">Cars here typically stay ~${c.typical} days (median of departed cars) — an estimate. Prices: used online; yard price from the yard’s list where published.</p><div style="height:90px"></div>
  </main><div class="bar"><a class="btn main" href="#">${icon('pin')}Directions · row ${esc(c.row)}</a><a class="btn alt" href="#" aria-label="Save to trip">${icon('heart')}</a></div>${tabs('results', 'deskonly')}`;
}

function part() {
  const alt = CIV[0].parts.find(p => p.name.startsWith('Alternator'));
  const by = {}; CIV.forEach(c => (by[c.yard] = by[c.yard] || []).push(c));
  return `${hdr('Alternator', go('home'))}<main>
    <section class="ans"><div class="small mono" style="letter-spacing:.08em">FOR YOUR 2008 CIVIC · 1.8L</div><h1>${CIV.length} donors, closest 1 mi away</h1><p>At 3 Pick-n-Pull yards within 50 mi</p>
      <div class="cmpbar" role="img" aria-label="Price comparison">
        <div class="r"><span>Pick-n-Pull</span><span class="t"><i style="left:0;width:${42.98 / 90 * 100}%"></i></span><b>$42.98</b></div>
        <div class="r"><span>Used online</span><span class="t"><i class="o" style="left:${alt.low / 90 * 100}%;width:${(alt.high - alt.low) / 90 * 100}%"></i></span><b>${money(alt.low)}–${money(alt.high)}</b></div>
      </div><p class="small" style="margin-top:var(--s2)">Pick-n-Pull price includes a $9.99 core charge, refunded when you return your old one.</p></section>
    ${Object.entries(by).sort((a, b) => a[1][0].mi - b[1][0].mi).map(([y, l]) => `<p class="grp">${esc(yardShort(y))} <span>${l[0].mi} mi · ${l.length} car${l.length > 1 ? 's' : ''}</span></p>${l.map(c => donor(c)).join('')}`).join('')}
    <div style="height:90px"></div></main>
    <div class="bar"><a class="btn main" href="${go('watches')}">${icon('bell')}Tell me when another lands</a></div>${tabs('results', 'deskonly')}`;
}

function watches() {
  return `${hdr()}<main><h1 class="title">Alerts</h1>
    <article class="acar"><h3>2008 Honda Civic</h3><div class="s">From your garage · donors 2006–2011 within 50 mi</div>
      <div class="opt-row"><div>Weekly recap<small>Mondays · free</small></div><span class="tg" role="switch" aria-checked="true"></span></div>
      <div class="opt-row"><div>Push within hours <span class="pro-tag">PRO</span><small>When a donor is set out</small></div><span class="tg off" role="switch" aria-checked="false"></span></div></article>
    <article class="acar"><h3>2000 Toyota Tacoma</h3><div class="s">From your garage · 1995–2004 within 50 mi</div>
      <div class="opt-row"><div>Weekly recap<small>Mondays · free</small></div><span class="tg" role="switch" aria-checked="true"></span></div></article>
    <p class="kicker">Other watches</p>
    <article class="acar"><h3>Mazda MX-5 Miata</h3><div class="s">Any year · within 100 mi · 1 on a lot now (Richmond, row 54)</div></article>
    <p class="small">Watches you already saved stay exactly as you set them. Garage cars are a separate, new list.</p>
  </main>${tabs('watches')}`;
}

function pro() {
  return `${home()}<div class="scrim"></div><section class="sheet" role="dialog" aria-modal="true" aria-labelledby="ph"><div class="grab"></div>
    <div class="proof"><b>${CIV.length}</b><p>Civic donors were set out within 50 mi of you in the last 5 days. Pro pushes you within hours, before the good parts walk.</p></div>
    <h2 id="ph">YardScout Pro</h2>
    <ul class="ticks"><li>${icon('check')}<span><b>Push within hours</b> for every garage car and watch</span></li>
      <li>${icon('check')}<span><b>Every part with prices</b> — yard vs used online</span></li>
      <li>${icon('check')}<span><b>Leaving-soon</b> and nationwide search</span></li></ul>
    <div class="plans"><div class="plan"><span><b>$8.99</b> / month</span><span class="small">Cancel anytime</span></div></div>
    <a class="btn main w" href="#">Start Pro</a><p class="fine">Secure checkout by Stripe · also in the iPhone app</p>
    <a class="already" href="#">Already have Pro? Restore with your email</a></section>`;
}

function yards() {
  return `${hdr()}<main><h1 class="title">Yards near 95112</h1>${D.yards.map(y => `<a class="donor" href="${go('results')}"><h3>${esc(yardShort(y.name))}</h3><div class="meta">${esc(chain(y.name))} · ${y.mi} mi · ${y.cars.toLocaleString()} cars</div><div class="rw"><small>NEW</small><b style="color:var(--accent)">${y.newWeek}</b></div></a>`).join('')}</main>${tabs('yards')}`;
}

document.getElementById('app').innerHTML = `<div class="app">${({ home, results, car: carScreen, part, watches, pro, yards }[SCREEN] || home)()}</div>`;
protoNav(SCREENS);
