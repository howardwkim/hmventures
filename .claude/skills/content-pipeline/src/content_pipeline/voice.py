"""The composed voice doc handed to the brief-writer and drafter subagents.

Two layers: a static hand-owned SEED (the operator's config brand_context,
or a generic good-writing default when unset) and a learned layer rendered
from the style canon (permanent rules + provisional tendencies). The seed is
the floor; the learned layer is composed on top. The seed changes only when
the operator edits their brand_context; the learned layer evolves via
synthesis. This is the single input a stage receives for "how to write":
audience, tone, length, and structure belong here, not in the per-article
brief.
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


def voice_doc(conn) -> str:
    """Compose the voice doc: static seed first, learned layer second."""
    seed = config.brand_context() or DEFAULT_SEED
    learned = canon.style_context(conn)
    if learned:
        return f"{seed}\n\n--- Learned preferences ---\n\n{learned}"
    return seed
