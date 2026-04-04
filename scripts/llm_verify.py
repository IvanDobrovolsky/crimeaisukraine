"""
LLM Verification of Russia-labeled articles.

Re-fetches article text, sends to Claude Haiku with context,
determines if the article ENDORSES Russian sovereignty or is
REPORTING/QUOTING/CRITICIZING it.

Usage:
    python scripts/llm_verify.py
    python scripts/llm_verify.py --limit 100 --dry-run
    python scripts/llm_verify.py --resume
"""

import argparse
import json
import re
import time
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

PROJECT = Path(__file__).parent.parent
DATA = PROJECT / "data"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html", "Accept-Language": "en-US,en;q=0.9",
}

# Anthropic API
ANTHROPIC_API = "https://api.anthropic.com/v1/messages"


def fetch_text(url: str) -> str:
    """Fetch and extract text from URL."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            ct = resp.headers.get("Content-Type", "")
            if "text" not in ct:
                return ""
            raw = resp.read()
            try:
                html = raw.decode("utf-8")
            except:
                html = raw.decode("latin-1", errors="replace")
            # Strip HTML
            html = re.sub(r'<(script|style|nav|footer|header|aside)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<[^>]+>', ' ', html)
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:3000]  # Cap for token budget
    except:
        return ""


def verify_with_llm(text: str, url: str, domain: str, country: str, signals: list, api_key: str) -> dict:
    """Ask Claude Haiku if article endorses Russian sovereignty or is reporting/quoting."""
    signals_str = ", ".join(signals[:3])

    prompt = f"""Analyze this article excerpt for Crimea sovereignty framing.

URL: {url}
Domain: {domain} ({country})
Detected signals: {signals_str}

Article text (excerpt):
{text[:2000]}

Question: Does this article ENDORSE or NORMALIZE Crimea as Russian territory, or is it REPORTING ON / QUOTING / CRITICIZING Russian claims?

Respond with EXACTLY one of:
- ENDORSES: The article treats Crimea as Russian territory (uses "Republic of Crimea" as normal location, lists Crimea under Russia without qualification)
- REPORTS: The article reports on Russia's claims, quotes Russian officials, or discusses the dispute. It does NOT endorse Russian sovereignty.
- UNCLEAR: Cannot determine from the excerpt.

Then one sentence explaining why."""

    body = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 100,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    req = urllib.request.Request(ANTHROPIC_API, data=body, headers={
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    })

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            response_text = data["content"][0]["text"].strip()

            if "ENDORSES" in response_text.upper()[:20]:
                return {"verdict": "endorses", "explanation": response_text}
            elif "REPORTS" in response_text.upper()[:20]:
                return {"verdict": "reports", "explanation": response_text}
            else:
                return {"verdict": "unclear", "explanation": response_text}
    except Exception as e:
        return {"verdict": "error", "explanation": str(e)}


def verify_academic_with_llm(title: str, signals: list, journal: str, api_key: str) -> dict:
    """Verify academic paper — no need to fetch, use title + signals."""
    signals_str = ", ".join(signals[:3])

    prompt = f"""Analyze this academic paper for Crimea sovereignty framing.

Title: {title}
Journal: {journal}
Detected signals: {signals_str}

Question: Does this paper ENDORSE or NORMALIZE Crimea as Russian territory (e.g., uses "Republic of Crimea" as a normal location label, lists institution in "Russia, Crimea"), or is it ANALYZING / CRITICIZING Russian claims?

Respond with EXACTLY one of:
- ENDORSES: Uses Russian administrative terminology as default location label without qualification.
- ANALYZES: Discusses annexation/occupation critically or academically.
- UNCLEAR: Cannot determine from title alone.

Then one sentence explaining why."""

    body = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 100,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    req = urllib.request.Request(ANTHROPIC_API, data=body, headers={
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    })

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            response_text = data["content"][0]["text"].strip()
            if "ENDORSES" in response_text.upper()[:20]:
                return {"verdict": "endorses", "explanation": response_text}
            elif "ANALYZ" in response_text.upper()[:20]:
                return {"verdict": "analyzes", "explanation": response_text}
            else:
                return {"verdict": "unclear", "explanation": response_text}
    except Exception as e:
        return {"verdict": "error", "explanation": str(e)}


def load_done(output_path: str) -> set:
    done = set()
    p = Path(output_path)
    if p.exists():
        with open(p) as f:
            for line in f:
                if line.strip():
                    try:
                        r = json.loads(line)
                        done.add(r.get("url", ""))
                    except:
                        pass
    return done


def main():
    parser = argparse.ArgumentParser(description="LLM verification of Russia-labeled articles")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--api-key", default="")
    args = parser.parse_args()

    # Get API key
    api_key = args.api_key
    if not api_key:
        import os
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key and not args.dry_run:
        print("ERROR: Set ANTHROPIC_API_KEY env var or use --api-key")
        return

    with open(DATA / "llm_verification_queue.json") as f:
        queue = json.load(f)

    if args.limit > 0:
        queue = queue[:args.limit]

    done_urls = set()
    output_path = DATA / "llm_verification_results.jsonl"
    if args.resume:
        done_urls = load_done(str(output_path))
        print(f"Resume: {len(done_urls)} already verified")

    to_verify = [a for a in queue if a['url'] not in done_urls]
    print(f"To verify: {len(to_verify)} articles")

    if args.dry_run:
        print("DRY RUN — would verify:")
        for a in to_verify[:10]:
            print(f"  {a['domain']:30s} {a['url'][:60]}")
        return

    mode = "a" if args.resume and done_urls else "w"
    outf = open(output_path, mode)

    stats = {"endorses": 0, "reports": 0, "unclear": 0, "error": 0, "fetch_failed": 0}
    start_time = time.time()

    for i, article in enumerate(to_verify):
        url = article['url']
        is_academic = article.get('source') == 'academic'

        if is_academic:
            result = verify_academic_with_llm(
                article.get('title', ''),
                article.get('signals', []),
                article.get('domain', ''),
                api_key
            )
        else:
            # Fetch article text
            text = fetch_text(url)
            if not text:
                result = {"verdict": "fetch_failed", "explanation": "Could not fetch article"}
                stats["fetch_failed"] += 1
            else:
                result = verify_with_llm(
                    text, url,
                    article.get('domain', ''),
                    article.get('domain_country', ''),
                    article.get('signals', []),
                    api_key
                )

        verdict = result['verdict']
        if verdict in stats:
            stats[verdict] += 1

        row = {
            "url": url,
            "domain": article.get('domain', ''),
            "domain_country": article.get('domain_country', ''),
            "original_label": article.get('label', ''),
            "signals": article.get('signals', []),
            "llm_verdict": verdict,
            "llm_explanation": result.get('explanation', ''),
            "source": "academic" if is_academic else "media",
        }

        outf.write(json.dumps(row, ensure_ascii=False) + "\n")
        outf.flush()

        icon = {"endorses": "R", "reports": "~", "analyzes": "~", "unclear": "?", "error": "!", "fetch_failed": "X"}.get(verdict, "?")
        if (i + 1) % 50 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            eta = (len(to_verify) - i - 1) / max(rate, 0.01) / 60
            print(f"  [{i+1}/{len(to_verify)}] {rate:.1f}/s ETA={eta:.0f}min | {stats}")

        # Rate limit: ~2 requests/sec for Haiku
        time.sleep(0.5)

    outf.close()

    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"LLM VERIFICATION COMPLETE in {elapsed/60:.0f} min")
    print(f"Results: {stats}")
    print(f"\nSaved to {output_path}")

    # Summary
    total_verified = stats['endorses'] + stats['reports'] + stats['unclear']
    if total_verified > 0:
        print(f"\nOf verified articles:")
        print(f"  ENDORSES (true Russia framing): {stats['endorses']} ({round(stats['endorses']/total_verified*100)}%)")
        print(f"  REPORTS (false positive):        {stats['reports']} ({round(stats['reports']/total_verified*100)}%)")
        print(f"  UNCLEAR:                         {stats['unclear']} ({round(stats['unclear']/total_verified*100)}%)")
        print(f"  Fetch failed:                    {stats['fetch_failed']}")
        print(f"  API errors:                      {stats['error']}")

    # Write summary
    with open(DATA / "llm_verification_summary.json", "w") as f:
        json.dump({
            "date": datetime.now(timezone.utc).isoformat(),
            "total_queue": len(queue),
            "total_verified": total_verified,
            "stats": stats,
            "precision_estimate": round(stats['endorses'] / max(total_verified, 1) * 100, 1),
        }, f, indent=2)


if __name__ == "__main__":
    main()
