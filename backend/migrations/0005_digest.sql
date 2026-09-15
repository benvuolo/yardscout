-- Rolling window of recent arrivals, refreshed on every inventory commit.
-- The weekly digest cron matches these against free users' watches — instant
-- push (Pro) reads arrivals straight from the commit payload and never needs
-- this table. Pruned to ~10 days on each commit.

CREATE TABLE arrivals (
  vehicle_id TEXT PRIMARY KEY,
  year       INTEGER,
  make       TEXT,
  model      TEXT,
  row        TEXT,
  location   TEXT,
  city       TEXT,
  state      TEXT,
  lat        REAL,
  lng        REAL,
  date_added TEXT,
  seen_at    TEXT NOT NULL
);
CREATE INDEX idx_arrivals_seen ON arrivals (seen_at);
