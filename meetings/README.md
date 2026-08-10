# meetings/

Every meeting, from every source, lands here. One directory per meeting.

```
YYYY-MM-DD-slug/
  meta.json           identity, participants, recording URL, re-fetch handles
  raw/                vendor export exactly as received
  transcript.json     ours — turn level, speaker-labeled
  vendor-summary.md   theirs, labeled as vendor-generated
  summary.md          ours — takeaways, decisions, next steps, ideas, quotes
```

**This directory is gitignored except `summary.md`, `index.md`, and this file.**
The repo is public; transcripts are verbatim recordings of private conversations.

To ingest a meeting, drop the link, transcript, or media file into a session —
the `meeting-ingest` skill handles the rest. Its `SKILL.md` is the spec.

Transcripts are ours, made locally with whisper.cpp plus diarization. **Turn
level** — one timestamp per speaker turn. Word-level timestamps are opt-in
(`--word-timings`) and only needed for cutting video clips.

Media never lives here. `meta.json` holds the pointer and enough to re-fetch.
