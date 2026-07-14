"""Fetch YouTube transcripts for each video in videos.jsonl.

Writes data/bronze/transcripts/<video_id>.json. Videos with transcripts
disabled/unavailable are logged and skipped, not treated as fatal.
Already-fetched transcripts are skipped on re-run.
"""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "bronze"
VIDEOS_PATH = DATA_DIR / "videos.jsonl"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"


def load_video_ids(path: Path) -> list[str]:
    with path.open() as f:
        return [json.loads(line)["video_id"] for line in f if line.strip()]


def fetch_one(video_id: str) -> dict:
    api = YouTubeTranscriptApi()
    transcript = api.fetch(video_id)
    return {
        "video_id": video_id,
        "segments": [
            {"text": s.text, "start": s.start, "duration": s.duration}
            for s in transcript
        ],
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="only fetch the first N not-yet-fetched transcripts (for sampling)",
    )
    args = parser.parse_args()

    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    video_ids = load_video_ids(VIDEOS_PATH)
    pending = [
        vid for vid in video_ids if not (TRANSCRIPTS_DIR / f"{vid}.json").exists()
    ]
    if args.limit is not None:
        pending = pending[: args.limit]

    print(f"{len(pending)} transcript(s) to fetch (of {len(video_ids)} total)")

    for video_id in pending:
        try:
            data = fetch_one(video_id)
        except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as exc:
            print(f"  SKIP {video_id}: {exc.__class__.__name__}")
            continue
        except Exception as exc:  # noqa: BLE001 - log and continue
            print(f"  FAILED {video_id}: {exc}")
            continue

        out_path = TRANSCRIPTS_DIR / f"{video_id}.json"
        with out_path.open("w") as f:
            json.dump(data, f)
        print(f"  OK {video_id}: {len(data['segments'])} segments")
        time.sleep(0.5)  # be polite to YouTube


if __name__ == "__main__":
    main()
