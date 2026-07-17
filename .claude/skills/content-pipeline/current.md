# Content Pipeline — Current

**What this is:** Evaluating the `content-pipeline` skill by exercising it against the live DB and logging change requests. Feedback is captured in `FEEDBACK-LOG.md` (feedback-only); this file is the resume snapshot; session history in `reference/session-log.md`.

**Live DB:** `~/.content-pipeline/pipeline.sqlite`
**Skill dir:** `.claude/skills/content-pipeline/` (run CLI from here: `uv run python -m content_pipeline.cli --db ~/.content-pipeline/pipeline.sqlite <verb>`)

---

**Last updated:** 2026-07-10
**Just completed:** Fixed the `status` reporting bug — picked-but-not-started candidates were invisible. `status` now emits `picked_not_started_count` + `articles_by_status`. 99 tests pass. Change is **uncommitted** (repo started this session clean).

**Next:**
- Now: Pick the fork — (a) implement feedback #1's remaining half (startup numbered-menu / auto-jump orientation) in `SKILL.md`, or (b) resume actually working an article. Also commit the `status` fix (writing.py + cli.py), currently uncommitted.
- On deck: Resume the "Ai is ruining business" article (`reddit-1ur1fix`, mid-interview, 0 answers) or start the picked "$62 yesterday" article (`reddit-1uq35d9`).

**Live pipeline state:** 8 candidates pending review · 1 picked-not-started ("$62 yesterday") · 1 article interviewing ("Ai is ruining business", 0 answers) · 0 drafts/approved.

**Key decisions:**
- `FEEDBACK-LOG.md` is feedback-only; resume state lives here in `current.md`. Both files are used.
- `status` reporting gap treated as a real bug and fixed in code (not just logged) — it delivers the "chosen to write" + "drafted" counts feedback #1 wants.

**Open feedback (see FEEDBACK-LOG.md):**
1. Startup orientation: programmatic counts + numbered menu with auto-jump — counts half done (the fix above), menu/prose half outstanding.
2. No reset-to-picked path for a stuck article; and changing interview questions orphans answers (keyed to question text).

**Session ref:** `claude --resume 1ed39b77-dfca-49e6-93b6-b50d24b44255`
