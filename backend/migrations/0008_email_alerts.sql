-- Email alerts for web Pro members (account-less entitlements).
--
-- The web app has no accounts: a Pro member's email IS their identity
-- (ENTITLEMENTS KV on the site Worker, ent:<email> / tok:<token>). This
-- mirrors the native `devices` model — one row per subscriber, watches as
-- JSON, a dedupe log — but keyed by entitlement email instead of device id.
-- Pro status is NOT cached here: dispatch re-checks the KV entitlement at
-- send time, so a lapsed subscription stops emailing immediately.

CREATE TABLE email_watchers (
  email         TEXT PRIMARY KEY,            -- entitlement email (normalized lowercase)
  watches_json  TEXT,                        -- [{make,model,year_min,year_max,lat,lng,radius_mi}]
  enabled       INTEGER NOT NULL DEFAULT 1,  -- 0 = unsubscribed (email channel only; Pro unaffected)
  created_at    TEXT NOT NULL,
  updated_at    TEXT NOT NULL,
  last_email_at TEXT
);

-- Dedupe: (email, vehicle) pairs already emailed. Mirrors alerts_sent /
-- device_alerts_sent; pruned by age alongside them.
CREATE TABLE email_alerts_sent (
  email      TEXT NOT NULL,
  vehicle_id TEXT NOT NULL,
  sent_at    TEXT NOT NULL,
  PRIMARY KEY (email, vehicle_id)
);
CREATE INDEX idx_email_alerts_sent_at ON email_alerts_sent (sent_at);
