/* Pick ONE value out of a large JSON text without JSON.parse-ing all of it.
 *
 * Why (2026-11-18): GET /v1/vehicles/:id parsed a whole id-index bucket
 * (~10,000 entries) and then a whole yard shard (up to ~2,500 cars) to answer
 * for one car: about 15 ms of CPU on a plan that allows 10 ms. While a
 * crawler walked the website's /car/ pages (up to 2,600 an hour on 11-17)
 * Cloudflare stopped 656 of those requests between 12:00 and 15:00 UTC.
 *
 * The texts are the scan's own compact JSON (scraper/push_inventory.py
 * canonical(): separators "," and ":"). Two facts make a substring search
 * safe there:
 *   - `"key":` can only be an object key: inside a JSON string every quote is
 *     escaped (\"), and a string VALUE is always followed by "," "]" or "}".
 *   - a value is cut out by walking only that value (strings skipped with
 *     their escapes, brackets counted), then parsed on its own.
 * Callers still verify what they got and fall back to a full parse whenever a
 * pick comes back empty, so a wrong guess here can cost CPU, never a car. */

const WS = new Set([0x20, 0x09, 0x0a, 0x0d]);

/** Index just past the JSON value that starts at text[i] (after optional
 * whitespace), or -1 when it does not end inside the text. */
export function jsonValueEnd(text, i) {
  const n = text.length;
  while (i < n && WS.has(text.charCodeAt(i))) i++;
  if (i >= n) return -1;
  const c = text.charCodeAt(i);
  if (c === 0x22) {                       // "string"
    for (let j = i + 1; j < n; j++) {
      const d = text.charCodeAt(j);
      if (d === 0x5c) { j++; continue; }  // \x
      if (d === 0x22) return j + 1;
    }
    return -1;
  }
  if (c === 0x5b || c === 0x7b) {         // [array] or {object}
    let depth = 0;
    for (let j = i; j < n; j++) {
      const d = text.charCodeAt(j);
      if (d === 0x22) {                   // skip a string inside
        for (j++; j < n; j++) {
          const e = text.charCodeAt(j);
          if (e === 0x5c) { j++; continue; }
          if (e === 0x22) break;
        }
        continue;
      }
      if (d === 0x5b || d === 0x7b) depth++;
      else if (d === 0x5d || d === 0x7d) { if (--depth === 0) return j + 1; }
    }
    return -1;
  }
  let j = i;                              // number, true, false, null
  while (j < n) {
    const d = text.charCodeAt(j);
    if (d === 0x2c || d === 0x5d || d === 0x7d || WS.has(d)) break;
    j++;
  }
  return j > i ? j : -1;
}

/** The value of the first `"key":` at or after `from`, parsed; undefined when
 * the key is not there or its value cannot be read. */
export function pickKey(text, key, from = 0) {
  const needle = JSON.stringify(String(key)) + ':';
  const at = text.indexOf(needle, from);
  if (at < 0) return undefined;
  const start = at + needle.length;
  const end = jsonValueEnd(text, start);
  if (end < 0) return undefined;
  try { return JSON.parse(text.slice(start, end)); } catch { return undefined; }
}

/** In a yard shard text {"vehicles":[[id,...],...],"vpic":{...}}: the vehicle
 * row whose first field is `id` (number or string, as the index stored it),
 * checked to have `width` fields; null when not found this way. */
export function pickRow(text, id, width) {
  const vAt = text.indexOf('"vehicles":[');
  if (vAt < 0) return null;
  const vpicAt = text.indexOf('"vpic":', vAt);
  const stop = vpicAt < 0 ? text.length : vpicAt;
  const needle = '[' + JSON.stringify(id) + ',';
  let at = text.indexOf(needle, vAt);
  while (at >= 0 && at < stop) {
    const prev = text.charCodeAt(at - 1);             // a row starts after "[" or ","
    if (prev === 0x5b || prev === 0x2c) {
      const end = jsonValueEnd(text, at);
      if (end > 0) {
        try {
          const row = JSON.parse(text.slice(at, end));
          if (Array.isArray(row) && String(row[0]) === String(id) && (!width || row.length === width)) return row;
        } catch { /* not a row: keep looking */ }
      }
    }
    at = text.indexOf(needle, at + 1);
  }
  return null;
}

/** shard.vpic[String(id)] from a yard shard text, or null. */
export function pickVpic(text, id) {
  const vpicAt = text.indexOf('"vpic":{');
  if (vpicAt < 0) return null;
  const v = pickKey(text, String(id), vpicAt + 7);
  return v === undefined ? null : v;
}
