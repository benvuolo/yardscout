/* Shared prototype helpers: data access, formatting, icons, routing.
   Data is a real sample of docs/data/inventory_live.json (scan 2026-11-06,
   zip 95112 / San Jose, 50-mile radius) — see design/shared/sample.js. */
const D = window.YS;
const qs = new URLSearchParams(location.search);
const SCREEN = qs.get('s') || 'home';
if (qs.has('shot')) document.documentElement.classList.add('shot');
if (qs.get('theme')) document.documentElement.dataset.theme = qs.get('theme');
if (qs.get('zoom')) document.documentElement.style.fontSize = (16 * +qs.get('zoom') / 100) + 'px';

const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const yardShort = y => y.replace(/^Pick-n-Pull - /, '');
const chain = y => y.split(' - ')[0];
const money = n => '$' + Math.round(n).toLocaleString();
const isOption = p => p.status === 'unconfirmed';
const cleanPart = n => n.replace(/\s*\([^)]*\)/, '');
const partNote = n => (n.match(/\(([^)]*)\)/) || [])[1] || '';
const transShort = t => /manual/i.test(t) && !/automat/i.test(t) ? 'Manual' : (t || '').replace('Continuously Variable Transmission (CVT)', 'CVT').replace(/^Automatic$/, 'Auto');
const isManual = c => /manual/i.test(c.trans) && !/automat/i.test(c.trans);
const setOut = c => { const d = new Date(c.dateAdded + 'T12:00'); return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }); };
function value(c) {
  const conf = c.parts.filter(p => !isOption(p));
  const best = conf.slice().sort((a, b) => b.high - a.high)[0];
  return { conf, opt: c.parts.filter(isOption), best, sumLow: conf.reduce((s, p) => s + p.low, 0), sumHigh: conf.reduce((s, p) => s + p.high, 0) };
}
function stay(c) {
  const pct = Math.min(1, c.day / c.typical);
  const label = pct < .34 ? 'Fresh' : pct < .75 ? 'Mid-stay' : 'Leaving soon';
  return { pct, label, txt: `Day ${c.day} of ~${c.typical}` };
}
const car = id => D.cars.find(c => String(c.id) === String(id)) || D.civics.find(c => String(c.id) === String(id));
const PNP = { Alternator: 42.98, Starter: 40.98 }; // real Pick-n-Pull price list, incl. core
const yardPrice = p => { const k = Object.keys(PNP).find(k => p.name.startsWith(k)); return k ? money2(PNP[k]) : '~' + money(p.cost); };
const money2 = n => '$' + n.toFixed(2);

const ICONS = {
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
  pin: '<path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
  bell: '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>',
  wrench: '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',
  car: '<path d="M5 17h14M5 17a2 2 0 1 1-4 0v-4l2-5h12l3 5h3v4a2 2 0 1 1-4 0"/><circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/>',
  list: '<path d="M9 6h11M9 12h11M9 18h11"/><path d="m3 6 1 1 2-2M3 12l1 1 2-2M3 18l1 1 2-2"/>',
  map: '<path d="m9 4-6 2v14l6-2 6 2 6-2V4l-6 2-6-2Z"/><path d="M9 4v14M15 6v14"/>',
  back: '<path d="m15 18-6-6 6-6"/>',
  chev: '<path d="m9 18 6-6-6-6"/>',
  down: '<path d="m6 9 6 6 6-6"/>',
  x: '<path d="M18 6 6 18M6 6l12 12"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  share: '<path d="M12 3v13M8 7l4-4 4 4"/><path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7"/>',
  heart: '<path d="M19 14c1.5-1.46 3-3.2 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.04 3 5.5l7 7Z"/>',
  locate: '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/><circle cx="12" cy="12" r="7"/>',
  filter: '<path d="M4 6h16M7 12h10M10 18h4"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  lock: '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
  gear: '<path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z"/>',
  ext: '<path d="M7 17 17 7M8 7h9v9"/>',
  copy: '<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/>',
  garage: '<path d="M3 21V9l9-6 9 6v12"/><path d="M7 21v-8h10v8M7 17h10"/>',
  spark: '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8"/>',
  shift: '<circle cx="6" cy="5" r="2"/><circle cx="12" cy="5" r="2"/><circle cx="18" cy="5" r="2"/><circle cx="6" cy="19" r="2"/><circle cx="12" cy="19" r="2"/><path d="M6 7v12M12 7v12M18 7v5H6"/>',
};
const icon = (n, cls = '') => `<svg class="ico ${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[n] || ''}</svg>`;

function protoNav(screens) {
  const n = document.createElement('nav'); n.className = 'proto-nav'; n.setAttribute('aria-label', 'Prototype screens');
  n.innerHTML = screens.map(s => `<a href="?s=${s}"${s === SCREEN ? ' aria-current="page"' : ''}>${s}</a>`).join('') + `<a href="../">all</a>`;
  document.body.appendChild(n);
}
const go = (s, extra = '') => `?s=${s}${extra}`;
