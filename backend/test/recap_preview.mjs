/* Renders a sample FREE weekly recap (HTML + text) from fixture data through
 * the production builder (src/alerts.js buildDigestEmail), and screenshots
 * it at phone width with Playwright.
 *   node test/recap_preview.mjs [outDir]   (default: ../design/screenshots/recap-teaser)
 * Fixture: Monday 2026-11-09 15:00 UTC cron, a free user watching 4Runners
 * and Civics around Salt Lake City; one car already gone, one found only
 * hours before the email (so it correctly gets no "Pro would have" line). */
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { buildDigestEmail } from '../src/alerts.js';

const here = dirname(fileURLToPath(import.meta.url));
const out = resolve(process.argv[2] || resolve(here, '../../design/screenshots/recap-teaser'));
mkdirSync(out, { recursive: true });

const NOW = Date.parse('2026-11-09T15:00:00Z');
const matches = [
  { id: 71203, year: 2001, make: 'Toyota', model: '4Runner', row: '42', location: 'Utah Pic-A-Part - Ogden',
    dateAdded: '2026-11-03', seenAt: '2026-11-03T18:12:00Z' },
  { id: 71877, year: 1999, make: 'Toyota', model: '4Runner', row: '17', location: 'Pick-n-Pull - Salt Lake City',
    dateAdded: '2026-11-04', seenAt: '2026-11-04T22:05:00Z' },
  { id: 72015, year: 2004, make: 'Honda', model: 'Civic', row: '8', location: 'Pull-N-Save - Salt Lake City',
    dateAdded: '2026-11-06', seenAt: '2026-11-06T16:40:00Z' },
  { id: 72290, year: 2003, make: 'Honda', model: 'Civic', row: '23', location: 'Utah Pic-A-Part - Orem',
    dateAdded: '2026-11-09', seenAt: '2026-11-09T10:30:00Z' },
];
const presence = new Map([['71203', 'present'], ['71877', 'gone'], ['72015', 'present'], ['72290', 'present']]);
const sales = [{ yard: 'Utah Pic-A-Part - Ogden', start_date: '2026-11-14', end_date: '2026-11-15', pct: 50 }];

const em = buildDigestEmail({ APP_URL: 'https://yardscout.io/' }, 'sample@example.com', matches,
  { weekly: true, now: NOW, presence, sales });
writeFileSync(resolve(out, 'sample-free-recap.html'), em.html);
writeFileSync(resolve(out, 'sample-free-recap.txt'), `Subject: ${em.subject}\n\n${em.text}\n`);

const { chromium } = createRequire(import.meta.url)('playwright');
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
await page.setContent(em.html, { waitUntil: 'load' });
await page.screenshot({ path: resolve(out, 'free-recap-phone.png'), fullPage: true });
await browser.close();
console.log(`wrote ${out}/free-recap-phone.png, sample-free-recap.html, sample-free-recap.txt`);
console.log(`Subject: ${em.subject}\n\n${em.text}`);
