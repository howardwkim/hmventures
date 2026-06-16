---
name: social-post
description: Create and publish a social media post from a file or inline content. Use when the user says "post this", "create a post", "upload to social", "post to LinkedIn/X/Instagram/etc", "share this on social", "schedule a post", or "/social-post". Drives the whole flow — picks accounts, fills required fields, confirms it actually went live. Backend (woopsocial) lives behind a swappable adapter.
---

# social-post

Take content the user hands you (a file path or inline text, optionally media) and get it published to their social accounts — confirmed live, not just submitted.

This skill is **backend-agnostic by construction**. The orchestration below speaks in abstract verbs. Exactly one file maps those verbs to the live backend:

**Active adapter: `woopsocial-adapter.md` (read it before doing anything).**

To swap backends later, you rewrite *only* the adapter file. Never put a backend's tool names or API details in this file.

## The five verbs

The adapter implements each of these. This file decides *when* to call them.

1. `resolve_targets()` → the projects and social accounts available to post to
2. `required_fields(platform, postType)` → which fields a given target demands
3. `upload_media(projectId, filePath)` → a media handle to reference in content
4. `publish({text, mediaHandles, targets, mode, scheduledFor?})` → submits, returns a postId
5. `confirm(postId, mode)` → resolves what actually happened per account

## Flow

Run this top to bottom. Stop and ask only when a field is genuinely required and you can't infer a sane default.

### 1. Get the content
- If the user named a file, read it. If inline, use it as-is.
- Separate **text** from **media** (image/video paths). A post can be text-only, media-only, or both.
- Don't rewrite the content unless asked. If it's obviously too long for a named platform (X), flag it — don't silently truncate.

### 2. Resolve targets
- Call `resolve_targets()`. This lists projects (Business Profiles) and the social accounts under each.
- Map the user's intent to accounts:
  - They named platforms ("post to LinkedIn and X") → match those accounts.
  - They named nothing → show the available accounts and ask which, **recommending** a default set if there's an obvious one (e.g. all accounts in the only project).
- **Hard constraint:** every target in one post must belong to the **same project**. If the selection spans projects, split into separate posts (one per project) and say so.

### 3. Determine required fields, fill the gaps
- For each chosen account, call `required_fields(platform, postType)`. Platforms differ a lot:
  - Some need almost nothing (X, LinkedIn).
  - Some need a `postType` (Facebook, Instagram, TikTok).
  - Some need extra data (Pinterest: a board; YouTube: title + privacy; TikTok: privacy + a batch of disclosure booleans).
- For every required field not already provided: **propose a default and confirm in one batched message** — don't interrogate field-by-field. Example: "TikTok needs privacy + a few flags. I'll use Public, comments on, duet/stitch on, not branded content — ok?"
- Infer `postType` from the media when possible (video file → VIDEO/REEL; image → IMAGE/POST; no media → TEXT_ONLY).

### 4. Upload media (only if there is media)
- For each media file, call `upload_media(projectId, filePath)` → handle.
- This can be slow for video. Say so if it's a big file.

### 5. Decide the mode
Three modes — ask only if ambiguous; default to **publish-now** when the user said "post this":
- `publish-now` — go live immediately
- `schedule-for-later` — needs a UTC time; convert from whatever the user said
- `draft` — save without delivering

### 6. Dry-run, then publish
- **Always dry-run first** if the backend supports validation (the adapter says how). Catch field/media errors before committing.
- Then `publish(...)`. Capture the returned `postId`.

### 7. Confirm — this is the point of the skill
Never report success on submission alone. `confirm(postId, mode)`:
- **publish-now** → poll until every account reaches a terminal state or a ~60–90s timeout. Report per account: ✅ live / ❌ failed (with the reason) / ⏳ still pending at timeout. A post can succeed on one account and fail on another — report the truth, per account.
- **schedule-for-later** → confirm accepted + echo the scheduled time. Can't watch it go live; say so.
- **draft** → confirm the draft exists.

### 8. Report
End with a short result block: per-account outcome, the postId, and — for anything failed/pending — the next action.

## Notes
- Test without touching real platforms: the adapter exposes a sandbox target (`WOOPTEST`) that runs the full pipeline but publishes nowhere. Use it when validating this skill or a config change.
- If targets, project IDs, or default account sets start needing to be remembered across runs, that's a config file — propose one then; don't build it speculatively.
