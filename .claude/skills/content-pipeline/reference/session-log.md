# Content Pipeline — Session Log

Append-only history. Latest snapshot lives in `../current.md`.

---

## 2026-07-10 — Skill evaluation, first feedback pass + status bug fix
**Started:** ~14:00 PDT
**Closed:** 15:15 PDT
**Planned:** (none — first session on this evaluation)
**Actually did:** Activated the content-pipeline skill and oriented on the live DB. Established the true pipeline state (10 candidates: 8 pending, 2 picked-yes; one picked candidate "Ai is ruining business" is the in-flight article, mid-interview with 0 answers; "$62 yesterday" picked but not started). Logged two feedback items to `FEEDBACK-LOG.md`. Diagnosed and **fixed** a `status` reporting bug where picked-but-not-started candidates counted nowhere: added `writing.pipeline_counts()` and new `status` fields `picked_not_started_count` + `articles_by_status`; 99 tests pass. Set up the knowledge-system files: `current.md` (resume snapshot) + this log; kept `FEEDBACK-LOG.md` feedback-only.
**Left off:** `status` fix uncommitted. Feedback #1's startup numbered-menu/auto-jump prose still unimplemented. Two articles awaiting work.
**Key decisions:** FEEDBACK-LOG.md is feedback-only; resume state → current.md. Reporting gap treated as a real bug and fixed in code, not just logged.
**Session ref:** `claude --resume 1ed39b77-dfca-49e6-93b6-b50d24b44255`
