#!/usr/bin/env python3
"""General-purpose stealth-fetch primitive, built on Scrapling.

Not Reddit-specific — any skill/tool that needs a page past ordinary bot
detection calls this. Three tiers, cheapest first:

  http      Fetcher — curl_cffi TLS/browser impersonation, no browser process.
  stealthy  StealthyFetcher — Camoufox (stealth Firefox), works headless.
  dynamic   DynamicFetcher — Playwright/Chromium, full automation control.

Usage:
    uv run fetch.py <url> [--tier http|stealthy|dynamic] [--headless/--headed]

Prints JSON to stdout: {"url": ..., "status": ..., "ok": bool, "html": "..."}
"""
from __future__ import annotations

import argparse
import json
import sys


def fetch(url: str, tier: str = "stealthy", headless: bool = True, impersonate: str = "chrome") -> dict:
    if tier == "http":
        from scrapling.fetchers import Fetcher
        r = Fetcher.get(url, impersonate=impersonate)
    elif tier == "stealthy":
        from scrapling.fetchers import StealthyFetcher
        r = StealthyFetcher.fetch(url, headless=headless)
    elif tier == "dynamic":
        from scrapling.fetchers import DynamicFetcher
        r = DynamicFetcher.fetch(url, headless=headless)
    else:
        raise SystemExit(f"unknown tier: {tier!r} (expected http|stealthy|dynamic)")

    body = r.body or ""
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")

    return {
        "url": url,
        "status": r.status,
        "ok": 200 <= r.status < 300,
        "html": body,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("url")
    p.add_argument("--tier", default="stealthy", choices=["http", "stealthy", "dynamic"])
    p.add_argument("--headed", action="store_true", help="run a real (non-headless) browser window; only applies to stealthy/dynamic tiers")
    p.add_argument("--impersonate", default="chrome", help="browser fingerprint to impersonate; only applies to the http tier")
    args = p.parse_args()

    result = fetch(args.url, tier=args.tier, headless=not args.headed, impersonate=args.impersonate)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
