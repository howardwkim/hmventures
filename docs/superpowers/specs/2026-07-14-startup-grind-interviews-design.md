# Startup Grind Interviews — Bronze Layer

## Purpose

Build a data pipeline that extracts Startup Grind interview data from
[michaelgrabham.com/startup-grind-interviews](https://www.michaelgrabham.com/startup-grind-interviews/)
into a bronze layer: raw interviewee bios, raw video links, YouTube metadata, and
transcripts. Silver and gold layers (cleaning, joining, matching videos to
interviewees) are out of scope for this spec — bronze only.

## Source page structure

The page (WordPress + Elementor) has three distinct sections. Findings from
inspecting the raw HTML directly:

1. **"The Interviewees"** (`#interviewees`) — 200+ profile cards: name, title,
   company, short bio, LinkedIn URL. No video link anywhere in this section.
2. **"Interviews"** — ~52 embedded YouTube videos (`youtu.be/<id>` in Elementor
   `data-settings` JSON). No caption, title, or name text anywhere near each
   embed — they're a plain sequential grid. There is no reliable way to tie a
   video to a specific interviewee from the page HTML alone.
3. **"LinkedIn LIVE"** (`#linkedin-live`) — paired thumbnails, most linking to
   LinkedIn feed posts, a few linking directly to YouTube. **Deferred** — not
   handled by this spec, may be picked up in a later pass.

Because sections 1 and 2 are unlinked in the source HTML, bronze captures them
as two separate, uncorrelated tables. Matching a video to an interviewee by
name (once we have YouTube titles) is a silver-layer concern, not bronze.

## Project layout

```
projects/startup-grind-interviews/
  pyproject.toml               # uv-managed
  scripts/
    scrape_page.py
    enrich_videos.py
    fetch_transcripts.py
  data/
    bronze/
      interviewees.jsonl
      videos.jsonl
      transcripts/
        <video_id>.json
```

Python, managed with `uv` (per standing tooling preference). No database —
JSONL files are the bronze store.

## Pipeline stages

### 1. `scrape_page.py`

Fetches the page once, parses with an HTML parser (BeautifulSoup), and writes
two files:

- `data/bronze/interviewees.jsonl` — one line per profile card in
  `#interviewees`:
  `{name, title, company, bio, linkedin_url, scraped_at}`
- `data/bronze/videos.jsonl` — one line per embedded video found in the
  "Interviews" section:
  `{video_id, youtube_url, position, scraped_at}`
  (`position` = index in page order, kept only as a debugging aid — not a
  join key to interviewees.)

Idempotent: re-running overwrites both files fresh from the current page
state (no incremental diffing needed at bronze scale — ~250 rows total).

### 2. `enrich_videos.py`

Reads `videos.jsonl`, and for each `video_id` not yet enriched:

- Calls the YouTube oEmbed endpoint (`https://www.youtube.com/oembed?url=...`,
  no API key) for `title` and `author_name` (channel).
- Fetches the video's watch page and extracts the `datePublished` /
  `uploadDate` meta tag for the publish date. (No official Data API key
  required for either step.)

Writes the enriched fields back into `videos.jsonl` (same file, one row per
video, now with `title`, `channel`, `published_at` added).

**Before running against all ~52 videos:** run against a small sample (e.g.
3-5 video IDs) first and manually confirm the title/date/channel come back
correctly, before enriching the full set.

### 3. `fetch_transcripts.py`

Reads `videos.jsonl`, and for each `video_id` without an existing transcript
file, pulls the transcript via `youtube-transcript-api` (no auth) and writes
it to `data/bronze/transcripts/<video_id>.json` (full transcript segments,
plus video_id and fetched_at).

Videos with transcripts disabled or unavailable are logged and skipped, not
treated as fatal errors.

**Before running against all videos:** run against the same small sample
first and manually confirm the transcript content looks right, before
fetching the full set.

## Error handling

- Network/parse failures on an individual video (enrichment or transcript)
  are logged with the video_id and skipped — they don't abort the run for
  the rest of the batch.
- Scripts are safe to re-run; already-enriched videos / already-fetched
  transcripts are skipped on subsequent runs (checked by presence of the
  enriched fields / transcript file).

## Testing

- Sample-first verification (3-5 videos) is a required manual step before
  each of the enrich and transcript scripts is run against the full set —
  called out explicitly per Howard's request, not just implied by "test it."
- No automated test suite planned for this bronze-layer scraping/fetching
  code; correctness is verified by inspecting sample output.

## Out of scope

- Silver/gold layers (cleaning, matching videos to interviewees, joins).
- The "LinkedIn LIVE" section.
- Any interviewee without a resolvable video (all 200+ are captured
  regardless — resolution to a video happens later, not here).
