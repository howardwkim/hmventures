#!/usr/bin/env python3
"""Aggregate founder-wedge tags from data/wedge/*.json into a ranked review doc.

Reads the per-interview wedge files produced by the tagging subagents, keeps only
founder_wedge=true nuggets, ranks them by wedge_score (desc), and writes
data/wedge_review.md plus prints summary stats (total judged, passed, trimmed).
"""
import json
import glob
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEDGE_DIR = os.path.join(ROOT, "data", "wedge")
OUT = os.path.join(ROOT, "data", "wedge_review.md")

KIND_LABEL = {"automate": "Automate/AI", "pain": "Sharp pain", "both": "Both"}


def main():
    files = sorted(glob.glob(os.path.join(WEDGE_DIR, "*.json")))
    total = 0
    passes = []  # (score, kind, interviewee, category, note, summary)
    per_person = {}  # name -> [judged, passed]
    for f in files:
        d = json.load(open(f))
        name = d.get("interviewee_name", "?")
        title = d.get("interviewee_title", "")
        for n in d.get("nuggets", []):
            total += 1
            per_person.setdefault(name, [0, 0, title])
            per_person[name][0] += 1
            if n.get("founder_wedge"):
                per_person[name][1] += 1
                passes.append((
                    n.get("wedge_score") or 0,
                    n.get("wedge_kind") or "?",
                    name, title,
                    n.get("category", ""),
                    n.get("wedge_note", ""),
                    n.get("summary", ""),
                ))

    passes.sort(key=lambda x: (-x[0], x[2]))
    kept = len(passes)
    trimmed = total - kept
    by_score = {}
    by_kind = {}
    for p in passes:
        by_score[p[0]] = by_score.get(p[0], 0) + 1
        by_kind[p[1]] = by_kind.get(p[1], 0) + 1

    lines = []
    lines.append("# Founder-Wedge Filter — Ranked Review")
    lines.append("")
    lines.append(f"Rubric: reference/founder-wedge-rubric-v1.md")
    lines.append("")
    lines.append(f"**{kept} of {total} nuggets kept** ({trimmed} trimmed, "
                 f"{100*kept//total if total else 0}% pass rate).")
    lines.append("")
    lines.append("Score distribution: " +
                 ", ".join(f"{s}★×{by_score[s]}" for s in sorted(by_score, reverse=True)))
    lines.append("Kind: " + ", ".join(f"{KIND_LABEL.get(k,k)}×{v}" for k, v in
                 sorted(by_kind.items(), key=lambda x: -x[1])))
    lines.append("")

    # Ranked table
    for score in sorted({p[0] for p in passes}, reverse=True):
        group = [p for p in passes if p[0] == score]
        lines.append(f"## {score}★ — {len(group)} nuggets")
        lines.append("")
        for _, kind, name, title, cat, note, summ in group:
            klabel = KIND_LABEL.get(kind, kind)
            lines.append(f"- **[{klabel}] {name}** ({title}) — _{cat}_")
            if note:
                lines.append(f"  - Wedge: {note}")
            lines.append(f"  - {summ}")
        lines.append("")

    # Per-person density
    lines.append("## Wedge density by interviewee")
    lines.append("")
    lines.append("| Interviewee | Passed / Judged |")
    lines.append("|---|---|")
    for name in sorted(per_person, key=lambda n: -per_person[n][1]):
        j, p, _t = per_person[name]
        lines.append(f"| {name} | {p} / {j} |")
    lines.append("")

    open(OUT, "w").write("\n".join(lines))
    print(f"Total judged: {total}")
    print(f"Kept (founder_wedge=true): {kept}")
    print(f"Trimmed: {trimmed}")
    print(f"By score: {dict(sorted(by_score.items(), reverse=True))}")
    print(f"By kind: {by_kind}")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
