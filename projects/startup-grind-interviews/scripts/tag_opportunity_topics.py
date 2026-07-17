"""One-off script: tag the 124 opportunity_signal=true nuggets with a topic bucket
and a strength tier.

Rubric: reference/opportunity-topic-taxonomy-v1.md (locked 2026-07-17). Topics are one
of the 8 buckets there; tiers are A (live gap) / B (replicable practice) / C
(color/anecdote).

Tags were hand-assigned by reading all 124 opportunity_signal=true nuggets across the
17 already-extracted files; this script just applies them and writes the files back
out. Only nuggets with opportunity_signal=true get the two new fields -- everything
else is left untouched.
"""
import json
from pathlib import Path

GOLD_DIR = Path(__file__).parent.parent / "data" / "gold"

# video_id -> list of (topic, tier) or None, one entry per nugget in file order.
# None means opportunity_signal is False for that nugget (skipped).
TAGS = {
    "0qfQh_JnfLI": [
        None, None, None, None, None, None,
        ("leadership-founder", "B"), None,
        ("leadership-founder", "B"), None, None,
        ("hiring-people", "B"), None, None, None, None, None, None, None,
    ],
    "985L7-Un8n8": [
        None, None, None,
        ("leadership-founder", "B"),
        ("market-timing", "B"),
        ("product-mvp", "B"),
        ("growth-marketing", "A"),
        ("growth-marketing", "A"),
        None, None, None, None, None,
        ("growth-marketing", "B"),
        ("growth-marketing", "B"),
        ("customer-discovery", "A"),
        ("growth-marketing", "B"),
        None,
    ],
    "FEzhDjxzEIs": [
        None, None, None, None,
        ("ops-failure", "A"),
        ("market-timing", "A"),
        None, None, None,
        ("customer-discovery", "B"),
        ("growth-marketing", "B"),
        None, None,
        ("product-mvp", "A"),
        None, None,
    ],
    "Hs8OFY1DP4Y": [
        ("product-mvp", "A"),
        ("growth-marketing", "A"),
        ("pricing-economics", "A"),
        None,
        ("hiring-people", "A"),
        ("hiring-people", "B"),
        ("leadership-founder", "A"),
        None, None,
        ("growth-marketing", "B"),
        None,
        ("leadership-founder", "B"),
        ("hiring-people", "B"),
        ("product-mvp", "A"),
        None, None, None, None,
        ("growth-marketing", "C"),
        ("growth-marketing", "A"),
        ("growth-marketing", "B"),
        ("growth-marketing", "C"),
        None, None,
    ],
    "Jl4wVX2G6t8": [
        None, None, None, None, None, None, None,
        ("market-timing", "A"),
        None, None, None, None,
        ("leadership-founder", "B"),
        None, None,
        ("leadership-founder", "B"),
        None, None, None,
    ],
    "KtauDMsH-mA": [
        None, None, None,
        ("leadership-founder", "B"),
        None, None, None, None, None, None, None,
        ("hiring-people", "A"),
        ("leadership-founder", "B"),
        ("customer-discovery", "A"),
        ("growth-marketing", "A"),
        ("customer-discovery", "B"),
        None, None,
        ("leadership-founder", "B"),
        None,
        ("hiring-people", "C"),
        ("customer-discovery", "B"),
    ],
    "RZpxreTDC30": [
        None, None, None, None, None, None, None, None,
        ("ops-failure", "B"),
        None,
    ],
    "Z3GZ8UeSyug": [
        ("customer-discovery", "A"),
        ("customer-discovery", "A"),
        ("customer-discovery", "A"),
        None, None, None, None, None,
        ("leadership-founder", "B"),
        ("leadership-founder", "B"),
        ("product-mvp", "A"),
        ("product-mvp", "A"),
        ("product-mvp", "A"),
        None, None, None,
        ("hiring-people", "B"),
        None, None,
        ("customer-discovery", "A"),
    ],
    "bhmtuyF-faQ": [
        None, None, None,
        ("customer-discovery", "A"),
        ("customer-discovery", "A"),
        ("leadership-founder", "B"),
        ("customer-discovery", "A"),
        ("pricing-economics", "A"),
        ("pricing-economics", "A"),
        ("hiring-people", "A"),
        ("hiring-people", "B"),
        ("hiring-people", "A"),
        ("growth-marketing", "B"),
        ("product-mvp", "A"),
        ("growth-marketing", "A"),
        ("market-timing", "A"),
        None,
        ("pricing-economics", "A"),
        None,
        ("hiring-people", "B"),
    ],
    "eWYL_szT_aQ": [
        ("customer-discovery", "A"),
        ("customer-discovery", "A"),
        ("customer-discovery", "A"),
        ("product-mvp", "A"),
        ("product-mvp", "A"),
        None,
        ("customer-discovery", "A"),
        ("customer-discovery", "B"),
        None,
        ("hiring-people", "B"),
        ("pricing-economics", "B"),
        ("leadership-founder", "B"),
        None,
        ("ops-failure", "A"),
        None,
        ("market-timing", "B"),
    ],
    "j4Zk8yTdI2E": [
        ("growth-marketing", "A"),
        None,
        ("product-mvp", "A"),
        None, None,
        ("customer-discovery", "A"),
        None, None,
        ("ops-failure", "B"),
        None, None, None, None, None, None,
        ("leadership-founder", "B"),
        None,
        ("hiring-people", "B"),
        None, None,
    ],
    "mYmpWRGVlc4": [
        ("customer-discovery", "A"),
        ("growth-marketing", "A"),
        None, None,
        ("hiring-people", "B"),
        None,
        ("pricing-economics", "B"),
        ("hiring-people", "B"),
        ("hiring-people", "B"),
        None, None, None,
    ],
    "qenvDqBIA10": [
        None,
        ("growth-marketing", "A"),
        ("growth-marketing", "A"),
        None,
        ("growth-marketing", "B"),
        ("growth-marketing", "B"),
        None, None,
        ("leadership-founder", "A"),
        None, None, None,
    ],
    "rELQXuZ5OKQ": [
        ("leadership-founder", "A"),
        None, None, None,
        ("pricing-economics", "A"),
        None,
        ("customer-discovery", "A"),
        None,
        ("hiring-people", "B"),
    ],
    "s1aH5xqyoXg": [
        None, None, None, None, None, None, None,
        ("ops-failure", "B"),
        None, None, None, None,
        ("hiring-people", "A"),
        None, None, None, None, None,
    ],
    "vbZ5b7KQcSM": [
        ("customer-discovery", "A"),
        ("customer-discovery", "A"),
        ("customer-discovery", "B"),
        None,
        ("leadership-founder", "A"),
        ("leadership-founder", "B"),
        None,
        ("product-mvp", "A"),
        ("market-timing", "B"),
        ("leadership-founder", "B"),
        ("market-timing", "A"),
        ("leadership-founder", "A"),
        ("market-timing", "A"),
        None, None,
        ("leadership-founder", "B"),
    ],
    "ymhropvCctw": [
        ("leadership-founder", "B"),
        ("leadership-founder", "A"),
        None,
        ("hiring-people", "A"),
        ("hiring-people", "B"),
        None,
        ("ops-failure", "A"),
        None, None, None, None,
        ("growth-marketing", "B"),
        ("product-mvp", "A"),
        ("leadership-founder", "B"),
    ],
}

VALID_TOPICS = {
    "customer-discovery", "product-mvp", "growth-marketing", "hiring-people",
    "pricing-economics", "ops-failure", "leadership-founder", "market-timing",
}
VALID_TIERS = {"A", "B", "C"}


def main():
    total_tagged = 0
    tier_counts = {"A": 0, "B": 0, "C": 0}
    topic_counts = {t: 0 for t in VALID_TOPICS}

    for video_id, tags in TAGS.items():
        path = GOLD_DIR / f"{video_id}.json"
        data = json.loads(path.read_text())
        nuggets = data["nuggets"]
        assert len(nuggets) == len(tags), (
            f"{video_id}: {len(nuggets)} nuggets vs {len(tags)} tags"
        )
        for nugget, tag in zip(nuggets, tags):
            is_opp = nugget.get("opportunity_signal", False)
            assert is_opp == (tag is not None), (
                f"{video_id}: opportunity_signal={is_opp} but tag={tag}"
            )
            if tag is None:
                continue
            topic, tier = tag
            assert topic in VALID_TOPICS, f"{video_id}: bad topic {topic!r}"
            assert tier in VALID_TIERS, f"{video_id}: bad tier {tier!r}"
            nugget["opportunity_topic"] = topic
            nugget["signal_strength"] = tier
            total_tagged += 1
            tier_counts[tier] += 1
            topic_counts[topic] += 1
        path.write_text(json.dumps(data, indent=2) + "\n")

    print(f"Tagged {total_tagged} opportunity_signal nuggets across {len(TAGS)} files")
    print(f"Tiers: {tier_counts}")
    print("Topics:")
    for topic, count in sorted(topic_counts.items(), key=lambda x: -x[1]):
        print(f"  {count:3d}  {topic}")


if __name__ == "__main__":
    main()
