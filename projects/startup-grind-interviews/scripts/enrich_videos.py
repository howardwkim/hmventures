"""Enrich videos.jsonl with YouTube title, channel, and publish date.

Uses only public, unauthenticated endpoints:
  - oEmbed (https://www.youtube.com/oembed) for title + channel name
  - the watch page's `datePublished` meta tag for the publish date

Already-enriched rows (have a "title" field) are skipped on re-run.
"""

import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "bronze"
VIDEOS_PATH = DATA_DIR / "videos.jsonl"

OEMBED_URL = "https://www.youtube.com/oembed"
WATCH_URL = "https://www.youtube.com/watch?v={video_id}"
DATE_PUBLISHED_RE = re.compile(
    r'itemprop="datePublished"\s+content="([^"]+)"'
)


def fetch_oembed(video_id: str) -> dict:
    resp = requests.get(
        OEMBED_URL,
        params={"url": WATCH_URL.format(video_id=video_id), "format": "json"},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    return {"title": data.get("title"), "channel": data.get("author_name")}


def fetch_published_date(video_id: str) -> str | None:
    resp = requests.get(
        WATCH_URL.format(video_id=video_id),
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15,
    )
    resp.raise_for_status()
    match = DATE_PUBLISHED_RE.search(resp.text)
    return match.group(1) if match else None


def enrich_one(video_id: str) -> dict:
    fields = fetch_oembed(video_id)
    fields["published_at"] = fetch_published_date(video_id)
    fields["enriched_at"] = datetime.now(timezone.utc).isoformat()
    return fields


def load_rows(path: Path) -> list[dict]:
    with path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def save_rows(path: Path, rows: list[dict]) -> None:
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="only enrich the first N not-yet-enriched videos (for sampling)",
    )
    args = parser.parse_args()

    rows = load_rows(VIDEOS_PATH)
    pending = [r for r in rows if "title" not in r]
    if args.limit is not None:
        pending = pending[: args.limit]

    print(f"{len(pending)} video(s) to enrich (of {len(rows)} total)")

    for row in pending:
        video_id = row["video_id"]
        try:
            fields = enrich_one(video_id)
        except Exception as exc:  # noqa: BLE001 - log and continue
            print(f"  FAILED {video_id}: {exc}")
            continue
        row.update(fields)
        print(f"  OK {video_id}: {fields['title']!r} ({fields['published_at']})")
        time.sleep(0.5)  # be polite to YouTube

    save_rows(VIDEOS_PATH, rows)
    print(f"wrote {VIDEOS_PATH}")


if __name__ == "__main__":
    main()
