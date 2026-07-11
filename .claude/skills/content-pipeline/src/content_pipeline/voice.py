"""The composed voice doc handed to the brief-writer and drafter subagents.

Two layers: a static hand-owned SEED (the operator's config brand_context,
or a generic good-writing default when unset) and a learned layer rendered
from the style canon (permanent rules + provisional tendencies). The seed is
the floor; the learned layer is composed on top. The seed changes only when
the operator edits their brand_context; the learned layer evolves via
synthesis. This is the single input a stage receives for "how to write":
audience, tone, length, and structure belong here, not in the per-article
brief.

Per-article override: an article may carry a `voice_override` (set when it is
forked with a pasted style guide). When present it is used verbatim as the
WHOLE voice doc - what you paste is exactly what the stage sees, with no
global seed or learned layer mixed in - so a style fork is a clean,
reproducible experiment rather than a blend with whatever the global config
happens to be.
"""

from content_pipeline import config
from content_pipeline.learning import canon

DEFAULT_SEED = """Voice and writing guidelines (generic default; refine over time):
- Write in plain, direct English. Prefer concrete nouns and verbs over abstraction.
- Short sentences, one idea each. Vary rhythm but favor brevity.
- Open with the point. Do not bury it under throat-clearing.
- No em dashes anywhere. Use commas, periods, or parentheses instead.
- Cut filler: "very", "really", "in order to", "the fact that".
- Prefer active voice and name the actor.
- Read it aloud; if you stumble, rewrite it."""


def voice_doc(conn, article_id=None) -> str:
    """Compose the voice doc for a stage. If article_id names an article that
    carries a voice_override, that override is the whole voice doc (verbatim,
    no seed/learned layer). Otherwise compose the default: static seed first,
    learned layer second."""
    if article_id is not None:
        row = conn.execute(
            "SELECT voice_override FROM articles WHERE id = ?", (article_id,)
        ).fetchone()
        if row is not None and row["voice_override"]:
            return row["voice_override"]

    seed = config.brand_context() or DEFAULT_SEED
    learned = canon.style_context(conn)
    if learned:
        return f"{seed}\n\n--- Learned preferences ---\n\n{learned}"
    return seed
