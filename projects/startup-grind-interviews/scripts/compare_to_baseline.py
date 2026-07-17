#!/usr/bin/env python3
"""Judge a candidate nugget list against the Sonnet gold-baseline for the same
transcript, via a local model call (same comparison prompt used for the Sonnet
subagent judgment, so the two are apples-to-apples)."""

import argparse
import json
import re
import sys
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]

COMPARISON_PROMPT = """You are comparing two lists of "golden nugget" extractions from the
SAME interview transcript. BASELINE is the ground-truth reference list. CANDIDATE is the
list produced by a technique under test.

For each BASELINE nugget, decide whether CANDIDATE contains a nugget describing the SAME
underlying fact, mistake, moment, or belief-change — even if worded very differently. That
counts as a match. A near-miss that only captures part of the same moment still counts as
a match.

Then identify any CANDIDATE nuggets that do NOT match any BASELINE nugget — these are
net-new. For each net-new nugget, judge whether it looks like a genuine, real nugget (the
technique found something Sonnet's baseline missed) or looks spurious/hallucinated/wrong.

Respond with ONLY this JSON object, no other text:
{
  "baseline_count": <int>,
  "candidate_count": <int>,
  "matched_count": <int>,
  "recall_pct": <float, matched_count/baseline_count * 100>,
  "missed": [<baseline nugget summaries not matched, verbatim>],
  "net_new_genuine": [<candidate nugget summaries that are real finds beyond baseline>],
  "net_new_spurious": [<candidate nugget summaries that look wrong/hallucinated>]
}"""


def call_chat(base_url: str, messages: list[dict], max_tokens: int = 6000) -> str:
    resp = requests.post(
        f"{base_url}/v1/chat/completions",
        json={
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": max_tokens,
        },
        timeout=900,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def parse_json_object(content: str) -> dict:
    content = content.strip()
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)
    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON object found in model output:\n{content[:500]}")
    return json.loads(content[start : end + 1])


def get_json_object(base_url: str, system: str, user: str, max_tokens: int = 6000, max_retries: int = 2) -> dict:
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    last_err = None
    for attempt in range(max_retries + 1):
        content = call_chat(base_url, messages, max_tokens)
        try:
            return parse_json_object(content)
        except (ValueError, json.JSONDecodeError) as e:
            last_err = e
            print(f"(JSON parse failed, attempt {attempt + 1}: {e})", file=sys.stderr)
            messages.append({"role": "assistant", "content": content})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"That was not valid JSON: {e}. Re-output the SAME "
                        "object, fixed so it is valid JSON — a plain JSON "
                        "object, no markdown fences, no other text. Escape any "
                        "double-quote characters inside string values with a "
                        "backslash."
                    ),
                }
            )
    raise ValueError(f"failed to get valid JSON after {max_retries} retries: {last_err}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True, help="path to Sonnet gold JSON")
    parser.add_argument("--candidate", required=True, help="path to candidate JSON (chunked_extraction output)")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    baseline = json.loads(Path(args.baseline).read_text())
    candidate = json.loads(Path(args.candidate).read_text())

    baseline_nuggets = [{k: v for k, v in n.items() if k in ("category", "summary", "quote")} for n in baseline["nuggets"]]
    candidate_nuggets = [{k: v for k, v in n.items() if k in ("category", "summary", "quote")} for n in candidate["nuggets"]]

    user = (
        f"BASELINE ({len(baseline_nuggets)} nuggets):\n{json.dumps(baseline_nuggets, indent=2)}\n\n"
        f"CANDIDATE ({len(candidate_nuggets)} nuggets):\n{json.dumps(candidate_nuggets, indent=2)}"
    )
    result = get_json_object(args.base_url, COMPARISON_PROMPT, user)
    result["video_id"] = baseline.get("video_id")
    result["judge"] = "qwen3.6-27b"

    print(json.dumps(result, indent=2))
    if args.out:
        Path(args.out).write_text(json.dumps(result, indent=2))
        print(f"wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
