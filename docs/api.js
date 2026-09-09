/* YardScout API layer — scaffold for the monetization backend.
 *
 * OFF BY DEFAULT: the app keeps loading the static data/inventory_live.json
 * exactly as before. API mode activates only when BOTH are true:
 *   1. A base URL is configured — either the YS_API_BASE constant below
 *      (set at cutover) or localStorage 'jh_api_base' (?apibase=<url> for dev).
 *   2. The feature flag is on — ?api=1 (persisted; ?api=0 turns it off).
 *
 * What API mode changes:
 *   - Inventory loads via radius query (server-side filtering, small tier-aware
 *     per-yard shards with ETags) instead of the one big public file.
 *   - Magic-link sign-in UI appears in the Pro sheet; the session tier drives
 *     the Pro gates server-side (free sessions never even receive value data).
 *
 * Session model: the API lives on a different origin (workers.dev) than the
 * PWA (github.io), so httpOnly cookies would be third-party (Safari blocks).
 * Sessions are bearer tokens: delivered once via the magic-link redirect's URL
 * fragment (#session=..., never sent to any server), stored in localStorage,
 * sent as an Authorization header. Tokens are 256-bit random and revocable
 * server-side (stored hashed, 90-day expiry).
 */

window.YSApi = (() => {
  // ── Cutover switch: set to the deployed Worker URL to make API mode
  //    available to users (still requires the ?api=1 flag until full cutover).
  //    e.g. 'https://yardscout-api.YOUR-SUBDOMAIN.workers.dev'
  const YS_API_BASE = '';

  // Generous fetch radius so every client-side radius filter (UI max 250mi)
  // works within already-loaded data without a refetch.
  const FETCH_RADIUS_MI = 250;
  const SHARD_CONCURRENCY = 8;

  /* Feature flag + base override via query params (persisted, like ?pro=1). */
  (() => {
    try {
      const qp = new URLSearchParams(location.search);
      if (qp.get('api') === '1') localStorage.setItem('jh_use_api', '1');
      if (qp.get('api') === '0') localStorage.removeItem('jh_use_api');
      const b = qp.get('apibase');
      if (b) localStorage.setItem('jh_api_base', b.replace(/\/+$/, ''));
      if (b === '') localStorage.removeItem('jh_api_base');
    } catch (e) { /* ignore */ }
  })();

  const base = () => (localStorage.getItem('jh_api_base') || YS_API_BASE).replace(/\/+$/, '');
  const enabled = () => !!base() && localStorage.getItem('jh_use_api') === '1';

  /* ===== session ===== */
  const TOKEN_KEY = 'jh_session';
  const getToken = () => localStorage.getItem(TOKEN_KEY) || '';

  async function api(path, opts = {}) {
    const headers = Object.assign({}, opts.headers || {});
    const t = getToken();
    if (t) headers['authorization'] = 'Bearer ' + t;
    return fetch(base() + path, Object.assign({}, opts, { headers }));
  }

  /* Consume the magic-link redirect fragment before the app touches the hash
   * (#car= deep links are unaffected — different prefix). */
  let loginNotice = null;
  (() => {
    try {
      if (location.hash.startsWith('#session=')) {
        localStorage.setItem(TOKEN_KEY, decodeURIComponent(location.hash.slice(9)));
        loginNotice = 'signed_in';
        history.replaceState(null, '', location.pathname + location.search);
      } else if (location.hash.startsWith('#login_error=')) {
        loginNotice = 'error:' + decodeURIComponent(location.hash.slice(13));
        history.replaceState(null, '', location.pathname + location.search);
      }
    } catch (e) { /* ignore */ }
  })();

  async function me() {
    if (!getToken()) return null;
    try {
      const r = await api('/v1/me');
      if (r.status === 401) { localStorage.removeItem(TOKEN_KEY); return null; }
      if (!r.ok) return null;
      return await r.json();
    } catch (e) { return null; }
  }

  async function requestLink(email) {
    const r = await api('/v1/auth/request-link', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(data.message || 'Could not send the link.');
    return data;
  }

  async function logout() {
    try { await api('/v1/auth/logout', { method: 'POST' }); } catch (e) { /* best effort */ }
    localStorage.removeItem(TOKEN_KEY);
  }

  /* ===== inventory ===== */

  function savedCenter() {
    try {
      const gps = localStorage.getItem('jh_gps');
      if (gps) return JSON.parse(gps);
      const zip = localStorage.getItem('jh_zip');
      if (zip) {
        const cache = JSON.parse(localStorage.getItem('jh_zip_coords') || '{}');
        if (cache[zip]) return cache[zip];
      }
    } catch (e) { /* ignore */ }
    return null;
  }

  async function fetchJson(path) {
    const r = await api(path);
    if (!r.ok) throw new Error('API ' + r.status + ' for ' + path);
    return r.json();
  }

  /** Load inventory through the API and reassemble a schema-v2 payload that
   * app.js's parseInventoryPayload() accepts unchanged. Free sessions get the
   * free variant (no dollar values) — enforced server-side. */
  async function fetchInventory() {
    const center = savedCenter();
    const qs = center
      ? `?lat=${encodeURIComponent(center.lat)}&lng=${encodeURIComponent(center.lng)}&radius=${FETCH_RADIUS_MI}`
      : '';
    const plan = await fetchJson('/v1/inventory' + qs);

    const jobs = [() => fetchJson(plan.partSetsPath)].concat(
      plan.yardIds.map((id) => () => fetchJson(plan.shardPathTemplate.replace('{yardId}', id)))
    );
    // Small concurrency pool — a national no-center load is ~150 shard fetches.
    const results = new Array(jobs.length);
    let next = 0;
    async function worker() {
      while (next < jobs.length) {
        const i = next++;
        results[i] = await jobs[i]();
      }
    }
    await Promise.all(Array.from({ length: Math.min(SHARD_CONCURRENCY, jobs.length) }, worker));

    const partSets = results[0];
    const vehicles = [];
    const vpic = {};
    for (let s = 1; s < results.length; s++) {
      const shard = results[s];
      for (const row of shard.vehicles) {
        const vp = shard.vpic && shard.vpic[String(row[0])];
        if (vp) vpic[String(vehicles.length)] = vp; // re-key to global index
        vehicles.push(row);
      }
    }
    return {
      schemaVersion: 2,
      scrapedAt: plan.scrapedAt,
      pricesLastReviewed: plan.pricesLastReviewed,
      fields: plan.fields,
      yardFields: plan.yardFields,
      yards: plan.yards,
      partSets,
      vpic,
      vehicles,
      __viaApi: true,
      __tier: plan.tier,
    };
  }

  /* ===== login UI (hidden unless API mode is on) ===== */

  let onAuthChange = null;
  let currentMe = null;

  function $(id) { return document.getElementById(id); }

  function renderAccountUi() {
    const wrap = $('account-wrap');
    if (!wrap) return;
    wrap.style.display = enabled() ? '' : 'none';
    if (!enabled()) return;
    const signedOut = wrap.querySelector('.account-signedout');
    const signedIn = wrap.querySelector('.account-signedin');
    if (currentMe) {
      signedOut.style.display = 'none';
      signedIn.style.display = '';
      $('account-user').textContent = currentMe.email;
      $('account-tier').textContent =
        currentMe.tier === 'pro_plus' ? 'Pro+' : currentMe.tier === 'pro' ? 'Pro' : 'Free plan';
    } else {
      signedOut.style.display = '';
      signedIn.style.display = 'none';
    }
  }

  function setStatus(msg, isError) {
    const el = $('account-status');
    if (!el) return;
    el.textContent = msg || '';
    el.style.color = isError ? 'var(--red)' : '';
  }

  async function handleSendLink() {
    const input = $('account-email');
    const email = (input.value || '').trim();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setStatus('Enter a valid email address.', true);
      return;
    }
    const btn = $('account-send-link');
    btn.disabled = true;
    setStatus('Sending…');
    try {
      const resp = await requestLink(email);
      setStatus('Check your email — the sign-in link works once and expires in 15 minutes.');
      // Local dev (wrangler dev + DEV_MODE): the link comes back directly.
      if (resp.dev_link) {
        setStatus('Dev mode: opening the magic link…');
        location.href = resp.dev_link;
      }
    } catch (e) {
      setStatus(e.message || 'Could not send the link. Try again.', true);
    } finally {
      btn.disabled = false;
    }
  }

  async function refreshAuth() {
    currentMe = await me();
    renderAccountUi();
    if (onAuthChange) onAuthChange(currentMe);
  }

  /** Called by app.js once its functions exist. Binds the login UI and
   * resolves the session (magic-link return included). */
  function init(hooks) {
    onAuthChange = hooks && hooks.onAuthChange || null;
    const send = $('account-send-link');
    if (send) send.addEventListener('click', handleSendLink);
    const emailEl = $('account-email');
    if (emailEl) emailEl.addEventListener('keydown', (e) => { if (e.key === 'Enter') handleSendLink(); });
    const out = $('account-logout');
    if (out) out.addEventListener('click', async () => { await logout(); await refreshAuth(); });
    renderAccountUi();
    if (enabled()) {
      if (loginNotice === 'signed_in') setStatus('Signed in.');
      else if (loginNotice && loginNotice.startsWith('error:')) {
        setStatus('Sign-in link problem: ' + loginNotice.slice(6).replace(/_/g, ' ') + '. Request a new one.', true);
      }
      refreshAuth();
    }
  }

  return { enabled, base, init, me, requestLink, logout, fetchInventory, getToken };
})();
