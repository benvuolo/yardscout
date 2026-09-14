/* YardScout service worker — instant launches + works offline in the yard.
   Strategy: network-first with cache fallback for everything same-origin, so the
   app is always fresh when online but still opens (with the last-seen inventory)
   when cell signal dies between the rows of cars. */

const CACHE = 'jh-v37';
const SHELL = [
  './',
  './index.html',
  './styles.css',
  './data.js',
  './app.js',
  './api.js',
  './privacy.html',
  './terms.html',
  './manifest.webmanifest',
  './icon-192.png',
  './icon-512.png',
  './apple-touch-icon.png',
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      // Only clean up old SHELL caches (jh-v*). The app owns 'jh-data-v1'
      // (inventory cache-first storage) — deleting it here would silently
      // undo the app's put on every SW update/first install.
      .then((keys) => Promise.all(keys.filter((k) => k.startsWith('jh-v') && k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== self.location.origin) return;
  // The big inventory file is managed by the app itself (Cache API,
  // cache-first + background revalidate in app.js) — network-first here would
  // make every repeat visit wait on the full 4MB download and store a
  // duplicate copy.
  if (url.pathname.endsWith('/data/inventory_live.json')) return;
  e.respondWith(
    fetch(e.request)
      .then((resp) => {
        if (resp.ok) {
          const clone = resp.clone();
          caches.open(CACHE).then((c) => c.put(e.request, clone));
        }
        return resp;
      })
      .catch(() => caches.match(e.request, { ignoreSearch: true }))
  );
});

/* ===== Web Push (watchlist alerts) =====
 * Payloads are JSON {title, body, url} encrypted end-to-end by the backend
 * (backend/src/push.js) — the push service in the middle can't read them. */
self.addEventListener('push', (e) => {
  let data = {};
  try { data = e.data ? e.data.json() : {}; } catch (err) { data = { body: e.data && e.data.text() }; }
  e.waitUntil(self.registration.showNotification(data.title || 'YardScout', {
    body: data.body || 'A watched car just hit the yard.',
    icon: './icon-192.png',
    badge: './icon-192.png',
    tag: 'yardscout-alert',      // collapse repeats into one banner
    data: { url: data.url || './' },
  }));
});

self.addEventListener('notificationclick', (e) => {
  e.notification.close();
  const target = new URL(e.notification.data && e.notification.data.url || './', self.location.href).href;
  e.waitUntil(clients.matchAll({ type: 'window', includeUncontrolled: true }).then((wins) => {
    for (const w of wins) {
      if (w.url.startsWith(self.registration.scope) && 'focus' in w) return w.focus();
    }
    return clients.openWindow(target);
  }));
});
