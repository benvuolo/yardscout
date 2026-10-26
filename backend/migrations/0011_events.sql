-- Per-source funnel counts (UTM attribution). No per-user rows: one counter
-- per (day, event, source, campaign, medium, platform), so the table stays
-- tiny and holds nothing personal.
CREATE TABLE IF NOT EXISTS events_daily (
  day       TEXT NOT NULL,
  event     TEXT NOT NULL,
  source    TEXT NOT NULL DEFAULT '',
  campaign  TEXT NOT NULL DEFAULT '',
  medium    TEXT NOT NULL DEFAULT '',
  platform  TEXT NOT NULL DEFAULT 'web',
  n         INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (day, event, source, campaign, medium, platform)
);
