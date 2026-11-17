-- Free emailed alert for web visitors (2026-11-17, owner: "do the free emailed
-- alert"; src/free_email_alert.js). The website's counterpart of the apps'
-- free instant push: ONE watch per email address, cars set out within the
-- same 50 mi the free push uses, no account. Pro email alerts
-- (email_watchers) and the Monday email (recap_*) are untouched.
--
-- Rule 6: the visitor's watches stay in their browser, unread and unchanged.
-- The page sends a COPY of the one chosen watch's free criteria (make, model,
-- year range, the zip centre rounded to ~1 km, the radius clamped to 50 mi);
-- that copy lives here and is deleted with the address.
--
-- free_email_alerts: one row per address.
--   confirmed_at   NULL until the address's owner clicked a confirmation link
--                  (double opt-in). No alert email is ever sent before it.
--   watch_json     the ONE watch being emailed (NULL while the first sign-up
--                  waits for its click); watch_set_at = when it was set.
--   pending_json   a sign-up, or a different car, waiting for a confirmation
--                  click. Confirming moves it into watch_json (replaces).
--   confirm_*      as recap_subscribers: SHA-256 of the outstanding token,
--                  its expiry, and a persistent per-address cap on
--                  confirmation emails.
--   pending_*      the visitor's link source, kept only until the click (as
--                  migration 0016 does for the Monday email).
--   last_email_at / first_email_at   last and first alert email accepted.
--   held_at        set when a matched alert was held back for the email
--                  budget; such cars are retried on later scans for 48 h.
-- No IP address, user agent or device identifier is stored.
CREATE TABLE free_email_alerts (
  email              TEXT PRIMARY KEY,          -- lowercased
  created_at         TEXT NOT NULL,
  confirmed_at       TEXT,
  watch_json         TEXT,
  watch_set_at       TEXT,
  pending_json       TEXT,
  confirm_hash       TEXT,
  confirm_expires_at TEXT,
  confirm_sent_at    TEXT,
  confirm_sends      INTEGER NOT NULL DEFAULT 0,
  confirm_window_at  TEXT,
  pending_source     TEXT,
  pending_campaign   TEXT,
  pending_medium     TEXT,
  last_email_at      TEXT,
  first_email_at     TEXT,
  held_at            TEXT
);
CREATE INDEX idx_free_email_alerts_confirm ON free_email_alerts (confirm_hash);

-- Per-(address, car) dedupe, as email_alerts_sent for Pro: seeded with the
-- cars already listed when a watch is set (alerts are for FUTURE arrivals),
-- cleared when the watch is replaced, pruned at 90 days, deleted with the
-- address.
CREATE TABLE free_email_alerts_sent (
  email      TEXT NOT NULL,
  vehicle_id TEXT NOT NULL,
  sent_at    TEXT NOT NULL,
  PRIMARY KEY (email, vehicle_id)
);
CREATE INDEX idx_free_email_alerts_sent_at ON free_email_alerts_sent (sent_at);
