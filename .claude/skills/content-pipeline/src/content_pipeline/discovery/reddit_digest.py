import logging
import os
import sqlite3

from content_pipeline.models import Candidate

logger = logging.getLogger(__name__)


class RedditDigestSource:
    """Reads an external, pre-existing digest_posts SQLite database (Howard's
    Hermes Reddit-digest tool) and maps its rows into Candidate objects.

    This adapter does not own or manage that database — it only reads from a
    configured path. If the path doesn't exist, fetch() degrades gracefully
    (returns [] and logs) rather than raising, per the self-sufficiency
    principle: the pipeline must keep running without a live source.
    """

    def __init__(self, digest_db_path: str, since_date: str | None = None):
        self.digest_db_path = digest_db_path
        self.since_date = since_date

    def fetch(self) -> list[Candidate]:
        if not os.path.exists(self.digest_db_path):
            logger.info(
                "RedditDigestSource: digest DB not found at %s, returning []",
                self.digest_db_path,
            )
            return []

        query = (
            "SELECT post_id, subreddit, title, reddit_url, summary, score, "
            "num_comments, upvote_ratio, quality_score, why_care, digest_date "
            "FROM digest_posts"
        )
        params: tuple = ()
        if self.since_date is not None:
            query += " WHERE digest_date >= ?"
            params = (self.since_date,)

        conn = sqlite3.connect(self.digest_db_path)
        try:
            rows = conn.execute(query, params).fetchall()
        finally:
            conn.close()

        candidates = []
        for row in rows:
            (
                post_id,
                subreddit,
                title,
                reddit_url,
                summary,
                score,
                num_comments,
                upvote_ratio,
                quality_score,
                why_care,
                _digest_date,
            ) = row
            candidates.append(
                Candidate(
                    source="reddit",
                    source_ref=post_id,
                    title=title,
                    url=reddit_url,
                    summary=summary,
                    engagement={
                        "score": score,
                        "num_comments": num_comments,
                        "upvote_ratio": upvote_ratio,
                    },
                    topic_tags=[subreddit],
                    news_hook=why_care,
                    predicted_relevance=(
                        round(quality_score / 10.0, 10)
                        if quality_score is not None
                        else None
                    ),
                )
            )
        return candidates
