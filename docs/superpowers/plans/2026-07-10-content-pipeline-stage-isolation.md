# Content Pipeline Stage Isolation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the `content-pipeline` skill so each judgment stage (interview, draft, edit, synthesis) is an isolated unit that communicates only through persisted artifacts — a per-article **brief** and a composed **voice doc** — with versioned drafts, so the pipeline can regenerate or resume at any stage.

**Architecture:** Add two DB tables (`briefs`, `draft_versions`) via a v2 migration, a `voice` module that composes a static seed + learned rules into one voice doc, a `brief` module for brief CRUD, draft versioning in `writing.py`, three new context-read CLI verbs matched to the subagent contracts, five swappable `references/` prompt/spec files, and a rewritten `SKILL.md` that orchestrates the four stages as `Task` subagents.

**Tech Stack:** Python 3.12, stdlib `sqlite3`, `argparse`, `pytest`, `uv` for all Python invocation. Markdown for skill/reference files.

## Global Constraints

- All Python runs through `uv`: tests via `uv run pytest`, CLI via `uv run python -m content_pipeline.cli`. Never `pip install`; never hand-edit `pyproject.toml` deps.
- Work happens inside `.claude/skills/content-pipeline/` (the skill package root). All paths below are relative to that directory unless prefixed with `docs/`.
- `--db` is a mandatory top-level CLI flag; there is no default. Tests use a scratch/`tmp_path` DB, never `~/.content-pipeline/pipeline.sqlite`.
- Article output (drafts) contains **no em dashes** anywhere — use commas, periods, or parentheses. This constraint lives in the voice default and the drafter/edit prompts.
- DB writes are additive / nothing-ephemeral: briefs and drafts are versioned (new rows), never overwritten.
- Reference/spec content lives in files under `references/`, loaded on demand — never inlined into `SKILL.md`, never in the DB.
- Follow existing test style (`tests/conftest.py` provides a `conn` fixture at schema head; tests import modules directly and assert on rows/events).

---

### Task 1: Schema v2 — `briefs` and `draft_versions` tables + migration

**Files:**
- Modify: `src/content_pipeline/db.py`
- Test: `tests/test_db.py`

**Interfaces:**
- Consumes: existing `_SCHEMA_V1`, `init_schema`, `migrate`, `schema_version`, `_MIGRATIONS`.
- Produces: `CURRENT_VERSION == 2`; tables `briefs(id, article_id, version, brief_json, created_at)` and `draft_versions(id, article_id, version, text, brief_id, voice_snapshot, created_at)`; a v1→v2 migration that creates both and backfills `draft_versions` (version 1) from any `articles` row with non-empty `draft_text`. After this task, `init_schema` and `migrate` both leave a DB at version 2.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_db.py`:

```python
from content_pipeline import db


def test_fresh_db_is_v2_with_new_tables(conn):
    assert db.schema_version(conn) == 2
    for table in ("briefs", "draft_versions"):
        found = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        assert found is not None, f"missing table {table}"


def test_v1_to_v2_migration_backfills_draft_versions(tmp_path):
    c = db.connect(str(tmp_path / "v1.sqlite"))
    c.executescript(db._SCHEMA_V1)
    c.execute("INSERT INTO schema_meta(version) VALUES (1)")
    c.execute(
        "INSERT INTO articles (id, candidate_id, status, draft_text, created_at) "
        "VALUES ('a1', NULL, 'reviewing', 'existing draft body', '2026-01-01T00:00:00+00:00')"
    )
    c.execute(
        "INSERT INTO articles (id, candidate_id, status, draft_text, created_at) "
        "VALUES ('a2', NULL, 'interviewing', NULL, '2026-01-01T00:00:00+00:00')"
    )
    c.commit()

    db.migrate(c)

    assert db.schema_version(c) == 2
    v = c.execute("SELECT * FROM draft_versions WHERE article_id='a1'").fetchone()
    assert v["version"] == 1
    assert v["text"] == "existing draft body"
    assert v["brief_id"] is None
    # article with no draft_text is not backfilled
    none_row = c.execute("SELECT * FROM draft_versions WHERE article_id='a2'").fetchone()
    assert none_row is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_db.py -k "v2 or v1_to_v2" -v`
Expected: FAIL (fresh DB is version 1; `draft_versions` table does not exist).

- [ ] **Step 3: Implement the migration and version bump**

In `src/content_pipeline/db.py`, change `CURRENT_VERSION` and add the migration. Replace the `CURRENT_VERSION = 1` line with `CURRENT_VERSION = 2`. Then add the v2 migration SQL after `_SCHEMA_V1` and register it:

```python
_MIGRATION_V2 = """
CREATE TABLE briefs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  article_id TEXT REFERENCES articles(id),
  version INTEGER NOT NULL,
  brief_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE draft_versions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  article_id TEXT REFERENCES articles(id),
  version INTEGER NOT NULL,
  text TEXT NOT NULL,
  brief_id INTEGER REFERENCES briefs(id),
  voice_snapshot TEXT,
  created_at TEXT NOT NULL
);
INSERT INTO draft_versions (article_id, version, text, brief_id, voice_snapshot, created_at)
  SELECT id, 1, draft_text, NULL, NULL, created_at
    FROM articles
   WHERE draft_text IS NOT NULL AND draft_text != '';
"""
```

Change `init_schema` so new DBs run the migration chain to head (single source of truth for v2):

```python
def init_schema(conn):
    conn.executescript(_SCHEMA_V1)
    conn.execute("INSERT INTO schema_meta(version) VALUES (1)")
    conn.commit()
    migrate(conn)
```

Register the migration (was `_MIGRATIONS = {}`):

```python
_MIGRATIONS = {1: (2, _MIGRATION_V2)}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_db.py -v`
Expected: PASS (both new tests and all existing `test_db.py` tests).

- [ ] **Step 5: Run the full suite to catch schema fallout**

Run: `uv run pytest -q`
Expected: PASS. The `conn` fixture now lands at v2; existing tests must be unaffected.

- [ ] **Step 6: Commit**

```bash
git add src/content_pipeline/db.py tests/test_db.py
git commit -m "feat(db): v2 schema — briefs + draft_versions tables and migration"
```

---

### Task 2: `voice` module — composed voice doc (static seed + learned layer)

**Files:**
- Create: `src/content_pipeline/voice.py`
- Test: `tests/test_voice.py`

**Interfaces:**
- Consumes: `config.brand_context()` (static seed source), `canon.style_context(conn)` (learned layer).
- Produces:
  - `DEFAULT_SEED: str` — a concrete generic good-writing seed used when `brand_context` is empty.
  - `voice_doc(conn) -> str` — the single composed voice doc handed to the brief-writer and drafter subagents: the seed (operator `brand_context` if set, else `DEFAULT_SEED`) followed by the learned layer from `style_context`, if any.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_voice.py`:

```python
from content_pipeline import voice, canon


def test_voice_doc_uses_default_seed_when_no_brand_context(conn, monkeypatch):
    monkeypatch.setattr("content_pipeline.config.brand_context", lambda: "")
    doc = voice.voice_doc(conn)
    assert voice.DEFAULT_SEED in doc
    assert "em dash" in doc.lower()  # the no-em-dash rule is part of the floor


def test_voice_doc_prefers_operator_brand_context(conn, monkeypatch):
    monkeypatch.setattr("content_pipeline.config.brand_context", lambda: "MY HOUSE VOICE")
    doc = voice.voice_doc(conn)
    assert "MY HOUSE VOICE" in doc
    assert voice.DEFAULT_SEED not in doc


def test_voice_doc_appends_learned_layer(conn, monkeypatch):
    monkeypatch.setattr("content_pipeline.config.brand_context", lambda: "SEED")
    canon.add_permanent_rule(conn, "Keep paragraphs short.", "positive", [1])
    doc = voice.voice_doc(conn)
    assert "SEED" in doc
    assert "Keep paragraphs short." in doc
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_voice.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'content_pipeline.voice'`.

- [ ] **Step 3: Implement `voice.py`**

Create `src/content_pipeline/voice.py`:

```python
"""The composed voice doc handed to the brief-writer and drafter subagents.

Two layers: a static hand-owned SEED (the operator's config brand_context,
or a generic good-writing default when unset) and a learned layer rendered
from the style canon (permanent rules + provisional tendencies). The seed is
the floor; the learned layer is composed on top. The seed changes only when
the operator edits their brand_context; the learned layer evolves via
synthesis. This is the single input a stage receives for "how to write" —
audience, tone, length, and structure belong here, not in the per-article
brief.
"""

from content_pipeline import config
from content_pipeline.learning import canon

DEFAULT_SEED = """Voice and writing guidelines (generic default; refine over time):
- Write in plain, direct English. Prefer concrete nouns and verbs over abstraction.
- Short sentences, one idea each. Vary rhythm but favor brevity.
- Open with the point. Do not bury it under throat-clearing.
- No em dashes anywhere. Use commas, periods, or parentheses instead.
- Cut filler: "very", "really", "in order to", "the fact that".
- Prefer active voice and name the actor.
- Read it aloud; if you stumble, rewrite it."""


def voice_doc(conn) -> str:
    """Compose the voice doc: static seed first, learned layer second."""
    seed = config.brand_context() or DEFAULT_SEED
    learned = canon.style_context(conn)
    if learned:
        return f"{seed}\n\n--- Learned preferences ---\n\n{learned}"
    return seed
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_voice.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/content_pipeline/voice.py tests/test_voice.py
git commit -m "feat(voice): composed voice doc from static seed + learned layer"
```

---

### Task 3: `brief` module — versioned brief CRUD

**Files:**
- Create: `src/content_pipeline/brief.py`
- Test: `tests/test_brief.py`

**Interfaces:**
- Consumes: `events.append` (for a `brief_saved` event), the `briefs` table from Task 1.
- Produces:
  - `save_brief(conn, article_id, brief: dict) -> int` — validate and persist a new brief version; returns the new version number (1-indexed per article). Appends a `brief_saved` event.
  - `current_brief(conn, article_id) -> dict | None` — the latest brief for the article as `{"id", "version", **brief_fields}`, or `None` if none saved.
  - Validation: `brief` must be a dict with string `topic`, string `angle`, and list `key_points`; else `ValueError`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_brief.py`:

```python
import json
import pytest
from content_pipeline import brief, events


def _brief(topic="Pricing", angle="Raise prices, lose the wrong customers"):
    return {
        "title": "The customers you want to lose",
        "topic": topic,
        "angle": angle,
        "key_points": ["cheap price attracts high-support churn", "revenue rose after the hike"],
        "source_snippet": "I raised it to $39. Lost about 40 users.",
        "constraints": ["do not name the product"],
    }


def test_save_brief_returns_incrementing_versions(conn):
    assert brief.save_brief(conn, "a1", _brief()) == 1
    assert brief.save_brief(conn, "a1", _brief(angle="revised angle")) == 2


def test_current_brief_returns_latest_with_id_and_version(conn):
    brief.save_brief(conn, "a1", _brief(angle="first"))
    brief.save_brief(conn, "a1", _brief(angle="second"))
    cur = brief.current_brief(conn, "a1")
    assert cur["version"] == 2
    assert cur["angle"] == "second"
    assert isinstance(cur["id"], int)


def test_current_brief_none_when_absent(conn):
    assert brief.current_brief(conn, "nope") is None


def test_save_brief_logs_event(conn):
    brief.save_brief(conn, "a1", _brief())
    kinds = [e["kind"] for e in events.recent(conn)]
    assert "brief_saved" in kinds


def test_save_brief_rejects_missing_required_fields(conn):
    with pytest.raises(ValueError):
        brief.save_brief(conn, "a1", {"topic": "x"})  # no angle, no key_points
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_brief.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'content_pipeline.brief'`.

- [ ] **Step 3: Implement `brief.py`**

Create `src/content_pipeline/brief.py`:

```python
"""Per-article brief: the interview stage's output and the drafter's main
input. Content only (the *what*): topic, angle, key points, a source
snippet, and content constraints. Versioned - saving a brief appends a new
row; old versions are preserved so a regenerate from a changed brief is a
new artifact beside the old one. Never holds voice/tone/audience - those
live in the voice doc.
"""

import json
from datetime import datetime, timezone

from content_pipeline import events


def _now():
    return datetime.now(timezone.utc).isoformat()


def _validate(brief: dict) -> None:
    if not isinstance(brief, dict):
        raise ValueError(f"brief must be a dict, got {brief!r}")
    if not isinstance(brief.get("topic"), str) or not brief["topic"]:
        raise ValueError("brief missing non-empty string 'topic'")
    if not isinstance(brief.get("angle"), str) or not brief["angle"]:
        raise ValueError("brief missing non-empty string 'angle'")
    if not isinstance(brief.get("key_points"), list):
        raise ValueError("brief missing list 'key_points'")


def save_brief(conn, article_id, brief: dict) -> int:
    """Persist a new brief version for article_id; return the version number."""
    _validate(brief)
    row = conn.execute(
        "SELECT MAX(version) AS v FROM briefs WHERE article_id = ?", (article_id,)
    ).fetchone()
    version = (row["v"] or 0) + 1
    conn.execute(
        "INSERT INTO briefs (article_id, version, brief_json, created_at) VALUES (?, ?, ?, ?)",
        (article_id, version, json.dumps(brief), _now()),
    )
    conn.commit()
    events.append(conn, "brief_saved", {"version": version}, article_id=article_id)
    return version


def current_brief(conn, article_id) -> dict | None:
    """Latest brief for the article as {id, version, **fields}, or None."""
    row = conn.execute(
        "SELECT id, version, brief_json FROM briefs WHERE article_id = ? "
        "ORDER BY version DESC LIMIT 1",
        (article_id,),
    ).fetchone()
    if row is None:
        return None
    data = json.loads(row["brief_json"])
    return {"id": row["id"], "version": row["version"], **data}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_brief.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/content_pipeline/brief.py tests/test_brief.py
git commit -m "feat(brief): versioned per-article brief CRUD"
```

---

### Task 4: Draft versioning in `writing.py`

**Files:**
- Modify: `src/content_pipeline/writing.py`
- Test: `tests/test_writing.py`

**Interfaces:**
- Consumes: `brief.current_brief(conn, article_id)`, `voice.voice_doc(conn)`, the `draft_versions` table.
- Produces:
  - New helper `append_draft_version(conn, article_id, text) -> int` — inserts a `draft_versions` row (next per-article version) capturing the current `brief_id` (from `current_brief`, `None` if absent) and `voice_snapshot` (from `voice_doc`). Returns the version number.
  - `save_draft` and `record_edit_round` now call `append_draft_version` so every draft and every edit round writes a version. Their existing signatures, return values, status transitions, and events are unchanged.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_writing.py`:

```python
from content_pipeline import brief as brief_mod


def test_save_draft_appends_version_one_with_inputs(conn, monkeypatch):
    monkeypatch.setattr("content_pipeline.config.brand_context", lambda: "SEEDVOICE")
    aid, cid = _start_article(conn)
    brief_mod.save_brief(conn, aid, {"topic": "t", "angle": "a", "key_points": ["k"]})

    writing.save_draft(conn, aid, "Draft body one.")

    v = conn.execute(
        "SELECT * FROM draft_versions WHERE article_id=? ORDER BY version", (aid,)
    ).fetchall()
    assert len(v) == 1
    assert v[0]["version"] == 1
    assert v[0]["text"] == "Draft body one."
    assert v[0]["brief_id"] is not None
    assert "SEEDVOICE" in v[0]["voice_snapshot"]


def test_regenerate_via_second_save_draft_adds_version_two(conn):
    aid, cid = _start_article(conn)
    writing.save_draft(conn, aid, "first generation")
    writing.save_draft(conn, aid, "regenerated from a changed brief")

    versions = conn.execute(
        "SELECT version, text FROM draft_versions WHERE article_id=? ORDER BY version", (aid,)
    ).fetchall()
    assert [r["version"] for r in versions] == [1, 2]
    assert versions[1]["text"] == "regenerated from a changed brief"


def test_edit_round_also_appends_a_draft_version(conn):
    aid = _draft_article(conn, text="v1 body")  # save_draft -> version 1
    writing.record_edit_round(conn, aid, "tighten it", "v1 body tighter")

    versions = conn.execute(
        "SELECT version, text FROM draft_versions WHERE article_id=? ORDER BY version", (aid,)
    ).fetchall()
    assert [r["version"] for r in versions] == [1, 2]
    assert versions[1]["text"] == "v1 body tighter"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_writing.py -k "version or regenerate or edit_round_also" -v`
Expected: FAIL (no `draft_versions` rows written by `save_draft`/`record_edit_round`).

- [ ] **Step 3: Implement versioning**

In `src/content_pipeline/writing.py`, add imports at the top (after the existing `from content_pipeline import events`):

```python
from content_pipeline import brief as brief_mod
from content_pipeline import voice
```

Add the helper (place it after `_char_diff_size`):

```python
def append_draft_version(conn, article_id, text) -> int:
    """Append a draft_versions row (next per-article version), capturing the
    brief_id and voice snapshot that produced this text. Returns the version
    number. Called by save_draft and record_edit_round so every draft and
    edit round is preserved - nothing overwritten."""
    row = conn.execute(
        "SELECT MAX(version) AS v FROM draft_versions WHERE article_id = ?", (article_id,)
    ).fetchone()
    version = (row["v"] or 0) + 1
    cur = brief_mod.current_brief(conn, article_id)
    brief_id = cur["id"] if cur else None
    conn.execute(
        "INSERT INTO draft_versions (article_id, version, text, brief_id, voice_snapshot, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (article_id, version, text, brief_id, voice.voice_doc(conn), _now()),
    )
    conn.commit()
    return version
```

In `save_draft`, add the version append immediately before the `events.append(... "draft_generated" ...)` call (after the `UPDATE articles ...` + `conn.commit()`):

```python
    append_draft_version(conn, article_id, draft_text)
```

In `record_edit_round`, add the version append immediately before the `events.append(... "edit_round" ...)` call (after the `UPDATE articles SET draft_text ...` + `conn.commit()`):

```python
    append_draft_version(conn, article_id, new_text)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_writing.py -v`
Expected: PASS (new versioning tests plus all existing writing tests).

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/content_pipeline/writing.py tests/test_writing.py
git commit -m "feat(writing): version every draft and edit round in draft_versions"
```

---

### Task 5: CLI verbs — `save-brief`, `brief-writer-context`, `brief-context`, `edit-context`

**Files:**
- Modify: `src/content_pipeline/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `brief.save_brief`, `brief.current_brief`, `voice.voice_doc`, `writing` article/draft reads.
- Produces four new subcommands, each printing one JSON object:
  - `save-brief ARTICLE_ID --json '<brief dict>'` → `{"article_id", "version"}`.
  - `brief-writer-context ARTICLE_ID` → `{"article_id", "answers", "source_snippet", "voice_doc"}` (input for the brief-writer subagent). `source_snippet` is the candidate title + summary.
  - `brief-context ARTICLE_ID` → `{"article_id", "brief", "voice_doc"}` (input for the drafter subagent). `brief` is `current_brief` or `null`.
  - `edit-context ARTICLE_ID` → `{"article_id", "current_draft", "brief", "voice_doc"}` (input for the edit subagent). `current_draft` is `articles.draft_text`.
- The existing `draft-context` verb stays (superseded, kept for transition per spec §9).

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_cli.py` (use the existing CLI-invocation pattern in that file; the version below drives `cli.main` and captures stdout, and seeds state through the real modules):

```python
import json
from content_pipeline import db, writing, brief as brief_mod, cli
from content_pipeline.discovery import source
from content_pipeline.models import Candidate
from content_pipeline import queue


def _run(capsys, dbpath, *argv):
    cli.main(["--db", dbpath, *argv])
    return json.loads(capsys.readouterr().out.strip().splitlines()[-1])


def _started_article(dbpath):
    c = db.connect(dbpath)
    # brand-new file has no tables; bootstrap exactly as the CLI's _get_conn does
    has_meta = c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_meta'"
    ).fetchone()
    db.init_schema(c) if has_meta is None else db.migrate(c)
    source.ingest(c, [Candidate(source="reddit", source_ref="r1", title="Pricing story",
                                url="u", summary="Raised price to $39, lost 40 users.")])
    cid = c.execute("SELECT id FROM candidates").fetchone()["id"]
    queue.decide(c, cid, "yes", today="2026-07-09")
    aid = writing.start_article(c, cid)
    c.close()
    return aid


def test_save_brief_and_brief_context_roundtrip(tmp_path, capsys):
    dbp = str(tmp_path / "p.sqlite")
    aid = _started_article(dbp)
    brief_json = json.dumps({"topic": "pricing", "angle": "lose the wrong customers",
                             "key_points": ["support-heavy churn"], "source_snippet": "…"})

    saved = _run(capsys, dbp, "save-brief", aid, "--json", brief_json)
    assert saved["version"] == 1

    ctx = _run(capsys, dbp, "brief-context", aid)
    assert ctx["brief"]["angle"] == "lose the wrong customers"
    assert isinstance(ctx["voice_doc"], str) and ctx["voice_doc"]


def test_brief_writer_context_has_answers_and_snippet(tmp_path, capsys):
    dbp = str(tmp_path / "p.sqlite")
    aid = _started_article(dbp)
    _run(capsys, dbp, "answer", aid, "--question", "What is the takeaway?",
         "--chosen", "custom", "--text", "cheap price selects bad customers")

    ctx = _run(capsys, dbp, "brief-writer-context", aid)
    assert ctx["answers"][0]["answer_text"] == "cheap price selects bad customers"
    assert "Raised price to $39" in ctx["source_snippet"]
    assert ctx["voice_doc"]


def test_edit_context_returns_current_draft(tmp_path, capsys):
    dbp = str(tmp_path / "p.sqlite")
    aid = _started_article(dbp)
    _run(capsys, dbp, "save-draft", aid, "--text", "the current draft body")

    ctx = _run(capsys, dbp, "edit-context", aid)
    assert ctx["current_draft"] == "the current draft body"
    assert "voice_doc" in ctx and "brief" in ctx
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_cli.py -k "brief or edit_context" -v`
Expected: FAIL (`invalid choice: 'save-brief'` from argparse).

- [ ] **Step 3: Implement the command handlers**

In `src/content_pipeline/cli.py`, add `brief` and `voice` to the imports:

```python
from content_pipeline import db, queue, writing, brief, voice
```

Add a source-snippet helper near the other private helpers:

```python
def _source_snippet(conn, article_id) -> str:
    """Short grounding excerpt from the originating candidate: title + summary."""
    row = conn.execute(
        "SELECT c.title, c.summary FROM candidates c "
        "JOIN articles a ON a.candidate_id = c.id WHERE a.id = ?",
        (article_id,),
    ).fetchone()
    if row is None:
        return ""
    return f"{row['title']}\n\n{row['summary']}".strip()
```

Add the four handlers (place them after `cmd_draft_context`):

```python
def cmd_save_brief(args):
    conn = _get_conn(args.db)
    try:
        data = json.loads(args.json)
        try:
            version = brief.save_brief(conn, args.article_id, data)
        except ValueError as e:
            raise SystemExit(str(e))
        _print_json({"article_id": args.article_id, "version": version})
    finally:
        conn.close()


def cmd_brief_writer_context(args):
    conn = _get_conn(args.db)
    try:
        answers = conn.execute(
            "SELECT question, chosen, answer_text FROM interview_answers "
            "WHERE article_id = ? ORDER BY id ASC",
            (args.article_id,),
        ).fetchall()
        _print_json({
            "article_id": args.article_id,
            "answers": _rows_to_dicts(answers),
            "source_snippet": _source_snippet(conn, args.article_id),
            "voice_doc": voice.voice_doc(conn),
        })
    finally:
        conn.close()


def cmd_brief_context(args):
    conn = _get_conn(args.db)
    try:
        _print_json({
            "article_id": args.article_id,
            "brief": brief.current_brief(conn, args.article_id),
            "voice_doc": voice.voice_doc(conn),
        })
    finally:
        conn.close()


def cmd_edit_context(args):
    conn = _get_conn(args.db)
    try:
        row = conn.execute(
            "SELECT draft_text FROM articles WHERE id = ?", (args.article_id,)
        ).fetchone()
        _print_json({
            "article_id": args.article_id,
            "current_draft": row["draft_text"] if row else None,
            "brief": brief.current_brief(conn, args.article_id),
            "voice_doc": voice.voice_doc(conn),
        })
    finally:
        conn.close()
```

Register the four subparsers in `build_parser` (place after the `draft-context` parser block):

```python
    p_save_brief = sub.add_parser("save-brief", help="Persist a versioned brief")
    p_save_brief.add_argument("article_id")
    p_save_brief.add_argument("--json", required=True, dest="json")
    p_save_brief.set_defaults(func=cmd_save_brief)

    p_bw_ctx = sub.add_parser("brief-writer-context", help="Context for the brief-writer subagent")
    p_bw_ctx.add_argument("article_id")
    p_bw_ctx.set_defaults(func=cmd_brief_writer_context)

    p_brief_ctx = sub.add_parser("brief-context", help="Context for the drafter subagent")
    p_brief_ctx.add_argument("article_id")
    p_brief_ctx.set_defaults(func=cmd_brief_context)

    p_edit_ctx = sub.add_parser("edit-context", help="Context for the edit subagent")
    p_edit_ctx.add_argument("article_id")
    p_edit_ctx.set_defaults(func=cmd_edit_context)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_cli.py -v`
Expected: PASS (new verbs plus existing CLI tests).

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/content_pipeline/cli.py tests/test_cli.py
git commit -m "feat(cli): save-brief + brief-writer/brief/edit context verbs"
```

---

### Task 6: Reference files — interview guide + four subagent prompts

**Files:**
- Create: `references/interview-guide.md`
- Create: `references/brief-writer-prompt.md`
- Create: `references/drafter-prompt.md`
- Create: `references/edit-prompt.md`
- Create: `references/synthesis-prompt.md`

**Interfaces:**
- Consumes: nothing at runtime (these are prompt/spec text the orchestrator loads on demand and passes into `Task` subagents).
- Produces: five self-contained markdown files. Each subagent prompt states its exact input contract (which `*-context` verb feeds it) and its required output shape. The synthesis prompt carries the full two-door reasoning moved out of `SKILL.md`.

- [ ] **Step 1: Write `references/interview-guide.md`**

```markdown
# Interview Guide (content dimensions)

The orchestrator reads this and generates candidate-tailored questions from it.
Ask ONE question at a time. Each question offers a recommended answer, one
alternate, and always allows free-text or skip. These dimensions are about the
CONTENT only — the operator has already read the source and decided it is worth
an article. Do NOT ask about tone, audience, length, or house style; those live
in the voice doc.

Probe these dimensions (skip any that do not fit the candidate):

1. **Thesis** — what is the operator's actual take on this topic? The one
   sentence they would stand behind.
2. **Key insight** — the non-obvious point that makes it worth publishing.
3. **Which points matter** — the 2 to 4 sub-points to cover; what to leave out.
4. **Grounding** — any personal experience, example, or specific detail that
   makes it concrete rather than generic.
5. **Why now** — what makes this timely or worth saying at all.

Stop when you have enough to write a brief. Do not interrogate.
```

- [ ] **Step 2: Write `references/brief-writer-prompt.md`**

```markdown
# Brief-Writer Subagent

You turn interview answers into a structured content brief. You do NOT write
the article.

**Input** (from `brief-writer-context ARTICLE_ID`): `answers` (the operator's
interview choices), `source_snippet` (the originating candidate's title +
summary), `voice_doc` (how the piece should read — read it only to keep the
brief consistent with it; do not copy voice rules into the brief).

**Output** — return ONLY a JSON object with these fields (content only, never
tone/audience/length):
- `title`: a working title (string)
- `topic`: one-line topic (string)
- `angle`: the thesis/slant to take (string)
- `key_points`: 2 to 5 points to hit (list of strings)
- `source_snippet`: a short verbatim excerpt from the source to ground a
  reference (string)
- `constraints`: content-specific must-avoids, may be empty (list of strings)

Base every field on the answers. Do not invent facts not present in the answers
or source snippet.
```

- [ ] **Step 3: Write `references/drafter-prompt.md`**

```markdown
# Drafter Subagent

You write the full article draft. You receive only two inputs and nothing about
where the topic came from.

**Input** (from `brief-context ARTICLE_ID`): `brief` (what to say — title,
topic, angle, key_points, source_snippet, constraints) and `voice_doc` (how to
say it — tone, audience, length, structure, phrasing rules).

**Task:** Write the complete draft. Apply the brief's angle and cover its
key_points. Apply every rule in the voice_doc verbatim. Honor the brief's
constraints.

**Hard constraint:** no em dashes anywhere. Use commas, periods, or parentheses.

**Output:** return ONLY the full draft text (no preamble, no commentary).
```

- [ ] **Step 4: Write `references/edit-prompt.md`**

```markdown
# Edit Subagent

You revise an existing draft in response to one round of operator feedback.

**Input** (from `edit-context ARTICLE_ID`): `current_draft` (the text to
revise), the operator's `feedback` (verbatim — passed to you by the
orchestrator), `brief` (the content contract) and `voice_doc` (the style
contract).

**Task:** Apply the operator's feedback to `current_draft`. Change what the
feedback asks for and leave the rest intact. Stay within the brief and the
voice_doc.

**Hard constraint:** no em dashes anywhere.

**Output:** return ONLY the full revised draft text (no preamble, no commentary).
```

- [ ] **Step 5: Write `references/synthesis-prompt.md`**

```markdown
# Synthesis Subagent (style learning)

You reason over recent edit/interview events and decide what the pipeline
should learn. You do not write articles.

**Input** (from `synthesis-context ARTICLE_ID`): `base_checkpoint`,
`new_events` (edit rounds + interview choices since the last synthesis),
`active_rules` (current permanent rules, by id), `promotion_allowed`.

**Two-door reasoning — apply exactly:**
1. **Additive only.** Never regenerate the full rule set. Propose only NEW
   rules to add, or EXISTING active rules to supersede (by id, with a reason).
2. **Cite evidence.** Every new rule and every tendency must cite the
   `new_events` ids in `evidence_ids`. No evidence → rejected by the backend.
3. **Generalizable vs one-off.** A lasting preference earns a rule or tendency;
   a one-off (fact correction, typo, detail unique to one article) earns
   nothing.
4. **Two-door promotion.** An explicit directive in the feedback (never,
   always, stop, from now on, don't, must) → a NEW permanent rule
   (`new_rules`). A silent, repeated preference with no directive → a
   provisional `tendency`, never a permanent rule.
5. **Contradiction → supersede.** If an edit contradicts an active rule,
   propose that rule in `supersede` with the reason.

If `promotion_allowed` is false, still send `tendencies`; expect no rule
promotion.

**Output** — return ONLY this JSON object:
```json
{
  "new_rules": [{"text": "...", "kind": "positive|negative", "evidence_ids": [1]}],
  "supersede": [{"id": 3, "reason": "..."}],
  "tendencies": [{"text": "...", "evidence_ids": [2]}]
}
```
```

- [ ] **Step 6: Verify the files exist and are em-dash-free**

Run: `ls references/ && ! grep -rl "—" references/`
Expected: the five files listed, and `grep` finds no em dash (the `!` makes the command succeed when none is found).

- [ ] **Step 7: Commit**

```bash
git add references/
git commit -m "docs(content-pipeline): interview guide + four subagent prompts"
```

---

### Task 7: Rewrite `SKILL.md` — orchestration + subagent dispatch

**Files:**
- Modify: `SKILL.md`

**Interfaces:**
- Consumes: all new verbs (`save-brief`, `brief-writer-context`, `brief-context`, `edit-context`) and reference files from Tasks 5–6.
- Produces: an orchestration-only `SKILL.md`. It keeps the numbered flow and stopping points, but each judgment stage now (a) loads its reference prompt file on demand and (b) dispatches a `Task` subagent with the matching `*-context` verb's output. The two-door reasoning prose is removed from `SKILL.md` (it now lives in `references/synthesis-prompt.md`); `SKILL.md` points to the file instead.

- [ ] **Step 1: Update the drafting section (step 6 of the flow)**

Replace the current "6. Draft — `draft-context`, then `save-draft`" section so it reads (keep surrounding sections intact):

```markdown
### 6. Brief, then draft — subagents
The interview's answers become a **brief**, then the brief plus the voice doc
become a **draft**. Both are subagent steps.

**Brief-writer.** Load `references/brief-writer-prompt.md`. Read
`brief-writer-context ARTICLE_ID` ({answers, source_snippet, voice_doc}).
Dispatch a `Task` subagent with the prompt + that context; it returns the brief
JSON. Persist it:

    save-brief ARTICLE_ID --json '<brief JSON>'

**Drafter.** Load `references/drafter-prompt.md`. Read
`brief-context ARTICLE_ID` ({brief, voice_doc}). Dispatch a `Task` subagent; it
returns the full draft text. Show the operator, then persist:

    save-draft ARTICLE_ID --text "<the full draft>"

`save-draft` records a new draft version each call, so to **regenerate** (after
a changed brief or voice) just run the drafter again and `save-draft` the new
text. Surface `pending_rule_notice` if non-null.
```

- [ ] **Step 2: Update the edit-loop section (step 7 of the flow)**

Replace the "7. Edit loop — `edit`" section:

```markdown
### 7. Edit loop — edit subagent
For each round of operator feedback: load `references/edit-prompt.md`, read
`edit-context ARTICLE_ID` ({current_draft, brief, voice_doc}), dispatch a `Task`
subagent with the prompt + context + the operator's verbatim feedback. It
returns the revised draft. Show it, then record the round:

    edit ARTICLE_ID --feedback "<verbatim operator feedback>" --text "<revised draft>"

Repeat per the operator's feedback until they approve. (This step is an inherent
back-and-forth; keep going without re-asking each round.)
```

- [ ] **Step 3: Update the interview section (steps 4–5 of the flow)**

In the "Start the next article" / "Record answers" area, add a line pointing at the guide (place after the paragraph that says you generate the questions yourself):

```markdown
Load `references/interview-guide.md` for the content dimensions to probe. It is
a swappable spec: change what gets asked by editing that file, not this skill.
Ask one question at a time (never batch), recording each with `answer` before
the next.
```

- [ ] **Step 4: Update the synthesis section (step 9 of the flow)**

Replace the inline two-door reasoning block under "9. Synthesize style" with a pointer + dispatch:

```markdown
Load `references/synthesis-prompt.md` (it carries the full two-door reasoning).
Read `synthesis-context ARTICLE_ID`, dispatch a `Task` subagent with the prompt
+ that context; it returns the decision JSON. Persist it:

    apply-synthesis ARTICLE_ID --base-checkpoint <base_checkpoint> --json '<decision>'

Passing `base_checkpoint` back is required (idempotency). See
`references/synthesis-prompt.md` for the reasoning rules; do not restate them
here.
```

Delete the now-duplicated "The two-door reasoning" prose section from `SKILL.md`.

- [ ] **Step 5: Verify structure and no stale references**

Run: `grep -n "references/" SKILL.md && ! grep -n "two-door" SKILL.md | grep -v "references/synthesis"`
Expected: the four `references/…` mentions present; the standalone two-door prose section is gone (only the pointer to the file remains).

- [ ] **Step 6: Sanity-run one new verb end to end (throwaway DB)**

Run: `uv run python -m content_pipeline.cli --db "$(mktemp -d)/t.sqlite" brief-context nonexistent`
Expected: JSON `{"article_id": "nonexistent", "brief": null, "voice_doc": "..."}` with the default seed voice — confirms wiring works against a fresh DB. (Throwaway DB only; never the real pipeline DB.)

- [ ] **Step 7: Commit**

```bash
git add SKILL.md
git commit -m "docs(content-pipeline): orchestrate stages as subagents with reference prompts"
```

---

## Self-Review

**Spec coverage:**
- §2 four stages as subagents → Tasks 6 (prompts) + 7 (dispatch); brief-writer split → Tasks 3, 5, 7.
- §3 composed voice doc (seed + learned, Model 1, code-constant default) → Task 2.
- §4 briefs table + verbs → Tasks 1, 3, 5; draft_versions + DB-not-git versioning → Tasks 1, 4.
- §5 swappable reference files under `references/` → Tasks 6, 7.
- §6 regeneration & resume → Task 4 (versioning) + Task 7 (regenerate via re-run) + existing `resumable()`.
- §7 learning relocated to prompt file → Tasks 6, 7.
- §8 non-goals honored: no onboarding, no Model-2, no git versioning; the voice default is a minimal generic floor (concrete, not Howard-specific), refinable later.
- §9 open details resolved: migration (Task 1), `draft-context` kept alongside new verbs (Task 5), voice render in a new `voice` module (Task 2).

**Placeholder scan:** No TBD/TODO; every code and test step shows complete content.

**Type consistency:** `save_brief`/`current_brief`, `append_draft_version`, `voice_doc`, and the four `cmd_*`/context JSON shapes are used identically across Tasks 3–7. `current_brief` returns `{id, version, **fields}`; `append_draft_version` reads `cur["id"]`; `brief-context` returns it under `brief` — consistent.

**One correction to `_get_conn` assumption:** existing `_get_conn` bootstraps with `init_schema` on a brand-new file and `migrate` otherwise; Task 1's `init_schema` change (run v1 then migrate) keeps both paths landing at v2. No CLI change needed for that.
