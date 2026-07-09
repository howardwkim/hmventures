import sqlite3
from content_pipeline.discovery.reddit_digest import RedditDigestSource


def _make_digest(path):
    c = sqlite3.connect(path)
    c.execute("""CREATE TABLE digest_posts (post_id TEXT PRIMARY KEY, subreddit TEXT,
      title TEXT, reddit_url TEXT, summary TEXT, score INTEGER, num_comments INTEGER,
      upvote_ratio REAL, quality_score REAL, why_care TEXT, digest_date TEXT)""")
    c.execute("INSERT INTO digest_posts VALUES (?,?,?,?,?,?,?,?,?,?,?)",
      ("p1","ClaudeCode","Title","http://r","summary",600,64,0.95,9.2,"matters","2026-07-09"))
    c.commit(); c.close()


def test_fetch_maps_rows_to_candidates(tmp_path):
    p = str(tmp_path/"digest.sqlite"); _make_digest(p)
    cands = RedditDigestSource(p).fetch()
    assert len(cands) == 1
    c = cands[0]
    assert c.source == "reddit" and c.source_ref == "p1"
    assert c.predicted_relevance == 0.92
    assert c.engagement["score"] == 600 and c.topic_tags == ["ClaudeCode"]


def test_missing_db_returns_empty(tmp_path):
    assert RedditDigestSource(str(tmp_path/"nope.sqlite")).fetch() == []


def _make_digest_multi(path, rows):
    """rows: list of (post_id, digest_date) tuples; other columns are filled
    with fixed placeholder values matching _make_digest's shape."""
    c = sqlite3.connect(path)
    c.execute("""CREATE TABLE digest_posts (post_id TEXT PRIMARY KEY, subreddit TEXT,
      title TEXT, reddit_url TEXT, summary TEXT, score INTEGER, num_comments INTEGER,
      upvote_ratio REAL, quality_score REAL, why_care TEXT, digest_date TEXT)""")
    for post_id, digest_date in rows:
        c.execute("INSERT INTO digest_posts VALUES (?,?,?,?,?,?,?,?,?,?,?)",
          (post_id, "ClaudeCode", "Title", "http://r", "summary", 600, 64, 0.95, 9.2,
           "matters", digest_date))
    c.commit(); c.close()


def test_since_date_filters_old_rows(tmp_path):
    p = str(tmp_path/"digest.sqlite")
    _make_digest_multi(p, [("old", "2026-07-01"), ("new", "2026-07-09")])
    cands = RedditDigestSource(p, since_date="2026-07-05").fetch()
    assert len(cands) == 1
    assert cands[0].source_ref == "new"
