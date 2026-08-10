#!/usr/bin/env python3
"""Speaker diarization merge for the video-clipper pipeline (mlx-audio Sortformer).

Adds a `speaker` field to every word/segment of an existing transcript.json --
without re-transcribing. Runs mlx-audio's Sortformer diarization model on the
audio (GPU/MLX/Metal), then maps speaker turns onto the already-aligned words via
dominant-overlap assignment (which word-span has the most overlap with which
speaker turn).

Replaces the WhisperX+pyannote version (2026-08-03): no HuggingFace gated-model
login needed, no CPU-only bottleneck. Sortformer benchmarks lower diarization
error than pyannote's own pipeline; verified word-level agreement against the
prior pyannote output on a 2-min slice: 86.8% (disagreements clustered on short
back-channel interjections -- "yeah", "right" -- the known hard case for any
diarizer, not a systematic regression).

Prereqs: mlx-audio in the skill venv (uv pip install mlx-audio). Apple Silicon only.

Usage:
  .venv/bin/python scripts/diarize.py <transcript.json> [--audio PATH] [--num-speakers N]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_DIA_MODEL = "mlx-community/diar_sortformer_4spk-v1-fp32"


def die(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def _srt_ts(sec) -> str:
    sec = float(sec or 0.0)
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _dominant_speaker(start, end, diar_segments):
    """The speaker whose diarization turn overlaps [start, end] the most."""
    if start is None or end is None:
        return None
    best_spk, best_overlap = None, 0.0
    for d in diar_segments:
        overlap = min(end, d["end"]) - max(start, d["start"])
        if overlap > best_overlap:
            best_overlap, best_spk = overlap, d["speaker"]
    return None if best_spk is None else f"SPEAKER_{best_spk:02d}"


def assign_speakers(diar_segments, transcript: dict) -> set[str]:
    """Dominant-overlap speaker assignment.

    Segment level is the default and the only level that always runs — it's what
    a turn-level transcript needs, and what makes a meeting readable. Words are
    labeled too, but only when the transcript actually carries word timings
    (transcribe.py --word-timings); their absence is the normal case, not a
    degraded one.
    """
    speakers_seen: set[str] = set()
    for seg in transcript["segments"]:
        for w in seg.get("words", []):
            label = _dominant_speaker(w.get("start"), w.get("end"), diar_segments)
            if label:
                w["speaker"] = label
                speakers_seen.add(label)
        words = seg.get("words") or []
        if words and words[0].get("speaker"):
            # first word's speaker (matches the prior word-level convention)
            seg["speaker"] = words[0]["speaker"]
        else:
            label = _dominant_speaker(seg.get("start"), seg.get("end"), diar_segments)
            if label:
                seg["speaker"] = label
                speakers_seen.add(label)
    return speakers_seen


def main() -> None:
    ap = argparse.ArgumentParser(description="mlx-audio (Sortformer) speaker diarization merge")
    ap.add_argument("transcript", help="path to a *.transcript.json from transcribe.py")
    ap.add_argument("--audio", help="audio/video path (default: the transcript's source)")
    ap.add_argument("--model", default=DEFAULT_DIA_MODEL)
    ap.add_argument("--threshold", type=float, default=0.5, help="speaker activity threshold (0-1)")
    ap.add_argument("--min-duration", type=float, default=0.0, help="minimum segment duration (sec)")
    ap.add_argument("--merge-gap", type=float, default=0.0, help="max gap to merge consecutive segments (sec)")
    args = ap.parse_args()

    tpath = Path(args.transcript).expanduser()
    if not tpath.exists():
        die(f"transcript not found: {tpath}")
    transcript = json.loads(tpath.read_text())
    audio_path = args.audio or transcript.get("source")
    if not audio_path or not Path(audio_path).exists():
        die(f"audio not found: {audio_path} (pass --audio)")

    from mlx_audio.vad.utils import load_model

    print(f"[1/2] diarizing with {args.model} ...", file=sys.stderr)
    model = load_model(args.model)
    diar_out = model.generate(
        audio_path,
        threshold=args.threshold,
        min_duration=args.min_duration,
        merge_gap=args.merge_gap,
    )
    diar_segments = [{"start": s.start, "end": s.end, "speaker": s.speaker} for s in diar_out.segments]

    print(f"[2/2] assigning speakers to segments ...", file=sys.stderr)
    speakers = assign_speakers(diar_segments, transcript)

    flat = []
    for seg in transcript["segments"]:
        for w in seg.get("words", []):
            flat.append({**w, "seg": seg["id"]})
    transcript["words"] = flat
    transcript["speakers"] = sorted(speakers)
    transcript["diarized"] = True

    tpath.write_text(json.dumps(transcript, indent=2, ensure_ascii=False))

    srt = []
    for i, seg in enumerate(transcript["segments"], 1):
        spk = seg.get("speaker") or (seg.get("words") or [{}])[0].get("speaker") or ""
        tag = f"[{spk}] " if spk else ""
        srt.append(str(i))
        srt.append(f"{_srt_ts(seg.get('start'))} --> {_srt_ts(seg.get('end'))}")
        srt.append(f"{tag}{seg.get('text','').strip()}")
        srt.append("")
    srt_path = tpath.with_name(tpath.name.replace(".transcript.json", ".speakers.srt"))
    srt_path.write_text("\n".join(srt))

    n_segs = sum(1 for s in transcript["segments"] if s.get("speaker"))
    detail = f"{n_segs} segments" + (f", {len(flat)} words" if flat else "")
    print(
        f"\ndiarized: {len(speakers)} speaker(s) {sorted(speakers)}\n"
        f"  {tpath}   (speaker field added to {detail})\n"
        f"  {srt_path}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
