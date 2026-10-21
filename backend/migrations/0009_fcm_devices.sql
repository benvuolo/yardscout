-- Android native push (FCM): devices get a second token column. A device has
-- exactly one platform so exactly one of (apns_token, fcm_token) is ever set;
-- a parallel table would duplicate the watches/tier/dedupe machinery for no
-- isolation win. Token uniqueness mirrors apns_token (UNIQUE, multiple NULLs
-- fine), and register "steals" a token from stale rows the same way.

ALTER TABLE devices ADD COLUMN fcm_token TEXT;
CREATE UNIQUE INDEX idx_devices_fcm_token ON devices (fcm_token);
