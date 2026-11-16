/* GET /geo: the visitor's approximate area.
 *
 * Cloudflare attaches a city-level location to every request it carries
 * (derived from the connecting IP address). The app asks this once, on a
 * first visit with no zip saved, so it can show the yards near that area
 * straight away instead of a zip prompt, clearly labelled as a guess that
 * the visitor can correct (2026-11-16; the zip prompt was the first screen
 * for every new visitor).
 *
 * Nothing is stored or logged here. The answer goes back to the visitor it
 * describes and is never cached. Coordinates are rounded to one decimal
 * (about 7 miles): "which yards are near" needs no more. US and Canada only,
 * the area the yards cover; anywhere else the app keeps its zip prompt.
 */
export function geoAnswer(cf) {
  const lat = parseFloat(cf && cf.latitude), lng = parseFloat(cf && cf.longitude);
  const country = String((cf && cf.country) || '').toUpperCase();
  if (!Number.isFinite(lat) || !Number.isFinite(lng) || Math.abs(lat) > 90 || Math.abs(lng) > 180) return { ok: false };
  if (country !== 'US' && country !== 'CA') return { ok: false };
  const clean = (s, n) => String(s == null ? '' : s).replace(/[<>"'&\\]/g, '').trim().slice(0, n);
  return {
    ok: true,
    lat: Math.round(lat * 10) / 10,
    lng: Math.round(lng * 10) / 10,
    city: clean(cf.city, 60),
    region: clean(cf.regionCode, 3).toUpperCase(),
    country,
  };
}

export function geoResponse(req) {
  return new Response(JSON.stringify(geoAnswer(req && req.cf)), {
    headers: {
      'content-type': 'application/json',
      // Per visitor: never from a shared or browser cache.
      'cache-control': 'no-store',
      'access-control-allow-origin': '*',
      'x-robots-tag': 'noindex',
    },
  });
}
