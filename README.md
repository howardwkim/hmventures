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

## Docs

Non-plugin reference material lives under `docs/`.

- [`docs/miho/`](docs/miho/) — MiHO Partners brand knowledge (positioning, voice, ICP, proven angles) and Mike's content-pipeline commands (`/staff-writer`, `/social-package`), kept for shared visibility. See that folder's README for what's runnable vs. reference-only.
