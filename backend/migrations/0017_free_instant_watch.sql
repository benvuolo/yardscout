-- Free instant alert (owner decision 2026-11-16): a FREE app install may flag
-- ONE watch as instant. The register handler stores that one watch here,
-- already sanitized and with its radius clamped to FREE_INSTANT_RADIUS_MI
-- (50), so each inventory commit reads one small column per free device
-- instead of re-parsing every watches_json. NULL = no instant watch (Pro
-- devices, and every build that never sends the flag): exactly today's path.
ALTER TABLE devices ADD COLUMN instant_watch_json TEXT;
CREATE INDEX IF NOT EXISTS idx_devices_instant ON devices (tier) WHERE instant_watch_json IS NOT NULL;
