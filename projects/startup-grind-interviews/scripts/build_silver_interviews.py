"""Build the silver-layer interview records gold-layer extraction reads from.

Joins video_interviewee_matches.jsonl against bronze videos, interviewees,
and transcripts to produce one denormalized record per matched video:
interviewee identity + video metadata + full transcript text, so gold
doesn't have to re-join three bronze sources on every extraction pass.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"


def load_jsonl(path: Path) -> list[dict]:
    with path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def index_by(records: list[dict], key: str) -> dict:
    return {r[key]: r for r in records}


def main() -> None:
    matches = load_jsonl(SILVER_DIR / "video_interviewee_matches.jsonl")
    videos_by_id = index_by(load_jsonl(BRONZE_DIR / "videos.jsonl"), "video_id")
    interviewees_by_name = index_by(load_jsonl(BRONZE_DIR / "interviewees.jsonl"), "name")

    out_path = SILVER_DIR / "interviews.jsonl"
    written, skipped = 0, []
    with out_path.open("w") as out:
        for m in matches:
            video = videos_by_id.get(m["video_id"])
            interviewee = interviewees_by_name.get(m["interviewee_name"])
            transcript_path = BRONZE_DIR / "transcripts" / f"{m['video_id']}.json"
            if not video or not interviewee or not transcript_path.exists():
                skipped.append(m["video_id"])
                continue
            transcript = json.loads(transcript_path.read_text())

            record = {
                "video_id": m["video_id"],
                "interviewee_name": interviewee["name"],
                "interviewee_title": interviewee.get("title"),
                "interviewee_bio": interviewee.get("bio"),
                "interviewee_linkedin_url": interviewee.get("linkedin_url"),
                "video_title": video["title"],
                "youtube_url": video["youtube_url"],
                "published_at": video["published_at"],
                "match_method": m["method"],
                "match_confidence": m["confidence"],
                "duration_sec": transcript.get("duration_sec"),
                "transcript_text": transcript["text"],
            }
            out.write(json.dumps(record) + "\n")
            written += 1

    print(f"wrote {written} interview records -> {out_path}")
    if skipped:
        print(f"skipped {len(skipped)} matches (missing video/interviewee/transcript): {skipped}")


if __name__ == "__main__":
    main()
