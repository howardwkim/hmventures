#!/usr/bin/env python3
"""
AI Visibility Audit — run a category's buyer questions through Google AI Overview,
ChatGPT, and Perplexity, and detect whether a brand is recommended (vs its competitors).
Python 3 stdlib only.

Hybrid sourcing (cost optimization, added 2026-08-03):
  - aioverview + perplexity -> Apify actor (nFJndFXA5zjCTuudP)
  - chatgpt -> OpenAI Responses API direct (gpt-5.6 + web_search tool) — ~$0.03-0.04/query
    vs Apify's chatgpt-result-scraped add-on (~$0.08+/event). Needs OPENAI_API_KEY.

Tokens: APIFY_TOKEN and OPENAI_API_KEY from env vars, <skill>/.env, or ./.env.

Usage:
  python3 run_audit.py --brand "Primally Pure" --domain primallypure.com --queries-file queries.txt [--country us] [--engines aiOverview,chatgpt,perplexity]

Output (./ai-visibility/): audit.json, audit.csv
"""
import os, sys, json, csv, time, argparse
from urllib.request import urlopen, Request
from urllib.parse import urlparse
from urllib.error import HTTPError, URLError

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.getcwd(), "ai-visibility")
ACTOR = "nFJndFXA5zjCTuudP"  # apify/google-search-scraper (AI Overview + Perplexity add-ons)
OPENAI_MODEL = "gpt-5.6"


def load_env_var(name):
    v = os.environ.get(name, "").strip()
    if v:
        return v
    for p in (os.path.join(SKILL_DIR, ".env"), os.path.join(os.getcwd(), ".env")):
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                line = line.strip()
                if line.startswith(name + "="):
                    v = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if v:
                        return v
    return ""


TOKEN = load_env_var("APIFY_TOKEN")
OPENAI_KEY = load_env_var("OPENAI_API_KEY")


def run_chatgpt_direct(queries):
    """Query OpenAI's Responses API with the web_search tool as a stand-in for ChatGPT search."""
    if not OPENAI_KEY:
        sys.exit("OPENAI_API_KEY not set — add it to this skill's .env to use the chatgpt engine.")
    out = {}
    for i, q in enumerate(queries, 1):
        body = json.dumps({
            "model": OPENAI_MODEL,
            "tools": [{"type": "web_search"}],
            "input": q,
        }).encode("utf-8")
        resp = None
        for attempt in range(3):
            req = Request("https://api.openai.com/v1/responses", data=body, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENAI_KEY}",
            })
            try:
                with urlopen(req, timeout=90) as r:
                    resp = json.loads(r.read().decode("utf-8"))
                break
            except HTTPError as e:
                print(f"  [chatgpt-direct] query {i}/{len(queries)} failed: HTTP {e.code}: {e.read().decode('utf-8')[:200]}")
                break
            except (URLError, OSError, TimeoutError) as e:
                print(f"  [chatgpt-direct] query {i}/{len(queries)} attempt {attempt+1}/3 network error: {e}")
                time.sleep(3)
        if resp is None:
            continue
        text, sources = "", []
        for item in resp.get("output", []):
            if item.get("type") == "message":
                for c in item.get("content", []):
                    text += c.get("text", "")
                    for ann in c.get("annotations", []):
                        if ann.get("type") == "url_citation" and ann.get("url"):
                            sources.append({"url": ann["url"]})
        out[q] = {"content": text, "sources": sources}
    return out


def _get(url):
    try:
        with urlopen(url, timeout=90) as r:
            return json.loads(r.read().decode("utf-8"))
    except HTTPError as e:
        raise SystemExit(f"Apify HTTP {e.code}: {e.read().decode('utf-8')[:200]}")
    except URLError as e:
        raise SystemExit(f"network error: {e.reason}")


def run_actor(queries, country, engines):
    # "chatgpt" is deliberately excluded here — it's sourced via run_chatgpt_direct() instead
    # (OpenAI's own API is far cheaper than Apify's chatgpt-result-scraped add-on).
    apify_engines = [e for e in engines if e != "chatgpt"]
    if not apify_engines:
        return []
    inp = {"queries": "\n".join(queries), "maxPagesPerQuery": 1, "countryCode": country}
    if "aioverview" in engines:
        inp["aiOverview"] = {"scrapeFullAiOverview": True}
    if "perplexity" in engines:
        inp["perplexitySearch"] = {"enablePerplexity": True}
    if "gemini" in engines:
        inp["geminiSearch"] = {"enableGemini": True}
    body = json.dumps(inp).encode("utf-8")
    req = Request(f"https://api.apify.com/v2/acts/{ACTOR}/runs?token={TOKEN}",
                  data=body, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=60) as r:
            run = json.loads(r.read().decode("utf-8"))["data"]
    except HTTPError as e:
        raise SystemExit(f"Apify start error {e.code}: {e.read().decode('utf-8')[:200]}")
    rid, dsid, st = run["id"], run["defaultDatasetId"], None
    print(f"Asking {len(queries)} buyer questions across {', '.join(engines)} (AI engines are slow — 5-10 min)...")
    for _ in range(400):  # up to ~20 min for larger query sets
        time.sleep(3)
        st = _get(f"https://api.apify.com/v2/actor-runs/{rid}?token={TOKEN}")["data"]["status"]
        if st in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            break
    if st != "SUCCEEDED":
        raise SystemExit(f"Apify run ended: {st}")
    return _get(f"https://api.apify.com/v2/datasets/{dsid}/items?token={TOKEN}&clean=true")


def domain_of(url):
    try:
        d = urlparse(url).netloc.lower()
        return d[4:] if d.startswith("www.") else d
    except Exception:
        return ""


ENGINE_FIELDS = {  # engine key -> (result field, source field)
    "aioverview": ("aiOverview", None),
    "chatgpt": ("chatGptSearchResult", None),
    "perplexity": ("perplexitySearchResult", None),
    "gemini": ("geminiSearchResult", None),
}


def parse(items, brand, domain, engines):
    bl = brand.lower()
    dl = (domain or "").lower().replace("www.", "")
    per_query = []
    eng_counts = {e: {"asked": 0, "seen": 0} for e in engines}
    for it in items:
        q = (it.get("searchQuery") or {}).get("term", "")
        row = {"query": q, "engines": {}}
        for e in engines:
            fld = ENGINE_FIELDS[e][0]
            block = it.get(fld) or {}
            text = block.get("content") or block.get("text") or ""
            if not text:
                continue
            eng_counts[e]["asked"] += 1
            srcs = block.get("sources") or []
            src_domains = sorted({domain_of(s.get("url", "")) for s in srcs if s.get("url")} - {""})
            mentioned = bl in text.lower()
            cited = bool(dl) and any(dl in (s.get("url", "") or "").lower() for s in srcs)
            if mentioned or cited:
                eng_counts[e]["seen"] += 1
            row["engines"][e] = {"mentioned": mentioned, "cited": cited,
                                 "answer": text[:700], "source_domains": src_domains[:12]}
        if row["engines"]:
            per_query.append(row)
    summary = {"brand": brand, "domain": domain,
               "per_engine": {e: {"visible_in": eng_counts[e]["seen"], "of": eng_counts[e]["asked"]} for e in engines}}
    total_asked = sum(c["asked"] for c in eng_counts.values())
    total_seen = sum(c["seen"] for c in eng_counts.values())
    summary["overall_visibility_pct"] = round(100 * total_seen / total_asked) if total_asked else 0
    return per_query, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand", required=True)
    ap.add_argument("--domain", default="")
    ap.add_argument("--queries-file", required=True)
    ap.add_argument("--country", default="us")
    ap.add_argument("--engines", default="aioverview,chatgpt,perplexity")
    a = ap.parse_args()
    engines = [e.strip().lower() for e in a.engines.split(",") if e.strip()]
    if any(e in engines for e in ("aioverview", "perplexity", "gemini")) and not TOKEN:
        sys.exit("APIFY_TOKEN not set — add it to this skill's .env (see PLAYBOOK.md).")
    if "chatgpt" in engines and not OPENAI_KEY:
        sys.exit("OPENAI_API_KEY not set — add it to this skill's .env.")
    queries = [q.strip() for q in open(a.queries_file, encoding="utf-8") if q.strip()]
    if not queries:
        sys.exit("No queries found in --queries-file.")

    items = run_actor(queries, a.country, engines)

    if "chatgpt" in engines:
        print(f"Asking {len(queries)} buyer questions via OpenAI ({OPENAI_MODEL} + web_search)...")
        by_query = {(it.get("searchQuery") or {}).get("term", ""): it for it in items}
        cg_results = run_chatgpt_direct(queries)
        for q, cg in cg_results.items():
            item = by_query.get(q)
            if item is None:
                item = {"searchQuery": {"term": q}}
                items.append(item)
                by_query[q] = item
            item["chatGptSearchResult"] = cg

    per_query, summary = parse(items, a.brand, a.domain, engines)

    os.makedirs(OUT, exist_ok=True)
    json.dump({"summary": summary, "queries": per_query},
              open(os.path.join(OUT, "audit.json"), "w", encoding="utf-8"), indent=2)
    with open(os.path.join(OUT, "audit.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["query", "engine", "mentioned", "cited"])
        for r in per_query:
            for e, d in r["engines"].items():
                w.writerow([r["query"], e, d["mentioned"], d["cited"]])

    print(f"\nOK  {a.brand} visibility: {summary['overall_visibility_pct']}% across {len(per_query)} queries → {OUT}/audit.json")
    for e in engines:
        pe = summary["per_engine"][e]
        print(f"  {e:12} seen in {pe['visible_in']}/{pe['of']} answers")


if __name__ == "__main__":
    main()
