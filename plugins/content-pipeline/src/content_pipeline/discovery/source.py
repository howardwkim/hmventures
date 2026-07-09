import hashlib
import json
from datetime import datetime, timezone
from typing import Protocol

from content_pipeline import events
from content_pipeline.models import Candidate


class DiscoverySource(Protocol):
    def fetch(self) -> list[Candidate]: ...


def _now():
    return datetime.now(timezone.utc).isoformat()


def _candidate_id(candidate: Candidate) -> str:
    """Deterministic id derived from (source, source_ref), so re-ingesting the
    same ref always produces the same primary key and collides on INSERT OR IGNORE."""
    key = f"{candidate.source}:{candidate.source_ref}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def ingest(conn, candidates: list[Candidate]) -> int:
    """Insert new candidates, deduping on (source, source_ref). Returns the
    count of rows newly inserted. Idempotent: re-ingesting an already-present
    source_ref is a no-op for that candidate."""
    inserted = 0
    for candidate in candidates:
        candidate_id = _candidate_id(candidate)
        cur = conn.execute(
            """INSERT OR IGNORE INTO candidates
               (id, source, source_ref, title, url, summary, engagement_json,
                topic_tags, emotional_driver, news_hook, predicted_relevance,
                status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)""",
            (
                candidate_id,
                candidate.source,
                candidate.source_ref,
                candidate.title,
                candidate.url,
                candidate.summary,
                json.dumps(candidate.engagement),
                json.dumps(candidate.topic_tags),
                candidate.emotional_driver,
                candidate.news_hook,
                candidate.predicted_relevance,
                _now(),
            ),
        )
        conn.commit()
        if cur.rowcount > 0:
            inserted += 1
            events.append(
                conn,
                "candidate_ingested",
                {"source": candidate.source, "source_ref": candidate.source_ref},
                candidate_id=candidate_id,
            )
    return inserted
