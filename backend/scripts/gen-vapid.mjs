/* Generate VAPID keys for Web Push. Run once:
 *   node backend/scripts/gen-vapid.mjs
 * Then:
 *   - VAPID_PUBLIC_KEY  → [vars] in wrangler.toml (it's public, commit it)
 *   - VAPID_PRIVATE_JWK → npx wrangler secret put VAPID_PRIVATE_JWK
 *   - VAPID_SUBJECT     → [vars], e.g. mailto:you@example.com
 */
const pair = await crypto.subtle.generateKey(
  { name: 'ECDSA', namedCurve: 'P-256' }, true, ['sign', 'verify']
);
const rawPub = new Uint8Array(await crypto.subtle.exportKey('raw', pair.publicKey));
const jwk = await crypto.subtle.exportKey('jwk', pair.privateKey);
const b64u = (b) => Buffer.from(b).toString('base64url');

console.log('VAPID_PUBLIC_KEY (wrangler.toml [vars]):\n' + b64u(rawPub));
console.log('\nVAPID_PRIVATE_JWK (wrangler secret put VAPID_PRIVATE_JWK):\n' + JSON.stringify(jwk));
