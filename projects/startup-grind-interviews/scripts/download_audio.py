"""Bulk-download audio for every video in videos.jsonl.

Decoupled from transcription so downloads (fast, I/O-bound) don't block on
transcription (slow, compute-bound) - run this once, transcribe whenever.

Writes to data/bronze/audio/<video_id>.<ext>. Already-downloaded files are
skipped on re-run.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "bronze"
VIDEOS_PATH = DATA_DIR / "videos.jsonl"
AUDIO_DIR = DATA_DIR / "audio"


def load_video_ids(path: Path) -> list[str]:
    with path.open() as f:
        return [json.loads(line)["video_id"] for line in f if line.strip()]


def already_downloaded(video_id: str) -> bool:
    return any(AUDIO_DIR.glob(f"{video_id}.*"))


def download_one(video_id: str) -> None:
    out_template = str(AUDIO_DIR / f"{video_id}.%(ext)s")
    subprocess.run(
        [
            "uv", "run", "yt-dlp",
            "-f", "bestaudio",
            "-o", out_template,
            f"https://www.youtube.com/watch?v={video_id}",
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="only download the first N not-yet-downloaded videos (for sampling)",
    )
    args = parser.parse_args()

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    video_ids = load_video_ids(VIDEOS_PATH)
    pending = [vid for vid in video_ids if not already_downloaded(vid)]
    if args.limit is not None:
        pending = pending[: args.limit]

    print(f"{len(pending)} audio file(s) to download (of {len(video_ids)} total)")

    for video_id in pending:
        try:
            download_one(video_id)
        except subprocess.CalledProcessError as exc:
            print(f"  FAILED {video_id}: {exc.stderr[-300:]}", file=sys.stderr)
            continue
        path = next(AUDIO_DIR.glob(f"{video_id}.*"))
        size_mb = path.stat().st_size / 1_000_000
        print(f"  OK {video_id}: {path.name} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
