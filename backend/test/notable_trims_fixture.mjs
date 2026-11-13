/* notableTrims for browser tests that serve docs/ locally.
 * The scan publishes notableTrims (make -> model -> trim gate words) in
 * docs/data/inventory_live.json and docs/data/inv/manifest.json from the
 * first scan after design/notable-trims merges. Until the checked-out data
 * carries it, the test servers add it to those two files as they serve them,
 * computed by the scraper's own notable_trims_from_spans over the file's
 * modelYears, so the tests exercise exactly what the scan will publish.
 *   import { serveWithNotableTrims } from './notable_trims_fixture.mjs';
 *   const body = serveWithNotableTrims(filePath);   // Buffer, or null = serve as is
 */
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const DATA = path.join(ROOT, 'docs', 'data');
let _nt = null;
const _cache = new Map();

/* The map the scan would publish for the checked-out data. */
export function notableTrimsFixture() {
  if (_nt) return _nt;
  const src = fs.existsSync(path.join(DATA, 'inv', 'manifest.json'))
    ? path.join(DATA, 'inv', 'manifest.json') : path.join(DATA, 'inventory_live.json');
  const out = execFileSync('python3', ['-c', [
    'import json, sys',
    `sys.path.insert(0, ${JSON.stringify(path.join(ROOT, 'scraper'))})`,
    'import junkyard_scraper as js',
    `m = json.load(open(${JSON.stringify(src)}))`,
    'print(json.dumps(m.get("notableTrims") or js.notable_trims_from_spans(m.get("modelYears") or {})))',
  ].join('\n')], { cwd: ROOT, maxBuffer: 1 << 26, stdio: ['ignore', 'pipe', 'ignore'] });
  _nt = JSON.parse(out.toString());
  return _nt;
}

/* Body to serve for a docs/ file: the two inventory files with notableTrims
 * added when they lack it; null for every other file (serve it unchanged). */
export function serveWithNotableTrims(file) {
  const f = path.resolve(file);
  if (f !== path.join(DATA, 'inventory_live.json') && f !== path.join(DATA, 'inv', 'manifest.json')) return null;
  if (_cache.has(f)) return _cache.get(f);
  const raw = fs.readFileSync(f);
  // Cheap check first: the 37 MB file is parsed only when it needs the field.
  let body = raw;
  if (!raw.includes('"notableTrims"')) {
    const j = JSON.parse(raw.toString());
    j.notableTrims = notableTrimsFixture();
    body = Buffer.from(JSON.stringify(j));
  }
  _cache.set(f, body);
  return body;
}
