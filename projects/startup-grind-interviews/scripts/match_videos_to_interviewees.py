"""Match bronze videos to bronze interviewees by name, using title text.

Primary pass: does an interviewee's normalized name appear anywhere as a
substring of the normalized title? This is robust to prefix/suffix cruft
("Startup Grind Seattle Hosts ...", "... at Startup Grind Eastside", trailing
titles/companies) and to multiple people sharing one title (co-founder
pairs), without needing a pattern per title format. Mike Grabham is a
recurring host, never the interviewee, so he's excluded from candidacy.

Fallback pass (for titles with no exact substring hit, e.g. a name typo):
extract a candidate span around the likely name markers and fuzzy-match it
against the interviewee list.

Writes data/silver/video_interviewee_matches.jsonl (video_id, interviewee
name, match method) for everything resolved, and prints the remainder - both
unmatched videos and interviewees with no video - so what's left can be
resolved by hand or against transcript content.
"""

import json
import re
from difflib import SequenceMatcher
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"

HOST_NAMES = {"mike grabham"}
FUZZY_THRESHOLD = 0.72


def load_jsonl(path: Path) -> list[dict]:
    with path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def normalize(name: str) -> str:
    name = re.sub(r"[^a-z\s]", " ", name.lower())
    return re.sub(r"\s+", " ", name).strip()


def substring_matches(title: str, interviewees: list[dict]) -> list[dict]:
    title_norm = f" {normalize(title)} "
    hits = []
    for iv in interviewees:
        name_norm = normalize(iv["name"])
        if name_norm in HOST_NAMES or not name_norm:
            continue
        if f" {name_norm} " in title_norm:
            hits.append(iv)
    return hits


def extract_candidate(title: str) -> str | None:
    """Pull the most likely person-name substring out of a video title."""
    t = title.strip()

    m = re.search(r"\bhosts?\s+(.+)$", t, flags=re.IGNORECASE)
    if m:
        t = m.group(1)

    if "(" in t:
        t = t.split("(")[0]
    if "|" in t:
        t = t.split("|")[0]

    mw = re.search(r"\bw(?:ith)?/\s*|\bwith\s+", t, flags=re.IGNORECASE)
    if "grabham" in t.lower() and mw:
        left, right = t[: mw.start()], t[mw.end() :]
        t = right if "grabham" in left.lower() else left
        t = re.sub(r"^(with|w/)\s*", "", t, flags=re.IGNORECASE)

    return t.split(",")[0].strip()


def fuzzy_match(candidate: str, interviewees: list[dict]) -> tuple[dict | None, float]:
    if not candidate or normalize(candidate) in HOST_NAMES:
        return None, 0.0
    cand_norm = normalize(candidate)
    if not cand_norm:
        return None, 0.0
    best, best_score = None, 0.0
    for iv in interviewees:
        score = SequenceMatcher(None, cand_norm, normalize(iv["name"])).ratio()
        if score > best_score:
            best, best_score = iv, score
    return best, best_score


def main() -> None:
    videos = load_jsonl(BRONZE_DIR / "videos.jsonl")
    interviewees = load_jsonl(BRONZE_DIR / "interviewees.jsonl")

    matches = []
    unmatched_videos = []
    for v in videos:
        hits = substring_matches(v["title"], interviewees)
        if hits:
            for iv in hits:
                matches.append(
                    {
                        "video_id": v["video_id"],
                        "title": v["title"],
                        "interviewee_name": iv["name"],
                        "method": "substring",
                        "confidence": 1.0,
                    }
                )
            continue

        candidate = extract_candidate(v["title"])
        iv, score = fuzzy_match(candidate, interviewees)
        if iv and score >= FUZZY_THRESHOLD:
            matches.append(
                {
                    "video_id": v["video_id"],
                    "title": v["title"],
                    "interviewee_name": iv["name"],
                    "method": "fuzzy",
                    "candidate_extracted": candidate,
                    "confidence": round(score, 3),
                }
            )
        else:
            unmatched_videos.append(
                {
                    "video_id": v["video_id"],
                    "title": v["title"],
                    "candidate_extracted": candidate,
                    "best_guess": iv["name"] if iv else None,
                    "best_score": round(score, 3),
                }
            )

    matched_names = {m["interviewee_name"] for m in matches}
    unmatched_interviewees = [iv["name"] for iv in interviewees if iv["name"] not in matched_names]

    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    out_path = SILVER_DIR / "video_interviewee_matches.jsonl"
    with out_path.open("w") as f:
        for m in matches:
            f.write(json.dumps(m) + "\n")

    print(f"videos: {len(videos)}  interviewees: {len(interviewees)}")
    print(f"matched: {len(matches)} -> {out_path}")
    print(f"\nunmatched videos: {len(unmatched_videos)}")
    for u in unmatched_videos:
        print(
            f"  {u['video_id']}  {u['title']!r}\n"
            f"    candidate={u['candidate_extracted']!r}  best_guess={u['best_guess']!r} ({u['best_score']})"
        )
    print(f"\nunmatched interviewees (no video found): {len(unmatched_interviewees)}")
    for name in unmatched_interviewees:
        print(f"  {name}")


if __name__ == "__main__":
    main()
