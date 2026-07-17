"""One-off script: tag the 17 already-extracted gold nuggets with two bools.

opportunity_signal: pain-point/insider-knowledge framed around customer-discovery
    thinking (would this reveal something buildable/solvable?). Excludes
    fundraising/financing/deal-and-equity-structure content broadly -- not just
    VC pitch/valuation mechanics, but anything about how a company is
    capitalized or how ownership is structured/documented: debt vs. equity
    choice, LLC vs. C-corp, revenue-share/profit-share models, cap tables,
    stock options, vesting, board-approval paperwork for equity. (Rule
    widened 2026-07-17 after a Howard review pass flagged financing/equity
    -structure nuggets -- LLC profit-share, SaaS Capital debt round, 83(b)
    election, undocumented option grants -- as false positives even though
    none of them were literally VC-pitch mechanics.)
small_business_focus: independent tag, not a filter.

Tags were hand-assigned by reading all 285 nuggets across the 17 files; this
script just applies them and writes the files back out.
"""
import json
from pathlib import Path

GOLD_DIR = Path(__file__).parent.parent / "data" / "gold"

# video_id -> list of (opportunity_signal, small_business_focus) in nugget order
TAGS = {
    "0qfQh_JnfLI": [
        (False, False), (False, False), (False, False), (False, False), (False, False),
        (False, False), (True, False), (False, False), (True, False), (False, False),
        (False, False), (True, False), (False, False), (False, False), (False, False),
        (False, False), (False, False), (False, False), (False, False),
    ],
    "985L7-Un8n8": [
        (False, False), (False, True), (False, True), (True, False), (True, False),
        (True, False), (True, False), (True, False), (False, False), (False, False),
        (False, False), (False, False), (False, False), (True, False), (True, False),
        (True, True), (True, True), (False, False),
    ],
    "FEzhDjxzEIs": [
        (False, False), (False, False), (False, False), (False, False), (True, False),
        (True, False), (False, False), (False, False), (False, False), (True, False),
        (True, False), (False, False), (False, False), (True, False), (False, False),
        (False, False),
    ],
    "Hs8OFY1DP4Y": [
        (True, False), (True, False), (True, False), (False, False), (True, False),
        (True, False), (True, False), (False, False), (False, False), (True, False),
        (False, False), (True, False), (True, False), (True, False), (False, False),
        (False, False), (False, False), (False, False), (True, False), (True, False),
        (True, False), (True, True), (False, False), (False, True),
    ],
    "Jl4wVX2G6t8": [
        (False, False), (False, False), (False, False), (False, False), (False, False),
        (False, False), (False, False), (True, False), (False, False), (False, False),
        (False, False), (False, False), (True, False), (False, False), (False, False),
        (True, False), (False, False), (False, False), (False, False),
    ],
    "KtauDMsH-mA": [
        (False, False), (False, False), (False, False), (True, False), (False, False),
        (False, False), (False, False), (False, False), (False, False), (False, False),
        (False, False), (True, False), (True, False), (True, False), (True, False),
        (True, False), (False, False), (False, False), (True, False), (False, False),
        (True, False), (True, False),
    ],
    "RZpxreTDC30": [
        (False, False), (False, False), (False, False), (False, False), (False, False),
        (False, False), (False, False), (False, False), (True, False), (False, False),
    ],
    "Z3GZ8UeSyug": [
        (True, True), (True, False), (True, False), (False, False), (False, False),
        (False, False), (False, False), (False, False), (True, False), (True, False),
        (True, False), (True, True), (True, False), (False, False), (False, False),
        (False, False), (True, False), (False, False), (False, False), (True, False),
    ],
    "bhmtuyF-faQ": [
        (False, False), (False, False), (False, True), (True, True), (True, True),
        (True, False), (True, True), (True, True), (True, True), (True, False),
        (True, False), (True, False), (True, True), (True, False), (True, False),
        (True, False), (False, False), (True, False), (False, True), (True, False),
    ],
    "eWYL_szT_aQ": [
        (True, True), (True, True), (True, True), (True, True), (True, False),
        (False, False), (True, True), (True, False), (False, False), (True, False),
        (True, True), (True, False), (False, False), (True, True), (False, False),
        (True, False),
    ],
    "j4Zk8yTdI2E": [
        (True, True), (False, False), (True, True), (False, False), (False, False),
        (True, False), (False, False), (False, False), (True, True), (False, False),
        (False, False), (False, True), (False, False), (False, False), (False, False),
        (True, False), (False, False), (True, False), (False, False), (False, False),
    ],
    "mYmpWRGVlc4": [
        (True, False), (True, True), (False, False), (False, False), (True, True),
        (False, False), (True, True), (True, False), (True, True), (False, False),
        (False, False), (False, False),
    ],
    "qenvDqBIA10": [
        (False, False), (True, False), (True, True), (False, False), (True, True),
        (True, False), (False, False), (False, False), (True, False), (False, False),
        (False, False), (False, False),
    ],
    "rELQXuZ5OKQ": [
        (True, False), (False, True), (False, False), (False, False), (True, True),
        (False, False), (True, False), (False, False), (True, False),
    ],
    "s1aH5xqyoXg": [
        (False, False), (False, True), (False, False), (False, False), (False, False),
        (False, False), (False, False), (True, False), (False, False), (False, False),
        (False, False), (False, False), (True, False), (False, False), (False, False),
        (False, False), (False, False), (False, False),
    ],
    "vbZ5b7KQcSM": [
        (True, False), (True, False), (True, False), (False, False), (True, False),
        (True, False), (False, False), (True, False), (True, False), (True, False),
        (True, False), (True, False), (True, False), (False, False), (False, False),
        (True, False),
    ],
    "ymhropvCctw": [
        (True, False), (True, True), (False, True), (True, False), (True, True),
        (False, False), (True, False), (False, False), (False, False), (False, False),
        (False, False), (True, True), (True, False), (True, True),
    ],
}


def main():
    total_opp = 0
    total_sb = 0
    total_nuggets = 0
    for video_id, tags in TAGS.items():
        path = GOLD_DIR / f"{video_id}.json"
        data = json.loads(path.read_text())
        nuggets = data["nuggets"]
        assert len(nuggets) == len(tags), (
            f"{video_id}: {len(nuggets)} nuggets vs {len(tags)} tags"
        )
        for nugget, (opp, sb) in zip(nuggets, tags):
            nugget["opportunity_signal"] = opp
            nugget["small_business_focus"] = sb
            total_nuggets += 1
            total_opp += int(opp)
            total_sb += int(sb)
        path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Tagged {total_nuggets} nuggets across {len(TAGS)} files")
    print(f"opportunity_signal=True: {total_opp}")
    print(f"small_business_focus=True: {total_sb}")


if __name__ == "__main__":
    main()
