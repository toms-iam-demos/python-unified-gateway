PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS events (
  event_id        TEXT PRIMARY KEY,
  kind            TEXT NOT NULL,                -- inbound_http | outbound_http | internal
  source          TEXT NOT NULL,                -- docusign | msgraph | system | etc
  namespace       TEXT NOT NULL DEFAULT '',

  correlation_id  TEXT NOT NULL,
  parent_event_id TEXT,

  received_at     TEXT NOT NULL,

  method          TEXT,
  host            TEXT,
  path            TEXT,
  remote_addr     TEXT,
  status_code     INTEGER,

  headers_json    TEXT NOT NULL DEFAULT '{}',
  body_raw        BLOB NOT NULL,
  body_sha256     TEXT NOT NULL,
  json_parsed     TEXT,

  verify_status   TEXT NOT NULL DEFAULT 'unknown',
  verify_reason   TEXT,

  dedupe_key      TEXT NOT NULL,
  UNIQUE(source, kind, dedupe_key),

  FOREIGN KEY(parent_event_id) REFERENCES events(event_id)
);

CREATE INDEX IF NOT EXISTS idx_events_received_at ON events(received_at);
CREATE INDEX IF NOT EXISTS idx_events_corr        ON events(correlation_id);

