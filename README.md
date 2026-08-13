# hmventures

Shared workspace for Howard Kim (@howardwkim) and Matt Grabham (@mgrabham).

Primary interface: Claude Code.

This repo is also a Claude Code [plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces) — shared skills live under `plugins/`.

## Install a shared skill (one-time, per person)

In Claude Code:

```
/plugin marketplace add howardwkim/hmventures
/plugin install social-post@hmventures
```

Then restart Claude Code.

## Skills

### social-post
Create and publish a social media post from a file or inline content. Picks accounts,
fills required platform fields, and confirms the post actually went live (not just
submitted). Backend is woopsocial, isolated behind a swappable adapter.

**Requires the woopsocial MCP.** The skill posts through it. Add it once (the API key
is shared privately, not stored in this repo):

```
claude mcp add --transport http -s user woopsocial "https://api.woopsocial.com/mcp?api_key=PASTE_KEY_HERE"
```

Restart Claude Code after adding. Then point the skill at a file — e.g. *"post this video to TikTok."*

### ai-visibility-audit
Audits whether AI (Google AI Overview, ChatGPT, Perplexity) recommends a brand for buyer-intent
category questions — shows who AI names instead, scores overall AI visibility, and flags
reputation risk when a review platform surfaces a rating under 3/5. HM Ventures fork of
[mikefutia/ai-visibility-audit](https://github.com/mikefutia/ai-visibility-audit) — see that
plugin's own README for what changed in this fork.

```
/plugin install ai-visibility-audit@hmventures
```

**Requires an Apify token + an OpenAI key**, both in a local `.env` (keys are per-person, not
stored in this repo). Follow `PLAYBOOK.md` inside the plugin for setup. Then say *"run the ai
visibility audit."*

### miho-blog-post
Publish a finished article to the MiHO Partners blog at
[mihopartners.com/blog](https://mihopartners.com/blog). Takes finished writing in any
format, converts it into the site's article format, checks it builds, pushes, and confirms it
actually went live. It only publishes — it does not write or edit.

**Requires collaborator access** to the private site repo `howardwkim/miho-partners-landing`
(ask Howard). No Vercel account is needed — the push itself triggers the deploy.

```
/plugin install miho-blog-post@hmventures
```

Then hand it a finished article — e.g. *"publish this to the blog."*

## Docs

Non-plugin reference material lives under `docs/`.

- [`docs/miho/`](docs/miho/) — MiHO Partners brand knowledge (positioning, voice, ICP, proven angles) and Mike's content-pipeline commands (`/staff-writer`, `/social-package`), kept for shared visibility. See that folder's README for what's runnable vs. reference-only.
