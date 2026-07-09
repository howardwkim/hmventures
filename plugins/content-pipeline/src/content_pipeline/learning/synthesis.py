"""PLACEHOLDER STUB for Task D4 (learning.synthesis).

This module exists only so that writing.approve() has a real, importable
target to call and monkeypatch in tests before Task D4 is implemented.
Task D4's implementer should OVERWRITE this file (not create a new one)
with the real synthesis logic: reading events since the last synthesis
run, updating permanent_rules / provisional_tendencies, and recording a
synthesis_runs row.
"""


def on_approval(conn, article_id) -> None:
    """No-op placeholder. Called by writing.approve() after an article is
    approved. Task D4 replaces this body with the real synthesis pass."""
    return None
