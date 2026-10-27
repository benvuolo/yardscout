-- Pro alerts, round 2:
--   1. Saved-car alerts ("it's gone" / "leaving soon"). Clients mirror their
--      saved cars (the yard-visit list) next to their watches on the same
--      register/sync paths; dispatch resolves each key through the vindex
--      shard after every commit. One alert per (owner, key, kind), ever.
--   2. Trim / drivetrain filters on watches (Pro). Stored per watch; matched
--      against the VIN decode (vpic) on both client and server, so arrivals
--      now carry the decode too (vpic_json) for the seed/digest paths.

ALTER TABLE devices ADD COLUMN saved_json TEXT;         -- [{key,year,make,model,location}] (cap 50)
ALTER TABLE email_watchers ADD COLUMN saved_json TEXT;  -- same shape, web Pro members

ALTER TABLE watches ADD COLUMN drive_filter TEXT;       -- '4x4' | '2wd' | NULL (any)
ALTER TABLE watches ADD COLUMN trim_filter TEXT;        -- case-insensitive substring of trim/series

ALTER TABLE arrivals ADD COLUMN vpic_json TEXT;         -- [trim, trimQuality, series, driveType]

-- Dedupe log for saved-car alerts. owner_kind: 'device' | 'email'.
-- kind: 'gone' (off the yard's list) | 'leaving' (>= 80% of the yard's
-- typical stay). A 'gone' row ends the key's story — never re-evaluated.
CREATE TABLE saved_alerts_sent (
  owner_kind  TEXT NOT NULL,
  owner_id    TEXT NOT NULL,
  vehicle_key TEXT NOT NULL,
  kind        TEXT NOT NULL,
  sent_at     TEXT NOT NULL,
  PRIMARY KEY (owner_kind, owner_id, vehicle_key, kind)
);
CREATE INDEX idx_saved_alerts_sent_at ON saved_alerts_sent (sent_at);
