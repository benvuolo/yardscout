-- Monday email sign-ups by link (2026-11-13, growth; src/recap_signup.js).
-- The weekly scorecard's per-link line could only show addresses GIVEN per
-- tagged link: the confirmation click is counted on the server, which did
-- not know which link the person came from. The sign-up request now carries
-- the visitor's remembered link source (the same source / campaign / medium
-- the app already attaches to its anonymous funnel counters), and it is kept
-- here only while the sign-up is PENDING:
--   - set when a confirmation email is sent to an address not yet confirmed
--     ('' when the visitor came through no tagged link);
--   - read once at the confirmation click, which counts 'email-confirmed'
--     under it in events_daily (the anonymous daily counter), and set back
--     to NULL in the same step;
--   - also NULLed when the confirmation link expires (hourly prune), and gone
--     with the row when an unconfirmed address is deleted after 7 days or on
--     unsubscribe.
-- Nothing else is added: no IP, user agent or device identifier.
ALTER TABLE recap_subscribers ADD COLUMN pending_source TEXT;
ALTER TABLE recap_subscribers ADD COLUMN pending_campaign TEXT;
ALTER TABLE recap_subscribers ADD COLUMN pending_medium TEXT;
