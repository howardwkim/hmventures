---
name: ai-visibility-audit
description: >
  Audit whether AI recommends a brand. Runs a category's buyer questions through Google
  AI Overview, ChatGPT, and Perplexity, detects if the brand is mentioned/cited, shows
  which competitors AI recommends instead, and scores overall AI visibility. Trigger on
  "run the ai visibility audit", "does AI recommend my brand", "am I showing up in
  ChatGPT / AI search", "AI search visibility", "GEO audit", "AEO audit".
allowed-tools: Bash(python3 *) Read Write
---

# AI Visibility Audit

When invoked, run this pipeline. Scripts are Python 3 **stdlib only**. Output → `./ai-visibility/`. It queries live AI engines, so a run takes **5–10 minutes** (more queries = longer) — tell the user that up front so the wait isn't a surprise.

**Ask the user two questions first (wait for answers):**
1. **What's your brand name and website?** (e.g. "Primally Pure — primallypure.com")
2. **What category are you in?** (e.g. "natural deodorant", "project management software") — used to generate the buyer questions people actually ask AI.

(Default market is US; default engines are Google AI Overview + ChatGPT + Perplexity.)

## 0 — Token check (and first-run setup)
Hybrid sourcing (cost optimization added 2026-08-03): AI Overview + Perplexity run through Apify; ChatGPT runs through OpenAI's own Responses API (`gpt-5.6` + `web_search` tool) directly — far cheaper than Apify's chatgpt-result-scraped add-on (~$0.03-0.04/query vs ~$0.08+/event).
Needs both `APIFY_TOKEN` and `OPENAI_API_KEY`, from env vars, this skill's `.env`, or `./.env`. If missing, walk the user through it (don't just point at a file): Apify token at console.apify.com/settings/integrations, OpenAI key at platform.openai.com/api-keys → add both to `${CLAUDE_SKILL_DIR}/.env`, tell them to paste it into that file (never into chat), then continue.
Apify's free tier caps at **$5/month** — hits mid-run for anything beyond ~1 audit. For regular client audits (2-3/week), the Starter plan ($29/mo) is required.

## 1 — Generate the buyer questions
Write **20–25 real buyer-intent queries** for the category to `./ai-visibility/queries.txt` (one per line) — more queries = a truer visibility score and a fuller competitor leaderboard. If the user asks for more/fewer, follow that. Mix these shapes:
- `best {category}`, `best {category} for {use case}`, `top {category} brands`
- `most effective {category}`, `{category} reviews`, `is {brand} worth it`
- `{brand} vs {top competitor}`, `{category} for {specific audience}`
Make them the questions a real buyer would type into ChatGPT — not keywords.

## 2 — Run the audit
```
python3 ${CLAUDE_SKILL_DIR}/scripts/run_audit.py --brand "<brand>" --domain <domain> --queries-file ./ai-visibility/queries.txt --country us
```
Runs every query through Google AI Overview + ChatGPT + Perplexity, detects if the brand is **mentioned** (named in the answer) or **cited** (its domain in the sources), and writes `./ai-visibility/audit.json` + `.csv`. (Add `--engines aioverview,chatgpt` to go faster/cheaper, or add `gemini`.)

## 3 — Mine (the analysis step)
Read `./ai-visibility/audit.json`. For each query + engine, read the AI `answer` and:
- **Extract the competitor brands the AI recommends** (the named brands in the answer). Build a **leaderboard** of who shows up most across all queries/engines — that's who's winning AI search in this category.
- Note **where the brand is invisible** (which engines/queries) and **what AI recommends instead** there.
- Write a one-line **verdict** (e.g. "Strong on Perplexity, nearly invisible on ChatGPT").
- Write 3–5 **fixes** grounded in the data (e.g. "ChatGPT pulls from Good Housekeeping / Byrdie roundups you're not in — get placed there").

Write `./ai-visibility/mined.json`:
```json
{ "stats": {"brand":"","category":"","overall_pct":0,"queries":0,
    "per_engine":{"aioverview":{"seen":0,"of":0},"chatgpt":{"seen":0,"of":0},"perplexity":{"seen":0,"of":0}}},
  "verdict":"",
  "competitors":[{"brand":"","count":0}],
  "queries":[{"query":"","aioverview":true,"chatgpt":false,"perplexity":true,"recommends_instead":"Native, Lume"}],
  "fixes":[""],
  "reputation_risk": null }
```
(Carry the per-engine seen/of counts and overall_pct straight from audit.json's `summary`. Leave `reputation_risk` null unless step 3.5 triggered — if it did, set it to `{"platform":"Yelp","rating":1.4,"review_count":11,"summary":"...","themes":["..."]}`, using only reviews from the last 3 years.)

## 3.5 — Reputation check (only if a platform rating comes in under 3/5)
While mining, if any review platform surfaced in the audit answers (Yelp, Google, BBB, Angi, etc.) shows an aggregate rating under 3/5, pull the real underlying reviews and summarize what's actually going wrong — don't just report the AI's paraphrase of it, verify it directly:
- Find the business's real Yelp/Google/BBB listing URLs (WebSearch).
- Yelp and Angi block direct fetch — use ScraperAPI (`SCRAPERAPI_KEY`, see global credentials) the same way `wine-bot/scrapers/yelp_scraper.py` does: no JS render, parse the `data-apollo-state` Apollo cache for aggregate rating/count. Individual review text is JS-loaded and Yelp blocks ScraperAPI's render tier too — instead get real quoted reviews via WebSearch/mirror sites (e.g. local.yahoo.com listings often mirror Yelp review text) or BBB's own `/customer-reviews` and `/complaints` sub-pages (fetch directly, not JS-blocked).
- **Only count reviews from the last 3 years** — filter by date before drawing any conclusion. This business's own history shows why: only 1 of 5 real reviews found was inside that window; presenting all 5 as "the pattern" would have overstated a stale problem.
- Verify claims — don't repeat what an AI engine's answer *said* the reviews say without checking the actual source page. On the RAZR Restoration audit (2026-08-04), Perplexity claimed BBB showed a complaint about "flooded basement" delays; BBB's own `/complaints` page showed **0 complaints on file** — that detail was an AI fabrication, not a real complaint. Flag any such discrepancy explicitly in the report rather than passing it through.
- Summarize the *recurring* theme across qualifying reviews (billing disputes, missed follow-through, rushed assessments, etc.) in plain language, and add this as a distinct section in `mined.json` (`"reputation_risk"`) and in the client brief — this is a different, more urgent kind of finding than pure AI-search invisibility and should be called out as such, not buried in the fixes list.

## 4 — Render
```
python3 ${CLAUDE_SKILL_DIR}/scripts/render_dashboard.py
```
Writes `./ai-visibility/dashboard.html` (visibility score, per-engine bars, competitor leaderboard, per-query grid, fixes) and opens it.

## 5 — PDF (always run this — every audit gets a deliverable, not just a dashboard)
```
python3 ${CLAUDE_SKILL_DIR}/scripts/export_pdf.py
```
Writes `./ai-visibility/dashboard.pdf` via headless Chrome/Edge, **and opens it automatically** (`os.startfile`/`open`/`xdg-open` — no separate step needed). This is the file Mike forwards to the client — do this automatically on every run, don't wait to be asked, and don't just report the file path in chat and stop there. If for any reason the script's auto-open doesn't visibly work, explicitly open the PDF yourself before reporting done — showing the report *is* the deliverable, not an optional extra step.

## 6 — Client brief (write this every time, alongside the PDF)
Write 3-5 short sentences Mike can paste straight into an email to the client, in plain client-safe language (no "engines", "mentioned vs cited", or internal jargon):
- The headline number and what it means in plain terms.
- Where they're weakest and who's winning instead (1-2 competitor names, not the full leaderboard).
- The single highest-leverage fix.
- Frame it as an opportunity, not just a deficiency — this is a sales-adjacent deliverable.
Save it to `./ai-visibility/brief.txt` and also show it inline in the response so Mike can copy it immediately.

## 7 — Report
The overall visibility %, the engine where they're weakest, the top 3 competitors AI recommends instead, and the #1 fix. Confirm the PDF and brief are ready to forward.

## Notes
- "Mentioned" (named in the answer) matters more than "cited" — being *recommended by name* is the goal.
- Runs are slow because AI engines are slow; ~12 queries × 3 engines ≈ a few minutes.
- Token setup is inline in step 0 — self-contained, no separate doc needed.
