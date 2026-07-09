import pytest

from content_pipeline.learning import health


def _approve_article(conn, article_id, approved_at):
    conn.execute(
        "INSERT INTO articles (id, status, created_at, approved_at) "
        "VALUES (?, 'approved', ?, ?)",
        (article_id, approved_at, approved_at),
    )
    conn.commit()


def _add_edit_round(conn, article_id, round_number, edit_size):
    conn.execute(
        "INSERT INTO edit_rounds "
        "(article_id, round, operator_feedback, what_changed, edit_size, created_at) "
        "VALUES (?, ?, 'fb', 'changed', ?, '2026-01-01T00:00:00+00:00')",
        (article_id, round_number, edit_size),
    )
    conn.commit()


def _seed_article(conn, article_id, approved_at, edit_sizes):
    """Approve one article and give it edit_rounds with the given
    per-round edit_size values (round count is implied by len(edit_sizes))."""
    _approve_article(conn, article_id, approved_at)
    for i, size in enumerate(edit_sizes, start=1):
        _add_edit_round(conn, article_id, i, size)


def test_edit_effort_trend_rising_pattern_is_spiking_and_blocks_promotion(conn):
    # window=4, 2+2 split: prior two articles have small, single-round
    # edits; recent two articles have much larger, multi-round edits.
    _seed_article(conn, "a1", "2026-01-01T00:00:00+00:00", [10])
    _seed_article(conn, "a2", "2026-01-02T00:00:00+00:00", [10])
    _seed_article(conn, "a3", "2026-01-03T00:00:00+00:00", [200, 200])
    _seed_article(conn, "a4", "2026-01-04T00:00:00+00:00", [200, 200])

    trend = health.edit_effort_trend(conn, window=4)

    assert trend["prior_mean"] == pytest.approx(10 + 1)  # sum(edit_size) + round_count
    assert trend["recent_mean"] == pytest.approx(400 + 2)
    assert trend["rising"] is True
    assert trend["spiking"] is True

    assert health.promotion_allowed(conn) is False
    assert health.nudge(conn) is not None
    assert "review the writing rules" in health.nudge(conn)


def test_edit_effort_trend_flat_pattern_allows_promotion_no_nudge(conn):
    # window=4, 2+2 split: all four articles have the same effort profile.
    _seed_article(conn, "a1", "2026-01-01T00:00:00+00:00", [10])
    _seed_article(conn, "a2", "2026-01-02T00:00:00+00:00", [10])
    _seed_article(conn, "a3", "2026-01-03T00:00:00+00:00", [10])
    _seed_article(conn, "a4", "2026-01-04T00:00:00+00:00", [10])

    trend = health.edit_effort_trend(conn, window=4)

    assert trend["prior_mean"] == pytest.approx(11)
    assert trend["recent_mean"] == pytest.approx(11)
    assert trend["rising"] is False
    assert trend["spiking"] is False

    assert health.promotion_allowed(conn) is True
    assert health.nudge(conn) is None


def test_edit_effort_trend_uses_only_approved_articles_ordered_by_approved_at(conn):
    # An abandoned article should be excluded even if it has edit_rounds.
    _seed_article(conn, "a1", "2026-01-01T00:00:00+00:00", [10])
    _seed_article(conn, "a2", "2026-01-02T00:00:00+00:00", [10])
    conn.execute(
        "INSERT INTO articles (id, status, created_at) VALUES ('a-abandoned', 'abandoned', '2026-01-03T00:00:00+00:00')"
    )
    _add_edit_round(conn, "a-abandoned", 1, 9999)
    conn.commit()
    _seed_article(conn, "a3", "2026-01-04T00:00:00+00:00", [10])
    _seed_article(conn, "a4", "2026-01-05T00:00:00+00:00", [10])

    trend = health.edit_effort_trend(conn, window=4)

    assert trend["recent_mean"] == pytest.approx(11)
    assert trend["prior_mean"] == pytest.approx(11)
    assert trend["spiking"] is False


def test_edit_effort_trend_fewer_than_window_approved_articles(conn):
    # Only 2 approved articles exist; window=4 asks for more than available.
    # half = len(articles) // 2 = 1, so prior=[a1] (mean 11), recent=[a2]
    # (mean 31). The split still bisects what's there and must not error.
    _seed_article(conn, "a1", "2026-01-01T00:00:00+00:00", [10])
    _seed_article(conn, "a2", "2026-01-02T00:00:00+00:00", [30])

    trend = health.edit_effort_trend(conn, window=4)

    assert trend["prior_mean"] == pytest.approx(11)
    assert trend["recent_mean"] == pytest.approx(31)
    assert trend["rising"] is True
    assert trend["spiking"] is True  # 31 > 11 * 1.5 (16.5)


def test_edit_effort_trend_no_approved_articles_returns_zeroed_dict_no_crash(conn):
    trend = health.edit_effort_trend(conn, window=4)

    assert trend["recent_mean"] == 0
    assert trend["prior_mean"] == 0
    assert trend["rising"] is False
    assert trend["spiking"] is False

    assert health.promotion_allowed(conn) is True
    assert health.nudge(conn) is None
