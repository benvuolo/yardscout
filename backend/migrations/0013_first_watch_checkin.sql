-- One-time "first watch" check-in for free native devices: ~48 h after a
-- device first syncs a watch, one push listing what has landed for it since
-- (only if something did). checkin_at = sent, or given up after 7 quiet days.
ALTER TABLE devices ADD COLUMN first_watch_at TEXT;
ALTER TABLE devices ADD COLUMN checkin_at TEXT;
-- Devices that already had watches before this shipped aren't new users:
-- mark them done so nobody gets a surprise "check-in" weeks into using it.
UPDATE devices SET checkin_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
  WHERE watches_json IS NOT NULL AND watches_json != '[]';
