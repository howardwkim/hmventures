---
name: meeting-ingest
description: Ingest a meeting into the global meetings/ store. Use whenever Howard drops in anything from a meeting — a Fathom share link or pasted Fathom transcript, a Zoom recording or VTT, a Google Meet recording or Gemini notes doc, or a raw audio/video file — or says "here's a meeting", "ingest this call", "process this transcript", "add this to meetings". Transcribes locally (whisper.cpp + diarization, turn level) when there's media, files everything under meetings/YYYY-MM-DD-slug/, and writes the summary.
---

# meeting-ingest

Every meeting, from every source, lands in one place: `meetings/` at the repo root.
Not per-project. One directory per meeting.

## The store

```
meetings/
  index.md                        one line per meeting; rebuilt, never hand-edited
  YYYY-MM-DD-slug/
    meta.json                     identity + pointers + re-fetch handles
    raw/                          vendor export, exactly as received
    transcript.json               OURS — turn level, speaker-labeled
    vendor-summary.md             THEIRS — labeled as vendor-generated
    summary.md                    OURS — the thing you actually read
```

**Slug:** `YYYY-MM-DD-` plus what you'd recognize scanning a directory listing.
`2026-07-10-miho-partner-meeting`, `2026-07-07-mike-call`.

**Git:** `meetings/` is gitignored *except* `summary.md`, `index.md`, `README.md`.
This repo is public. Transcripts and vendor exports are verbatim recordings of
private conversations and must never be committed. Do not "helpfully" add an
exception — if a summary itself contains something that shouldn't be public,
that's a reason to write the summary differently, not to loosen the rule.

## Ingest

### 1. Identify and create

Work out date, title, participants, source, duration. Create the directory.
Write `meta.json`: identity, `recording_url`, and a `refetch` block with enough
to pull the media again later (Drive file id, Zoom recording id, Fathom share id).

### 2. Put the raw thing in `raw/`

Whatever arrived, unmodified — pasted Fathom text, a Zoom `.vtt`, a Gemini notes
export. Never edit it. It's the provenance record.

### 3. Transcribe, if there's media

Whenever audio or video exists, make our own transcript rather than trusting the
vendor's. Local, free, no API.

```bash
python3 .claude/skills/meeting-ingest/scripts/transcribe.py <media> -o meetings/<slug> --stem transcript
```

Then add speaker labels:

```bash
.venv/bin/python .claude/skills/meeting-ingest/scripts/diarize.py meetings/<slug>/transcript.transcript.json --audio <media>
```

**Turn level is the default and is what you want.** A timestamp per speaker turn,
not per word. `--word-timings` exists only for cutting video clips to exact
boundaries; it inflates the file ~12x (measured: 1.47 MB vs 119 KB on a 51-minute
recording). Don't pass it as a matter of course. If a clip is needed later,
re-run — transcription is local and costs nothing.

Bias the spelling of names and jargon with `--prompt`:

```bash
--prompt "Howard Kim, Mike Grabham, MiHO, HM Ventures."
```

If there's no media — a pasted transcript with the audio long gone — say so in
`meta.json` (`"transcript": {"ours": false, "reason": "..."}`) rather than
pretending the vendor text is ours.

### 4. Keep the vendor's summary, separately

If the source produced its own AI summary (Fathom's, Gemini's, Zoom's), save it
as `vendor-summary.md` and label it as theirs at the top. Never merge it into
`summary.md`. We write our own regardless.

### 5. Write `summary.md`

The reason the store exists. Sections, in this order:

- **Takeaways** — what actually matters from this conversation
- **Decisions** — what got settled, and why
- **Next steps** — action items, with an owner on each
- **Ideas** — things raised worth returning to, not yet decided
- **Quotes** — lines worth reusing verbatim, with speaker and timestamp

Mark anything that looks like content material as a content candidate. The
content pipeline reads this store when asked; most meetings never become content,
so don't force it.

### 6. Update `index.md`

One line: date, title, participants, one-line outcome. Rebuilt from the
summaries — never maintained by hand.

## Source notes

| Source | What you get | How to pull it |
|---|---|---|
| **Fathom** | Share link, or pasted text `@M:SS - Speaker`. Already turn level. | **Scrape the share link with firecrawl** (below) — it returns the transcript *and* Fathom's AI summary. Paste also works. |
| **Google Meet** | MP4 in Drive, Gemini notes as a Doc | `google drive export <id> -o <path> -m text/plain` |
| **Zoom** | MP4 + M4A + VTT, cloud | **Cloud recordings expire by default** — pull the audio down promptly, don't rely on the link surviving |

### Pulling a Fathom share link

Fathom share pages are public but fully JS-rendered — `WebFetch` and the in-app
browser both fail on them. Firecrawl renders them:

```bash
cd ~/src/personal-ai/tools/firecrawl && uv run python firecrawl.py scrape "<share-url>"
```

Output goes to `raw/fathom.md` unmodified. It contains the transcript *and*
Fathom's own summary — split the summary into `vendor-summary.md` with a header
marking it vendor-generated, and leave `raw/` intact.

## Prerequisites

Verified present on this machine (2026-08-07): `whisper-cli`, `ffmpeg`, `ffprobe`,
`uv`, arm64, and the GGML model at the VoiceInk path `transcribe.py` defaults to.

`transcribe.py` is pure standard library — no venv needed. `diarize.py` runs from
this skill's `.venv/` (mlx-audio, installed 2026-08-07, Apple Silicon only); the
Sortformer model is cached locally after first use. Override binaries and model
with `VIDEO_WHISPER_BIN`, `VIDEO_FFMPEG_BIN`, `VIDEO_WHISPER_MODEL`.

Verified end to end 2026-08-07 on a 36-second two-speaker clip: all 10 segments
attributed correctly. **Diarization needs enough audio to separate voices** — on
a 5-second clip it collapsed both speakers into one. That's normal for any
diarizer and won't affect real meetings, but don't be alarmed by a short sample.

Mac-only by design. Howard runs ingest locally; nothing here is built to run on
Mike's Windows machine.

## Media

Video and audio never enter the repo. Archive audio outside it if you want a copy
independent of the vendor; record the path in `meta.json`. Video stays with the
vendor, referenced by URL plus whatever handle re-fetches it.
