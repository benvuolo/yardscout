-- Sale-day events (chain sale calendars), replaced wholesale on every
-- inventory commit. Rows are already expanded per-yard (chain-wide events
-- arrive as one row per yard of that chain, with the yard's coords), so the
-- Worker only ever does distance math — never chain-name matching.

CREATE TABLE sale_events (
  event_key  TEXT PRIMARY KEY,   -- yard|start_date
  chain      TEXT,
  yard       TEXT NOT NULL,
  title      TEXT,
  start_date TEXT NOT NULL,      -- YYYY-MM-DD
  end_date   TEXT NOT NULL,
  pct        INTEGER,
  lat        REAL,
  lng        REAL,
  stored_at  TEXT NOT NULL
);

-- Dedupe log: (user, sale event) pairs already alerted — a sale stays in the
-- feed for days of commits and must only ever push once per user.
CREATE TABLE sale_alerts_sent (
  user_id   TEXT NOT NULL,
  event_key TEXT NOT NULL,
  sent_at   TEXT NOT NULL,
  PRIMARY KEY (user_id, event_key)
);
CREATE INDEX idx_sale_alerts_sent_at ON sale_alerts_sent (sent_at);
