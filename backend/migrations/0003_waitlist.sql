-- Durable waitlist storage. Signups previously went only to a ntfy.sh topic
-- (~12h message cache) — a missed push meant a lost lead. One row per email;
-- a repeat signup updates the plan/price/trigger so the latest intent wins.
CREATE TABLE waitlist (
  email      TEXT PRIMARY KEY,             -- lowercased
  plan       TEXT,                         -- pro | pass (which card was selected)
  price      TEXT,                         -- price shown at signup time
  trigger    TEXT,                         -- which lock opened the sheet
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
