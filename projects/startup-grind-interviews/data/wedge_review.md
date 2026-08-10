# Founder-Wedge Filter — Ranked Review

Rubric: reference/founder-wedge-rubric-v1.md

**21 of 732 nuggets kept** (711 trimmed, 2% pass rate).

Score distribution: 5★×1, 4★×4, 3★×14, 2★×2
Kind: Automate/AI×8, Sharp pain×8, Both×5

## 5★ — 1 nuggets

- **[Both] Rian Buckley** (Founder Fitcode) — _number/metric_
  - Wedge: AI body-shape fit recommender for online apparel (denim first) to cut fit-driven returns; sharp segment (denim e-com brands), landing page writes itself.
  - Buckley cites concrete industry return-rate data that quantifies just how large the online-fashion-fit problem is: online returns overall run 40-60% of everything purchased, and within that, women's denim is the single worst category at 52% of all jeans purchased online being returned — driven by fit, not style, unlike women's dresses (the top returned item overall) where the driver is style rather than fit. This distinction — fit-driven vs. style-driven returns — is the reason FitCode targeted denim first and used it to prioritize its product roadmap (bottoms, then tops, then dresses) by ranked size of the fit-return problem in each category.

## 4★ — 4 nuggets

- **[Automate/AI] Dan Levitan** (CEO Maveron) — _concrete-detail_
  - Wedge: AI product-photography (gen/virtual studio) for high-volume ecommerce/flash-sale sellers shooting hundreds of SKUs a day to collapse studio cost.
  - Levitan tells a specific story about Zulily co-founder Daryl Cabin discovering that professional photographers — the acknowledged industry experts — quoted him a very high per-shoot cost to photograph merchandise, a cost that was a critical line item since Zulily runs hundreds of flash-sale events a day and photography is a major driver of the cost to deliver the service. Rather than accepting that quoted floor as a fixed constraint, Cabin found a way to do the same photography for roughly a tenth of what the industry insiders said was the minimum possible cost, which is what made the business model work economically. The lesson is that "industry expert" cost estimates often bake in assumptions and overhead that a fresh, disruptive approach can simply bypass, and treating an expert's stated floor as unquestionable can kill a viable business model before it's tested.
- **[Both] Oren Etzioni** (CEO Ai2) — _concrete-detail_
  - Wedge: AI pronunciation/spoken-English coach for call-center job seekers in developing markets; sharp segment, clear buildable product.
  - Etzioni's incubated company Blue Canoe (founded by Sarah Daniels) uses AI plus proprietary pedagogy to help non-native speakers improve English pronunciation -- not as a vanity or accent-reduction product, but because pronunciation quality is a literal gatekeeper to economic mobility in the developing world: in countries like Bangladesh or the Philippines, landing a good call-center job (a common path to the middle class) depends on how clearly someone pronounces English, so the product sells both internationally to individuals and to companies (including in Seattle) that need their workers to communicate more clearly.
- **[Both] Rian Buckley** (Founder Fitcode) — _concrete-detail_
  - Wedge: Aggregated body-shape analytics telling apparel brands which cuts don't fit X% of their real customers; interview denim/apparel product teams on fit-model-vs-customer gap.
  - A structural flaw in how denim brands manufacture product: each brand builds its entire jeans line off measurements from a single fit model — typically a professional model's body shape — and then simply scales that one shape up and down into a size run, assuming it will fit the brand's entire customer base. Buckley, herself a former denim model, says this is why garments can look perfect from the front on camera but require hidden clips and pins to hold them together in back — the underlying pattern was never designed around real customer body-shape distribution, which is exactly the gap FitCode's aggregated body-shape data lets brands see and correct (e.g., telling a retailer that a given cut doesn't fit 30% of its actual customer base and should be dropped from manufacturing).
- **[Sharp pain] Sally Bergesen** (CEO Oiselle) — _concrete-detail_
  - Wedge: Interview small/emerging apparel brands on MOQ pain; platform pooling small orders (or a low-MOQ factory matcher) to clear the ~200-unit floor.
  - The recurring obstacle Bergesen names as the biggest challenge in apparel manufacturing is minimum order quantities (MOQs), which apply both at the fabric level (minimum yardage you must purchase) and the production level (minimum units a factory will cut). As a concrete threshold, orders under roughly 200 units of an item are effectively unworkable — factories simply won't take them — forcing small brands into bigger upfront inventory bets than they'd otherwise choose, or into a search for niche factories willing to work at smaller scale.

## 3★ — 14 nuggets

- **[Automate/AI] Aaron Bird** (CEO/Founder Bizible) — _number/metric_
  - Wedge: Agent that monitors tech deprecations/migrations, crawls the web for the affected script tag/technographic signal, enriches contacts, and drafts urgency-timed outreach for replacement-product sellers.
  - One of Bizible's earliest customer-acquisition wins came from exploiting a narrow, time-boxed opportunity: Salesforce announced it was deprecating a free integration ("Salesforce for Google AdWords") that required a script tag on customers' websites. Bird's team crawled the web looking for that script tag, harvested the resulting list of domains, scraped phone numbers off those sites, and cold-called each one with an urgent message that their integration was dying in two months and Bizible had the replacement. That single hack-driven campaign landed roughly 40 customers in six weeks — a result that wouldn't have been possible through generic outbound or paid ads, illustrating that under-exploited, narrow, expiring opportunities can outperform conventional channels disproportionately.
- **[Automate/AI] Adrian Hanauer** (Owner Seattle Sounders FC) — _concrete-detail_
  - Wedge: Athlete-monitoring platform that ingests multi-vendor HR/GPS/CNS streams and auto-generates coach-ready insights, replacing the bespoke data-scientist-builds-graphs setup teams cobble together.
  - The Sounders' sports-science program runs on a specific, named stack: a heart-rate monitor and a GPS unit worn by every player at every training session, tracking acceleration, deceleration, distance, and speed, synchronized with drill data, plus a system called Omega Wave that measures central-nervous-system function to gauge sleep and recovery — about eight systems in total, feeding a database that a former Microsoft data scientist turns into usable graphs for coaches. As a concrete example, Hanauer recalls that during a 5v5 small-sided training game, Clint Dempsey's heart rate hit 97% of his max early in the drill, a red flag the staff could act on regarding his conditioning. The specificity of which vendors are used, how the data streams are combined, and who processes it is the kind of operational detail only someone actually running the program would know.
- **[Automate/AI] Eric Breon** (CEO Vacasa) — _concrete-detail_
  - Wedge: ML dynamic-pricing engine for small/independent short-term-rental hosts and property managers who still price by hand
  - Vacasa's nightly pricing used to be a manual process of staff eyeballing a rate grid, which didn't scale as more people tried to do it. The company moved to a hybrid model it describes as being like a level-two self-driving car: a machine-learning system sets most prices on its own, but a human analyst still acts as the 'safety driver,' watching over and correcting the algorithm rather than pricing manually or letting it run fully unsupervised. This is a concrete pattern for any ops-heavy business trying to scale a judgment-based task (pricing, matching, routing) beyond what a team of humans can consistently do by hand.
- **[Sharp pain] Eric Breon** (CEO Vacasa) — _concrete-detail_
  - Wedge: interview massage therapists on unfilled same-day slots and stressed consumers on instant-booking demand; last-minute appointment-fill marketplace
  - Breon's advice for picking a market to build in is to find a hugely fragmented, broken, and large industry (he cites vacation rentals as a $125 billion market) rather than a smaller or already-efficient one -- scale of brokenness is the opportunity. He illustrates the deeper point with a hypothetical he explicitly invites the audience to steal: an on-demand, last-minute massage booking service, aimed at someone who doesn't plan a massage three weeks out but wants one immediately after a rough day. His caveat is that the real opportunity isn't in building simple booking software (which he calls 'boring') but in figuring out how to actually control or capture a meaningful share of the underlying marketplace -- the software is not the moat, control of the supply or demand is.
- **[Both] Howard Behar** (Former President Starbucks) — _concrete-detail_
  - Wedge: Frontline demand-capture tool for multi-location retail/F&B: log and aggregate repeated in-store customer requests HQ never sees, to surface unmet product opportunities.
  - The idea for what became the Frappuccino came from a Southern California district manager, Dina Campion, who took Behar to visit a competitor selling a blended-ice drink and told him roughly 30 customers a day were asking Starbucks stores for something similar. Behar, without a college degree but with retail instincts, ran the math on the spot: 30 drinks a day at $3 each was about $90/day, roughly $30,000/year against a typical Starbucks store's ~$600,000 annual revenue -- a 5% sales lift from one product, which he recognized immediately as a big deal. After being told no by the head of product development, he had Campion's team (a store manager and barista who'd rigged up a blender with chocolate and no-fat milk) test the drink covertly in a single store -- no signage, no telling anyone, nightly phone updates only to Behar's home line -- and watched daily volume climb from 40 to 50 to 70 drinks per store per day within three weeks, which is what gave him the ammunition to force the idea back up the chain.
- **[Sharp pain] Joe Roets** (CEO Dragonchain) — _concrete-detail_
  - Wedge: Interview internal platform/dev-tools teams about request-prioritization that defaults to office politics and drives engineer turnover; build a transparent intake/priority-scoring system.
  - In one enterprise deployment, an internal engineering team that served other engineering teams had no way to prove which requesting groups were behaving well versus poorly, so prioritization defaulted to office politics ("I know your boss and I want this today") -- and that opacity was driving good engineers to quit rather than deal with it. The team initially rejected the idea of an internal currency as scary, but came back about six weeks later asking for it once they understood what it would do. Dragonchain modeled each group's actual contributions and activity, then monetized the good behavior with priority-granting tokens while leaving bad-behaving groups still functional but slower, without punishing anyone or escalating to a manager. The broader insight: making invisible political dynamics transparent and monetized, rather than escalating up the chain of command, can reduce internal-politics-driven turnover.
- **[Sharp pain] Joe Roets** (CEO Dragonchain) — _concrete-detail_
  - Wedge: Crowdfunding backers repeatedly burned by non-delivery; milestone-gated escrow that releases funds in tranches on verifiable/voted completion.
  - Roets describes a structural fix for the classic Kickstarter failure mode, where a creator takes all the money up front and then partially ships or never ships. Instead, funds sit in escrow and release in tranches tied to milestones: each release is triggered either automatically by pre-agreed, testable criteria, or by contributor vote confirming the milestone was actually met. If the creator stops delivering, contributors can collectively reclaim the un-released remainder, while the creator keeps only what was already earned for milestones genuinely completed. This turns crowdfunding from an all-or-nothing trust bet into a pay-as-delivered structure enforced in code rather than by hoping a platform's reputation system deters fraud.
- **[Automate/AI] John Cook** (Co-founder GeekWire) — _concrete-detail_
  - Wedge: Agent that monitors Delaware corporate-registry amendments to surface funding events / stealth startups ahead of PR — sold to reporters, VCs, sales intel.
  - When Redfin closed a $50 million funding round, GeekWire was deliberately left off the company's list of reporters given advance access — yet Cook still broke the story same-day, and beat Reuters, Wired, and the Wall Street Journal to it. His route around the lockout was a tipster who searched Delaware corporate filing records and found that Redfin's registration had recently been amended to reflect the new funding. This is a concrete, replicable investigative technique: state corporate-registry changes (Delaware being the default incorporation state for many US startups) can reveal a funding event independent of, and even despite, a company's PR gatekeeping.
- **[Sharp pain] Marc Barros** (Co-founder Moment) — _number/metric_
  - Wedge: Interview consumer-hardware brands on retail working-capital float; inventory/AR-financing product tuned to hardware payment timing.
  - Barros breaks down why selling hardware through big-box retail (e.g., Best Buy, Apple Stores) is a cash trap that isn't obvious until you're in it: retailers pay on long terms (net 90) while you must pay your suppliers much sooner (net 60), creating a multi-month negative cash float. Banks won't bridge that gap because they typically only lend against 50% of inventory or receivables value — so a $100 sale might only get you $50 of financing against it, well short of what's owed. In the Apple ecosystem specifically he cites a 60% margin structure across roughly 450 stores, which sounds attractive until the payment-timing math is run.
- **[Automate/AI] Oren Etzioni** (CEO Ai2) — _mistake_
  - Wedge: Auto-labeling / data-prep tooling for ML teams sitting on abundant raw but unlabeled data.
  - A common failure mode for AI/ML startups is assuming that having a lot of raw data is the same as being ready to build a model. Etzioni points out that the data has to be labeled -- organized into the categories the model needs to predict (e.g., "successful transaction" vs. not) -- and that this labeling step is the one founders most often skip or underestimate, even though raw data itself is often abundant (satellites, telescopes, cash registers).
- **[Automate/AI] Oren Etzioni** (CEO Ai2) — _changed-belief_
  - Wedge: Standardized plug-and-play AI/ML tooling layer so non-specialist engineers can ship apps without custom effort.
  - Etzioni frames the state of AI tooling as comparable to databases before standardized building blocks existed: databases only became broadly useful once standard components let most software engineers reliably build on them, but AI today has no equivalent -- there's no way to "plug your data into" a standard tool and have it work out of the box, and getting a successful application running still requires significant custom, painful effort. He frames this gap itself as a major startup opportunity: building the standardized tooling layer for AI, not just more models.
- **[Sharp pain] Rand Fishkin** (CEO SparkToro) — _number/metric_
  - Wedge: Podcast-ad marketplace/bidding system; interview podcasters + performance advertisers about the missing standardized buy-side.
  - Fishkin identifies podcast advertising as the single most under-monetized marketing channel he sees, backing it with a specific mismatch: roughly 22% of Americans had listened to multiple podcasts in the past month, yet under 5% of podcasts carried any advertising at all. He attributes this gap to the lack of a standardized marketplace or bidding system for podcast ads, which is a structural, non-obvious explanation for why such a popular medium remains commercially undertapped.
- **[Sharp pain] Sally Bergesen** (CEO Oiselle) — _concrete-detail_
  - Wedge: Interview small apparel brands on factory sourcing; a matching/vetting marketplace pairing them with right-sized factories willing to grow with them.
  - Bergesen's rule for choosing a factory partner is to pick one sized to match your own scale rather than the biggest or most prestigious option available — a huge factory producing millions of units will treat a small brand's order as low priority and give it poor service. A small brand is better served finding a factory willing to grow alongside it and invest in the relationship the same way the brand invests in them, rather than optimizing for factory size or reputation alone.
- **[Both] Scott Oki** (Founder Oki Developments) — _number/metric_
  - Wedge: Nonprofit financial-health/runway scoring from public 990 filings, for donors and grantmakers doing due diligence on which orgs are stable; validate by interviewing foundation program officers.
  - Oki gives a concrete financial-health benchmark he checks on every nonprofit balance sheet he reviews: at least a full year of operating costs held in the bank, so that if the donor base or an annual gala dries up, the organization has a year of runway to recover rather than collapsing immediately. He notes this is rare in practice -- most nonprofits are living day to day with no such buffer -- which makes it a useful diagnostic for donors or board members trying to assess whether an organization is actually stable versus one crisis away from failure.

## 2★ — 2 nuggets

- **[Automate/AI] Dan Price** (CEO Gravity Payments) — _number/metric_
  - Wedge: Async pre-screen tool for high-volume hirers that auto-sends a low-friction interview step and treats non-response as disqualifying, killing interviewer time wasted on no-shows; crowded category, marginal.
  - Early in building his hiring process, Price noticed a high no-show rate for scheduled in-person interviews and built a cheap filter to catch it before it wasted his time: as soon as a resume looked decent, he'd immediately reply with a copy-pasted email interview rather than book a meeting slot. About half of the candidates who would have no-showed the in-person interview also failed to respond to the email version, meaning the email step surfaced the same low-commitment signal at near-zero cost. It's a generalizable pre-screen: add a low-friction, asynchronous step before spending real calendar time, and treat non-response as the same disqualifying signal a no-show would be.
- **[Sharp pain] Joe Roets** (CEO Dragonchain) — _concrete-detail_
  - Wedge: Verifiers (banks/gov/employers) forced to hold sensitive PII they get breached on; user-held credentials + threshold-based partial-attribute verification so the verifier never stores the raw data.
  - Asked how blockchain could prevent an Equifax-style breach, Roets argues the fix isn't better security around a central data store but eliminating the central store entirely: individuals hold their own verified data (with proof anchored on-chain), and a verifying party defines a scoring threshold -- e.g., "provide any combination of these factors that adds up to X" -- rather than demanding one specific sensitive field like a Social Security number. A person could satisfy a verification request with a bank-signed home address instead of their SSN, clearing the score while exposing less, and any party that insists on holding data anyway becomes clearly liable for it. The reframe: an entity like Equifax or a government agency should never actually hold the underlying sensitive data at all, because a breach of data you never possessed can't happen.

## Wedge density by interviewee

| Interviewee | Passed / Judged |
|---|---|
| Joe Roets | 3 / 11 |
| Oren Etzioni | 3 / 11 |
| Sally Bergesen | 2 / 16 |
| Rian Buckley | 2 / 12 |
| Eric Breon | 2 / 19 |
| Dan Levitan | 1 / 37 |
| Rand Fishkin | 1 / 18 |
| Aaron Bird | 1 / 18 |
| Marc Barros | 1 / 24 |
| Howard Behar | 1 / 20 |
| Scott Oki | 1 / 13 |
| Dan Price | 1 / 17 |
| John Cook | 1 / 12 |
| Adrian Hanauer | 1 / 18 |
| Bill Bryant | 0 / 30 |
| Peter Hamilton | 0 / 11 |
| Chris DeVore | 0 / 12 |
| Leslie Feinzaig | 0 / 12 |
| Britta Jacobs | 0 / 12 |
| Jeana Jorgensen | 0 / 9 |
| Len Jordan | 0 / 11 |
| David Israel | 0 / 9 |
| Enrique Godreau III | 0 / 16 |
| Nick Huzar | 0 / 16 |
| Nick Soman | 0 / 22 |
| Jason Stoffer | 0 / 22 |
| Joe Wallin | 0 / 10 |
| Sarah Bird | 0 / 15 |
| Spencer Rascoff | 0 / 13 |
| Kirby Winfield | 0 / 14 |
| Scott Berkun | 0 / 12 |
| Sanjay Parthasarathy | 0 / 12 |
| Dan Lewis | 0 / 20 |
| Rudy Gadre | 0 / 16 |
| Robbie Bach | 0 / 11 |
| Mark Mader | 0 / 24 |
| Dave Parker | 0 / 20 |
| Lisa Nelson | 0 / 15 |
| Joe Heitzeberg | 0 / 16 |
| Rahul Sood | 0 / 12 |
| Jonathan Sposato | 0 / 12 |
| John Lauer | 0 / 16 |
| Tim Porter | 0 / 15 |
| Julie Sandler | 0 / 9 |
| Glenn Kelman | 0 / 16 |
| Hansen Hosein | 0 / 12 |
| Liz Pearce | 0 / 14 |
