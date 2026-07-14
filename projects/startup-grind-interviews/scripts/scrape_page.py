"""Scrape michaelgrabham.com/startup-grind-interviews/ into bronze JSONL.

Writes two files:
  data/bronze/interviewees.jsonl - all profile cards in "The Interviewees"
  data/bronze/videos.jsonl       - all embedded YouTube videos in "Interviews"

The two are unrelated in the source HTML (no name/title is attached to a
video embed) - matching them is a silver-layer concern, not this script's.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://www.michaelgrabham.com/startup-grind-interviews/"
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "bronze"

YOUTUBE_URL_RE = re.compile(r"https:\\/\\/youtu\.be\\/([A-Za-z0-9_-]+)")


def fetch_page() -> str:
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    resp.raise_for_status()
    return resp.text


def _section_slice(html: str, start_marker: str, end_marker: str | None) -> str:
    start = html.find(start_marker)
    if start == -1:
        raise RuntimeError(f"could not find {start_marker!r} on page")
    end = html.find(end_marker, start) if end_marker else -1
    return html[start:] if end == -1 else html[start:end]


def scrape_interviewees(html: str, scraped_at: str) -> list[dict]:
    # bs4 can't be trusted to nest cards under #interviewees (the page's
    # div structure is malformed), so slice the raw HTML by section instead.
    section_html = _section_slice(html, 'id="interviewees"', 'id="linkedin-live"')
    soup = BeautifulSoup(section_html, "html.parser")

    rows = []
    for card in soup.select(".profile-card"):
        name_el = card.select_one(".profile-title")
        title_el = card.select_one(".profile-designation")
        linkedin_el = card.select_one('a[href*="linkedin.com"]')

        # Bio text lives in the hidden modal, not the visible card.
        bio = ""
        modal_link = card.select_one("a.ekit-team-popup[data-mfp-src]")
        if modal_link is not None:
            modal_id = modal_link["data-mfp-src"].lstrip("#")
            modal = soup.find(id=modal_id)
            if modal is not None:
                bio_el = modal.select_one(".ekit-team-modal-content")
                if bio_el is not None:
                    bio = bio_el.get_text(" ", strip=True)

        rows.append(
            {
                "name": name_el.get_text(strip=True) if name_el else None,
                "title": title_el.get_text(strip=True) if title_el else None,
                "bio": bio or None,
                "linkedin_url": linkedin_el["href"] if linkedin_el else None,
                "scraped_at": scraped_at,
            }
        )
    return rows


def scrape_videos(html: str, scraped_at: str) -> list[dict]:
    interviews_html = _section_slice(html, ">Interviews<", 'id="interviewees"')

    video_ids = YOUTUBE_URL_RE.findall(interviews_html)
    rows = []
    for position, video_id in enumerate(video_ids):
        rows.append(
            {
                "video_id": video_id,
                "youtube_url": f"https://www.youtube.com/watch?v={video_id}",
                "position": position,
                "scraped_at": scraped_at,
            }
        )
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def main() -> None:
    scraped_at = datetime.now(timezone.utc).isoformat()
    html = fetch_page()

    interviewees = scrape_interviewees(html, scraped_at)
    videos = scrape_videos(html, scraped_at)

    write_jsonl(DATA_DIR / "interviewees.jsonl", interviewees)
    write_jsonl(DATA_DIR / "videos.jsonl", videos)

    print(f"interviewees: {len(interviewees)} -> {DATA_DIR / 'interviewees.jsonl'}")
    print(f"videos: {len(videos)} -> {DATA_DIR / 'videos.jsonl'}")


if __name__ == "__main__":
    main()
