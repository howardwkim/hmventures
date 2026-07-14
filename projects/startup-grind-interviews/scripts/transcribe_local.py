"""Transcribe already-downloaded audio (data/bronze/audio/) via local whisper.cpp.

Run download_audio.py first. Decoupled so the fast download step doesn't
block on the slow transcription step - download once, transcribe whenever.

Reuses the existing local transcription tool at
~/src/personal-ai/.claude/skills/video-transcribe (whisper.cpp + VoiceInk's
large-v3-turbo GGML model, Metal-accelerated on Apple Silicon). Measured ~50x
realtime on this machine (M5 Pro) - a 72.5-minute video transcribes in ~90s.
No cloud cost. (The same skill also has a WhisperX engine - skip it: it's
CPU-only on Mac since CTranslate2 has no Metal backend, ~30x slower here.)

Writes data/bronze/transcripts/<video_id>.json in the same normalized schema
transcribe.py produces (word-level timing, plus video_id/source_url added).
Already-fetched transcripts are skipped on re-run.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "bronze"
AUDIO_DIR = DATA_DIR / "audio"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"

VIDEO_TRANSCRIBE_SKILL = Path(
    "~/src/personal-ai/.claude/skills/video-transcribe"
).expanduser()
TRANSCRIBE_SCRIPT = VIDEO_TRANSCRIBE_SKILL / "scripts" / "transcribe.py"


def transcribe(audio_path: Path, work_dir: Path, video_id: str) -> dict:
    subprocess.run(
        [
            sys.executable, str(TRANSCRIBE_SCRIPT),
            str(audio_path), "-o", str(work_dir), "--stem", video_id,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    transcript_path = work_dir / f"{video_id}.transcript.json"
    return json.loads(transcript_path.read_text())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="only transcribe the first N not-yet-transcribed videos (for sampling)",
    )
    args = parser.parse_args()

    if not TRANSCRIBE_SCRIPT.exists():
        print(f"error: transcribe.py not found at {TRANSCRIBE_SCRIPT}", file=sys.stderr)
        sys.exit(1)
    if shutil.which("whisper-cli") is None:
        print("error: whisper-cli not on PATH (brew install whisper-cpp)", file=sys.stderr)
        sys.exit(1)

    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    audio_files = sorted(AUDIO_DIR.glob("*.*"))
    pending = [
        f for f in audio_files
        if not (TRANSCRIPTS_DIR / f"{f.stem}.json").exists()
    ]
    if args.limit is not None:
        pending = pending[: args.limit]

    print(f"{len(pending)} transcript(s) to fetch via whisper.cpp (of {len(audio_files)} audio files)")

    for audio_path in pending:
        video_id = audio_path.stem
        print(f"  {video_id}: transcribing ...")
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            try:
                data = transcribe(audio_path, work_dir, video_id)
            except subprocess.CalledProcessError as exc:
                print(f"    FAILED {video_id}: {exc.stderr[-500:]}")
                continue
            except Exception as exc:  # noqa: BLE001 - log and continue
                print(f"    FAILED {video_id}: {exc}")
                continue

        data["video_id"] = video_id
        data["source_url"] = f"https://www.youtube.com/watch?v={video_id}"
        data["fetched_at"] = datetime.now(timezone.utc).isoformat()

        out_path = TRANSCRIPTS_DIR / f"{video_id}.json"
        out_path.write_text(json.dumps(data, ensure_ascii=False))
        print(
            f"    OK {video_id}: {len(data['words'])} words, "
            f"{data['duration_sec']}s"
        )


if __name__ == "__main__":
    main()
