/**
 * Server-rendered share pages on yardscout.io — the "free distribution"
 * surface: someone drops https://yardscout.io/car/<vin> into an "I need a
 * donor" forum thread and the link unfurls with the car, the yard, the row,
 * the set-out date and the honest crush-window estimate. Nothing here needs
 * the app shell or the 37MB inventory: each page is two small cached calls
 * to yardscout-api (vehicle detail + yard directory).
 *
 *   /car/<id-or-vin>      one car (same key as the app's #car= deep link)
 *   /yard/<slug>          what arrived at one yard this week (SEO page)
 *   /sitemap-yards.xml    every yard page, for crawlers
 *
 * Tier rules are the API's: these pages only ever see the free variant, so
 * no dollar values can appear here regardless of what the API grows later.
 */
const API = 'https://yardscout-api.yardscout.workers.dev';
const SITE = 'https://yardscout.io';
const IOS_URL = 'https://apps.apple.com/app/yardscout-junkyard-parts/id6817126581';
const PLAY_URL = 'https://play.google.com/store/apps/details?id=io.yardscout.app';
const OG_IMAGE = SITE + '/og-card.png';

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => (
  { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
));

export function slugify(s) {
  return String(s || '').toLowerCase().replace(/&/g, ' and ')
    .replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}

async function apiJson(path, ttl) {
  const r = await fetch(API + path, {
    headers: { accept: 'application/json' },
    cf: { cacheTtl: ttl, cacheEverything: true },
  });
  if (!r.ok) return { status: r.status, data: null };
  return { status: r.status, data: await r.json() };
}

const DATA = 'https://benvuolo.github.io/yardscout/data';
async function dataJson(name, ttl) {
  const r = await fetch(`${DATA}/${name}`, { cf: { cacheTtl: ttl, cacheEverything: true } });
  return r.ok ? r.json() : null;
}

/* Chain price-list pages — same table as CHAIN_PRICE_PAGES in docs/app.js
 * (keep the two in step). Independent yards' lists come via the registry. */
const CHAIN_PRICE_PAGES = [
  [/^pick[\s-]*n[\s-]*pull/i, 'https://www.picknpull.com/part-pricing', 'Pick-n-Pull'],
  [/^pull[\s-]*a[\s-]*part/i, 'https://www.pullapart.com/used-auto-parts/parts-pricing/', 'Pull-A-Part'],
  [/^tear[\s-]*a[\s-]*part/i, 'https://tearapart.com/price-list/', 'Tear-A-Part'],
  [/pic[\s-]*a[\s-]*part/i, 'https://utpap.com/ogden-prices/', 'Utah Pic-A-Part'],
  [/wrench[\s-]*a[\s-]*part/i, 'https://wrenchapart.com/austin-price-list', 'Wrench-A-Part'],
  [/^u[\s-]*pull[\s-]*r/i, 'https://upullrparts.com/part-pricing/', 'U-Pull-R Parts'],
  [/^fenix[\s-]*u[\s-]*pull/i, 'https://fenixupull.com/parts-prices/', 'Fenix U-Pull'],
  [/^harry'?s[\s-]*u[\s-]*pull/i, 'https://wegotused.com/price-list/', "Harry's U-Pull-It"],
  [/^joliet u[\s-]*pull[\s-]*it/i, 'https://www.jolietupullit.com/auto-part-prices', 'Joliet U-Pull-It'],
  [/^go pull[\s-]*it/i, 'https://gopullit.com/parts-price-list/', 'Go Pull-It'],
  [/^195 used auto parts/i, 'https://www.195usedautoparts.com/Home/PartPrices', '195 Used Auto Parts'],
  [/^san antonio pick[\s-]*n[\s-]*pull/i, 'https://www.picknpullsa.com/price-list', 'San Antonio Pick-N-Pull'],
];
function priceListFor(loc) { const h = CHAIN_PRICE_PAGES.find((c) => c[0].test(loc || '')); return h ? { url: h[1], label: h[2] } : null; }
let siteLinksCache = { at: 0, rows: null };
async function yardSiteFor(loc) {
  if (!siteLinksCache.rows || Date.now() - siteLinksCache.at > 3600_000) {
    const rows = await dataJson('yard_site_links.json', 3600);
    siteLinksCache = { at: Date.now(), rows: (rows || []).map(([src, url]) => { try { return [new RegExp(src, 'i'), url]; } catch (e) { return null; } }).filter(Boolean) };
  }
  const hit = siteLinksCache.rows.find(([re]) => re.test(loc || ''));
  return hit ? hit[1] : null;
}


/* ---------- Inline price lists (same mapping as yardPriceList in docs/app.js) ----------
 * So a share page reader can check pull prices without leaving the page. */
const PRICE_FILES = [
  ['pick-n-pull', 'picknpull_pricing.json', 'list'], ['tear-a-part', 'tearapart_pricing.json', 'list'],
  ['utah pic-a-part', 'utpap_pricing.json', 'list'], ['u-pull-r', 'upullr_pricing.json', 'list'],
  ["harry's u-pull-it", 'harrys_pricing.json', 'list'], ['indy-u-pull-it', 'indy_pricing.json', 'list'],
  ["rupert's u-pull-it", 'ruperts_pricing.json', 'list'], ['u-pull-it', 'upullitne_pricing.json', 'list'],
  ['pull-n-save', 'pns_pricing.json', 'list'], ['parts galore', 'partsgalore_pricing.json', 'list'],
  ['chesterfield auto parts', 'chesterfield_pricing.json', 'list'], ['ace pick-a-part', 'ace_pricing.json', 'list'],
  ['sturtevant auto', 'sturtevant_pricing.json', 'list'], ['nevada pic-a-part', 'nvpap_pricing.json', 'list'],
  ["barry's u pull it", 'barrys_pricing.json', 'list'], ['195 used auto parts', 'p195_pricing.json', 'list'],
  ['m&m u-pull-it', 'mmupullit_pricing.json', 'list'], ["chuck & eddie's", 'chuckeddies_pricing.json', 'list'], ['polk county pick and pay', 'polkpickpay_pricing.json', 'list'],
  ['san antonio pick-n-pull', 'pnpsa_pricing.json', 'list'], ["ryan's pick-a-part", 'ryans_pricing.json', 'list'],
  ['us auto supply', 'usauto_pricing.json', 'list'], ['u-pull and save', 'upas_pricing.json', 'list'],
  ['budget u-pull-it', 'budget_pricing.json', 'dict'], ['pick your part', 'pyp_pricing.json', 'dict'],
  ['pull-a-part', 'pap_pricing.json', 'dict'], ['wrench-a-part', 'wap_pricing.json', 'dict'],
  ['fenix u-pull', 'fenix_pricing.json', 'dict'],
];
async function yardPriceRows(location) {
  const loc = (location || '').toLowerCase();
  const hit = PRICE_FILES.find(([pfx]) => pfx === 'wrench-a-part' ? loc.includes(pfx) : loc.startsWith(pfx));
  if (!hit) return null;
  const data = await dataJson(hit[1], 3600);
  if (!data) return null;
  let rows = [];
  if (hit[2] === 'list') rows = (Array.isArray(data) ? data : Object.values(data)).map((p) => ({ part: p.description, price: parseFloat(p.price), core: parseFloat(p.corePrice || 0) }));
  else rows = Object.entries(data[location] || {}).map(([k, v]) => ({ part: k, price: Number(v.price), core: Number(v.core || 0) }));
  rows = rows.filter((r) => r.part && Number.isFinite(r.price)).sort((a, b) => a.part.localeCompare(b.part));
  return rows.length ? rows : null;
}
function priceListHtml(rows, yardName) {
  if (!rows) return '';
  const money = (n) => '$' + n.toFixed(2);
  return `<details class="card-fold" id="prices"><summary class="section" style="cursor:pointer;margin-top:1rem">${esc(yardName)} price list <span>· ${rows.length} parts · tap to open</span></summary>
<div class="car-card"><input type="search" id="pl-q" placeholder="Filter parts…" aria-label="Filter the price list" style="width:100%;min-height:44px;padding:.6rem .75rem;border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--surface);color:var(--text);font:inherit;font-size:16px;margin-bottom:.6rem">
<ul class="rowlist" id="pl-rows">${rows.map((r) => `<li><a style="font-weight:600;font-size:.875rem">${esc(r.part)}</a><span class="meta">${money(r.price)}${r.core > 0 ? '<br>+ ' + money(r.core) + ' core' : ''}</span></li>`).join('')}</ul>
<p class="note">From the yard's own published price list. Pull prices change — confirm at the counter.</p></div></details>
<script>(function(){var q=document.getElementById('pl-q'),rows=[].slice.call(document.querySelectorAll('#pl-rows li'));if(!q)return;q.addEventListener('input',function(){var v=q.value.trim().toLowerCase();rows.forEach(function(li){li.style.display=!v||li.textContent.toLowerCase().indexOf(v)>-1?'':'none';});});})();</script>`;
}

/* Yard set-out dates are plain YYYY-MM-DD strings in the yard's local day;
 * compare against UTC midnight so "today" never reads as day 0 vs day 1
 * depending on the viewer's timezone. */
function daysSince(dateStr) {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(dateStr || '');
  if (!m) return null;
  const added = Date.UTC(+m[1], +m[2] - 1, +m[3]);
  const today = new Date(); const now = Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate());
  const d = Math.floor((now - added) / 86400000);
  return d < 0 ? 0 : d;
}

function fmtDate(dateStr) {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(dateStr || '');
  if (!m) return '';
  return new Date(Date.UTC(+m[1], +m[2] - 1, +m[3]))
    .toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });
}

function fmtStamp(iso) {
  const d = new Date(iso || 0);
  return isNaN(d) ? '' : d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', timeZone: 'UTC' }) + ' UTC';
}

/** Crush-window copy. Factual day count vs the yard's historical average —
 * worded as an estimate, never a schedule (same rules as the app card). */
export function crushWindow(daysOn, avg, basis) {
  if (daysOn == null) return { line: 'Set-out date not published by this yard.', soon: false, left: null };
  const where = basis === 'yard' ? 'at this yard' : basis === 'chain' ? 'at this chain' : 'across covered yards';
  if (!avg) return { line: `Day ${daysOn + 1} on the lot. Not enough departure history yet to estimate how long cars last here.`, soon: false, left: null };
  const left = Math.round(avg - daysOn);
  if (daysOn > 2 * avg) {
    return { line: `On the lot ${daysOn} days — well past the ~${avg}-day typical stay ${where}. It could go any day.`, soon: true, left: 0 };
  }
  if (left <= 0) {
    return { line: `Day ${daysOn + 1} on the lot — past the ~${avg}-day typical stay ${where}. Likely leaving soon.`, soon: true, left: 0 };
  }
  const soon = daysOn >= 0.8 * avg;
  return {
    line: `Day ${daysOn + 1} on the lot. Cars typically last ~${avg} days ${where}, so roughly ${left} day${left === 1 ? '' : 's'} left if this one follows the average.`,
    soon, left,
  };
}

// The pages load the app's own stylesheet (docs/styles.css, served at
// yardscout.io) and reuse its header, cards, stats and buttons, so a share
// link looks like the app it came from. Only share-page-specific bits below.
const CSS = `
body{padding-bottom:2.5rem}
.share-main{max-width:680px;margin:0 auto;padding:1rem 1.25rem}
.kicker{font-family:var(--font-mono);font-size:.625rem;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--text-dim);margin:.25rem 0 .5rem}
.kicker a{color:var(--accent);text-decoration:none}
.share-h{font-size:1.5rem;font-weight:800;letter-spacing:-.02em;line-height:1.15;margin:0 0 .35rem}
.share-sub{color:var(--text-dim);font-size:.875rem;line-height:1.5;margin:0 0 .9rem}
.car-card{content-visibility:visible;contain-intrinsic-size:auto;margin-bottom:.8rem}
.car-card a.car-link{color:inherit;text-decoration:none;display:block}
.car-card a.car-link:hover .car-name{color:var(--accent)}
.clock{margin-top:.7rem;padding:.55rem .7rem;border-left:3px solid var(--border-dark);background:var(--surface2);font-size:.875rem;line-height:1.45}
.clock.soon{border-left-color:var(--accent)}
.clock small{display:block;color:var(--text-dim);font-size:.75rem;margin-top:.3rem}
.facts{display:grid;grid-template-columns:1fr 1fr;gap:.6rem .9rem;margin:.6rem 0 0;padding-top:.6rem;border-top:1px dashed var(--border)}
.facts dt{font-family:var(--font-mono);font-size:.625rem;letter-spacing:.09em;text-transform:uppercase;color:var(--text-dim)}
.facts dd{margin:0;font-size:.875rem;font-weight:600;overflow-wrap:anywhere}
.facts dd.mono{font-family:var(--font-mono);font-weight:500;font-size:.8125rem}
.facts dd a{color:var(--text)}
.cta{display:flex;flex-wrap:wrap;gap:.5rem;margin:.9rem 0 .4rem}
.cta .btn{padding:.7rem 1rem;font-size:.875rem;min-height:44px;white-space:normal;text-decoration:none;display:inline-flex;align-items:center}
.stores{color:var(--text-dim);font-size:.8125rem;margin:.6rem 0 0}
.note{color:var(--text-dim);font-size:.75rem;line-height:1.5;margin:.9rem 0 0}
.section{font-family:var(--font-mono);font-size:.75rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--text);margin:1.3rem 0 .6rem;padding-bottom:.3rem;border-bottom:1px dashed var(--border)}
.section span{color:var(--text-dim);font-weight:500}
.rowlist{list-style:none;margin:0;padding:0}
.rowlist li{display:flex;justify-content:space-between;gap:.8rem;padding:.55rem 0;border-top:1px dashed var(--border)}
.rowlist li:first-child{border-top:0}
.rowlist a{color:var(--text);text-decoration:none;font-weight:700;font-size:.9375rem;letter-spacing:-.01em}
.rowlist a:hover{color:var(--accent)}
.rowlist .where{display:block;color:var(--text-dim);font-weight:500;font-size:.75rem}
.rowlist .meta{font-family:var(--font-mono);font-size:.65rem;color:var(--text-dim);white-space:nowrap;text-align:right;line-height:1.6}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:.5rem;list-style:none;padding:0;margin:0}
.grid a{display:block;padding:.6rem .75rem;border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--surface);text-decoration:none;color:var(--text);font-weight:700;font-size:.9rem}
.grid a small{display:block;font-family:var(--font-mono);font-size:.625rem;color:var(--text-dim);font-weight:500;margin-top:.15rem}
.statenav{font-family:var(--font-mono);font-size:.7rem;line-height:1.9;color:var(--text-dim)}
.statenav a{color:var(--accent);text-decoration:none}
form label{display:block;font-family:var(--font-mono);font-size:.625rem;letter-spacing:.09em;text-transform:uppercase;color:var(--text-dim);margin:.7rem 0 .3rem}
form input{width:100%;min-height:44px;padding:.6rem .75rem;border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--surface);color:var(--text);font:inherit;font-size:16px}
form button{margin-top:.9rem;cursor:pointer}
.ok{color:var(--accent2);font-weight:600;font-size:.875rem}.err{color:var(--red);font-weight:600;font-size:.875rem}
.gone-card{border-left:3px solid var(--red)}
`;

const PIN = '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>';

function layout({ title, desc, canonical, body, status = 200, robots = 'index,follow', cache = 300, ogTitle, type = 'website', spec = 'SELF-SERVICE YARD INTEL' }) {
  const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>${esc(title)}</title>
<meta name="description" content="${esc(desc)}">
<meta name="robots" content="${robots}"><meta name="theme-color" content="#F4F2EC" media="(prefers-color-scheme: light)"><meta name="theme-color" content="#1C1C1A" media="(prefers-color-scheme: dark)">
<link rel="canonical" href="${esc(canonical)}">
<link rel="icon" type="image/png" sizes="192x192" href="${SITE}/favicon.ico?v=3" sizes="any"><link rel="icon" type="image/png" sizes="32x32" href="${SITE}/favicon-32.png?v=3"><link rel="apple-touch-icon" href="${SITE}/apple-touch-icon.png?v=3">
<meta property="og:type" content="${type}"><meta property="og:site_name" content="YardScout">
<meta property="og:title" content="${esc(ogTitle || title)}"><meta property="og:description" content="${esc(desc)}">
<meta property="og:url" content="${esc(canonical)}"><meta property="og:image" content="${OG_IMAGE}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="${esc(ogTitle || title)}"><meta name="twitter:description" content="${esc(desc)}"><meta name="twitter:image" content="${OG_IMAGE}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Saira+Stencil+One&display=swap" rel="stylesheet">
<link rel="stylesheet" href="${SITE}/styles.css">
<script>try{var t=localStorage.getItem('ys_theme');if(t=='dark'||t=='light')document.documentElement.setAttribute('data-theme',t);}catch(e){}</script>
<style>${CSS}</style></head>
<body>
<header>
  <div class="header-row">
    <a href="${SITE}/" aria-label="YardScout home" style="display:block"><svg class="brand-mark" viewBox="4 29 122 72" aria-hidden="true"><g fill="var(--mark-rim)"><circle cx="40" cy="65" r="36"/><circle cx="90" cy="65" r="36"/></g><g fill="#F26B1D"><circle cx="40" cy="65" r="32"/><circle cx="90" cy="65" r="32"/></g><g transform="translate(65 64) scale(0.88) translate(-66.5 -63)"><path d="M16 76 V62 Q16 59 19 59 H35 L46 44.5 Q47 43.5 49 43.5 H79 Q81 43.5 82 44.5 L92 58 L110 60 Q114 60.5 114 63 V76 Q114 79 111 79 H106 A10 10 0 0 0 86 79 H44 A10 10 0 0 0 24 79 H19 Q16 79 16 76 Z" fill="#1C1C1A"/><path d="M49 46.8 H78.3 L88 57.4 H46.6 L44 54.2 Z" fill="#F26B1D"/><rect x="63" y="46" width="2.6" height="12" fill="#1C1C1A"/><g fill="#1C1C1A"><circle cx="34" cy="80" r="8"/><circle cx="96" cy="80" r="8"/></g><g fill="#F26B1D"><circle cx="34" cy="80" r="3.2"/><circle cx="96" cy="80" r="3.2"/></g></g></svg></a>
    <div class="wordmark"><h1><a href="${SITE}/" style="color:inherit;text-decoration:none">Yard<span class="wm-scout">Scout</span></a></h1><span class="head-spec">${esc(spec)}</span></div>
  </div>
  <div style="display:flex;align-items:center;gap:0.5rem">
    <button type="button" id="theme-toggle" class="theme-toggle" title="Switch light / dark" aria-label="Switch light or dark theme"><svg class="ico ico-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"/></svg><svg class="ico ico-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg></button>
    <a class="btn" href="${SITE}/" style="text-decoration:none">Open the app</a>
  </div>
</header>
<script>
(function(){var b=document.getElementById('theme-toggle');if(!b)return;b.addEventListener('click',function(){var h=document.documentElement,p=h.getAttribute('data-theme');var cur=(p=='dark'||p=='light')?p:(window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');var n=cur=='dark'?'light':'dark';h.setAttribute('data-theme',n);try{localStorage.setItem('ys_theme',n);}catch(e){}});})();
</script>
<main class="share-main">
${body}
</main></body></html>`;
  return new Response(html, {
    status,
    headers: {
      'content-type': 'text/html; charset=utf-8',
      'cache-control': `public, max-age=${cache}`,
    },
  });
}

function storesLine() {
  return `<p class="stores">Arrival alerts live in the app: <a href="${IOS_URL}">iPhone</a> · <a href="${PLAY_URL}">Android</a> · or use the <a href="${SITE}/">web version</a>.</p>`;
}


function carCard({ name, yardName, where, row, metaHtml, specs, clock, href, badge }) {
  const inner = `<div class="car-header"><div style="min-width:0;">
      <div class="car-name">${esc(name)}</div>
      <div class="live-card-location">${PIN} <span class="loc-name">${esc(yardName)}</span>${where ? ' <span class="dist">&middot; ' + esc(where) + '</span>' : ''}${row ? '<span class="live-card-row">Row ' + esc(row) + '</span>' : ''}</div>
      ${metaHtml ? `<div class="car-meta">${metaHtml}</div>` : ''}
      ${specs ? `<div class="car-meta car-specs">${esc(specs)}</div>` : ''}
      ${clock ? `<div class="lot-clock${clock.soon ? ' lot-clock-soon' : ''}">${esc(clock.short)}</div>` : ''}
    </div>${badge ? `<div class="car-badges"><span class="badge badge-new">${esc(badge)}</span></div>` : ''}</div>`;
  return `<div class="car-card match-card" style="--tier-color:var(--accent);">${href ? `<a class="car-link" href="${href}">${inner}</a>` : inner}</div>`;
}

export async function renderCarPage(token) {
  token = decodeURIComponent(token || '').trim();
  if (!token || token.length > 32 || !/^[A-Za-z0-9-]+$/.test(token)) {
    return layout({ title: 'YardScout', desc: 'Live self-service junkyard inventory.', canonical: SITE + '/', status: 404, robots: 'noindex', body: '<div class="car-card gone-card"><div class="car-name">Not a car link</div><div class="share-sub" style="margin:.4rem 0 0">Car links look like yardscout.io/car/&lt;VIN or id&gt;.</div></div>' });
  }
  const canonical = `${SITE}/car/${encodeURIComponent(token)}`;
  const [det, dir] = await Promise.all([apiJson('/v1/vehicles/' + encodeURIComponent(token), 300), apiJson('/v1/yards', 300)]);

  if (!det.data || !det.data.vehicle) {
    // A car that was shared and then pulled/crushed is the normal case here,
    // not an error — say so and turn it into the alert pitch.
    return layout({
      title: 'This car is no longer listed — YardScout',
      desc: 'It was likely pulled or crushed. YardScout can alert you when the next one lands at a yard near you.',
      canonical, status: 404, robots: 'noindex', cache: 120, spec: 'GONE FROM THE YARD LIST',
      body: `<p class="kicker">Gone from the yard list</p><h2 class="share-h">This car is no longer listed</h2>
<p class="share-sub">Yards drop a car from their published inventory when it's pulled or crushed. The link may also be older than the inventory we keep.</p>
<div class="cta"><a class="btn btn-primary" href="${SITE}/#tab=alerts">Watch for the next one</a><a class="btn" href="${SITE}/">Search what's in the yards now</a></div>${storesLine()}`,
    });
  }

  const d = det.data; const v = d.vehicle; const y = d.yard || {};
  const yf = (dir.data && dir.data.yardFields) || [];
  const yrow = dir.data && dir.data.yards && dir.data.yards[y.id];
  const avg = yrow ? yrow[yf.indexOf('avgLifespanDays')] : null;
  const basis = yrow ? yrow[yf.indexOf('lifespanBasis')] : null;
  const daysOn = daysSince(v.dateAdded);
  const cw = crushWindow(daysOn, avg, basis);
  const name = `${v.year} ${v.make} ${v.model}`.trim();
  const yardName = y.location || 'a covered yard';
  const where = [y.city, y.state].filter(Boolean).join(', ');
  const key = v.vin || String(v.id);
  const vp = Array.isArray(d.vpic) ? d.vpic : [];
  const trim = vp[0] && vp[1] === 'usable' ? vp[0] : '';
  const drive = vp[3] ? String(vp[3]).split('/')[0] : '';
  const yardHref = `${SITE}/yard/${slugify(yardName)}`;
  const isNew = daysOn != null && daysOn <= 7;

  const descBits = [`${name} at ${yardName}`];
  if (v.row) descBits.push(`Row ${v.row}`);
  if (v.dateAdded) descBits.push(`set out ${fmtDate(v.dateAdded)}`);
  if (daysOn != null && avg) descBits.push(cw.left > 0 ? `~${cw.left} days left at this yard's typical pace` : 'past this yard\'s typical stay');
  const desc = descBits.join(' · ') + '. Live self-service yard inventory on YardScout.';

  const meta = [v.dateAdded ? `Set out ${esc(fmtDate(v.dateAdded))}` : 'Set-out date not published',
    v.vin ? `&middot; VIN ${esc(v.vin)}` : ''].join(' ');
  const shortClock = avg && daysOn != null
    ? { short: daysOn > avg ? `On the lot ${daysOn} days · past the ~${avg} typical` : `Day ${daysOn + 1} on the lot · ~${avg} typical ${basis === 'yard' ? 'at this yard' : basis === 'chain' ? 'for this chain' : 'across yards'}`, soon: cw.soon }
    : (daysOn != null ? { short: `Day ${daysOn + 1} on the lot`, soon: false } : null);

  const [siteUrl, price, priceRows] = [await yardSiteFor(yardName), priceListFor(yardName), await yardPriceRows(yardName)];
  const yardLinks = (siteUrl || price)
    ? `<p class="share-sub" style="margin:.2rem 0 .4rem">${siteUrl ? `<a href="${esc(siteUrl)}" target="_blank" rel="noopener">Yard's own inventory page &#8599;</a>` : ''}${siteUrl && price ? ' &middot; ' : ''}${price ? `<a href="${esc(price.url)}" target="_blank" rel="noopener">${esc(price.label)} price list &#8599;</a>` : ''}</p>` : '';
  const body = `<p class="kicker">Seen in a self-service yard · <a href="${yardHref}">${esc(yardName)}</a></p>
${carCard({ name, yardName, where, row: v.row, metaHtml: meta, specs: [trim, drive].filter(Boolean).join(' · '), clock: shortClock, badge: isNew ? 'New' : '' })}
<div class="car-card">
<div class="clock${cw.soon ? ' soon' : ''}">${esc(cw.line)}<small>Based on how long departed cars sat on this lot before they left — an estimate, not a schedule. Call the yard before a long drive.</small></div>
</div>
${yardLinks}
${priceListHtml(priceRows, yardName)}
<div class="cta"><a class="btn btn-primary" href="${SITE}/#car=${encodeURIComponent(key)}">Open in YardScout</a><a class="btn" href="${SITE}/#tab=alerts">Alert me when the next ${esc(v.make)} ${esc(v.model)} lands near me</a></div>
${storesLine()}
<p class="note">Row and set-out date come straight from the yard's own published list, refreshed every 4 hours (inventory as of ${esc(fmtStamp(d.scrapedAt))}). Yards track cars, not the parts still on them — a car that has sat a while may be picked over.</p>`;

  return layout({ title: `${name} at ${yardName} — YardScout`, ogTitle: `${name}${v.row ? ' · Row ' + v.row : ''} · ${yardName}`, desc, canonical, body, type: 'article', spec: `${where || 'SELF-SERVICE YARD'} · ROW ${v.row || '—'}` });
}

export async function renderYardPage(slug) {
  slug = decodeURIComponent(slug || '').trim().toLowerCase();
  const dir = (await apiJson('/v1/yards', 300)).data;
  if (!dir) return layout({ title: 'YardScout', desc: 'Live self-service junkyard inventory.', canonical: SITE + '/', status: 503, robots: 'noindex', cache: 60, body: '<div class="car-card"><div class="car-name">Inventory is briefly unavailable</div><div class="share-sub" style="margin:.4rem 0 0">Try again in a minute.</div></div>' });
  const yf = dir.yardFields || [];
  const iLoc = yf.indexOf('location');
  const idx = dir.yards.findIndex((y) => slugify(y[iLoc]) === slug);
  if (idx < 0) {
    return layout({ title: 'Yard not found — YardScout', desc: 'We don\'t cover a yard by that name yet.', canonical: SITE + '/', status: 404, robots: 'noindex', cache: 120, body: `<h2 class="share-h">We don't cover that yard yet</h2><p class="share-sub">YardScout tracks ${dir.yards.length} self-service yards. Missing one? Ask on the <a href="${SITE}/yards#request">coverage page</a>.</p><div class="cta"><a class="btn btn-primary" href="${SITE}/yards">See covered yards</a></div>` });
  }
  const y = dir.yards[idx];
  const name = y[iLoc]; const city = y[yf.indexOf('city')]; const state = y[yf.indexOf('state')];
  const avg = y[yf.indexOf('avgLifespanDays')]; const basis = y[yf.indexOf('lifespanBasis')];
  const canonical = `${SITE}/yard/${slug}`;
  const shard = (await apiJson('/v1/inventory/shard/' + idx, 900)).data;
  // /v1/yards doesn't carry the row layout; this is the documented order
  // (backend/src/inventory.js) and only ever grows at the end.
  const f = dir.fields || ['id', 'vin', 'year', 'make', 'model', 'row', 'dateAdded', 'yard', 'partSet', 'maxValue', 'premium'];
  const iYear = f.indexOf('year'), iMake = f.indexOf('make'), iModel = f.indexOf('model'), iRow = f.indexOf('row'), iDate = f.indexOf('dateAdded'), iVin = f.indexOf('vin'), iId = f.indexOf('id');
  const rows = (shard && shard.vehicles) || [];
  const total = rows.length;
  const recent = rows.filter((r) => { const d = daysSince(r[iDate]); return d != null && d <= 7; })
    .sort((a, b) => String(b[iDate]).localeCompare(String(a[iDate])) || String(a[iMake]).localeCompare(String(b[iMake])));
  const where = [city, state].filter(Boolean).join(', ');
  const title = `What's at ${name} this week`;
  const desc = `${total} cars on the lot at ${name}${where ? ' (' + where + ')' : ''}, ${recent.length} set out in the last 7 days${avg ? `, cars typically last ~${avg} days here` : ''}. Live list, refreshed every 4 hours.`;
  // A taste, not a search tool: the full list (and filters) live in the app.
  const SHOW = 30;
  const items = recent.slice(0, SHOW).map((r) => {
    const key = r[iVin] || String(r[iId]);
    const car = `${r[iYear]} ${r[iMake]} ${r[iModel]}`.trim();
    return `<li><a href="${SITE}/car/${encodeURIComponent(key)}">${esc(car)}</a><span class="meta">${r[iRow] ? 'Row ' + esc(r[iRow]) + '<br>' : ''}${esc(fmtDate(r[iDate]))}</span></li>`;
  }).join('');
  const [ySite, yPrice, yRows] = [await yardSiteFor(name), priceListFor(name), await yardPriceRows(name)];
  const lifeLine = avg
    ? `Cars typically last ~${avg} days here${basis === 'chain' ? ' (chain average)' : basis === 'all' ? ' (all-yards average)' : ''}, based on when departed cars arrived and left.`
    : 'Not enough departure history yet to estimate how long cars last here.';
  const body = `<p class="kicker">Self-service yard · ${esc(where)}</p>
<h2 class="share-h">${esc(title)}</h2>
<div class="stats-bar"><div class="stat-card"><span class="label">On the lot</span><span class="value">${total.toLocaleString()}</span></div><div class="stat-card"><span class="label">New this week</span><span class="value accent">${recent.length}</span></div><div class="stat-card"><span class="label">Typical stay</span><span class="value">${avg ? '~' + avg + ' days' : '—'}</span></div></div>
<p class="share-sub">${esc(lifeLine)}${ySite ? ` <a href="${esc(ySite)}" target="_blank" rel="noopener">Yard's own inventory page &#8599;</a>` : ''}${yPrice ? ` &middot; <a href="${esc(yPrice.url)}" target="_blank" rel="noopener">${esc(yPrice.label)} price list &#8599;</a>` : ''}</p>
<div class="section">Set out in the last 7 days <span>· ${recent.length}</span></div>
<div class="car-card">${items ? `<ul class="rowlist">${items}</ul>` : '<p style="margin:0;color:var(--text-dim);font-size:.875rem">No new set-outs in the last 7 days on the yard\'s published list.</p>'}${recent.length > SHOW ? `<p class="note">Showing ${SHOW} of ${recent.length}. The full list is in the app.</p>` : ''}</div>
${priceListHtml(yRows, name)}
<div class="cta"><a class="btn btn-primary" href="${SITE}/">Search this yard in YardScout</a><a class="btn" href="${SITE}/#tab=alerts">Alert me when a car I want lands here</a></div>
${storesLine()}
<p class="note">Straight from the yard's own published list, refreshed every 4 hours (inventory as of ${esc(fmtStamp(dir.scrapedAt))}). Row numbers and dates are the yard's; call ahead before a long drive.</p>`;
  return layout({ title: `${title} — YardScout`, ogTitle: title, desc, canonical, body, cache: 900, spec: `${total.toLocaleString()} CARS ON ROW · ${esc(where)}` });
}

export async function renderYardSitemap() {
  const dir = (await apiJson('/v1/yards', 300)).data;
  if (!dir) return new Response('', { status: 503 });
  const iLoc = dir.yardFields.indexOf('location');
  const seen = new Set();
  const landed = await dataJson('landed.json', 900);
  const makeUrls = landed ? Object.entries(landed.makes).filter(([, m]) => m.total >= 20)
    .map(([mk]) => `<url><loc>${SITE}/landed/${slugify(mk)}</loc><changefreq>daily</changefreq></url>`).join('') : '';
  const urls = `<url><loc>${SITE}/yards</loc><changefreq>daily</changefreq></url><url><loc>${SITE}/landed</loc><changefreq>daily</changefreq></url>`
    + makeUrls + dir.yards.map((y) => slugify(y[iLoc])).filter((s) => s && !seen.has(s) && seen.add(s))
    .map((s) => `<url><loc>${SITE}/yard/${s}</loc><changefreq>daily</changefreq></url>`).join('');
  return new Response(`<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls}</urlset>`, {
    headers: { 'content-type': 'application/xml; charset=utf-8', 'cache-control': 'public, max-age=3600' },
  });
}

const STATE_NAMES = { AL:'Alabama',AK:'Alaska',AZ:'Arizona',AR:'Arkansas',CA:'California',CO:'Colorado',CT:'Connecticut',DE:'Delaware',FL:'Florida',GA:'Georgia',HI:'Hawaii',ID:'Idaho',IL:'Illinois',IN:'Indiana',IA:'Iowa',KS:'Kansas',KY:'Kentucky',LA:'Louisiana',ME:'Maine',MD:'Maryland',MA:'Massachusetts',MI:'Michigan',MN:'Minnesota',MS:'Mississippi',MO:'Missouri',MT:'Montana',NE:'Nebraska',NV:'Nevada',NH:'New Hampshire',NJ:'New Jersey',NM:'New Mexico',NY:'New York',NC:'North Carolina',ND:'North Dakota',OH:'Ohio',OK:'Oklahoma',OR:'Oregon',PA:'Pennsylvania',RI:'Rhode Island',SC:'South Carolina',SD:'South Dakota',TN:'Tennessee',TX:'Texas',UT:'Utah',VT:'Vermont',VA:'Virginia',WA:'Washington',WV:'West Virginia',WI:'Wisconsin',WY:'Wyoming',DC:'Washington DC' };

/** /yards — public coverage page: every tracked yard by state with counts,
 * recently added yards, and a request-a-yard form (POSTs to the API's
 * coverage endpoint with kind=yard). */
export async function renderYardsPage() {
  const [landed, added] = await Promise.all([dataJson('landed.json', 900), dataJson('yards_added.json', 900)]);
  if (!landed) return layout({ title: 'Covered yards — YardScout', desc: 'Self-service yards YardScout tracks.', canonical: SITE + '/yards', status: 503, robots: 'noindex', cache: 60, body: '<div class="car-card"><div class="car-name">Coverage list is briefly unavailable</div></div>' });
  const byState = new Map();
  let totalCars = 0;
  for (const [loc, city, state, n, recent] of landed.yards) {
    if (!loc) continue;
    totalCars += n || 0;
    const st = state || '—';
    if (!byState.has(st)) byState.set(st, []);
    byState.get(st).push({ loc, city, n: n || 0, recent: recent || 0 });
  }
  const states = [...byState.keys()].sort((a, b) => (STATE_NAMES[a] || a).localeCompare(STATE_NAMES[b] || b));
  const stateBlocks = states.map((st) => {
    const yards = byState.get(st).sort((a, b) => a.loc.localeCompare(b.loc));
    return `<div class="section" id="${esc(st)}">${esc(STATE_NAMES[st] || st)} <span>· ${yards.length} yard${yards.length === 1 ? '' : 's'}</span></div>
<div class="car-card"><ul class="rowlist">${yards.map((y) => `<li><a href="${SITE}/yard/${slugify(y.loc)}">${esc(y.loc)}${y.city ? `<span class="where">${esc(y.city)}</span>` : ''}</a><span class="meta">${y.n.toLocaleString()} cars<br>${y.recent} this week</span></li>`).join('')}</ul></div>`;
  }).join('');
  const newYards = (added || []).slice(0, 20);
  const stateNav = states.map((st) => `<a href="#${esc(st)}">${esc(st)}</a>`).join(' · ');
  const desc = `${landed.yards.length} self-service junkyards in ${states.length} states, ${totalCars.toLocaleString()} cars on the lots, scanned every 4 hours. Don't see your yard? Ask and it's usually in within a day or two.`;
  const body = `<p class="kicker">Coverage</p>
<h2 class="share-h">${landed.yards.length} self-service yards, every 4 hours</h2>
<div class="stats-bar"><div class="stat-card"><span class="label">Yards</span><span class="value">${landed.yards.length}</span></div><div class="stat-card"><span class="label">States</span><span class="value">${states.length}</span></div><div class="stat-card"><span class="label">Cars on row</span><span class="value accent">${totalCars.toLocaleString()}</span></div></div>
<p class="share-sub">As of ${esc(fmtStamp(landed.scrapedAt))}. Coverage is limited to yards that publish their inventory online — phone-only yards can't be tracked.</p>
<div class="car-card" id="request"><div class="car-name">Missing your yard?</div>
<p class="share-sub" style="margin:.3rem 0 0">If it posts inventory online, it's usually added within a day or two.</p>
<form id="yard-req" onsubmit="return ysReq(event)">
<label for="yn">Yard name</label><input id="yn" name="yard" required maxlength="80" placeholder="e.g. U-Pull-It Des Moines">
<label for="yu">Inventory page URL</label><input id="yu" name="url" type="url" maxlength="300" placeholder="https://…">
<label for="yc">City, state</label><input id="yc" name="city" maxlength="80" placeholder="Des Moines, IA">
<label for="ye">Your email (optional — we'll tell you when it's live)</label><input id="ye" name="email" type="email" maxlength="254">
<button class="btn btn-primary" type="submit">Ask for this yard</button> <span id="yard-req-msg" role="status"></span>
</form></div>
${newYards.length ? `<div class="section">Recently added</div><div class="car-card"><ul class="rowlist">${newYards.map((y) => `<li><a href="${SITE}/yard/${slugify(y.location)}">${esc(y.location)}${y.city ? `<span class="where">${esc([y.city, y.state].filter(Boolean).join(', '))}</span>` : ''}</a><span class="meta">added ${esc(fmtDate(y.added))}</span></li>`).join('')}</ul></div>` : ''}
<div class="section">By state</div><p class="statenav">${stateNav}</p>
${stateBlocks}
<div class="cta"><a class="btn btn-primary" href="${SITE}/">Search near your zip</a><a class="btn" href="${SITE}/landed">What landed this week, by make</a></div>
${storesLine()}
<script>
async function ysReq(e){e.preventDefault();const f=e.target,m=document.getElementById('yard-req-msg');m.textContent='Sending…';m.className='';
const url=f.url.value.trim(),city=f.city.value.trim();
try{const r=await fetch('${API}/v1/coverage/request',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({kind:'yard',part:f.yard.value.trim().slice(0,80),note:[url,city].filter(Boolean).join(' · ').slice(0,500),email:f.email.value.trim()})});
const j=await r.json().catch(()=>({}));if(r.ok){m.textContent='Got it — thanks. We check requests every day.';m.className='ok';f.reset();}else{m.textContent=j.message||'Could not send — try again.';m.className='err';}}
catch(err){m.textContent='Could not send — try again.';m.className='err';}return false;}
</script>`;
  return layout({ title: 'Covered yards — YardScout', ogTitle: `${landed.yards.length} self-service junkyards tracked by YardScout`, desc, canonical: SITE + '/yards', body, cache: 900, spec: `${landed.yards.length} YARDS · ${states.length} STATES · EVERY 4H` });
}

/** /landed and /landed/<make-slug> — what set out in the last 7 days, by
 * make, from docs/data/landed.json (written by every scan). The data-post
 * engine: "N 3rd-gen 4Runners landed this week" with row + yard, shareable. */
export async function renderLandedPage(slug) {
  const landed = await dataJson('landed.json', 900);
  if (!landed) return layout({ title: 'What landed — YardScout', desc: '', canonical: SITE + '/landed', status: 503, robots: 'noindex', cache: 60, body: '<div class="car-card"><div class="car-name">Briefly unavailable</div></div>' });
  const makes = Object.entries(landed.makes).filter(([, m]) => m.total >= 20);
  const stamp = esc(fmtStamp(landed.scrapedAt));
  if (!slug) {
    makes.sort((a, b) => b[1].recentCount - a[1].recentCount);
    const weekTotal = makes.reduce((n, [, m]) => n + m.recentCount, 0);
    const body = `<p class="kicker">Last ${landed.days} days</p><h2 class="share-h">What landed in the yards this week</h2>
<div class="stats-bar"><div class="stat-card"><span class="label">Set out this week</span><span class="value accent">${weekTotal.toLocaleString()}</span></div><div class="stat-card"><span class="label">Yards</span><span class="value">${landed.yards.length}</span></div><div class="stat-card"><span class="label">Updated</span><span class="value value-sm">${stamp}</span></div></div>
<p class="share-sub">Every car that set out at a tracked self-service yard in the last ${landed.days} days, by make.</p>
<ul class="grid">${makes.map(([mk, m]) => `<li><a href="${SITE}/landed/${slugify(mk)}">${esc(mk)}<small>${m.recentCount} this week · ${m.total.toLocaleString()} on lots</small></a></li>`).join('')}</ul>
<div class="cta"><a class="btn btn-primary" href="${SITE}/">Search near your zip</a><a class="btn" href="${SITE}/#tab=alerts">Get the weekly recap for a model you want</a></div>${storesLine()}`;
    return layout({ title: 'What landed in self-service yards this week — YardScout', ogTitle: 'What landed in the junkyards this week', desc: `New set-outs at ${landed.yards.length} self-service yards in the last ${landed.days} days, by make.`, canonical: SITE + '/landed', body, cache: 900, spec: `${weekTotal.toLocaleString()} SET OUT THIS WEEK` });
  }
  slug = decodeURIComponent(slug).toLowerCase();
  const hit = Object.entries(landed.makes).find(([mk]) => slugify(mk) === slug);
  if (!hit) return layout({ title: 'Make not found — YardScout', desc: '', canonical: SITE + '/landed', status: 404, robots: 'noindex', cache: 120, body: `<h2 class="share-h">No cars of that make on the lists</h2><div class="cta"><a class="btn btn-primary" href="${SITE}/landed">All makes</a></div>` });
  const [mk, m] = hit;
  // Public taste of the week: newest 40 per make, grouped by model. The
  // nationwide search this would otherwise become is the Pro "Any distance"
  // feature in the app, so the page stops well short of it.
  const SHOWN = 40;
  const shown = m.recent.slice(0, SHOWN);
  const byModel = new Map();
  for (const r of shown) { const k = String(r[2] || '—'); if (!byModel.has(k)) byModel.set(k, []); byModel.get(k).push(r); }
  const models = [...byModel.entries()].sort((a, b) => b[1].length - a[1].length || a[0].localeCompare(b[0]));
  const yardName = (i) => (landed.yards[i] || [])[0] || '';
  const yardState = (i) => (landed.yards[i] || [])[2] || '';
  const blocks = models.map(([model, rows]) => `<div class="section">${esc(mk)} ${esc(model)} <span>· ${rows.length}</span></div>
<div class="car-card"><ul class="rowlist">${rows.map((r) => `<li><a href="${SITE}/car/${encodeURIComponent(r[5])}">${esc(r[0])} ${esc(mk)} ${esc(model)}<span class="where">${esc(yardName(r[6]))}${yardState(r[6]) ? ', ' + esc(yardState(r[6])) : ''}</span></a><span class="meta">${r[3] ? 'Row ' + esc(r[3]) + '<br>' : ''}${esc(fmtDate(r[4]))}</span></li>`).join('')}</ul></div>`).join('');
  const truncated = m.recentCount > shown.length ? `<p class="note" style="margin-top:0">Showing the newest ${shown.length} of ${m.recentCount.toLocaleString()} set-outs this week. The full list, filters and alerts are in the app.</p>` : '';
  const desc = `${m.recentCount} ${mk} set out at self-service yards in the last ${landed.days} days (${m.total.toLocaleString()} on the lots right now), with row numbers and yards. As of ${fmtStamp(landed.scrapedAt)}.`;
  const body = `<p class="kicker">Last ${landed.days} days · <a href="${SITE}/landed">all makes</a></p>
<h2 class="share-h">${m.recentCount} ${esc(mk)}${m.recentCount === 1 ? '' : 's'} landed in self-service yards this week</h2>
<div class="stats-bar"><div class="stat-card"><span class="label">This week</span><span class="value accent">${m.recentCount.toLocaleString()}</span></div><div class="stat-card"><span class="label">On the lots now</span><span class="value">${m.total.toLocaleString()}</span></div><div class="stat-card"><span class="label">Yards</span><span class="value">${landed.yards.length}</span></div></div>
<p class="share-sub">Cars typically last about 70 days before the crusher, busy yards under three weeks — if one you want is on this list, your window is short.</p>
${truncated}${blocks}
<div class="cta"><a class="btn btn-primary" href="${SITE}/#tab=alerts">Alert me when a ${esc(mk)} I want lands near me</a><a class="btn" href="${SITE}/">Search near your zip</a></div>${storesLine()}
<p class="note">Straight from each yard's published list, refreshed every 4 hours. Row numbers and dates are the yard's; call ahead before a long drive.</p>`;
  return layout({ title: `${mk}: what landed in self-service yards this week — YardScout`, ogTitle: `${m.recentCount} ${mk}${m.recentCount === 1 ? '' : 's'} landed in junkyards this week`, desc, canonical: `${SITE}/landed/${slug}`, body, cache: 900, spec: `${m.recentCount.toLocaleString()} ${esc(mk).toUpperCase()} THIS WEEK` });
}
