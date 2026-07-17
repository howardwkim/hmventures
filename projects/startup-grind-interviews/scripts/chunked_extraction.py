#!/usr/bin/env python3
"""Chunked-overlap extraction test.

Splits a transcript into N overlapping chunks, runs the locked gold-extraction
prompt on each chunk via a local model server (llama-server, OpenAI-compatible
API), then dedupes the unioned nugget list with a second pass on the same
model. Chunk count and overlap percentage are tunable.
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
INTERVIEWS_PATH = REPO_ROOT / "data" / "silver" / "interviews.jsonl"
LOCKED_PROMPT_PATH = REPO_ROOT / "reference" / "gold-extraction-prompt.md"


def load_locked_prompt(path: Path = LOCKED_PROMPT_PATH) -> str:
    """Load the extraction prompt verbatim from a prompt file, with zero
    additions. Any chunking-specific framing lives only in how the chunk text
    is wrapped for the model, not in this prompt. The canonical locked prompt
    file starts with a "# Gold-layer extraction prompt" heading, which is
    stripped; candidate prompt files with no heading pass through unchanged."""
    text = path.read_text().strip()
    if text.startswith("#"):
        _, _, text = text.partition("\n\n")
    return text.strip()

DEDUP_PROMPT = """You are deduping a list of extracted "golden nuggets" from an interview
transcript. The list below was produced by running an extraction pass over
overlapping chunks of the same transcript, so some nuggets describe the exact
same underlying fact, mistake, or moment — extracted more than once because
they fell in an overlap zone between two chunks.

Merge duplicates: for each group of nuggets describing the same underlying
fact/moment/quote, keep exactly one — pick the best-phrased version, or merge
details if one version has something the other lacks. Do NOT merge nuggets
that are merely topically similar; only merge when they clearly describe the
SAME specific fact, mistake, or moment. Every distinct nugget must survive.

Respond with ONLY a JSON array of the deduped nugget objects (same three
fields: category, summary, quote), no other text."""


def load_interview(video_id: str) -> dict:
    with open(INTERVIEWS_PATH) as f:
        for line in f:
            d = json.loads(line)
            if d["video_id"] == video_id:
                return d
    raise ValueError(f"video_id {video_id!r} not found in {INTERVIEWS_PATH}")


def chunk_transcript(text: str, num_chunks: int, overlap_pct: float) -> list[str]:
    words = text.split()
    total = len(words)
    if num_chunks <= 1:
        return [text]
    overlap_frac = overlap_pct / 100
    chunk_size = total / (1 + (num_chunks - 1) * (1 - overlap_frac))
    step = chunk_size * (1 - overlap_frac)
    chunks = []
    for i in range(num_chunks):
        start = int(round(i * step))
        end = total if i == num_chunks - 1 else int(round(start + chunk_size))
        chunks.append(" ".join(words[start:end]))
    return chunks


CALL_TIMINGS = []


def call_chat(base_url: str, messages: list[dict], max_tokens: int = 6000) -> str:
    wall_start = time.time()
    resp = requests.post(
        f"{base_url}/v1/chat/completions",
        json={
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": max_tokens,
        },
        timeout=1800,
    )
    wall_elapsed = time.time() - wall_start
    resp.raise_for_status()
    data = resp.json()
    usage = data.get("usage", {})
    timings = data.get("timings", {})
    CALL_TIMINGS.append(
        {
            "wall_seconds": round(wall_elapsed, 1),
            "completion_tokens": usage.get("completion_tokens"),
            "predicted_ms": timings.get("predicted_ms"),
        }
    )
    return data["choices"][0]["message"]["content"]


def parse_json_array(content: str) -> list[dict]:
    content = content.strip()
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)
    start = content.find("[")
    end = content.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON array found in model output:\n{content[:500]}")
    return json.loads(content[start : end + 1])


def get_json_array(base_url: str, system: str, user: str, max_tokens: int = 6000, max_retries: int = 2) -> list[dict]:
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    last_err = None
    for attempt in range(max_retries + 1):
        content = call_chat(base_url, messages, max_tokens)
        try:
            return parse_json_array(content)
        except (ValueError, json.JSONDecodeError) as e:
            last_err = e
            print(f"    (JSON parse failed, attempt {attempt + 1}: {e})", file=sys.stderr)
            messages.append({"role": "assistant", "content": content})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"That was not valid JSON: {e}. Re-output the SAME nugget "
                        "list, fixed so it is valid JSON — a plain JSON array, no "
                        "markdown fences, no other text. Escape any double-quote "
                        "characters inside string values with a backslash."
                    ),
                }
            )
    raise ValueError(f"failed to get valid JSON after {max_retries} retries: {last_err}")


def extract_chunk(base_url: str, prompt: str, chunk_text: str, chunk_idx: int, max_tokens: int) -> list[dict]:
    user = f"TRANSCRIPT EXCERPT:\n\n{chunk_text}"
    nuggets = get_json_array(base_url, prompt, user, max_tokens=max_tokens)
    for n in nuggets:
        n["_chunk"] = chunk_idx
    return nuggets


def dedup_nuggets(base_url: str, nuggets: list[dict], max_tokens: int) -> list[dict]:
    if not nuggets:
        return []
    stripped = [{k: v for k, v in n.items() if k != "_chunk"} for n in nuggets]
    user = f"NUGGET LIST ({len(stripped)} items):\n\n{json.dumps(stripped, indent=2)}"
    return get_json_array(base_url, DEDUP_PROMPT, user, max_tokens=max_tokens)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--num-chunks", type=int, default=4)
    parser.add_argument("--overlap-pct", type=float, default=20)
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--prompt-file", default=str(LOCKED_PROMPT_PATH))
    parser.add_argument("--reasoning", action="store_true", help="record run as a reasoning-mode run (server must already be launched with --reasoning on); only affects max_tokens headroom and output metadata")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    extract_max_tokens = 9000 if args.reasoning else 6000
    dedup_max_tokens = 11000 if args.reasoning else 8000

    prompt = load_locked_prompt(Path(args.prompt_file))
    interview = load_interview(args.video_id)
    chunks = chunk_transcript(interview["transcript_text"], args.num_chunks, args.overlap_pct)
    print(
        f"[{args.video_id}] {interview['interviewee_name']}: "
        f"{len(interview['transcript_text'].split())} words -> "
        f"{args.num_chunks} chunks @ {args.overlap_pct}% overlap "
        f"(sizes: {[len(c.split()) for c in chunks]}), reasoning={args.reasoning}",
        file=sys.stderr,
    )

    run_start = time.time()
    raw_nuggets = []
    for i, chunk in enumerate(chunks):
        chunk_start = time.time()
        nuggets = extract_chunk(args.base_url, prompt, chunk, i, extract_max_tokens)
        print(f"  chunk {i}: {len(nuggets)} nuggets ({time.time() - chunk_start:.1f}s)", file=sys.stderr)
        raw_nuggets.extend(nuggets)

    print(f"  raw union: {len(raw_nuggets)} nuggets, deduping...", file=sys.stderr)
    dedup_start = time.time()
    final_nuggets = dedup_nuggets(args.base_url, raw_nuggets, dedup_max_tokens)
    print(f"  final: {len(final_nuggets)} nuggets ({time.time() - dedup_start:.1f}s)", file=sys.stderr)
    total_elapsed = time.time() - run_start
    print(f"  total elapsed: {total_elapsed:.1f}s", file=sys.stderr)

    out = {
        "video_id": args.video_id,
        "interviewee_name": interview["interviewee_name"],
        "interviewee_title": interview["interviewee_title"],
        "method": {
            "technique": "chunked-overlap",
            "model": "Qwen3.6-27B-Q4_K_M",
            "reasoning": args.reasoning,
            "num_chunks": args.num_chunks,
            "overlap_pct": args.overlap_pct,
            "prompt_file": Path(args.prompt_file).name,
        },
        "timing": {
            "total_elapsed_seconds": round(total_elapsed, 1),
            "per_call": CALL_TIMINGS,
        },
        "raw_nugget_count": len(raw_nuggets),
        "deduped_nugget_count": len(final_nuggets),
        "nuggets": final_nuggets,
    }

    out_path = Path(args.out) if args.out else REPO_ROOT / "data" / "experiments" / "chunked-qwen" / f"{args.video_id}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))
    print(f"wrote {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
