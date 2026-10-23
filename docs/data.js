/* YardScout — shared date/price utilities used by app.js.
   (The old static DATABASE demo dataset that used to live here was removed
   in the Oct 2026 buyer-lens rework: it was no longer referenced anywhere
   and its seller-lens copy predated the app's mechanic/enthusiast framing.) */

function formatPrice(n) { return '$' + n.toLocaleString(); }
/* Parse a yard-published date for display. dateAdded is the yard's set-out
   date as a bare calendar date ('YYYY-MM-DD', no timezone). new Date() reads
   that as UTC MIDNIGHT, and toLocaleDateString() anywhere west of Greenwich
   then renders the PREVIOUS day — an Oct 5 set-out displayed as "Oct 4" in
   Utah (owner-reported 2026-10-21). Parse it as a LOCAL date so the app shows
   the same calendar date the yard publishes. Returns null when unparseable.

   Defensive against yard-feed garbage (owner-reported 2026-10-21: Fenix
   epoch placeholders shipped as 2070-01-01 and rendered 'Set out Jan 1 ·
   fresh' + NEW, because toLocaleDateString drops the year and a future date
   makes daysSinceAdded 0). The scraper now clamps at the source, but old
   payloads linger (stale-keep, HTTP caches), so the renderer also rejects
   implausible dates: more than 2 days ahead (UTC-dated feeds can be a
   calendar day ahead of the scanner, and the viewer's local zone another)
   or older than 15 years -> null, i.e. 'Set-out date unknown'. */
function parseYardDate(dateStr) {
  if (!dateStr) return null;
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(dateStr);
  const d = m ? new Date(+m[1], +m[2] - 1, +m[3]) : new Date(dateStr);
  if (isNaN(d.getTime())) return null;
  const now = Date.now();
  if (d.getTime() > now + 2 * 86400000) return null;          // future garbage
  if (d.getTime() < now - 15 * 365 * 86400000) return null;   // epoch/ancient garbage
  return d;
}

/* Epoch ms of the yard's set-out date (local midnight), 0 when unknown —
   for sorts and freshness math that previously used Date.parse(). */
function yardDateMs(dateStr) {
  const d = parseYardDate(dateStr);
  return d ? d.getTime() : 0;
}

function isNew(dateStr) {
  const d = parseYardDate(dateStr);
  if (!d) return false;
  return (new Date() - d) / 86400000 <= 7;
}

function daysSinceAdded(dateStr) {
  const d = parseYardDate(dateStr);
  if (!d) return 999;
  return Math.max(0, (new Date() - d) / 86400000);
}

function freshnessMultiplier(dateStr) {
  const days = daysSinceAdded(dateStr);
  if (days <= 3) return 1.0;
  if (days <= 7) return 0.90;
  if (days <= 14) return 0.75;
  if (days <= 30) return 0.55;
  return 0.35;
}

function freshnessLabel(dateStr) {
  const days = daysSinceAdded(dateStr);
  if (days <= 3) return { text: 'Fresh', color: 'var(--accent2)' };
  if (days <= 7) return { text: 'Recent', color: 'var(--accent)' };
  if (days <= 14) return { text: '1-2 wks', color: 'var(--orange)' };
  if (days <= 30) return { text: '2-4 wks', color: 'var(--text-dim)' };
  return { text: '30+ days', color: 'var(--red)' };
}

