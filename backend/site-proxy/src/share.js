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

const CSS = `
:root{--bg:#efece4;--surface:#faf8f2;--surface2:#eae6da;--border:#d8d2c2;--text:#1b1913;--dim:#5f594a;--accent:#bf4a08;--accent-hover:#a03d06;--red:#b03429;--green:#3f6c33}
@media(prefers-color-scheme:dark){:root{--bg:#17150f;--surface:#211e16;--surface2:#2a261c;--border:#3b3628;--text:#efece4;--dim:#b0a890;--accent:#e8702a;--accent-hover:#f08a4a;--red:#e06b60;--green:#8dbb7d}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--text);font:16px/1.5 Inter,-apple-system,BlinkMacSystemFont,system-ui,sans-serif}
a{color:var(--accent)}main{max-width:640px;margin:0 auto;padding:16px 16px 48px}
.top{display:flex;align-items:center;justify-content:space-between;padding:8px 0 20px}
.wordmark{font-weight:900;letter-spacing:-.02em;text-decoration:none;color:var(--text);font-size:1.1rem}
.wordmark span{color:var(--accent)}
.kicker{color:var(--dim);font-size:.8125rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;margin:0 0 4px}
h1{font-size:1.75rem;line-height:1.15;letter-spacing:-.02em;margin:0 0 6px;font-weight:800}
.sub{color:var(--dim);margin:0 0 20px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px;margin:0 0 14px}
.facts{display:grid;grid-template-columns:1fr 1fr;gap:12px 16px;margin:0}
.facts div{min-width:0}.facts dt{color:var(--dim);font-size:.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin:0 0 2px}
.facts dd{margin:0;font-weight:600;overflow-wrap:anywhere}.mono{font-family:ui-monospace,SF Mono,Menlo,Consolas,monospace;font-size:.9rem;font-weight:500}
.clock{border-left:3px solid var(--border);padding:2px 0 2px 12px;margin:14px 0 0;color:var(--text)}
.clock.soon{border-color:var(--accent)}.clock small{display:block;color:var(--dim);margin-top:4px}
.cta{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0 6px}
.btn{display:inline-block;min-height:44px;padding:11px 18px;border-radius:10px;font-weight:700;text-decoration:none;border:1px solid var(--accent);color:var(--accent);background:transparent}
.btn.primary{background:var(--accent);color:#fff}.btn:hover{border-color:var(--accent-hover)}.btn.primary:hover{background:var(--accent-hover)}
.stores{color:var(--dim);font-size:.875rem;margin:8px 0 0}
.note{color:var(--dim);font-size:.8125rem;margin:18px 0 0}
.list{list-style:none;padding:0;margin:0}.list li{display:flex;justify-content:space-between;gap:12px;padding:10px 0;border-top:1px solid var(--border)}
.list li:first-child{border-top:0}.list a{font-weight:600;text-decoration:none;color:var(--text)}.list a:hover{color:var(--accent)}.list .meta{color:var(--dim);font-size:.875rem;white-space:nowrap}
.gone{border-color:var(--red)}
`;

function layout({ title, desc, canonical, body, status = 200, robots = 'index,follow', cache = 300, ogTitle, type = 'website' }) {
  const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)}</title>
<meta name="description" content="${esc(desc)}">
<meta name="robots" content="${robots}">
<link rel="canonical" href="${esc(canonical)}">
<link rel="icon" href="${SITE}/icons/icon-192.png">
<meta property="og:type" content="${type}"><meta property="og:site_name" content="YardScout">
<meta property="og:title" content="${esc(ogTitle || title)}"><meta property="og:description" content="${esc(desc)}">
<meta property="og:url" content="${esc(canonical)}"><meta property="og:image" content="${OG_IMAGE}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="${esc(ogTitle || title)}"><meta name="twitter:description" content="${esc(desc)}"><meta name="twitter:image" content="${OG_IMAGE}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>${CSS}</style></head>
<body><main>
<div class="top"><a class="wordmark" href="${SITE}/">Yard<span>Scout</span></a><a href="${SITE}/" style="font-size:.875rem">Search yards near you →</a></div>
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

export async function renderCarPage(token) {
  token = decodeURIComponent(token || '').trim();
  if (!token || token.length > 32 || !/^[A-Za-z0-9-]+$/.test(token)) {
    return layout({ title: 'YardScout', desc: 'Live self-service junkyard inventory.', canonical: SITE + '/', status: 404, robots: 'noindex', body: '<div class="card gone"><h1>Not a car link</h1><p class="sub">Car links look like yardscout.io/car/&lt;VIN or id&gt;.</p></div>' });
  }
  const canonical = `${SITE}/car/${encodeURIComponent(token)}`;
  const [det, dir] = await Promise.all([apiJson('/v1/vehicles/' + encodeURIComponent(token), 300), apiJson('/v1/yards', 300)]);

  if (!det.data || !det.data.vehicle) {
    // A car that was shared and then pulled/crushed is the normal case here,
    // not an error — say so and turn it into the alert pitch.
    return layout({
      title: 'This car is no longer listed — YardScout',
      desc: 'It was likely pulled or crushed. YardScout can alert you when the next one lands at a yard near you.',
      canonical, status: 404, robots: 'noindex', cache: 120,
      body: `<div class="card gone"><p class="kicker">Gone from the yard list</p><h1>This car is no longer listed</h1>
<p class="sub">Yards drop a car from their published inventory when it's pulled or crushed. The link may also be older than the inventory we keep.</p>
<div class="cta"><a class="btn primary" href="${SITE}/#tab=alerts">Watch for the next one</a><a class="btn" href="${SITE}/">Search what's in the yards now</a></div>${storesLine()}</div>`,
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
  const engine = vp[0] && vp[1] === 'usable' ? vp[0] : '';
  const drive = vp[3] ? String(vp[3]).split('/')[0] : '';
  const yardHref = `${SITE}/yard/${slugify(yardName)}`;

  const descBits = [`${name} at ${yardName}`];
  if (v.row) descBits.push(`Row ${v.row}`);
  if (v.dateAdded) descBits.push(`set out ${fmtDate(v.dateAdded)}`);
  if (daysOn != null && avg) descBits.push(cw.left > 0 ? `~${cw.left} days left at this yard's typical pace` : 'past this yard\'s typical stay');
  const desc = descBits.join(' · ') + '. Live self-service yard inventory on YardScout.';

  const facts = [
    ['Yard', `<a href="${yardHref}">${esc(yardName)}</a>${where ? `<br><span style="font-weight:500;color:var(--dim)">${esc(where)}</span>` : ''}`],
    ['Row', v.row ? esc(v.row) : '<span style="color:var(--dim);font-weight:500">not published</span>'],
    ['Set out', v.dateAdded ? esc(fmtDate(v.dateAdded)) : '<span style="color:var(--dim);font-weight:500">not published</span>'],
    ['VIN', v.vin ? `<span class="mono">${esc(v.vin)}</span>` : '<span style="color:var(--dim);font-weight:500">not published</span>'],
  ];
  if (engine || drive) facts.push(['Decoded from VIN', esc([engine, drive].filter(Boolean).join(' · '))]);

  const body = `<p class="kicker">Seen in a self-service yard</p>
<h1>${esc(name)}</h1>
<p class="sub">${esc(yardName)}${where ? ' · ' + esc(where) : ''}</p>
<div class="card">
<dl class="facts">${facts.map(([k, val]) => `<div><dt>${k}</dt><dd>${val}</dd></div>`).join('')}</dl>
<p class="clock${cw.soon ? ' soon' : ''}">${esc(cw.line)}<small>Based on how long departed cars sat on this lot before they left — an estimate, not a schedule. Call the yard before a long drive.</small></p>
</div>
<div class="cta"><a class="btn primary" href="${SITE}/#car=${encodeURIComponent(key)}">Open in YardScout</a><a class="btn" href="${SITE}/#tab=alerts">Alert me when the next ${esc(v.make)} ${esc(v.model)} lands near me</a></div>
${storesLine()}
<p class="note">Row and set-out date come straight from the yard's own published list, refreshed every 4 hours (this page: inventory as of ${esc(fmtStamp(d.scrapedAt))}). Yards track cars, not the parts still on them — a car that has sat a while may be picked over.</p>`;

  return layout({ title: `${name} at ${yardName} — YardScout`, ogTitle: `${name}${v.row ? ' · Row ' + v.row : ''} · ${yardName}`, desc, canonical, body, type: 'article' });
}

export async function renderYardPage(slug) {
  slug = decodeURIComponent(slug || '').trim().toLowerCase();
  const dir = (await apiJson('/v1/yards', 300)).data;
  if (!dir) return layout({ title: 'YardScout', desc: 'Live self-service junkyard inventory.', canonical: SITE + '/', status: 503, robots: 'noindex', cache: 60, body: '<div class="card"><h1>Inventory is briefly unavailable</h1><p class="sub">Try again in a minute.</p></div>' });
  const yf = dir.yardFields || [];
  const iLoc = yf.indexOf('location');
  const idx = dir.yards.findIndex((y) => slugify(y[iLoc]) === slug);
  if (idx < 0) {
    return layout({ title: 'Yard not found — YardScout', desc: 'We don\'t cover a yard by that name yet.', canonical: SITE + '/', status: 404, robots: 'noindex', cache: 120, body: `<div class="card gone"><h1>We don't cover that yard yet</h1><p class="sub">YardScout tracks ${dir.yards.length} self-service yards. Ask us to add one from the Parts tab in the app.</p><div class="cta"><a class="btn primary" href="${SITE}/">See covered yards</a></div></div>` });
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
  const SHOW = 80;
  const items = recent.slice(0, SHOW).map((r) => {
    const key = r[iVin] || String(r[iId]);
    const car = `${r[iYear]} ${r[iMake]} ${r[iModel]}`.trim();
    return `<li><a href="${SITE}/car/${encodeURIComponent(key)}">${esc(car)}</a><span class="meta">${r[iRow] ? 'Row ' + esc(r[iRow]) + ' · ' : ''}${esc(fmtDate(r[iDate]))}</span></li>`;
  }).join('');
  const lifeLine = avg
    ? `Cars typically last ~${avg} days here${basis === 'chain' ? ' (chain average)' : basis === 'all' ? ' (all-yards average)' : ''}, based on when departed cars arrived and left.`
    : 'Not enough departure history yet to estimate how long cars last here.';
  const body = `<p class="kicker">Self-service yard · ${esc(where)}</p>
<h1>${esc(title)}</h1>
<p class="sub">${total} cars on the lot · ${recent.length} set out in the last 7 days</p>
<div class="card"><p style="margin:0">${esc(lifeLine)}</p></div>
<div class="card">${items ? `<ul class="list">${items}</ul>` : '<p style="margin:0;color:var(--dim)">No new set-outs in the last 7 days on the yard\'s published list.</p>'}${recent.length > SHOW ? `<p class="note">Showing ${SHOW} of ${recent.length}. The full list is in the app.</p>` : ''}</div>
<div class="cta"><a class="btn primary" href="${SITE}/">Search this yard in YardScout</a><a class="btn" href="${SITE}/#tab=alerts">Alert me when a car I want lands here</a></div>
${storesLine()}
<p class="note">Straight from the yard's own published list, refreshed every 4 hours (inventory as of ${esc(fmtStamp(dir.scrapedAt))}). Row numbers and dates are the yard's; call ahead before a long drive.</p>`;
  return layout({ title: `${title} — YardScout`, ogTitle: title, desc, canonical, body, cache: 900 });
}

export async function renderYardSitemap() {
  const dir = (await apiJson('/v1/yards', 300)).data;
  if (!dir) return new Response('', { status: 503 });
  const iLoc = dir.yardFields.indexOf('location');
  const seen = new Set();
  const urls = dir.yards.map((y) => slugify(y[iLoc])).filter((s) => s && !seen.has(s) && seen.add(s))
    .map((s) => `<url><loc>${SITE}/yard/${s}</loc><changefreq>daily</changefreq></url>`).join('');
  return new Response(`<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls}</urlset>`, {
    headers: { 'content-type': 'application/xml; charset=utf-8', 'cache-control': 'public, max-age=3600' },
  });
}
