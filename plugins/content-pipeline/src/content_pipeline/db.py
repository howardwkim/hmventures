import os, sqlite3
from pathlib import Path

CURRENT_VERSION = 1
DEFAULT_DB = "~/.content-pipeline/pipeline.sqlite"

def _resolve(path):
    p = path or os.environ.get("CONTENT_PIPELINE_DB") or DEFAULT_DB
    p = Path(p).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    return str(p)

def connect(path=None):
    conn = sqlite3.connect(_resolve(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

_SCHEMA_V1 = """
CREATE TABLE schema_meta (version INTEGER NOT NULL);
CREATE TABLE candidates (
  id TEXT PRIMARY KEY, source TEXT NOT NULL, source_ref TEXT,
  title TEXT NOT NULL, url TEXT, summary TEXT,
  engagement_json TEXT, topic_tags TEXT, emotional_driver TEXT, news_hook TEXT,
  predicted_relevance REAL,
  status TEXT NOT NULL DEFAULT 'pending',  -- pending|yes|no|snoozed
  snoozed_until TEXT, idea_note TEXT,
  created_at TEXT NOT NULL, decided_at TEXT
);
CREATE TABLE articles (
  id TEXT PRIMARY KEY, candidate_id TEXT REFERENCES candidates(id),
  status TEXT NOT NULL DEFAULT 'interviewing', -- interviewing|drafting|reviewing|approved|abandoned
  draft_text TEXT, final_text TEXT,
  created_at TEXT NOT NULL, approved_at TEXT
);
CREATE TABLE interview_answers (
  id INTEGER PRIMARY KEY AUTOINCREMENT, article_id TEXT REFERENCES articles(id),
  question TEXT NOT NULL, options_json TEXT,
  chosen TEXT, -- recommended|alternate|custom|skip
  answer_text TEXT, created_at TEXT NOT NULL
);
CREATE TABLE edit_rounds (
  id INTEGER PRIMARY KEY AUTOINCREMENT, article_id TEXT REFERENCES articles(id),
  round INTEGER NOT NULL, operator_feedback TEXT, what_changed TEXT,
  edit_size INTEGER, created_at TEXT NOT NULL
);
CREATE TABLE permanent_rules (
  id INTEGER PRIMARY KEY AUTOINCREMENT, rule_text TEXT NOT NULL,
  kind TEXT NOT NULL,   -- positive|negative
  status TEXT NOT NULL DEFAULT 'active', -- active|superseded
  provenance_event_ids TEXT, created_at TEXT NOT NULL,
  superseded_by INTEGER, superseded_reason TEXT
);
CREATE TABLE provisional_tendencies (
  id INTEGER PRIMARY KEY AUTOINCREMENT, tendency_text TEXT NOT NULL,
  evidence_event_ids TEXT, rebuilt_at TEXT NOT NULL
);
CREATE TABLE synthesis_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL,
  artifact TEXT NOT NULL, last_event_id_seen INTEGER, event_count INTEGER
);
CREATE TABLE events (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, kind TEXT NOT NULL,
  article_id TEXT, candidate_id TEXT, payload_json TEXT
);
CREATE INDEX idx_candidates_status ON candidates(status);
CREATE INDEX idx_events_kind ON events(kind);
"""

def init_schema(conn):
    conn.executescript(_SCHEMA_V1)
    conn.execute("INSERT INTO schema_meta(version) VALUES (?)", (CURRENT_VERSION,))
    conn.commit()

def schema_version(conn):
    row = conn.execute("SELECT version FROM schema_meta").fetchone()
    return row["version"] if row else 0

# Migration registry: {from_version: (to_version, sql_or_callable)}
_MIGRATIONS = {}

def migrate(conn):
    v = schema_version(conn)
    while v in _MIGRATIONS:
        to, step = _MIGRATIONS[v]
        step(conn) if callable(step) else conn.executescript(step)
        conn.execute("UPDATE schema_meta SET version=?", (to,))
        conn.commit()
        v = to
