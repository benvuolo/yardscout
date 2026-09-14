-- Per-account alerts: server-side watches, Web Push subscriptions, and a
-- sent-log so a vehicle only ever alerts a user once (scans overlap, so the
-- same arrival can appear in several consecutive commits).

CREATE TABLE watches (
  id         TEXT PRIMARY KEY,              -- uuid
  user_id    TEXT NOT NULL REFERENCES users (id),
  make       TEXT,                          -- NULL = any make
  model      TEXT,                          -- NULL = any model
  year_min   INTEGER,
  year_max   INTEGER,
  lat        REAL,                          -- watch center (NULL = nationwide)
  lng        REAL,
  radius_mi  INTEGER,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_watches_user ON watches (user_id);

-- One row per browser/device push subscription (a user can have several:
-- phone PWA, desktop). endpoint is unique per subscription by spec.
CREATE TABLE push_subscriptions (
  endpoint     TEXT PRIMARY KEY,
  user_id      TEXT NOT NULL REFERENCES users (id),
  p256dh       TEXT NOT NULL,               -- client public key (base64url)
  auth         TEXT NOT NULL,               -- client auth secret (base64url)
  created_at   TEXT NOT NULL,
  last_sent_at TEXT
);
CREATE INDEX idx_push_user ON push_subscriptions (user_id);

-- Dedupe log: (user, vehicle) pairs already alerted. Pruned by age.
CREATE TABLE alerts_sent (
  user_id    TEXT NOT NULL,
  vehicle_id TEXT NOT NULL,
  sent_at    TEXT NOT NULL,
  PRIMARY KEY (user_id, vehicle_id)
);
CREATE INDEX idx_alerts_sent_at ON alerts_sent (sent_at);
