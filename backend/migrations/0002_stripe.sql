-- Stripe billing: remember each account's Stripe customer for webhook lookups
-- and customer-portal (cancel/manage) sessions.
ALTER TABLE users ADD COLUMN stripe_customer_id TEXT;
CREATE INDEX idx_users_stripe ON users (stripe_customer_id);
