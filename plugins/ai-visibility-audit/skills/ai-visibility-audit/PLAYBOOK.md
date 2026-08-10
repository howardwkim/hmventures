# Setup — get your API keys (one time, ~5 min)

This is the HM Ventures hybrid version: AI Overview + Perplexity go through Apify, ChatGPT goes
through OpenAI's Responses API directly (cheaper than routing it through Apify too). You need
two keys.

## Apify token
1. Sign in (or sign up free) at **[apify.com](https://apify.com)**.
2. Go to **Settings → Integrations** ([console.apify.com/settings/integrations](https://console.apify.com/settings/integrations)).
3. Copy your **Personal API token**.
4. **Free tier caps at $5/month and hard-aborts a run mid-way once you hit it** — fine for trying
   the skill once, not enough for recurring use. Upgrade to **Starter ($29/mo)** before running this
   more than a couple times.

## OpenAI key
1. Get an API key at **[platform.openai.com/api-keys](https://platform.openai.com/api-keys)**.
2. Needs access to the **Responses API** with the `web_search` tool (used for the ChatGPT leg).

## Save both
Create a file named **`.env`** in **this skill's folder**:
```
APIFY_TOKEN=your_apify_token_here
OPENAI_API_KEY=your_openai_key_here
```
Don't paste either key into chat or commit `.env` — it's gitignored.

## Then just say
> **run the ai visibility audit**

It asks for your brand + website and your category, then checks whether AI recommends you.

## Cost & notes
- **Apify (AI Overview + Perplexity):** on Starter tier, a full 24-query run costs roughly
  $0.40–$0.50 — much cheaper than the free-tier per-event rate. Don't extrapolate cost from a
  free-tier run.
- **OpenAI (ChatGPT leg):** roughly $0.03–0.04/query direct via the Responses API, ~$0.75-1.00
  for a full 24-query run.
- **Blended total: ~$1.15–1.40 per 24-query audit.** At 2-3 audits/week that's ~$10-18/month in
  API cost on top of the $29 Apify Starter base.
- **Runs take a few minutes** — the AI engines (ChatGPT/Perplexity) are slow to answer. That's normal.
- Requires **Python 3**.
- Any review platform surfaced in the audit with a rating under 3/5 triggers a reputation-risk
  check — the script pulls real underlying reviews rather than trusting the AI engines' paraphrase
  (AI answers have been caught inventing complaints that don't exist in the source).
- Every run auto-produces `dashboard.pdf` + `brief.txt` in the output folder, ready to forward to
  a client.
