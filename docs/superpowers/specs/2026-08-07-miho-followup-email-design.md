# Follow-up Email Tool — Design Specification

**Date:** 2026-08-07
**Status:** Approved design, not yet built
**Project:** `projects/miho-followup-email/`
**Origin:** `meetings/2026-08-07-miho-partner-meeting/summary.md`
**Decision trail:** `projects/miho-followup-email/reference/decisions.md`

## Summary

A service business owner finishes a job, opens the app on his phone, types the customer's
first name and email, and hits add. The app sends a thank-you immediately and a check-in
two weeks later. Both end with a link to leave a Google review. That is the entire product.

It is **not a CRM**, and the discipline is load-bearing. These businesses don't have one and
won't adopt one, so the app builds only the single step they already skip. Any feature that
starts absorbing more of the customer relationship is out of scope by default.

The target user is Mike's one-man plumber: bad presenter, Yahoo address, possibly no
website. Every decision below is tested against him.

## The experience

1. **Sign in.** Magic link, password, or Google. The session does not expire — realistically
   he signs in once, ever.
2. **Setup, once.** Business name, zip, optional website. We find his Google listing and
   build his review link for him. Both email templates arrive pre-written; editing exists
   but is a deliberate step he has to go take.
3. **Add a job.** Customer first name, email, and a toggle for whether the job went fine.
   Add clears the form and leaves it ready, so he can enter five at the end of the day.
4. **See what's queued.** The thank-you going out now, the check-in dated two weeks out,
   each with a cancel button.
5. **See what's done.** Below the queue, everything already sent — so logging back in weeks
   later shows him the tool has been working.

## Architecture

No server renders any page. The browser downloads a static app once and talks to Supabase
for data. This is the right shape because the app is entirely behind a login: no search
engine will ever see it, and server rendering would buy nothing while forcing a paid Node
host.

| Layer | Choice | Cost |
|---|---|---|
| Frontend | Static React (Vite), served as files at `app.<domain>` | free on Cloudflare Pages or Netlify |
| Database, auth, server logic | Supabase — Postgres, three sign-in methods, Edge Functions | free tier |
| Delayed send | Inngest durable workflow | free (25,000 runs/month) |
| Email delivery | Resend, from a dedicated mail subdomain | free to 3,000/month |
| Review links | Google Places API, at setup only | pennies |

Anything requiring a secret (Resend key, Places key) runs in a Supabase Edge Function, never
in the browser.

### Why not Next.js on Vercel

Next.js is fine; nothing here needs it. Server rendering is its main draw and this app
doesn't want it. Vercel's Hobby plan forbids commercial use, so keeping Next.js would mean
$20/month for a capability the product doesn't use.

### Why not Cloudflare Workers

Considered as the free Node-less host. Rejected: Cloudflare emulates Node rather than
running it, which produces a class of runtime gaps — the known one being Next middleware
importing `async_hooks`. With a static frontend there is no server runtime at all, so the
entire question disappears rather than being worked around.

### Why Inngest over cron

Vercel-style cron is best-effort: failed runs are never retried and the same run can fire
twice. A durable workflow engine expresses this natively — send, sleep fourteen days, check
for cancellation, send — with the sleep costing nothing while idle. Inngest over Trigger.dev
because Trigger.dev's cloud enforces a fourteen-day ceiling on runs, which is exactly our
delay, and its free tier retains logs for one day, meaning the thank-you's logs are gone
before the check-in fires.

## Data model

**owners** — id, email, first/last name, business name, zip, website, `google_place_id`,
`google_review_url`, `reply_to_email`, `daily_send_cap`, `status`, `created_at`.

**templates** — owner_id, kind (`thank_you` | `check_in`), subject, body, `edited_at`
(null means still the supplied default).

**jobs** — id, owner_id, customer first name, customer email, `job_went_well`,
`inngest_run_id`, `cancelled_at`, `created_at`.

**sends** — id, job_id, kind, status (`pending` | `sent` | `failed` | `cancelled`),
`scheduled_for`, `sent_at`, `provider_message_id`, `error`.

The `sends` table backs both lists in the UI: pending rows are the queue, sent rows are the
history. There is deliberately no `customers` table — a repeat customer is just another job
row, and deduplicating them is a CRM feature.

## Sending

Mail goes out from a dedicated subdomain we own and authenticate (`send.<domain>`), never
the root domain, so a deliverability problem can never damage MiHO's own business email.

The From address is ours. The **display name** is the owner's business, and **Reply-To** is
his address, so replies land in his real inbox. This is standard multi-tenant transactional
practice, not spoofing — the From domain and the signing domain are both ours, so no "via"
warning appears. It requires nothing at all from the owner: no OAuth, no DNS.

Every email carries an unsubscribe link.

## Review links

At setup, the owner types his business name and zip. We query the Google Places API, show
two or three matches with addresses, and he taps his. From the place id we construct
`search.google.com/local/writereview?placeid=<id>` ourselves — he never has to find a link.

If no listing matches, he continues without one and his emails send check-in-only. That is a
real slice of this audience and it must not block signup.

**Google only. Yelp is excluded on policy, not technology** — Yelp forbids businesses from
soliciting reviews and specifically names services that email customers asking for them.
Penalties include filtering the solicited reviews out and ranking penalties on the business's
page. A Yelp ask would actively damage the customer.

## Abuse guardrails

Every owner shares one sending reputation, so one spammer could stop delivery for everyone.
Signup stays open, with automated containment:

- New accounts are capped at 20 sends per day, lifting to 200 after 14 days with no hard
  bounces and no complaints. The cap is generous against real usage — a one-man operation
  does a handful of jobs a day — and tight against a spammer.
- Bounce and complaint webhooks from Resend feed a per-owner rate; crossing a threshold
  suspends sending and alerts us.
- Hitting the cap queues sends rather than dropping them.
- Signup itself is rate limited.

## Error handling

- **Send failure** — Inngest retries. After retries are exhausted the send row is marked
  failed with the provider error, and it's visible to the owner rather than silent.
- **Hard bounce on a customer address** — no retry, mark failed, suppress the later check-in
  for that job. Emailing a dead address twice helps nobody.
- **Cancellation** — an Inngest cancel event, plus a status check immediately before sending.
  Both, because sending a cheerful check-in to an angry customer is the most damaging thing
  this product can do.
- **Places lookup fails or returns nothing** — continue without a review link, never block.
- **Supabase unreachable at send time** — Inngest retries the step; the workflow survives.

## Testing

- **Unit** — template rendering and review-link construction from a place id.
- **Integration** — the full workflow with the delay behind a configurable value so staging
  runs it in two minutes instead of two weeks. The fourteen-day path must be exercised, not
  assumed.
- **Manual smoke, before anything else ships** — a real send to a real Gmail and a real
  Yahoo inbox, confirming it lands in the primary tab rather than spam, that the display name
  reads as the business, and that hitting reply goes to the owner.
- **Cancellation** — cancel a queued check-in and confirm nothing sends.

## Explicitly out of the MVP

- Gmail OAuth sending. Deferred to v2, where it buys the message landing in the owner's own
  Sent folder and the thread living in his mailbox. See `projects/miho-followup-email/reference/decisions.md`.
- Receiving customer mail in the app.
- Forwarding an invoice email to add a job automatically.
- Any reminder nudging the owner to enter jobs. Ship without it, watch whether BNI users
  actually enter jobs, and let that decide.
- Per-customer message editing. Templates are set up once.
- SMS. Lost to email on cost in the originating meeting.

## Open items

- Name the domain. Howard already owns one; this doc writes `app.<domain>` and
  `send.<domain>` until it's picked. Static hosting must be Cloudflare Pages or Netlify, not
  Vercel Hobby, whose terms forbid commercial use.
- Confirm the Google review link actually resolves for an unclaimed listing — test against a
  real plumber's listing before relying on the fallback logic.
- Confirm Resend's acceptable-use terms cover the review ask, which is not purely
  transactional.
- Warm the sending subdomain before launch. A new domain delivers poorly for its first weeks;
  this is a start-now action, not a launch-week one.
- Pricing is unresolved. Mike's number was five to eight dollars a month. At a hundred users
  that is $500–800 against roughly zero running cost, so the "marketing spend or revenue
  line" question is live and now has real numbers behind it.
- Run the sender reversal past Mike. It changes a call made with him in the room.
