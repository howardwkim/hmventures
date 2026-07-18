# Content profile contract

Discovery consumes one authored Markdown file. It never creates or edits it.

## Frontmatter

Required:

- `profile_id`: stable kebab slug
- `version`: string
- `authored_at`: ISO date
- `source_documents`: list of paths or source labels

Optional:

- `reddit_sources`: path (relative to the profile file) to a sibling Reddit-sources
  config — see `reddit-sources-contract.md`. When present, the reddit-researcher reads
  it for subreddits/query/sort/window/gate instead of any default. The profile
  references this file so an editorial-territory or audience change prompts a check
  of whether the Reddit sources still fit — the two are edited together, not merged
  into one file.

## Body headings

1. Identity
2. Business and offering
3. Target audience
4. Audience problems
5. Expertise and authority
6. Editorial territory
7. Proven angles
8. Exclusions and boundaries
9. Discovery guidance
10. Writing voice and defaults

Only `Identity` plus one of Business and offering, Target audience, Expertise and
authority, or Editorial territory must contain substantive text. Optional empty
sections contain exactly `Not specified`. Treat that marker as absent. Never infer
missing profile facts merely to make the profile look complete.

## Runtime resolution

State directory: `<state_root>/<profile_id>/`, where `state_root` comes from this
skill's `config.json` (default `~/.content-profiles` if the file or key is absent).
An explicit state-root supplied by the caller overrides the config value for tests.
