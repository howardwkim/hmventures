# Adapter: woopsocial

The active backend for `social-post`. This is the **only** file in the skill that
references woopsocial. To swap backends, replace this file's verb mappings; leave
`SKILL.md` untouched.

All tool names below are MCP tools (`mcp__woopsocial__*`), invoked by the agent.
The one exception is the media byte upload (a plain HTTP PUT), noted in verb 3.

## Model

`Organization → Projects (UI: "Business Profiles") → Social Accounts`.
A social account belongs to exactly one project. **All targets in a single post
must share one project.**

Platforms: `FACEBOOK`, `INSTAGRAM`, `LINKEDIN`, `LINKEDIN_PAGES`, `PINTEREST`,
`TIKTOK`, `X`, `YOUTUBE`, and `WOOPTEST` (sandbox — full pipeline, publishes nowhere).

## Verb 1 — resolve_targets()

- `mcp__woopsocial__projects_list` → projects (each ≈ a Business Profile).
- `mcp__woopsocial__social_accounts_list({projectId})` → accounts usable for publishing
  in that project. Omit `projectId` to list across all.
- Each account carries its `socialAccountId` and `platform` — both needed downstream.

## Verb 2 — required_fields(platform, postType)

woopsocial validates per platform. Required fields by platform (beyond `platform` +
`socialAccountId`):

| Platform | Required | Optional / notes |
|---|---|---|
| `X` | — | text and/or media |
| `LINKEDIN` / `LINKEDIN_PAGES` | — | `link` (preview card) |
| `FACEBOOK` | `postType` ∈ TEXT_ONLY, IMAGE, VIDEO, REEL, STORY | `link` |
| `INSTAGRAM` | `postType` ∈ POST, REEL, STORY | `coverMediaId` (REEL only) |
| `PINTEREST` | `pinterestBoardId` | `title`, `link` |
| `YOUTUBE` | `title`, `privacy` ∈ public, private, unlisted | `tags`, `category`, `madeForKids` |
| `TIKTOK` | `postType` ∈ VIDEO, PHOTO; `privacyLevel` ∈ PUBLIC_TO_EVERYONE, SELF_ONLY, MUTUAL_FOLLOW_FRIENDS, FOLLOWER_OF_CREATOR; **all of** `allowComment`, `allowDuet`, `allowStitch`, `isYourBrand`, `isBrandedContent`, `autoAddMusic` (booleans) | `postMode`, cover ids |
| `WOOPTEST` | — | `shouldSucceed` (default true; set false to simulate failure) |

TikTok's boolean disclosure flags are all *required by the API* even when a given
flag doesn't apply to the chosen postType — send sane defaults for all six.

## Verb 3 — upload_media(projectId, filePath)

Chunked upload, three steps:

1. `mcp__woopsocial__media_uploads_create_session({projectId, fileSizeInBytes})`
   → returns `uploadSessionId`, `partCount`, `partSizeInBytes`, and `parts[]` each
   with an `uploadUrl`.
2. **HTTP PUT each part** to its `parts[n].uploadUrl` (NOT an MCP call — use curl).
   Every part except the last must be exactly `partSizeInBytes`; the last may be smaller.
3. `mcp__woopsocial__media_uploads_complete_session({uploadSessionId})` → finalizes
   and yields the **`mediaId`**. (Poll `media_uploads_get_session` if you need status.)

The media handle is `{ type: "MEDIA_LIBRARY", mediaId }`.

## Verb 4 — publish({text, mediaHandles, targets, mode, scheduledFor?})

`mcp__woopsocial__posts_create` (dry-run with the identical `mcp__woopsocial__posts_validate`).

Request shape:
```
{
  content: [ { text: "<text>", media: [ { type: "MEDIA_LIBRARY", mediaId } , ... ] } ],   // exactly 1 item
  schedule: { type: "PUBLISH_NOW" }
           | { type: "DRAFT" }
           | { type: "SCHEDULE_FOR_LATER", scheduledFor: "<UTC ISO-8601>" },
  socialAccounts: [ { platform, socialAccountId, ...platform-required fields }, ... ],
  autoDeleteMediaAfterPublish?: false
}
```
- `mode` maps to `schedule.type`: publish-now→`PUBLISH_NOW`, schedule-for-later→`SCHEDULE_FOR_LATER` (+ `scheduledFor`), draft→`DRAFT`.
- Per-account `contentOverride` is available if one account needs different text/media.
- Validation is atomic: if any account fails, nothing is created. Returns the `postId`.

## Verb 5 — confirm(postId, mode)

`mcp__woopsocial__posts_get({postId})` → the post with its **social account child posts
inline**, each carrying a delivery state.

- **publish-now**: poll `posts_get` until every child post is terminal (success/failure)
  or ~60–90s elapses. Report per account from the child states.
- **schedule-for-later**: one `posts_get` to confirm it's accepted/scheduled; report the time.
- **draft**: one `posts_get` to confirm the draft exists.

Webhooks (`webhooks_create_endpoint`) exist for out-of-session delivery events — not used
by the in-session flow, but available if a future caller wants push confirmation instead of polling.

## Swapping this adapter

A replacement backend must provide the five verbs. A likely second adapter is a
browser-automation publish layer (no API): it would implement `resolve_targets`
from a local account registry, `upload_media` as a local file reference, `publish`
by driving a headful browser, and `confirm` by reading the posted URL back. Keep
that target in mind, but don't build it until it's real.
