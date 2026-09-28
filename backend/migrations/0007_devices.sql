-- Anonymous native devices (iOS app): no account, no email. A device registers
-- its APNs token + mirrors its local watches as JSON; tier is client-claimed
-- (the app is client-gated everywhere else too — StoreKit receipt validation
-- can tighten this later without a schema change).

CREATE TABLE devices (
  id           TEXT PRIMARY KEY,            -- client-generated uuid, stable per install
  apns_token   TEXT UNIQUE,                 -- hex APNs device token (rotates; upsert by id)
  platform     TEXT NOT NULL DEFAULT 'ios',
  tier         TEXT NOT NULL DEFAULT 'free',
  watches_json TEXT,                        -- [{make,model,yearMin,yearMax,lat,lng,radiusMi}]
  created_at   TEXT NOT NULL,
  updated_at   TEXT NOT NULL,
  last_push_at TEXT
);
CREATE INDEX idx_devices_tier ON devices (tier);

-- Dedupe: (device, vehicle) pairs already pushed. Mirrors alerts_sent.
CREATE TABLE device_alerts_sent (
  device_id  TEXT NOT NULL,
  vehicle_id TEXT NOT NULL,
  sent_at    TEXT NOT NULL,
  PRIMARY KEY (device_id, vehicle_id)
);
CREATE INDEX idx_device_alerts_sent_at ON device_alerts_sent (sent_at);

-- Dedupe for sale-day pushes. Mirrors sale_alerts_sent.
CREATE TABLE device_sale_alerts_sent (
  device_id TEXT NOT NULL,
  event_key TEXT NOT NULL,
  sent_at   TEXT NOT NULL,
  PRIMARY KEY (device_id, event_key)
);
CREATE INDEX idx_device_sale_sent_at ON device_sale_alerts_sent (sent_at);
