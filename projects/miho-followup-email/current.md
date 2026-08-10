# miho-followup-email — CURRENT

**Last updated:** 2026-08-07

**Next:**
- Now: Howard reviews `docs/superpowers/specs/2026-08-07-miho-followup-email-design.md`. The
  design is agreed end to end — experience, stack, data model, sending, guardrails, error
  handling, testing — and nothing is built. After review, the next step is an implementation
  plan.
- On deck: Run the sender decision past Mike; it reverses a call made with him in the room on
  2026-08-07 and he has not seen the reasoning. Name the domain. Warm the sending subdomain,
  which is a start-now action because a new domain delivers poorly for its first few weeks.
  Settle pricing — at a hundred users, five to eight dollars a month is $500–800 against
  roughly zero running cost, so "marketing spend or revenue line" now has real numbers.

**Standing constraints:**
- Not a CRM. The scope is the last step only — the follow-up the owner already skips. Any
  feature that starts absorbing more of the customer relationship is out by default.
- The target customer is the one-man plumber in Mike's BNI group: bad presenter, Yahoo
  address, possibly no website. If a decision doesn't work for him, it's the wrong decision.
- Nothing may require the business owner to touch DNS.
- The app suggests both message drafts. These users need that; a blank compose box fails them.
  Owner can edit and save, and the app does everything after that.
- Email only. SMS was considered and lost on cost.

**Key decisions:** v1 sends from our own authenticated domain with the business name as the
From display name and the owner's address as Reply-To — no setup at all for the owner. Gmail
OAuth is deferred to v2, where it buys the sent message landing in the owner's own Sent folder
and the thread living in their mailbox. Receiving customer mail in the app is explicitly out
of the MVP. The app is a static React frontend with Supabase behind it, Inngest for the
fourteen-day wait and Resend for delivery — no server rendering, because everything is behind
a login, which makes the whole stack free. Google reviews only; Yelp forbids soliciting them.

**Canonical assets:**
- `docs/superpowers/specs/2026-08-07-miho-followup-email-design.md` → the agreed MVP design;
  authoritative for scope, stack and data model
- `reference/decisions.md` → the trail for why the sender approach is what it is

**Origin:** `meetings/2026-08-07-miho-partner-meeting/summary.md`
