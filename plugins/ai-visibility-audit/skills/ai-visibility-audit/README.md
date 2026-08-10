# AI Visibility Audit (Claude skill)

HM Ventures fork of the skill originally built by **[Mike Futia](https://www.skool.com/scale-ai/about)**
(more Claude Code systems like this inside **[SCALE AI](https://www.skool.com/scale-ai/about)**).
Modified here for a cheaper hybrid API setup and a couple of extra checks — see "What's different
in this fork" below.

When people ask AI for the best product in your category, does it recommend **you** — or your
competitors? This skill runs your category's buyer questions through **Google AI Overview,
ChatGPT, and Perplexity**, detects whether your brand is named/cited, shows **who AI recommends
instead**, and scores your overall AI visibility — in a dashboard, plus a PDF + brief ready to send
a client.

## Install

Installed as part of the `hmventures` plugin marketplace:
```
/plugin marketplace add howardwkim/hmventures
/plugin install ai-visibility-audit@hmventures
```
Restart Claude Code after installing.

Then do the one-time key setup: follow **PLAYBOOK.md** (Apify token + OpenAI key in a `.env`).
Copy `.env.example` to `.env` and paste your keys there — `.env` is gitignored, so it stays local.

## Use
> **run the ai visibility audit**

It asks two questions — your **brand + website** and your **category** — then generates the
buyer questions, queries the AI engines, and opens a dashboard with your visibility score,
per-engine breakdown, the competitor leaderboard, and how to fix the gaps.
Output lands in `./ai-visibility/`.

## What's inside
```
ai-visibility-audit/
├── SKILL.md                 the runbook Claude follows
├── PLAYBOOK.md              one-time Apify + OpenAI key setup
├── .env.example             copy to .env, add your keys
├── .gitignore               keeps .env and run output out of git
└── scripts/
    ├── run_audit.py         queries the AI engines, detects brand presence
    ├── render_dashboard.py  renders the dark dashboard + reputation-risk section
    └── export_pdf.py        headless-Chrome dashboard.pdf + brief.txt for every run
```

## What's different in this fork
- **ChatGPT leg moved off Apify** — calls OpenAI's Responses API directly (`web_search` tool)
  instead of routing it through an Apify add-on. Cheaper and one less thing for Apify's free
  tier to hard-abort mid-run on.
- **Reputation-risk check** — any review platform surfaced in the audit with a rating under 3/5
  triggers a pull of the real underlying reviews, since the AI engines have been caught inventing
  complaints that aren't actually in the source.
- **Auto PDF + brief export** — every run produces `dashboard.pdf` and `brief.txt`, no manual export
  step, so a run is immediately forwardable to a client.
- **Windows console encoding fix** — unicode in `print()` no longer crashes the run on `cp1252`.

## Notes
- Being **named in the answer** is the goal (that's a recommendation) — stronger than just being cited in the sources.
- Runs take a few minutes (AI engines are slow). ~$1.15–1.40 per 24-query audit on this fork's
  Apify Starter + OpenAI direct setup — see PLAYBOOK.md for the breakdown.
- Requires an Apify token + an OpenAI key (PLAYBOOK.md) + Python 3.

## Example run

Run against **HexClad** (24 buyer questions, US, July 2026):

| | Result |
|---|---|
| Overall visibility | **28%** |
| Queries containing "HexClad" | **100%** (12/12) |
| Queries that don't name the brand | **12%** (7/59) |
| `hexclad.com` cited as a source | 4 of 71 answers |
| Named most instead | All-Clad, Tramontina, GreenPan |

A brand that spends heavily on ads was named every time a buyer already knew it, and almost never in the
questions that *start* a purchase — which is the gap this skill is built to find.

## Who built this

Made by **Mike Futia**.

I build production-grade Claude Code systems for ecommerce brands, creative agencies, and performance
marketers, and I drop new workflows like this one every week inside my community.

**[Join 600+ brands and agencies in SCALE AI →](https://www.skool.com/scale-ai/about)**
