-- YardScout backend schema.
-- Applied with: npx wrangler d1 migrations apply yardscout-db [--local|--remote]

-- Accounts. Tier lives here; entitlement changes are audited in
-- entitlement_events. tier_expires_at (ISO 8601) lets Apple-IAP renewals slot
-- in later: an expired paid tier resolves to 'free' at request time.
CREATE TABLE users (
  id              TEXT PRIMARY KEY,             -- uuid
  email           TEXT NOT NULL UNIQUE,         -- lowercased
  tier            TEXT NOT NULL DEFAULT 'free', -- free | pro (single paid tier; legacy pro_plus collapses to pro at read)
  tier_source     TEXT,                         -- manual | revenuecat | apple_iap
  tier_expires_at TEXT,                         -- NULL = does not expire
  created_at      TEXT NOT NULL,
  last_login_at   TEXT
);

-- Magic-link tokens: stored hashed (SHA-256 of the high-entropy token),
-- single-use (used_at set atomically on redemption), 15-minute expiry.
CREATE TABLE magic_tokens (
  token_hash TEXT PRIMARY KEY,
  email      TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  used_at    TEXT,
  created_at TEXT NOT NULL,
  request_ip TEXT
);
CREATE INDEX idx_magic_email_created ON magic_tokens (email, created_at);

-- Bearer sessions: token stored hashed, 90-day expiry.
CREATE TABLE sessions (
  token_hash   TEXT PRIMARY KEY,
  user_id      TEXT NOT NULL REFERENCES users (id),
  created_at   TEXT NOT NULL,
  expires_at   TEXT NOT NULL,
  last_seen_at TEXT
);
CREATE INDEX idx_sessions_user ON sessions (user_id);

-- Audit trail for every tier change (manual grants now; Apple IAP /
-- RevenueCat webhook events later). Never deleted.
CREATE TABLE entitlement_events (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     TEXT,
  email       TEXT,
  tier        TEXT NOT NULL,
  source      TEXT NOT NULL,        -- manual | revenuecat
  expires_at  TEXT,
  note        TEXT,
  raw_payload TEXT,                 -- webhook body for debugging (no secrets)
  created_at  TEXT NOT NULL
);

-- Inventory shards, pre-computed per tier by scraper/push_inventory.py so the
-- Worker never transforms the big JSON (free-plan CPU limit is 10ms/request).
--   kind='yard'     key=<yard index>  variant free|pro   → {"vehicles":[rows],"vpic":{id:...}}
--   kind='partsets' key='all'         variant free|pro   → the partSets lookup table
--   kind='vindex'   key=<bucket 0-63> variant 'all'      → {"<id|vin>":[yardIdx,id]}
-- body is gzip-compressed JSON; sha256 is of the UNcompressed JSON and doubles
-- as the HTTP ETag.
CREATE TABLE inv_shards (
  kind       TEXT NOT NULL,
  key        TEXT NOT NULL,
  variant    TEXT NOT NULL,
  sha256     TEXT NOT NULL,
  body       BLOB NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (kind, key, variant)
);

-- Single-row pointer to the current upload: the yard directory (public
-- metadata: yards, coords, counts, scrapedAt) and the shard manifest
-- ("kind/key/variant" → sha256) used by the push script to skip unchanged
-- shards on the next run.
CREATE TABLE inv_meta (
  id         INTEGER PRIMARY KEY CHECK (id = 1),
  directory  TEXT NOT NULL,
  manifest   TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
