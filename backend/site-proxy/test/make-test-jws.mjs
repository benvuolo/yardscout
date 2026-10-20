#!/usr/bin/env node
/* Generates a fake StoreKit-2-shaped signed transaction for LOCAL tests of
 * /api/ent/verify-ios: a 3-cert ECDSA chain (root P-384 → intermediate P-384
 * → leaf P-256) and an ES256 JWS with the chain in the x5c header.
 *
 * The Worker only accepts this chain when DEV_MODE=1 and the test root is
 * injected via APPLE_ROOT_CA_B64_TEST (see .dev.vars.example) — production
 * pins the real Apple Root CA G3.
 *
 * Usage: node make-test-jws.mjs <outdir> [payloadOverridesJson] [outname]
 * Writes <outdir>/<outname|jws.txt>, <outdir>/root_b64.txt (+ key/cert PEMs).
 * An existing chain in <outdir> is reused, so multiple JWS variants verify
 * against the same injected test root.
 */
import { execFileSync } from 'node:child_process';
import { createSign, createPrivateKey } from 'node:crypto';
import { mkdirSync, writeFileSync, readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const outdir = process.argv[2] || '.out';
const overrides = process.argv[3] ? JSON.parse(process.argv[3]) : {};
const outname = process.argv[4] || 'jws.txt';
mkdirSync(outdir, { recursive: true });
const f = (name) => join(outdir, name);
const sh = (args) => execFileSync('openssl', args, { stdio: ['ignore', 'pipe', 'pipe'] });

if (!existsSync(f('root.pem'))) {
  // Root (P-384, self-signed) — stands in for Apple Root CA G3.
  sh(['ecparam', '-name', 'secp384r1', '-genkey', '-noout', '-out', f('root.key')]);
  sh(['req', '-new', '-x509', '-key', f('root.key'), '-sha384', '-days', '3',
    '-subj', '/CN=YardScout Test Root', '-out', f('root.pem')]);

  // Intermediate (P-384) signed by root.
  sh(['ecparam', '-name', 'secp384r1', '-genkey', '-noout', '-out', f('inter.key')]);
  sh(['req', '-new', '-key', f('inter.key'), '-subj', '/CN=YardScout Test Intermediate', '-out', f('inter.csr')]);
  writeFileSync(f('inter.ext'), 'basicConstraints=CA:TRUE\n');
  sh(['x509', '-req', '-in', f('inter.csr'), '-CA', f('root.pem'), '-CAkey', f('root.key'),
    '-CAcreateserial', '-sha384', '-days', '2', '-extfile', f('inter.ext'), '-out', f('inter.pem')]);

  // Leaf (P-256) signed by intermediate — ES256 JWS signer.
  sh(['ecparam', '-name', 'prime256v1', '-genkey', '-noout', '-out', f('leaf.key')]);
  sh(['req', '-new', '-key', f('leaf.key'), '-subj', '/CN=YardScout Test Leaf', '-out', f('leaf.csr')]);
  sh(['x509', '-req', '-in', f('leaf.csr'), '-CA', f('inter.pem'), '-CAkey', f('inter.key'),
    '-CAcreateserial', '-sha256', '-days', '1', '-out', f('leaf.pem')]);
}

const derB64 = (pem) =>
  readFileSync(pem, 'utf8').replace(/-----[^-]+-----/g, '').replace(/\s+/g, '');

const b64url = (buf) =>
  Buffer.from(buf).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

const header = { alg: 'ES256', x5c: [derB64(f('leaf.pem')), derB64(f('inter.pem')), derB64(f('root.pem'))] };
const payload = {
  transactionId: '2000000123456789',
  originalTransactionId: '2000000123456789',
  bundleId: 'com.benvuolo.yardscout',
  productId: 'yardscout_pro_monthly',
  type: 'Auto-Renewable Subscription',
  purchaseDate: Date.now() - 3600_000,
  expiresDate: Date.now() + 25 * 24 * 3600_000,
  environment: 'Production',
  ...overrides,
};

const signingInput = `${b64url(JSON.stringify(header))}.${b64url(JSON.stringify(payload))}`;
const signer = createSign('SHA256');
signer.update(signingInput);
const sig = signer.sign({
  key: createPrivateKey(readFileSync(f('leaf.key'))),
  dsaEncoding: 'ieee-p1363', // raw r||s — what JWS ES256 wants
});

writeFileSync(f(outname), `${signingInput}.${b64url(sig)}\n`);
writeFileSync(f('root_b64.txt'), derB64(f('root.pem')) + '\n');
console.log('wrote', f(outname), 'and', f('root_b64.txt'));
