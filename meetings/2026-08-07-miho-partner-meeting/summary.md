# MiHO partner meeting — 2026-08-07

Howard + Mike Grabham, 68 min, Fathom. Source: `raw/fathom.md`. Fathom's own AI summary is
in `vendor-summary.md` — this file is ours.

## Takeaways

**A viral LinkedIn post established what actually drives engagement.** Mike's post on a NYC
restaurant owner reacting to a minimum wage hike hit 4,000+ impressions against a ~200
average. Three things made it work, and they're now the content filter: the source article
was under 24 hours old, the topic was controversial enough to provoke anger, and Mike added
his own opinion rather than reposting. The control case is instructive — a post built on a
two-month-old article got 100 impressions. Freshness under 72 hours is the hard gate.

**A new product idea landed: a follow-up email tool for service businesses.** Full detail
below; this was the substantive new thing in the meeting.

**Lead generation via a free "AI Visibility Report" for BNI members.** Grades a business's
SEO and AI visibility with competitor analysis, costs about $0.35 to produce. The funnel
Mike sketched: generate the report for a prospect, use a design tool to produce a free
AI-generated redesign of their current site, then present both together.

**A video pipeline is running end to end.** Claude writes a ~90-second script, Descript
records against a teleprompter and auto-inserts B-roll, Claude proposes 4-second visual
hooks, Remotion renders the chosen one for ~$0.30, and the result goes to five platforms.

## The follow-up email tool

**The core insight is that it is deliberately not a CRM.** Service businesses don't have
CRMs and won't adopt one — Mike's landscaper of six years communicates "all random." So skip
consolidating their communications entirely and build only the one step they already skip.
Howard's first instinct was to route all customer communication into one place; Mike pushed
back, and that reframe is the idea.

**The product as sketched:**

- Web app. No download, no install. They create an account.
- Job finishes → type the customer's name and email → hit add.
- Sends a thank-you immediately, then a check-in two weeks later: "how's things going, let
  us know if you need any additional help."
- The app suggests both messages, because these users need that. User can edit and save.
  The app does everything after that.

SMS was raised first (Twilio, a few cents a message) but email won on cost — free.

**The one real technical hurdle, and its resolution.** Mail has to come from the business
owner's address, not ours. Mike asked whether the sender could be masked; Howard ruled it
out — it gets flagged, and the DNS route is far beyond this audience. The answer landed on
a one-time OAuth approval, the "log in with Google" pattern, after which the app sends on
their behalf. The approval step is unavoidable, but it's one click instead of DNS records.

**Deliberately out of the MVP:** once Gmail is connected, the owner's customer mail is
already flowing through it, so the app could send *and* receive. Noted and set aside.

**Pricing:** near-free. Mike's number was five to eight dollars a month — can't give it away,
can't charge much. Howard raised that if running costs are near zero, it may be better
treated as marketing spend than a revenue line.

**The target customer is a specific person:** the one-man plumber who just joined Mike's BNI
group. Bad presenter, Yahoo email address, possibly no website. Mike's framing — "how do we
help that guy" — is the test the MVP has to pass.

## Decisions

1. **Content filter is freshness plus controversy plus opinion.** Under 72 hours old,
   emotionally provocative, with a personal take attached. Established empirically by the
   4,000-impression post against the 100-impression control.
2. **The follow-up tool is single-purpose, not a CRM.** Scope is the last step only.
3. **OAuth connection over sender masking.** Masking is not viable; DNS is too much to ask
   of this audience. — *Superseded later the same day. Spoofing the owner's address is still
   out, but sending from our own domain with their business name as the display name and
   their address as Reply-To is not spoofing, and it removes the hurdle entirely. See
   `projects/miho-followup-email/reference/decisions.md`.*

## Next steps

**Howard**
- Research technical feasibility and MVP requirements for the follow-up email tool, and
  assess build effort
- Design business cards for BNI networking
- Apply for BNI membership

**Mike**
- Refine the topic-finding agent to surface fresh (under 72 hours) controversial topics
- Generate and distribute AI Visibility Reports to all BNI members

## Ideas

- Send *and* receive customer mail in the app once Gmail is connected — the natural second
  step after the MVP
- A separate agent that connects broad trends (new laws, policy changes) to small-business
  implications, as a content source
- The "puppy dog close": hand a prospect the visibility report plus a free AI redesign of
  their site to demonstrate value before asking for anything

## Quotes

> "How do we help that guy? I haven't been to his website, but I'm sure it's — well,
> actually, I don't even know if he has a website because he has a Yahoo email address."
> — Mike Grabham

*Content candidate.* The archetype customer in one line.

> "Our intent isn't to build up the CRM thing. It's to make it very easy for a user to send
> these follow-ups." — Howard Kim

*Content candidate.* The scoping discipline, stated plainly.

> "They already don't have a CRM. Most of them don't have a CRM. I can guarantee if I called
> Marcus, my landscaper, who I've known for five years, six years, I almost guarantee he has
> no CRM." — Mike Grabham
