**Last updated:** 2026-07-14
**Just completed:** Bronze layer built and verified — 78 interviewees, 52 videos (enriched with
title/channel/published_at), 52 transcripts (669,413 words, via local whisper.cpp/Metal).

**Next:**
- Now: Design the silver layer — decide how to match videos to interviewees (likely by fuzzy name
  match against video titles, e.g. "Jason Stoffer (Maveron) at Startup Grind Seattle"), then the
  gold layer for analysis. Start with brainstorming, same as this session did for bronze.
- On deck: Scrape the deferred "LinkedIn LIVE" section (out of scope so far — separate, smaller set
  of videos, some link to LinkedIn posts instead of YouTube).

**Key decisions:** Interviewees and videos are unlinked in bronze by design — matching is a silver
job. Transcript engine is whisper.cpp (Metal-accelerated, via the `personal-ai` `video-transcribe`
skill), not YouTube captions or WhisperX — see session log for why. Full spec:
`docs/superpowers/specs/2026-07-14-startup-grind-interviews-design.md` (hmventures repo root).
**Session ref:** `claude --resume d613338d-fad7-4841-a05a-1c56c95bff19`
