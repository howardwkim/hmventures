#!/usr/bin/env python3
"""Reddit candidate fetcher for the content-discovery reddit-researcher.

Portable — no ssh to a named machine, no dependency on Howard's personal
Hermes digest or its config. Calls the stealth-fetch tool vendored alongside
this script under scripts/vendor/scrapling/ (path configurable via the
skill's config.json, key "scrapling_project") — headless Camoufox clears
Reddit's bot-detection block; confirmed 2026-07-15 — and parses
old.reddit.com's HTML directly, since the .json endpoint stays blocked even
through this route.

Everything here is deterministic — regex/attribute parsing only, no LLM calls
anywhere in this file. Judgment (is this a good pitch, what's the angle)
belongs entirely to the caller; this script only collects and cleans data.

Two listing modes, chosen by whether --query is set:
  browse  (query blank, the default) — a subreddit's hot/new/rising/top/
          controversial listing.
  search  (query set)                — keyword search within the subreddit,
          restricted to it (restrict_sr=on).

Pipeline: fetch listing/search -> dedupe by post_id -> drop --exclude-ids ->
engagement gate (--min-score/--min-comments) -> fetch full detail (body text +
top real comments, AutoModerator/stickied dropped programmatically) for the
top --detail-limit gated posts by score.

Usage:
    uv run reddit_fetch.py --subreddits smallbusiness,Entrepreneur \
        --sort top --t week --min-score 25 --min-comments 3 --detail-limit 15

    uv run reddit_fetch.py --subreddits smallbusiness --query delegation \
        --sort top --t year --exclude-ids t3_1uviptz,t3_1uw84p0

Prints a JSON array of candidate posts to stdout. Read-only: never records,
never marks anything viewed, never writes runtime state — the caller (the
reddit-researcher agent) owns all judgment and all writes.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path


def _load_scrapling_tool() -> Path:
    """Resolve the vendored scrapling project, honoring config.json's
    "scrapling_project" override (relative paths resolve against the skill
    root; absolute paths pass through unchanged)."""
    skill_root = Path(__file__).resolve().parents[1]
    config_path = skill_root / "config.json"
    config = json.loads(config_path.read_text()) if config_path.exists() else {}
    raw = config.get("scrapling_project", "scripts/vendor/scrapling")
    path = Path(raw).expanduser()
    return path if path.is_absolute() else (skill_root / path)


SCRAPLING_TOOL = _load_scrapling_tool()

# Listing sorts that take a time window (?t=); hot/new/rising don't.
_WINDOWED_SORTS = {"top", "controversial"}


class ThingParser(HTMLParser):
    """Pulls attributes off old.reddit's <div class="... thing ..."> listing rows."""

    def __init__(self) -> None:
        super().__init__()
        self.posts: list[dict] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "div":
            return
        d = dict(attrs)
        classes = (d.get("class") or "").split()
        if "thing" not in classes or "link" not in classes:
            return
        if not d.get("data-fullname"):
            return
        self.posts.append(d)


def fetch_html(url: str) -> str:
    proc = subprocess.run(
        ["uv", "run", "--project", str(SCRAPLING_TOOL), str(SCRAPLING_TOOL / "fetch.py"), url, "--tier", "stealthy"],
        capture_output=True, text=True, timeout=120,
    )
    if proc.returncode not in (0, 1):
        raise RuntimeError(f"fetch.py crashed for {url}: {proc.stderr.strip()[-500:]}")
    payload = json.loads(proc.stdout)
    if not payload["ok"]:
        raise RuntimeError(f"fetch failed for {url}: status {payload['status']}")
    return payload["html"]


def fetch_subreddit_listing(sub: str, sort: str, t: str, limit: int) -> list[dict]:
    url = f"https://old.reddit.com/r/{urllib.parse.quote(sub)}/{sort}/"
    if sort in _WINDOWED_SORTS:
        url += f"?t={t}"
    html = fetch_html(url)
    parser = ThingParser()
    parser.feed(html)

    posts = []
    for d in parser.posts[:limit]:
        permalink = d.get("data-permalink", "")
        posts.append({
            "post_id": d.get("data-fullname"),
            "subreddit": sub,
            "title": d.get("data-title") or _title_from_permalink(permalink),
            "reddit_url": f"https://old.reddit.com{permalink}",
            "external_domain": d.get("data-domain"),
            "score": _to_int(d.get("data-score")),
            "num_comments": _to_int(d.get("data-comments-count")),
            "created_utc_ms": _to_int(d.get("data-timestamp")),
            "author": d.get("data-author"),
        })
    return posts


_SEARCH_ROW_RE = re.compile(
    r'data-fullname="(?P<id>t3_[a-z0-9]+)".*?'
    r'class="search-title[^"]*">(?P<title>[^<]+)</a>.*?'
    r'<span class="search-score">(?P<score>[\d,]+)\s*points?</span>.*?'
    r'class="search-comments[^"]*">(?P<comments>[\d,]+)\s*comments?</a>.*?'
    r'<time[^>]*datetime="(?P<datetime>[^"]+)"',
    re.DOTALL,
)
_SEARCH_AUTHOR_RE = re.compile(r'class="author[^"]*">(?P<author>[^<]+)</a>')


def fetch_subreddit_search(sub: str, query: str, sort: str, t: str, limit: int) -> list[dict]:
    params = {"q": query, "restrict_sr": "on", "sort": sort, "t": t}
    url = f"https://old.reddit.com/r/{urllib.parse.quote(sub)}/search/?{urllib.parse.urlencode(params)}"
    html = fetch_html(url)

    posts = []
    for m in list(_SEARCH_ROW_RE.finditer(html))[:limit]:
        block_start = m.start()
        url_match = re.search(r'<a href="([^"]+)" class="search-title', html[block_start:block_start + 2000])
        reddit_url = url_match.group(1) if url_match else None
        author_match = _SEARCH_AUTHOR_RE.search(html, m.end(), m.end() + 500)

        created_utc_ms = None
        try:
            created_utc_ms = int(dt.datetime.fromisoformat(m.group("datetime")).timestamp() * 1000)
        except ValueError:
            pass

        posts.append({
            "post_id": m.group("id"),
            "subreddit": sub,
            "title": _unescape(m.group("title")),
            "reddit_url": reddit_url,
            "external_domain": None,
            "score": _to_int(m.group("score").replace(",", "")),
            "num_comments": _to_int(m.group("comments").replace(",", "")),
            "created_utc_ms": created_utc_ms,
            "author": author_match.group("author") if author_match else None,
        })
    return posts


# --- post detail (body + top real comments) -------------------------------

_COMMENT_THING_RE = re.compile(
    r'<div class="(?P<classes>[^"]*\bcomment\b[^"]*)"[^>]*data-author="(?P<author>[^"]*)"'
)
_MD_RE = re.compile(r'<div class="md">(.*?)</div>\s*</div>', re.DOTALL)


def fetch_post_detail(post_id: str, reddit_url: str, comment_limit: int = 5) -> dict:
    html = fetch_html(reddit_url)

    post_start = html.find(f'data-fullname="{post_id}"')
    commentarea_start = html.find('class="commentarea"')
    if post_start == -1 or commentarea_start == -1:
        return {"body_text": None, "top_comments": []}

    post_region = html[post_start:commentarea_start]
    body_text = None
    body_idx = post_region.find("usertext-body")
    if body_idx != -1:
        body_m = _MD_RE.search(post_region[body_idx:body_idx + 4000])
        if body_m:
            body_text = _clean_html_text(body_m.group(1))

    commentarea = html[commentarea_start:]
    comments = []
    for m in _COMMENT_THING_RE.finditer(commentarea):
        if "stickied" in m.group("classes"):
            continue
        author = m.group("author")
        if not author or author.lower() == "automoderator":
            continue
        tail = commentarea[m.end():m.end() + 3000]
        body_m = _MD_RE.search(tail)
        if not body_m:
            continue
        text = _clean_html_text(body_m.group(1))
        if not text:
            continue
        comments.append({"author": author, "text": text[:500]})
        if len(comments) >= comment_limit:
            break

    return {"body_text": body_text, "top_comments": comments}


def _clean_html_text(fragment: str) -> str:
    text = _unescape(re.sub(r"<[^<]+?>", " ", fragment))
    return re.sub(r"\s+", " ", text).strip()


def _unescape(s: str) -> str:
    import html as html_lib
    return html_lib.unescape(s).strip()


def _title_from_permalink(permalink: str) -> str:
    parts = [p for p in permalink.split("/") if p]
    return parts[-1].replace("_", " ") if parts else ""


def _to_int(v: str | None) -> int | None:
    try:
        return int(v) if v is not None else None
    except (ValueError, TypeError):
        return None


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--subreddits", required=True, help="comma-separated subreddit names")
    p.add_argument("--query", default="", help="keyword search within each subreddit; blank (default) browses the listing instead")
    p.add_argument("--sort", default="top", choices=["top", "hot", "new", "rising", "controversial"])
    p.add_argument("--t", default="week", choices=["day", "week", "month", "year", "all"])
    p.add_argument("--limit-per-sub", type=int, default=25)
    p.add_argument("--min-score", type=int, default=25)
    p.add_argument("--min-comments", type=int, default=3)
    p.add_argument("--exclude-ids", default="", help="comma-separated post fullnames (t3_...) already seen in prior runs — dropped before gating")
    p.add_argument("--detail-limit", type=int, default=15, help="how many gated posts (top-scoring first) get a full body+comments fetch; the rest stay title/metadata-only")
    args = p.parse_args()

    candidates = []
    errors = []
    for raw_sub in args.subreddits.split(","):
        sub = raw_sub.strip().lstrip("r/")
        if not sub:
            continue
        try:
            if args.query.strip():
                candidates.extend(fetch_subreddit_search(sub, args.query.strip(), args.sort, args.t, args.limit_per_sub))
            else:
                candidates.extend(fetch_subreddit_listing(sub, args.sort, args.t, args.limit_per_sub))
        except Exception as e:
            errors.append({"subreddit": sub, "error": str(e)})

    # dedupe by post_id (first occurrence wins), preserving order
    seen_ids = set()
    deduped = []
    for c in candidates:
        pid = c["post_id"]
        if pid in seen_ids:
            continue
        seen_ids.add(pid)
        deduped.append(c)

    exclude_ids = {x.strip() for x in args.exclude_ids.split(",") if x.strip()}
    deduped = [c for c in deduped if c["post_id"] not in exclude_ids]

    gated = [
        c for c in deduped
        if (c["score"] or 0) >= args.min_score and (c["num_comments"] or 0) >= args.min_comments
    ]

    gated.sort(key=lambda c: c["score"] or 0, reverse=True)
    to_fetch = [i for i, post in enumerate(gated) if i < args.detail_limit and post.get("reddit_url")]
    for i, post in enumerate(gated):
        if i not in to_fetch:
            post["detail_fetched"] = False

    def _fetch_one(i: int) -> tuple[int, dict | None, str | None]:
        post = gated[i]
        try:
            return i, fetch_post_detail(post["post_id"], post["reddit_url"]), None
        except Exception as e:
            return i, None, str(e)

    if to_fetch:
        with ThreadPoolExecutor(max_workers=min(5, len(to_fetch))) as executor:
            for i, detail, err in executor.map(_fetch_one, to_fetch):
                post = gated[i]
                if err is None:
                    post.update(detail)
                    post["detail_fetched"] = True
                else:
                    post["detail_fetched"] = False
                    errors.append({"post_id": post["post_id"], "error": err})

    print(json.dumps({
        "posts": gated,
        "raw_count": len(candidates),
        "deduped_count": len(deduped),
        "gated_count": len(gated),
        "detail_fetched_count": sum(1 for p in gated if p.get("detail_fetched")),
        "errors": errors,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
