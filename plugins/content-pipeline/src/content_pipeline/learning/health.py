SPIKE_FACTOR = 1.5

NUDGE_MESSAGE = "drafts needed more editing lately, want to review the writing rules?"


def _approved_article_ids(conn, window):
    """The last `window` approved articles, ordered oldest-first (i.e.
    ascending by approved_at) within the window. Only articles.status =
    'approved' are considered."""
    rows = conn.execute(
        """SELECT id FROM articles
           WHERE status = 'approved'
           ORDER BY approved_at DESC
           LIMIT ?""",
        (window,),
    ).fetchall()
    return [row["id"] for row in reversed(rows)]  # oldest-first


def _article_effort(conn, article_id) -> float:
    """Per-article edit effort = sum(edit_size across all rounds) +
    round_count (a round of edits costs something even at zero size - each
    round is an operator touching the draft again)."""
    row = conn.execute(
        """SELECT COALESCE(SUM(edit_size), 0) AS total_size, COUNT(*) AS round_count
           FROM edit_rounds WHERE article_id = ?""",
        (article_id,),
    ).fetchone()
    return (row["total_size"] or 0) + (row["round_count"] or 0)


def edit_effort_trend(conn, window=10) -> dict:
    """Edit-effort trend over the last `window` approved articles.

    Split strategy: take the last `window` approved articles ordered by
    approved_at, oldest-first. Bisect that ordered list at
    half = len(articles) // 2: the first half is "prior", the second half
    is "recent". This is a plain midpoint split (not a fixed N/2 of the
    nominal window) so it degrades gracefully when fewer than `window`
    approved articles exist - the split always uses what's actually
    there. With window=4 and a full window, that's a clean 2+2 split.

    recent_mean / prior_mean are the mean per-article effort
    (sum(edit_size) + round_count) within each half.

    rising = prior_mean > 0 and recent_mean > prior_mean (any increase).
    spiking = prior_mean > 0 and recent_mean > prior_mean * SPIKE_FACTOR (the
    promotion gate trips on this, not on `rising` alone).

    Both rising and spiking require a positive prior_mean as a baseline to
    compare against - without it, any nonzero recent effort would trivially
    read as a rise/spike, which would wrongly block promotion on an
    operator's very first approvals (exactly when the two-door promotion
    mechanism needs to work).

    With 0 approved articles there's nothing to split; recent_mean and
    prior_mean are both 0 and rising/spiking are both False. With exactly 1
    approved article, half = 0, so prior_ids is empty (prior_mean = 0) and
    recent_ids holds that one article (recent_mean is its own nonzero
    effort, not 0) - the prior_mean > 0 guard is what keeps rising/spiking
    False in this case too.
    """
    article_ids = _approved_article_ids(conn, window)

    half = len(article_ids) // 2
    prior_ids = article_ids[:half]
    recent_ids = article_ids[half:]

    def _mean_effort(ids):
        if not ids:
            return 0
        return sum(_article_effort(conn, aid) for aid in ids) / len(ids)

    prior_mean = _mean_effort(prior_ids)
    recent_mean = _mean_effort(recent_ids)

    rising = prior_mean > 0 and recent_mean > prior_mean
    spiking = prior_mean > 0 and recent_mean > prior_mean * SPIKE_FACTOR

    return {
        "recent_mean": recent_mean,
        "prior_mean": prior_mean,
        "rising": rising,
        "spiking": spiking,
    }


def promotion_allowed(conn) -> bool:
    """The core safeguard: learn from calm, not thrash. Promotion of
    provisional tendencies into permanent rules is only allowed while the
    edit-effort trend is not spiking."""
    return not edit_effort_trend(conn)["spiking"]


def nudge(conn) -> str | None:
    """If the edit-effort trend is rising, surface a nudge to review the
    writing rules. None otherwise."""
    if edit_effort_trend(conn)["rising"]:
        return NUDGE_MESSAGE
    return None
