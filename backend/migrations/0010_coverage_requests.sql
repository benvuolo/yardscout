-- Coverage requests — "we don't cover this yet, ask us to add it" (Parts tab).
-- One row per submission, append-only: the same person asking twice is signal,
-- not noise (the admin view aggregates by request_key). Email is optional and
-- only ever used for a manual "it's in now" ping — no automated promises.
CREATE TABLE coverage_requests (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  request_key TEXT NOT NULL,     -- normalized kind|year|make|model|part for aggregation
  kind        TEXT NOT NULL,     -- car (no interchange for the car) | engine (family not listed) | part (not in catalog)
  year        INTEGER,
  make        TEXT,
  model       TEXT,
  part        TEXT,
  zip         TEXT,              -- 5-digit, if the seeker had one set
  email       TEXT,              -- optional "ping me when it's in" (manual, best-effort)
  note        TEXT,              -- optional free text ("it's the 3.0 V6", etc.)
  created_at  TEXT NOT NULL
);
CREATE INDEX idx_coverage_requests_key ON coverage_requests (request_key);
CREATE INDEX idx_coverage_requests_created ON coverage_requests (created_at);

-- Single-row throttle state for the owner digest email (max one per day,
-- piggybacked on the inventory-commit hook — see src/coverage.js).
CREATE TABLE coverage_digest_state (
  id           INTEGER PRIMARY KEY CHECK (id = 1),
  last_sent_at TEXT NOT NULL
);
