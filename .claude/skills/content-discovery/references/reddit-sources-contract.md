# Reddit sources contract

An authored YAML file, sibling to a content profile, naming where and how the
reddit-researcher looks on Reddit for that profile. Optional — a profile with no
`reddit_sources` field gets no Reddit research. Discovery never creates or edits it.

Referenced from the profile's `reddit_sources` frontmatter field so the two are
authored together: an editorial-territory or audience change is a prompt to check
whether this file still fits, not a separate untracked concern.

## Shape

```yaml
subreddits:
  - smallbusiness
  - Entrepreneur
  - sweatystartup

query: ""       # blank = browse the listing; set to keyword-search each subreddit
sort: top       # top | hot | new | rising | controversial
t: week         # day | week | month | year | all — time window (only applies to top/controversial)
min_score: 25
min_comments: 3
```

All fields optional except `subreddits`; omitted fields take `reddit_fetch.py`'s own
defaults (`query: ""`, `sort: top`, `t: week`, `min_score: 25`, `min_comments: 3`).

## Notes

- `query` blank is the default — pure top/hot/new/rising/controversial browsing of each
  subreddit. Set it to search a specific term inside each subreddit instead
  (`restrict_sr=on`); the search and browse code paths use different parsers, both
  implemented in `scripts/reddit_fetch.py`.
- This file is where cadence/target tuning happens over time — swap in a different
  time window, try a new subreddit, change the query — without touching profile prose
  or the skill's own instructions.
- Auto-exploring new subreddits/queries beyond what's listed here (when the known-good
  set goes stale) is a deferred feature, not yet built.
