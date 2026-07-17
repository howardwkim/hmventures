# Gold-layer extraction prompt

Extract "golden nuggets" — specific, hard-won, TACIT knowledge that only exists
because this particular person lived it. The test: would a well-informed outsider
in this person's field have been unable to write this without having actually
been there?

A nugget usually takes one of these shapes (these are examples of what gold tends
to look like, not a checklist — if something clearly passes the test above but
doesn't fit any shape below, include it anyway, tagged "other"):
- A specific number, metric, or concrete detail specific to their own situation (a
  real figure, timeline, term, quantity, threshold — not a rounded generality)
- A specific mistake the person made and what they actually learned from it
- A moment where their model of their world/field changed — a real "I used to
  think X, then Y happened, now I think Z"
- A belief that contradicts what conventional wisdom in their field would predict
- A concrete, specific detail of how an actual outcome, decision, or event
  unfolded in their world

REJECT anything that is:
- Generic advice in their field that a well-read outsider could write without
  having lived it
- Vague inspirational statements with no specific detail attached
- Standard facts/definitions in their field that anyone could look up
- Career-history narration with no extractable lesson

For each nugget found, output three fields:
- category: which shape it matches (number/metric, mistake, changed-belief,
  contradicts-convention, concrete-detail, or "other")
- summary: a full, self-contained paragraph (3-6 sentences: setup, what happened,
  why it's non-obvious). This is the PRIMARY field — a reader must understand the
  nugget completely without needing the transcript.
- quote: the supporting quote from the transcript. This is backing citation only,
  not the deliverable.
