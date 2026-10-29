-- Send accounting for ops monitoring (src/ops.js, src/ops_monitor.js).
-- 2026-10-29: free digests and magic links silently went nowhere for weeks
-- (sandbox Resend sender) and nothing noticed. Every send site now counts
-- its outcome here so the hourly check and the daily email can see it.
--
-- ops_counters: one row per (UTC day, metric). Metrics are
--   "<channel>:<ok|fail|gone>"       daily total
--   "<channel>:<ok|fail|gone>@HH"    that day's UTC hour HH (rolling 24 h math)
-- channels: apns, fcm, webpush, email:auth, email:digest, email:pro-alert,
--           email:saved, email:coverage, email:ops
CREATE TABLE ops_counters (
  day    TEXT NOT NULL,          -- UTC YYYY-MM-DD
  metric TEXT NOT NULL,
  n      INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (day, metric)
);

-- Recent send failures (pruned to the newest ~500 rows). detail is scrubbed:
-- truncated, no tokens, recipient reduced to its domain.
CREATE TABLE ops_errors (
  at      TEXT NOT NULL,         -- ISO timestamp
  channel TEXT NOT NULL,
  status  INTEGER,               -- HTTP status; 0 = network error / exception
  detail  TEXT
);
CREATE INDEX ops_errors_at ON ops_errors (at);
