#!/usr/bin/env python3
"""Timestamped transcription for meeting ingest.

Takes any local audio/video file and produces a canonical transcript at
**sentence/turn level** — a timestamp per segment, not per word.

Word-level timings are OFF BY DEFAULT and opt-in via `--word-timings`. They
inflate the file roughly 12x (measured: 1.47 MB vs 119 KB on a 51-minute
recording) and buy nothing unless you are cutting video clips to frame-accurate
boundaries. For reading, quoting, jumping to a moment, and speaker attribution,
segment-level is what you want. If you later need word timings for a clip, just
re-run with the flag — transcription is local and free.

Engine: whisper.cpp (`whisper-cli`, brew install whisper-cpp) + a local GGML
model. No Python dependencies — standard library only, plus the `ffmpeg` and
`whisper-cli` binaries on PATH. The default model is the VoiceInk-shipped
large-v3-turbo.

Pipeline:
  input (mp4/mov/mkv/mp3/m4a/wav/…)
    -> ffmpeg transcode to 16kHz mono PCM wav (what whisper.cpp wants)
    -> whisper-cli -ojf (full JSON: segments + per-token offsets/probabilities)
    -> normalize into transcript.json + .srt + .vtt + .txt

Canonical transcript.json schema (default, turn level):
  {
    "source": "<abs path to input>",
    "engine": "whisper.cpp",
    "model": "ggml-large-v3-turbo-q5_0",
    "language": "en",
    "duration_sec": 4.68,
    "word_timings": false,
    "text": "Most people are using AI backwards...",
    "segments": [{"id": 0, "start": 0.0, "end": 4.68, "text": "..."}],
    "words": []
  }

With `--word-timings`, each segment gains a "words" list and the top-level
flat "words" array is populated with {word, start, end, prob, seg} entries.

Times are seconds (float, 3dp). Run scripts/diarize.py afterwards to add a
"speaker" field to each segment.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Same default model the voice tool uses (VoiceInk ships it). Override with
# --model or VIDEO_WHISPER_MODEL.
DEFAULT_MODEL = Path(
    os.environ.get("VIDEO_WHISPER_MODEL")
    or (
        Path.home()
        / "Library/Application Support/com.prakashjoshipax.VoiceInk"
        / "WhisperModels/ggml-large-v3-turbo-q5_0.bin"
    )
)
WHISPER_BIN = os.environ.get("VIDEO_WHISPER_BIN", "whisper-cli")
FFMPEG_BIN = os.environ.get("VIDEO_FFMPEG_BIN", "ffmpeg")

# whisper.cpp emits special control tokens (e.g. "[_BEG_]", "[_TT_123]") in the
# token stream; they are not words.
SPECIAL_TOK = re.compile(r"^\[_.*\]$")


def die(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def check_deps() -> None:
    for binname in (FFMPEG_BIN, WHISPER_BIN):
        if shutil.which(binname) is None:
            die(f"required binary not found on PATH: {binname}")


def extract_audio(src: Path, dst_wav: Path) -> None:
    """Transcode any media to 16kHz mono PCM wav for whisper.cpp."""
    cmd = [
        FFMPEG_BIN, "-y", "-i", str(src),
        "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
        str(dst_wav), "-loglevel", "error",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not dst_wav.exists():
        die(f"ffmpeg failed:\n{r.stderr.strip()}")


def run_whisper(wav: Path, out_stem: Path, model: Path, language: str,
                threads: int, prompt: str | None) -> Path:
    """Run whisper-cli, writing <out_stem>.json/.srt/.vtt/.txt. Returns json path."""
    cmd = [
        WHISPER_BIN, "-m", str(model), "-f", str(wav),
        "-of", str(out_stem),
        "-ojf",            # full JSON: segments + per-token offsets + probs
        "-osrt", "-ovtt", "-otxt",
        "-l", language,
        "-t", str(threads),
        "-sow",            # split on word boundaries, not mid-token
    ]
    if prompt:
        cmd += ["--prompt", prompt]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        die(f"whisper-cli failed:\n{r.stderr.strip()}")
    json_path = out_stem.with_suffix(".json")
    if not json_path.exists():
        die(f"whisper-cli produced no JSON at {json_path}")
    return json_path


def _round(ms: int) -> float:
    return round(ms / 1000.0, 3)


def words_from_tokens(tokens: list[dict]) -> list[dict]:
    """Merge whisper sub-word tokens into words using the leading-space marker.

    whisper tokenizes into sub-words; a token whose text starts with a space
    begins a new word, continuation tokens (no leading space, e.g. sub-words and
    punctuation) extend the current word and its end time.
    """
    words: list[dict] = []
    for tok in tokens:
        text = tok.get("text", "")
        if SPECIAL_TOK.match(text.strip()):
            continue
        off = tok.get("offsets") or {}
        start, end = off.get("from"), off.get("to")
        if start is None or end is None:
            continue
        prob = tok.get("p")
        starts_word = text.startswith(" ") or not words
        clean = text.strip()
        if not clean:
            # whitespace-only token: extend previous word's end, skip
            if words:
                words[-1]["_end_ms"] = max(words[-1]["_end_ms"], end)
            continue
        if starts_word:
            words.append({
                "word": clean,
                "_start_ms": start,
                "_end_ms": end,
                "_probs": [prob] if prob is not None else [],
            })
        else:
            w = words[-1]
            w["word"] += clean
            w["_end_ms"] = max(w["_end_ms"], end)
            if prob is not None:
                w["_probs"].append(prob)
    # finalize
    out = []
    for w in words:
        probs = w.pop("_probs")
        out.append({
            "word": w["word"],
            "start": _round(w.pop("_start_ms")),
            "end": _round(w.pop("_end_ms")),
            "prob": round(sum(probs) / len(probs), 4) if probs else None,
        })
    return out


def normalize(
    raw: dict, src: Path, model: Path, language: str, word_timings: bool = False
) -> dict:
    """Normalize whisper's raw output. Segment level always; word level only
    when word_timings is set (see the module docstring for why it's off)."""
    segs_raw = raw.get("transcription", [])
    segments: list[dict] = []
    flat_words: list[dict] = []
    full_text_parts: list[str] = []
    duration = 0.0
    for i, s in enumerate(segs_raw):
        off = s.get("offsets") or {}
        start = _round(off.get("from", 0))
        end = _round(off.get("to", 0))
        duration = max(duration, end)
        text = (s.get("text") or "").strip()
        full_text_parts.append(text)
        seg = {"id": i, "start": start, "end": end, "text": text}
        if word_timings:
            seg_words = words_from_tokens(s.get("tokens", []))
            for w in seg_words:
                flat_words.append({**w, "seg": i})
            seg["words"] = seg_words
        segments.append(seg)
    return {
        "source": str(src.resolve()),
        "engine": "whisper.cpp",
        "model": model.stem,
        "language": language,
        "duration_sec": duration,
        "word_timings": word_timings,
        "text": " ".join(full_text_parts).strip(),
        "segments": segments,
        "words": flat_words,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Turn-level timestamped transcription")
    ap.add_argument("input", help="path to a local audio/video file")
    ap.add_argument("-o", "--out-dir", help="output directory (default: alongside input)")
    ap.add_argument("--stem", help="output basename (default: input filename stem)")
    ap.add_argument("--model", default=str(DEFAULT_MODEL), help="GGML whisper model path")
    ap.add_argument("-l", "--language", default="en", help="language ('auto' to detect)")
    ap.add_argument("-t", "--threads", type=int, default=8)
    ap.add_argument("--prompt", help="initial prompt to bias spelling (optional)")
    ap.add_argument("--keep-wav", action="store_true", help="keep the intermediate 16k wav")
    ap.add_argument(
        "--word-timings",
        action="store_true",
        help="also emit per-word timestamps (~12x larger; only needed for clip cutting)",
    )
    args = ap.parse_args()

    check_deps()
    src = Path(args.input).expanduser()
    if not src.exists():
        die(f"input not found: {src}")
    model = Path(args.model).expanduser()
    if not model.exists():
        die(f"whisper model not found: {model}\n(set --model or VIDEO_WHISPER_MODEL)")

    out_dir = Path(args.out_dir).expanduser() if args.out_dir else src.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = args.stem or src.stem
    out_stem = out_dir / stem

    with tempfile.TemporaryDirectory() as td:
        wav = (out_dir / f"{stem}.16k.wav") if args.keep_wav else Path(td) / "audio.wav"
        print(f"[1/3] extracting audio -> {wav.name}", file=sys.stderr)
        extract_audio(src, wav)
        print(f"[2/3] transcribing with {model.stem} ...", file=sys.stderr)
        json_path = run_whisper(wav, out_stem, model, args.language, args.threads, args.prompt)
        print("[3/3] normalizing transcript.json", file=sys.stderr)
        raw = json.loads(json_path.read_text())

    transcript = normalize(raw, src, model, args.language, args.word_timings)
    transcript_path = out_dir / f"{stem}.transcript.json"
    transcript_path.write_text(json.dumps(transcript, indent=2, ensure_ascii=False))

    # whisper-cli wrote <stem>.json (raw), .srt, .vtt, .txt next to out_stem.
    detail = (
        f"{len(transcript['words'])} words, " if args.word_timings else "turn level, "
    )
    print(
        f"\nwrote:\n"
        f"  {transcript_path}   ({detail}"
        f"{len(transcript['segments'])} segments, {transcript['duration_sec']}s)\n"
        f"  {out_stem}.srt\n  {out_stem}.vtt\n  {out_stem}.txt\n"
        f"  {out_stem}.json   (raw whisper full output)",
        file=sys.stderr,
    )
    print(str(transcript_path))  # stdout = the canonical artifact path


if __name__ == "__main__":
    main()
