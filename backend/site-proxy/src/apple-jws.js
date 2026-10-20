/* Offline verification of StoreKit 2 signed transactions (JWS with x5c chain).
 *
 * Apple signs every StoreKit 2 transaction as a JWS whose header carries the
 * full certificate chain (leaf → intermediate → Apple Root CA G3). That lets
 * a server verify a transaction WITHOUT App Store Server API keys:
 *   1. pin the chain's root against the embedded Apple Root CA G3 DER,
 *   2. verify each certificate's signature against its issuer's public key,
 *   3. check validity windows + Apple's in-app-purchase marker OID on the leaf,
 *   4. verify the ES256 JWS signature with the leaf public key,
 *   5. hand the decoded payload (bundleId, productId, expiresDate, …) back to
 *      the caller for business checks.
 *
 * No dependencies — the ~100 lines of DER walking below parse just enough
 * X.509 (tbsCertificate, SPKI, validity, signature) for WebCrypto to do the
 * actual cryptography.
 */

/* Apple Root CA - G3 (ECC P-384, expires 2039) — apple.com/certificateauthority */
export const APPLE_ROOT_CA_G3_B64 =
  'MIICQzCCAcmgAwIBAgIILcX8iNLFS5UwCgYIKoZIzj0EAwMwZzEbMBkGA1UEAwwSQXBwbGUgUm9vdCBDQSAtIEczMSYwJAYDVQQLDB1BcHBsZSBDZXJ0aWZpY2F0aW9uIEF1dGhvcml0eTETMBEGA1UECgwKQXBwbGUgSW5jLjELMAkGA1UEBhMCVVMwHhcNMTQwNDMwMTgxOTA2WhcNMzkwNDMwMTgxOTA2WjBnMRswGQYDVQQDDBJBcHBsZSBSb290IENBIC0gRzMxJjAkBgNVBAsMHUFwcGxlIENlcnRpZmljYXRpb24gQXV0aG9yaXR5MRMwEQYDVQQKDApBcHBsZSBJbmMuMQswCQYDVQQGEwJVUzB2MBAGByqGSM49AgEGBSuBBAAiA2IABJjpLz1AcqTtkyJygRMc3RCV8cWjTnHcFBbZDuWmBSp3ZHtfTjjTuxxEtX/1H7YyYl3J6YRbTzBPEVoA/VhYDKX1DyxNB0cTddqXl5dvMVztK517IDvYuVTZXpmkOlEKMaNCMEAwHQYDVR0OBBYEFLuw3qFYM4iapIqZ3r6966/ayySrMA8GA1UdEwEB/wQFMAMBAf8wDgYDVR0PAQH/BAQDAgEGMAoGCCqGSM49BAMDA2gAMGUCMQCD6cHEFl4aXTQY2e3v9GwOAEZLuN+yRhHFD/3meoyhpmvOwgPUnPWTxnS4at+qIxUCMG1mihDK1A3UT82NQz60imOlM27jbdoXt2QfyFMm+YhidDkLF1vLUagM6BgD56KyKA==';

/* Apple's "in-app purchase signing" marker extension on StoreKit leaf certs:
 * OID 1.2.840.113635.100.6.11.1, as raw DER bytes to scan for in the TBS. */
const IAP_MARKER_OID_DER = [0x06, 0x0a, 0x2a, 0x86, 0x48, 0x86, 0xf7, 0x63, 0x64, 0x06, 0x0b, 0x01];

/* ---------- small byte helpers ---------- */

function b64ToBytes(b64) {
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}
function b64urlToBytes(s) {
  const b64 = s.replace(/-/g, '+').replace(/_/g, '/');
  return b64ToBytes(b64 + '='.repeat((4 - (b64.length % 4)) % 4));
}
function b64urlToStr(s) {
  return new TextDecoder().decode(b64urlToBytes(s));
}
function bytesEqual(a, b) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a[i] ^ b[i];
  return diff === 0;
}

/* ---------- minimal DER (TLV) walking ---------- */

function tlv(b, i) {
  if (i >= b.length) throw new Error('DER: truncated');
  const tag = b[i];
  let len = b[i + 1];
  let lenBytes = 1;
  if (len & 0x80) {
    const n = len & 0x7f;
    if (n === 0 || n > 4) throw new Error('DER: bad length');
    len = 0;
    for (let j = 0; j < n; j++) len = len * 256 + b[i + 2 + j];
    lenBytes = 1 + n;
  }
  const contentStart = i + 1 + lenBytes;
  const end = contentStart + len;
  if (end > b.length) throw new Error('DER: overrun');
  return { tag, start: i, contentStart, end };
}

function children(b, node) {
  const out = [];
  let i = node.contentStart;
  while (i < node.end) {
    const c = tlv(b, i);
    out.push(c);
    i = c.end;
  }
  return out;
}

/* Parse the handful of X.509 fields we need from a DER certificate. */
function parseCert(der) {
  const cert = tlv(der, 0); // Certificate ::= SEQUENCE
  const [tbsNode, sigAlgNode, sigValNode] = children(der, cert);
  const tbs = der.slice(tbsNode.start, tbsNode.end); // full TLV — the signed bytes

  const kids = children(der, tbsNode);
  let i = 0;
  if (kids[0] && kids[0].tag === 0xa0) i = 1; // explicit [0] version
  // kids[i]=serialNumber, i+1=signature alg, i+2=issuer, i+3=validity,
  // i+4=subject, i+5=subjectPublicKeyInfo
  const validityKids = children(der, kids[i + 3]);
  const spki = der.slice(kids[i + 5].start, kids[i + 5].end);

  // signatureAlgorithm → hash ('SHA-256' | 'SHA-384')
  const algOidNode = children(der, sigAlgNode)[0];
  const algOid = Array.from(der.slice(algOidNode.contentStart, algOidNode.end)).join(',');
  let hash = null;
  if (algOid === '42,134,72,206,61,4,3,2') hash = 'SHA-256'; // ecdsa-with-SHA256
  if (algOid === '42,134,72,206,61,4,3,3') hash = 'SHA-384'; // ecdsa-with-SHA384
  if (!hash) throw new Error('cert: unsupported signature algorithm');

  // signatureValue: BIT STRING → skip the leading unused-bits byte
  const sigDer = der.slice(sigValNode.contentStart + 1, sigValNode.end);

  return {
    tbs,
    spki,
    hash,
    sigDer,
    notBefore: parseTime(der, validityKids[0]),
    notAfter: parseTime(der, validityKids[1]),
    raw: der,
  };
}

function parseTime(der, node) {
  const s = new TextDecoder().decode(der.slice(node.contentStart, node.end));
  let iso;
  if (node.tag === 0x17) {
    // UTCTime YYMMDDHHMMSSZ — RFC 5280: YY < 50 → 20YY
    const yy = parseInt(s.slice(0, 2), 10);
    iso = `${yy < 50 ? 2000 + yy : 1900 + yy}-${s.slice(2, 4)}-${s.slice(4, 6)}T${s.slice(6, 8)}:${s.slice(8, 10)}:${s.slice(10, 12)}Z`;
  } else {
    // GeneralizedTime YYYYMMDDHHMMSSZ
    iso = `${s.slice(0, 4)}-${s.slice(4, 6)}-${s.slice(6, 8)}T${s.slice(8, 10)}:${s.slice(10, 12)}:${s.slice(12, 14)}Z`;
  }
  return new Date(iso);
}

/* Which curve is an SPKI on? Scan for the named-curve OID. */
function spkiCurve(spki) {
  const P256 = [0x06, 0x08, 0x2a, 0x86, 0x48, 0xce, 0x3d, 0x03, 0x01, 0x07];
  const P384 = [0x06, 0x05, 0x2b, 0x81, 0x04, 0x00, 0x22];
  if (findBytes(spki, P256) >= 0) return { namedCurve: 'P-256', size: 32 };
  if (findBytes(spki, P384) >= 0) return { namedCurve: 'P-384', size: 48 };
  throw new Error('cert: unsupported key curve');
}

function findBytes(haystack, needle) {
  outer: for (let i = 0; i <= haystack.length - needle.length; i++) {
    for (let j = 0; j < needle.length; j++) {
      if (haystack[i + j] !== needle[j]) continue outer;
    }
    return i;
  }
  return -1;
}

/* DER ECDSA-Sig-Value {r, s INTEGER} → raw fixed-width r||s for WebCrypto. */
function derSigToRaw(sigDer, size) {
  const seq = tlv(sigDer, 0);
  const [rNode, sNode] = children(sigDer, seq);
  const take = (n) => {
    let v = sigDer.slice(n.contentStart, n.end);
    while (v.length > size && v[0] === 0) v = v.slice(1); // strip sign padding
    if (v.length > size) throw new Error('cert: bad signature integer');
    const out = new Uint8Array(size);
    out.set(v, size - v.length);
    return out;
  };
  const raw = new Uint8Array(size * 2);
  raw.set(take(rNode), 0);
  raw.set(take(sNode), size);
  return raw;
}

async function importSpki(spki) {
  const { namedCurve, size } = spkiCurve(spki);
  const key = await crypto.subtle.importKey(
    'spki', spki, { name: 'ECDSA', namedCurve }, false, ['verify']
  );
  return { key, size };
}

/* Verify `cert`'s signature using the issuer's SPKI. */
async function verifyCertSignedBy(cert, issuerSpki) {
  const { key, size } = await importSpki(issuerSpki);
  const raw = derSigToRaw(cert.sigDer, size);
  return crypto.subtle.verify({ name: 'ECDSA', hash: cert.hash }, key, raw, cert.tbs);
}

/* ---------- public API ---------- */

/**
 * Verify a StoreKit 2 signed transaction (JWS) completely offline.
 *
 * @param {string} jws - the signed transaction (header.payload.signature)
 * @param {object} [opts]
 * @param {string} [opts.rootCaB64] - override the pinned root (DEV TESTS ONLY)
 * @returns {Promise<object>} the decoded transaction payload
 * @throws on any verification failure
 */
export async function verifyStoreKitJws(jws, opts = {}) {
  const parts = String(jws || '').split('.');
  if (parts.length !== 3) throw new Error('jws: malformed');
  const [h, p, s] = parts;

  let header;
  try { header = JSON.parse(b64urlToStr(h)); } catch { throw new Error('jws: bad header'); }
  if (header.alg !== 'ES256') throw new Error('jws: unexpected alg');
  const x5c = header.x5c;
  if (!Array.isArray(x5c) || x5c.length < 2 || x5c.length > 4) throw new Error('jws: bad x5c chain');

  const certs = x5c.map((c) => parseCert(b64ToBytes(c)));

  // 1. Pin the chain's root to Apple Root CA G3 (byte-for-byte).
  const pinnedRoot = b64ToBytes(opts.rootCaB64 || APPLE_ROOT_CA_G3_B64);
  if (!bytesEqual(certs[certs.length - 1].raw, pinnedRoot)) {
    throw new Error('jws: untrusted root certificate');
  }

  // 2. Each cert must be signed by the next one up; each must be in validity.
  const now = new Date();
  for (const cert of certs) {
    if (now < cert.notBefore || now > cert.notAfter) throw new Error('jws: certificate expired');
  }
  for (let i = 0; i < certs.length - 1; i++) {
    const ok = await verifyCertSignedBy(certs[i], certs[i + 1].spki);
    if (!ok) throw new Error('jws: broken certificate chain');
  }

  // 3. The leaf must carry Apple's in-app-purchase marker extension.
  //    (Skippable only when a dev test root override is in play.)
  if (!opts.rootCaB64 && findBytes(certs[0].tbs, IAP_MARKER_OID_DER) < 0) {
    throw new Error('jws: leaf is not an in-app purchase signing certificate');
  }

  // 4. Verify the JWS signature itself (ES256 → P-256 leaf key, raw r||s).
  const { key } = await importSpki(certs[0].spki);
  const sig = b64urlToBytes(s);
  if (sig.length !== 64) throw new Error('jws: bad signature length');
  const signed = new TextEncoder().encode(`${h}.${p}`);
  const ok = await crypto.subtle.verify({ name: 'ECDSA', hash: 'SHA-256' }, key, sig, signed);
  if (!ok) throw new Error('jws: signature verification failed');

  // 5. Decode and return the payload — business checks are the caller's job.
  let payload;
  try { payload = JSON.parse(b64urlToStr(p)); } catch { throw new Error('jws: bad payload'); }
  return payload;
}
