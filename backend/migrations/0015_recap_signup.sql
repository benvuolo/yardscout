-- Free Monday email for web visitors (2026-11-12, owner approved; src/recap_signup.js).
-- A web watch lives only in that browser's local storage. A visitor who
-- leaves an email gets a COPY of that watch's criteria stored here (rule 6:
-- the browser's watch is never read back, rewritten or migrated). Nothing is
-- sent until the address is confirmed (double opt-in). Unsubscribing deletes
-- the address, every copied watch and the dedupe rows for it.
--
-- recap_subscribers: one row per address.
--   confirmed_at   NULL until the first confirmation click
--   confirm_hash   SHA-256 of the outstanding confirmation token (NULL = none)
--   confirm_sends / confirm_window_at: persistent per-address cap on
--                  confirmation emails (survives isolate restarts)
-- No IP address, user agent or device identifier is stored.
CREATE TABLE recap_subscribers (
  email              TEXT PRIMARY KEY,          -- lowercased
  created_at         TEXT NOT NULL,
  confirmed_at       TEXT,
  confirm_hash       TEXT,
  confirm_expires_at TEXT,
  confirm_sent_at    TEXT,
  confirm_sends      INTEGER NOT NULL DEFAULT 0,
  confirm_window_at  TEXT,
  last_email_at      TEXT
);
CREATE INDEX idx_recap_sub_confirm ON recap_subscribers (confirm_hash);

-- Copied watch criteria: make, model, years, the zip centre rounded to
-- ~1 km and the radius. confirmed_at NULL = waiting for a confirmation click.
CREATE TABLE recap_watches (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  email        TEXT NOT NULL,
  make         TEXT NOT NULL,
  model        TEXT,
  year_min     INTEGER,
  year_max     INTEGER,
  lat          REAL NOT NULL,
  lng          REAL NOT NULL,
  radius_mi    INTEGER NOT NULL,
  created_at   TEXT NOT NULL,
  confirmed_at TEXT
);
CREATE INDEX idx_recap_watches_email ON recap_watches (email);

-- Per-(address, car) dedupe for recap emails, pruned at 90 days.
CREATE TABLE recap_sent (
  email      TEXT NOT NULL,
  vehicle_id TEXT NOT NULL,
  sent_at    TEXT NOT NULL,
  PRIMARY KEY (email, vehicle_id)
);
CREATE INDEX idx_recap_sent_at ON recap_sent (sent_at);

-- Magic-link ACCOUNT holders who used the recap's unsubscribe link: the
-- account's own recap stops; the account and its watches are untouched.
CREATE TABLE recap_optout (
  email TEXT PRIMARY KEY,
  at    TEXT NOT NULL
);
