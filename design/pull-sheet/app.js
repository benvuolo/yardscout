/* Direction A — Pull Sheet. Static prototype; every screen renders from real sample data. */
const SCREENS = ['home', 'results', 'car', 'part', 'watches', 'sheet', 'yards', 'pro'];
const CARS = D.cars;
const pick = id => car(id) || CARS[0];
const TL = pick(8002477), MIATA = pick(7997774), TACOMA = pick(8000716);

function topbar(title, back) {
  if (back) return `<header class="top"><a class="back" href="${back}" aria-label="Back">${icon('back')}</a><h1>${title}</h1><span class="spacer"></span><a class="loc-chip" href="#"><span class="mono">95112</span> · 50 mi</a></header>`;
  return `<header class="top"><a class="brand" href="${go('home')}" aria-label="YardScout home"><span class="mark"></span><span class="wordmark">YARD<b>SCOUT</b></span></a><span class="spacer"></span>
  <nav class="desk-only" aria-label="Main">${tabs(true)}</nav>
  <a class="loc-chip" href="#" aria-label="Location 95112, within 50 miles. Change">${icon('pin')}<span class="mono">95112</span> · 50 mi</a></header>`;
}
function tabs(inline) {
  const t = [['home', 'search', 'Find'], ['yards', 'map', 'Yards'], ['sheet', 'list', 'Pull sheet', 3], ['watches', 'bell', 'Watches', 2]];
  const cur = { results: 'home', car: 'home', part: 'home', pro: 'home' }[SCREEN] || SCREEN;
  const html = t.map(([s, i, l, b]) => `<a href="${go(s)}"${s === cur ? ' aria-current="page"' : ''}>${icon(i)}${l}${b ? `<span class="badge" aria-label="${b} items">${b}</span>` : ''}</a>`).join('');
  return inline ? `<div class="tabs">${html}</div>` : `<nav class="tabs phone-only" aria-label="Main">${html}</nav>`;
}
function stayMeter(c) { const s = stay(c); return `<div class="meter ${s.pct > .75 ? 'late' : s.pct > .34 ? 'mid' : ''}" role="img" aria-label="${s.txt} days typical"><i style="width:${Math.max(6, s.pct * 100)}%"></i></div>`; }
function carRow(c, sel) {
  const v = value(c);
  return `<li class="row${sel ? ' sel' : ''}"><a href="${go('car', '&id=' + c.id)}">
    <div class="plate" aria-label="Row ${esc(c.row)}"><small>ROW</small><b>${esc(c.row)}</b></div>
    <div><h3>${c.year} ${esc(c.make)} ${esc(c.model)} ${c.day <= 3 ? '<span class="tag new">New</span>' : ''}</h3>
      <div class="spec">${[c.engine, transShort(c.trans)].filter(Boolean).map(esc).join(' · ') || 'Engine not listed'}</div>
      <div class="where">${esc(yardShort(c.yard))} · ${c.mi} mi</div>
      <div class="stayline">${stayMeter(c)}<span>Day ${c.day} of ~${c.typical}</span></div>
      <div class="val">${v.conf.length} parts · best <b>${money(v.best.low)}–${money(v.best.high)}</b> ${isManual(c) ? '<span class="tag man">Manual</span>' : ''}</div></div>
  </a></li>`;
}
function home() {
  const fresh = [TL, TACOMA, MIATA, pick(8002800)];
  return `${topbar()}<main><div class="home-grid"><section class="hero">
    <h1>What are you pulling today?</h1>
    <p>Search a part or a car. We check ${D.carsNear.toLocaleString()} cars on 5 self-service lots within 50 miles.</p>
    <label class="search">${icon('search')}<span class="sr">Part or car</span><input placeholder="Alternator, ’08 Civic, Tacoma…" value=""></label>
    <div class="chips" aria-label="Quick searches">
      <a class="chip" href="${go('part')}">${icon('wrench')}Alternator · ’06–’11 Civic</a>
      <a class="chip" href="${go('results')}">Toyota Tacoma</a><a class="chip" href="${go('results')}">Manual only</a><a class="chip" href="${go('results')}">Mazda Miata</a>
    </div>
    <div class="pulse" aria-label="Near you">
      <div><b class="num">${D.carsNear.toLocaleString()}</b><span>cars in range</span></div>
      <div class="hot"><b class="num">${D.yards.reduce((a,y)=>a+y.newWeek,0)}</b><span>set out this week</span></div>
      <div><b>6:02</b><span>last scan, today</span></div>
    </div></section>
    <section><h2 class="sec">Fresh on the lots <a href="${go('results')}">See all</a></h2>
    <ul class="rows">${fresh.map(c => carRow(c)).join('')}</ul></section></div></main>${tabs()}`;
}

function results() {
  const list = [TL, TACOMA, pick(8002444), MIATA, pick(7968855), pick(8002800), pick(8002557), pick(8002078)];
  const filters = `<aside class="filters desk-only" aria-label="Filters">
    <h4>Sort</h4><div class="seg" style="flex-direction:column;align-items:stretch;border-radius:var(--r)">
    <a aria-current="true" style="border-radius:var(--r-sm)">Newest first</a><a>Leaving soon</a><a>Most value</a><a>Nearest</a></div>
    <h4>Yards</h4>${D.yards.map((y, i) => `<label><span class="cb ${i < 3 ? 'on' : ''}"></span>${esc(yardShort(y.name))} <span style="color:var(--text-dim);margin-left:auto" class="mono">${y.mi} mi</span></label>`).join('')}
    <h4>Make &amp; model</h4><div class="field">All makes ${icon('down')}</div>
    <h4>Years</h4><div style="display:flex;gap:8px"><div class="field" style="flex:1">From</div><div class="field" style="flex:1">To</div></div>
    <h4>Car</h4><label><span class="cb"></span>Manual transmission</label><label><span class="cb"></span>Set out this week</label></aside>`;
  const preview = `<aside class="preview desk-only" aria-label="Selected car">${detailBody(TL, true)}</aside>`;
  return `${topbar()}<main><div class="results-grid">${filters}<section>
    <div class="toolbar phone-only"><a class="chip on" href="#">${icon('filter')}Filters · 2</a>
      <div class="seg"><a aria-current="true">Newest</a><a>Leaving soon</a><a>Most value</a></div></div>
    <p class="count"><b>${D.carsNear.toLocaleString()} cars</b> at 5 yards near 95112 · newest set-outs first</p>
    <ul class="rows">${list.map((c, i) => carRow(c, i === 0)).join('')}</ul></section>${preview}</div></main>${tabs()}`;
}

function detailBody(c, compact) {
  const v = value(c), s = stay(c);
  const part = (p, done) => `<li class="part${done ? ' done' : ''}"><span class="box" role="checkbox" aria-checked="${!!done}" aria-label="Pulled">${done ? icon('check') : ''}</span>
    <div><div class="nm">${esc(cleanPart(p.name))}</div><div class="nt">${[partNote(p.name), p.speed === 'Fast' ? '<span class="fast">Sells fast</span>' : ''].filter(Boolean).join(' · ')}</div></div>
    <div class="px"><b>${money(p.low)}–${money(p.high)}</b><span>yard ${yardPrice(p)}</span></div></li>`;
  return `<div class="detail-head"><p class="eyebrow">Set out ${setOut(c)}${c.transSrc ? ' · VIN-decoded' : ''}</p>
    <h1>${c.year} ${esc(c.make)} ${esc(c.model)}</h1>
    <div class="locator"><div class="plate"><small>ROW</small><b>${esc(c.row)}</b></div>
      <div><h3>${esc(c.yard)}</h3><p>${esc(c.city)}, ${c.state} · ${c.mi} mi from 95112</p>
      <div class="links"><a href="#">${icon('pin')}Directions</a><a href="#">Yard listing ${icon('ext')}</a></div></div></div>
    <div class="staybar"><div class="lbl"><span>${s.txt} days</span><b>${s.label}</b></div>
      <div class="track" role="img" aria-label="${s.txt}"><i style="left:calc(${s.pct * 100}% - 2px)"></i></div>
      <div class="hint">Cars at this yard typically stay ~${c.typical} days (median of departed cars). An estimate, not a schedule.</div></div>
    <div class="specs">${c.engine ? `<span class="spec-chip">${esc(c.engine)}</span>` : ''}
      ${isManual(c) ? `<span class="spec-chip ok">${icon('check')}Manual · from VIN</span>` : c.trans ? `<span class="spec-chip">${esc(transShort(c.trans))}</span>` : ''}</div></div>
    <h2 class="sec">Worth pulling <span style="font:500 var(--t-sm)/1 var(--font-ui);color:var(--text-dim)">${v.conf.length} parts · used online</span></h2>
    <ul class="parts">${v.conf.slice(0, compact ? 5 : 99).map((p, i) => part(p, !compact && i === 1)).join('')}</ul>
    ${v.opt.length ? `<div class="opt-head">If equipped <span>· check on the car, not counted in value</span></div>
    <ul class="parts opt">${v.opt.map(p => part(p)).join('')}</ul>` : ''}
    ${compact ? `<div class="actionbar"><a class="btn primary" href="#">${icon('plus')}Add to pull sheet</a><a class="btn quiet" href="#" aria-label="Watch this model">${icon('bell')}</a></div>` : `
    <div class="vin mono">VIN ${esc(c.vin)} <button aria-label="Copy VIN">${icon('copy')}</button></div>
    <p class="footnote">Parts this model shipped with. Yards list whole cars, so some parts may already be gone. Prices are what the same used part sells for online — a guide, not a promise.</p>`}`;
}
function carScreen() {
  const c = pick(qs.get('id') || TACOMA.id);
  return `${topbar('Car', go('results'))}<main>${detailBody(c)}<div style="height:80px"></div></main>
  <div class="actionbar"><a class="btn primary" href="${go('sheet')}">${icon('plus')}Add to pull sheet</a>
  <a class="btn quiet" href="${go('watches')}" aria-label="Watch ${esc(c.make)} ${esc(c.model)}">${icon('bell')}</a><a class="btn quiet" href="#" aria-label="Share">${icon('share')}</a></div>`;
}

function part() {
  const cs = D.civics.slice().sort((a, b) => a.mi - b.mi || a.day - b.day);
  const groups = {}; cs.forEach(c => (groups[c.yard] = groups[c.yard] || []).push(c));
  const alt = cs[0].parts.find(p => p.name.startsWith('Alternator'));
  return `${topbar('Alternator', go('home'))}<main>
    <section class="answer"><h1>${cs.length} donor cars for your alternator</h1>
    <p>2006–2011 Honda Civic · within 50 mi of 95112</p>
    <div class="facts"><div><b>$42.98</b><span>Pick-n-Pull price, incl. $9.99 core</span></div>
    <div><b>${money(alt.low)}–${money(alt.high)}</b><span>used online</span></div><div><b>1 mi</b><span>closest donor</span></div></div></section>
    <div class="toolbar" style="margin-top:var(--s4)"><div class="seg"><a aria-current="true">Nearest</a><a>Newest</a></div><a class="chip" href="${go('watches')}">${icon('bell')}Watch for more</a></div>
    ${Object.entries(groups).map(([y, list]) => `<div class="yard-group"><h3>${esc(yardShort(y))} <span>${list[0].mi} mi · ${list.length} car${list.length > 1 ? 's' : ''}</span></h3>
    <ul class="rows">${list.map(c => carRow(c)).join('')}</ul></div>`).join('')}
    <p class="footnote">Fit basis: shown from the app’s interchange data for this generation. Spin-test the alternator at the yard; match the part number before you buy.</p></main>${tabs()}`;
}

function watches() {
  const W = [
    { t: 'Toyota Tacoma', c: '1995–2004 · Manual · within 50 mi', on: true, hits: [TACOMA], n: 2 },
    { t: 'Mazda MX-5 Miata', c: 'Any year · within 100 mi', on: true, hits: [MIATA], n: 1 },
    { t: 'Honda Civic', c: '2006–2011 · within 50 mi', on: false, hits: [], n: 6, note: 'Weekly recap only' },
  ];
  return `${topbar()}<main><p class="eyebrow">Watches</p><h2 class="sec" style="margin-top:0">Tell me when it lands <a href="#">${icon('plus')} New</a></h2>
  ${W.map(w => `<article class="watch"><header><div><h3>${w.t}</h3><div class="crit">${w.c}</div></div>
    <span class="switch ${w.on ? '' : 'off'}" role="switch" aria-checked="${w.on}" aria-label="Push alerts for ${w.t}"></span></header>
    <a class="hits" href="${go('results')}"><span><b>${w.n} on lots now</b>${w.hits[0] ? ` · newest ${w.hits[0].year} at ${esc(yardShort(w.hits[0].yard))}, row ${w.hits[0].row}` : ''}${w.note ? ` · ${w.note}` : ''}</span>${icon('chev')}</a></article>`).join('')}
  <h2 class="sec">How you hear about it</h2>
  <div class="card"><div class="channel">${icon('bell')}<div><b>Push within hours</b><small>When a watched car is set out</small></div><span class="pro-lock">${icon('lock')}Pro</span></div>
  <div class="channel">${icon('clock')}<div><b>Weekly recap</b><small>Every Monday, free</small></div><span class="switch" role="switch" aria-checked="true"></span></div>
  <div class="channel">${icon('list')}<div><b>Email same day</b><small>One email per scan with new matches</small></div><span class="pro-lock">${icon('lock')}Pro</span></div></div>
  <p class="footnote">Each yard is re-scanned about every 4 hours.</p></main>${tabs()}`;
}

function sheet() {
  const L = [TACOMA, pick(8000860), TL];
  return `${topbar()}<main><p class="eyebrow">Saturday trip · 2 yards</p><h2 class="sec" style="margin-top:0">Pull sheet <a href="#">${icon('share')} Share</a></h2>
  ${L.map(c => { const v = value(c); return `<div class="yard-group"><h3>${esc(yardShort(c.yard))} <span>${c.mi} mi</span></h3><ul class="rows">${carRow(c)}</ul>
  <ul class="parts">${v.conf.slice(0, 2).map((p, i) => `<li class="part${i === 0 && c === TL ? ' done' : ''}"><span class="box">${i === 0 && c === TL ? icon('check') : ''}</span><div><div class="nm">${esc(cleanPart(p.name))}</div><div class="nt">${partNote(p.name)}</div></div><div class="px"><b>${money(p.low)}–${money(p.high)}</b></div></li>`).join('')}</ul></div>`; }).join('')}
  <p class="footnote">Bring: hand &amp; battery tools only — no sawzalls or torches at Pick-n-Pull.</p></main>${tabs()}`;
}

function pro() {
  return `${results()}<div class="scrim"></div><section class="sheet" role="dialog" aria-modal="true" aria-labelledby="pro-h"><div class="grab"></div>
  <button class="x" aria-label="Close">${icon('x')}</button>
  <h2 id="pro-h">Get there before the crusher</h2>
  <p class="lede">Finding cars near you stays free. Pro is for planning the trip.</p>
  <div class="price"><b>$8.99</b><span>/ month · cancel anytime</span></div>
  <ul class="bens">
    <li><span class="ic">${icon('bell')}</span><div><b>Push alerts within hours</b><span>When a watched car is set out. Free gets the weekly recap.</span></div></li>
    <li><span class="ic">${icon('wrench')}</span><div><b>Every part and price</b><span>Yard price vs used-online, and which parts sell fast.</span></div></li>
    <li><span class="ic">${icon('clock')}</span><div><b>Leaving-soon sort</b><span>Days on the lot vs this yard’s typical stay.</span></div></li>
    <li><span class="ic">${icon('map')}</span><div><b>Nationwide + trim filters</b><span>Watch any yard; 4WD/AWD or trim confirmed by VIN.</span></div></li></ul>
  <a class="btn primary full" href="#">Start Pro — $8.99/mo</a>
  <p class="fine">Secure checkout by Stripe · or subscribe in the iPhone app</p>
  <a class="restore" href="#"><div><b>Already have Pro?</b><span>Unlock this device with your email</span></div>${icon('chev')}</a></section>`;
}

function yards() {
  return `${topbar()}<main><p class="eyebrow">Yards near 95112</p><h2 class="sec" style="margin-top:0">5 self-service yards</h2>
  <ul class="rows">${D.yards.map(y => `<li class="row"><a href="${go('results')}" style="grid-template-columns:1fr auto"><div><h3>${esc(yardShort(y.name))} <span class="spec">· ${esc(chain(y.name))}</span></h3>
  <div class="where">${y.mi} mi · ${y.cars.toLocaleString()} cars · <b style="color:var(--accent)">${y.newWeek} new this week</b></div>
  <div class="spec">Cars typically stay ~${y.typical} days · hand &amp; battery tools only</div></div>${icon('chev')}</a></li>`).join('')}</ul></main>${tabs()}`;
}

document.getElementById('app').innerHTML = `<div class="app ${['car','part'].includes(SCREEN) ? 'pushed' : ''}">${({ home, results, car: carScreen, part, watches, sheet, pro, yards }[SCREEN] || home)()}</div>`;
protoNav(SCREENS);
