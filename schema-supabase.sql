-- Run once in the Supabase SQL editor. These tables are not in the public API schema.
CREATE SCHEMA IF NOT EXISTS boutique_private;
REVOKE ALL ON SCHEMA boutique_private FROM PUBLIC, anon, authenticated;
CREATE TABLE IF NOT EXISTS boutique_private.users (
  id text PRIMARY KEY, name text NOT NULL, email text NOT NULL UNIQUE,
  password text NOT NULL, created bigint NOT NULL
);
CREATE TABLE IF NOT EXISTS boutique_private.shops (
  user_id text PRIMARY KEY REFERENCES boutique_private.users(id),
  data text NOT NULL, revision integer NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS boutique_private.sessions (
  token_hash text PRIMARY KEY, user_id text NOT NULL REFERENCES boutique_private.users(id),
  expires bigint NOT NULL
);
CREATE INDEX IF NOT EXISTS sessions_expires_idx ON boutique_private.sessions (expires);
REVOKE ALL ON ALL TABLES IN SCHEMA boutique_private FROM PUBLIC, anon, authenticated;
