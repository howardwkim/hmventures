# Content Discovery — Feedback Log

Change requests captured while evaluating the skill. Each entry: timestamp + verbatim-intent feedback.

---

## 2026-07-17 16:45 PDT — Don't narrate internal state mechanics to the operator

Observed: after an accept, the agent explained that the card was "removed from the reservoir"
and described `seeds-queue.jsonl` mechanics in the chat. The skill's own principle is that the
operator shouldn't see the glue — internal state transitions (reservoir/queue/event-log
bookkeeping) are implementation detail, not something Howard needs surfaced. This one instance
(reservoir removal + queue description right after accepting) is the example; not asking for a
fix right now, just logging the pattern.

---

## 2026-07-17 16:45 PDT — Missing explicit reaction options after presenting a pitch card

Observed: after presenting the pitch card this session, the agent didn't offer the usual
accept/pass/defer-style options — normally the operator gets something like yes/no/skip
(approve/decline/skip) to react to. That prompt didn't appear this time. Logging as a gap to
address, not fixing now.
