# miho-followup-email

The MiHO follow-up email tool for service businesses. Mike Grabham + Howard Kim.
Finish line: a live web app a one-man plumber can use to send his first follow-up.

A job finishes, the owner types the customer's name and email and hits add. The app sends
a thank-you immediately, then a check-in two weeks later. That is the whole product.

## The scoping discipline (this is the idea, not a detail)

**It is deliberately not a CRM.** Service businesses don't have one and won't adopt one, so
the app does not try to consolidate their communications — it builds only the single step
they already skip. Howard's first instinct was to route all customer communication into one
place; Mike pushed back, and the reframe *is* the product. Any proposal that starts
absorbing more of the customer relationship is out of scope by default.

The test every decision has to pass is Mike's: the one-man plumber who just joined his BNI
group. Bad presenter, Yahoo email address, possibly no website. "How do we help that guy."

## What belongs here

- **Product scope** — what's in the MVP, what's explicitly deferred, and why.
- **Build plan and architecture** — data model, screens, delayed-send queue, email provider.
- **Sender and deliverability decisions** — how mail leaves the system and whose name is on it.
- **Pricing** — near-free; whether it's a revenue line or marketing spend is still open.
- **The app itself**, once the plan is locked.

## What doesn't

- Meeting records. The originating conversation is
  `meetings/2026-08-07-miho-partner-meeting/summary.md` and is read, not copied here.
- MiHO brand ground-truth (positioning, voice, ICP) — `docs/miho/brand/`.
- Content-pipeline and landing-page work — their own projects under `projects/`.
- Lead generation (the AI Visibility Report, BNI outreach) — related go-to-market, but a
  different effort; it is not this tool.

## Local rules

- **Sender identity is a settled decision, not an open question.** See
  `reference/decisions.md` before reopening it.
- **Anything that requires the business owner to configure DNS is out.** That audience will
  not do it, and it was ruled out in the originating meeting.

## Knowledge system tiers

- `foundation/` — rarely changes. Nothing yet.
- `reference/` — trusted until superseded: decisions ledger, session log. The MVP design spec
  lives at `docs/superpowers/specs/2026-08-07-miho-followup-email-design.md`, following the
  repo's existing spec convention; `current.md` points at it.
- `current.md` — where things stand right now. Small, rebuilt rather than accumulated.
