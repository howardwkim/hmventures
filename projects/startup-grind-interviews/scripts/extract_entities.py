"""Enrich silver interview records with deterministic named-entity extraction.

Runs spaCy NER over each interview's transcript_text and writes an `entities`
field back into interviews.jsonl (in place, like enrich_videos.py enriches
videos.jsonl). Pure programmatic pass, no LLM involved — intended as a
reusable, auditable fact index (people/orgs/money/dates/etc. actually present
in a transcript), independent of any downstream LLM extraction step.
"""

import json
from collections import Counter
from pathlib import Path

import spacy

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SILVER_DIR = DATA_DIR / "silver"

# Entity types worth keeping for fact-checking a transcript-derived claim.
# Excludes spaCy types that are noisy or irrelevant here (LANGUAGE, LAW,
# WORK_OF_ART, NORP, ORDINAL, QUANTITY, TIME, FAC, LOC, EVENT, PRODUCT).
KEEP_LABELS = {"PERSON", "ORG", "MONEY", "PERCENT", "DATE", "GPE", "CARDINAL"}


def load_jsonl(path: Path) -> list[dict]:
    with path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def extract_entities(nlp, text: str) -> list[dict]:
    doc = nlp(text)
    counts = Counter(
        (ent.text.strip(), ent.label_)
        for ent in doc.ents
        if ent.label_ in KEEP_LABELS and ent.text.strip()
    )
    return [
        {"text": text, "label": label, "count": count}
        for (text, label), count in sorted(counts.items(), key=lambda kv: -kv[1])
    ]


def main() -> None:
    nlp = spacy.load("en_core_web_sm")

    path = SILVER_DIR / "interviews.jsonl"
    records = load_jsonl(path)

    with path.open("w") as out:
        for record in records:
            record["entities"] = extract_entities(nlp, record["transcript_text"])
            out.write(json.dumps(record) + "\n")

    print(f"enriched {len(records)} interview records with entities -> {path}")


if __name__ == "__main__":
    main()
