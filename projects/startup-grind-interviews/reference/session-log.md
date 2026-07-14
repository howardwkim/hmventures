## 2026-07-14 — Bronze layer built (scrape, enrich, transcribe)
**Started:** 2026-07-14 (session start)
**Closed:** 2026-07-14
**Planned:** N/A — first session for this project.
**Actually did:**
- Brainstormed and wrote a design spec for the bronze layer at
  `docs/superpowers/specs/2026-07-14-startup-grind-interviews-design.md` (hmventures repo).
- Inspected the real page HTML (michaelgrabham.com/startup-grind-interviews) and found it has
  three unlinked sections: "The Interviewees" (78 bios, no video link), "Interviews" (52 embedded
  YouTube videos, no name/caption attached), "LinkedIn LIVE" (deferred, not touched).
- Built `scripts/scrape_page.py` → `data/bronze/interviewees.jsonl` (78 rows) and
  `data/bronze/videos.jsonl` (52 rows).
- Built `scripts/enrich_videos.py` → filled in title/channel/published_at on all 52 videos via
  YouTube oEmbed + watch-page meta scrape (no API key).
- First transcript attempt used `youtube-transcript-api` (YouTube's own caption track) — got 31/52,
  16 had captions disabled, 5 hit a persistent IP block. Howard asked to check `personal-ai` for an
  existing transcript tool instead.
- Found `personal-ai/.claude/skills/video-transcribe`. Its default engine (WhisperX) turned out to
  be CPU-only on Mac (CTranslate2 has no Metal backend) — a 72.5-min video took 9.5+ min and didn't
  finish. Switched to that same skill's other engine, whisper.cpp (Metal-accelerated), which did the
  same video in ~90s (~50x realtime) on this M5 Pro.
- Split the work into `scripts/download_audio.py` (yt-dlp, all 52 files, ~2.8GB, fast) and
  `scripts/transcribe_local.py` (whisper.cpp via the personal-ai skill, reads from the audio dir).
  Ran both to completion in background: all 52 transcripts done, 669,413 words total, no failures.
- Deleted the audio files (no longer needed) and the old caption-based transcript backup — per
  Howard, transcripts are what matters, not the intermediate artifacts.
**Left off:** Bronze layer is complete and verified (52/52 videos scraped, enriched, and
transcribed; 78/78 interviewees captured). Nothing left mid-task.
**Key decisions:**
- Interviewees and videos are captured as two separate, unlinked bronze tables — the page HTML
  gives no way to tie a video to a specific interviewee. Matching by name (once titles are known)
  is explicitly a silver-layer job, not bronze.
- "LinkedIn LIVE" section is deferred entirely — not scraped this session.
- Transcript engine is whisper.cpp (via the personal-ai video-transcribe skill), not
  youtube-transcript-api and not WhisperX — chosen for reliability (no IP-block risk, works
  regardless of caption availability) and speed (Metal GPU on Apple Silicon).
- Audio files (`data/bronze/audio/`) are treated as disposable scratch, not a deliverable —
  gitignored, deleted once transcripts exist. Re-run `download_audio.py` + `transcribe_local.py` if
  ever needed again (both skip already-done work).
**Session ref:** `claude --resume d613338d-fad7-4841-a05a-1c56c95bff19`
