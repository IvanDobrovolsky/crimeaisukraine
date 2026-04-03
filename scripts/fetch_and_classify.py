"""
Fetch article bodies and classify sovereignty framing.
Works with GDELT BigQuery exports and OpenAlex data.

Usage:
    python scripts/fetch_and_classify.py --input data/crimea_2021_urls.json --output data/crimea_2021_classified.json
    python scripts/fetch_and_classify.py --input data/crimea_2021_urls.json --output data/crimea_2021_classified.json --limit 100
"""

import argparse
import json
import re
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from sovereignty_classifier import SovereigntyClassifier
from sovereignty_signals import CRIMEA_REFERENCE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

TLD_COUNTRY = {
    'ru': 'Russia', 'su': 'Russia', 'ua': 'Ukraine', 'by': 'Belarus',
    'de': 'Germany', 'fr': 'France', 'it': 'Italy', 'es': 'Spain',
    'uk': 'UK', 'co.uk': 'UK', 'pl': 'Poland', 'cz': 'Czechia',
    'nl': 'Netherlands', 'tr': 'Turkey', 'cn': 'China', 'jp': 'Japan',
    'com.au': 'Australia', 'co.nz': 'New Zealand', 'ca': 'Canada',
    'ie': 'Ireland', 'in': 'India', 'br': 'Brazil', 'ae': 'UAE',
    'kr': 'South Korea', 'jp': 'Japan',
}

KNOWN_DOMAINS = {
    'bbc.com': 'UK', 'reuters.com': 'UK', 'nytimes.com': 'US',
    'washingtonpost.com': 'US', 'cnn.com': 'US', 'theguardian.com': 'UK',
    'dw.com': 'Germany', 'aljazeera.com': 'Qatar', 'france24.com': 'France',
    'rt.com': 'Russia', 'sputniknews.com': 'Russia', 'ura.news': 'Russia',
    'pravda.com.ua': 'Ukraine', 'kyivindependent.com': 'Ukraine',
    'ukrinform.net': 'Ukraine', 'ukrinform.ua': 'Ukraine',
    'unian.net': 'Ukraine', 'kyivpost.com': 'Ukraine',
    'gordonua.com': 'Ukraine', 'globalsecurity.org': 'US',
    'menafn.com': 'Jordan', 'dailytelegraph.com.au': 'Australia',
    'couriermail.com.au': 'Australia', 'heraldsun.com.au': 'Australia',
    'goldcoastbulletin.com.au': 'Australia', 'bendbulletin.com': 'US',
    'thechronicle.com.au': 'Australia', 'tin247.com': 'Vietnam',
}


def get_domain_country(domain: str) -> str:
    domain = domain.lower().strip()
    for known, country in KNOWN_DOMAINS.items():
        if domain == known or domain.endswith('.' + known):
            return country
    parts = domain.rsplit('.', 2)
    if len(parts) >= 2:
        tld2 = '.'.join(parts[-2:])
        if tld2 in TLD_COUNTRY:
            return TLD_COUNTRY[tld2]
    tld = parts[-1] if parts else ''
    return TLD_COUNTRY.get(tld, '')


def extract_text(html: str) -> str:
    html = re.sub(r'<(script|style|nav|footer|header|aside|iframe)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', html)
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&nbsp;', ' ')
    text = text.replace('&#39;', "'").replace('&quot;', '"')
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:8000]


def fetch_url(url: str) -> tuple[str, str]:
    """Returns (text, status)."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            ct = resp.headers.get("Content-Type", "")
            if "text" not in ct:
                return "", "not_text"
            raw = resp.read()
            try:
                html = raw.decode("utf-8")
            except UnicodeDecodeError:
                html = raw.decode("latin-1", errors="replace")
            return extract_text(html), "ok"
    except urllib.error.HTTPError as e:
        return "", f"http_{e.code}"
    except Exception as e:
        return "", type(e).__name__


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, default=0, help="Limit articles (0=all)")
    parser.add_argument("--delay", type=float, default=0.15, help="Seconds between fetches")
    args = parser.parse_args()

    with open(args.input) as f:
        articles = json.load(f)

    if args.limit > 0:
        articles = articles[:args.limit]

    clf = SovereigntyClassifier()
    results = []
    stats = {"ok": 0, "errors": 0, "no_crimea": 0}
    by_label = {}

    total = len(articles)
    print(f"Fetching + classifying {total} articles...")
    start_time = time.time()

    for i, a in enumerate(articles):
        url = a["url"]
        domain = a.get("domain", "")

        # Fetch
        text, fetch_status = fetch_url(url)

        if fetch_status == "ok" and text:
            stats["ok"] += 1
        else:
            stats["errors"] += 1

        # Classify
        if text and clf.has_crimea_reference(text):
            result = clf.classify(text)
            a["label"] = result.label
            a["confidence"] = round(result.confidence, 3)
            a["ua_score"] = round(result.ua_score, 3)
            a["ru_score"] = round(result.ru_score, 3)
            a["signal_count"] = len(result.signals)
            a["signals"] = [
                {"matched": s.matched, "direction": s.direction, "type": s.signal_type}
                for s in result.signals[:10]
            ]
        elif text:
            a["label"] = "no_crimea_ref"
            stats["no_crimea"] += 1
            a["confidence"] = 0
            a["signals"] = []
        else:
            a["label"] = "fetch_failed"
            a["confidence"] = 0
            a["signals"] = []

        a["fetch_status"] = fetch_status
        a["domain_country"] = get_domain_country(domain)
        by_label[a["label"]] = by_label.get(a["label"], 0) + 1
        results.append(a)

        # Progress every 100
        if (i + 1) % 100 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            eta = (total - i - 1) / rate / 60
            print(f"  [{i+1}/{total}] {rate:.1f}/s ETA={eta:.1f}min | {by_label}")

        time.sleep(args.delay)

    # Summary
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"DONE in {elapsed/60:.1f} minutes")
    print(f"  Fetched: {stats['ok']} ok, {stats['errors']} errors, {stats['no_crimea']} no Crimea ref")
    print(f"  By label: {by_label}")

    # Non-Russian-domain violators
    violators = [r for r in results if r["label"] == "russia"]
    non_ru_violators = [r for r in violators if r.get("domain_country") not in ("Russia", "")]
    ru_violators = [r for r in violators if r.get("domain_country") == "Russia"]

    print(f"\n  Russia-framing: {len(violators)} total")
    print(f"    From Russian domains (noise): {len(ru_violators)}")
    print(f"    From non-Russian domains (SIGNIFICANT): {len(non_ru_violators)}")

    if non_ru_violators:
        print(f"\n  NON-RUSSIAN VIOLATORS:")
        for v in non_ru_violators[:20]:
            sigs = ", ".join(s["matched"] for s in v["signals"][:3])
            print(f"    [{v.get('domain_country','?'):12s}] {v['domain']:30s}")
            print(f"      {v['url']}")
            print(f"      Signals: {sigs}")

    # By country
    print(f"\n  Russia-framing by domain country:")
    by_country = {}
    for v in violators:
        c = v.get("domain_country") or "Unknown"
        by_country[c] = by_country.get(c, 0) + 1
    for c, n in sorted(by_country.items(), key=lambda x: -x[1]):
        print(f"    {c:20s}: {n}")

    # Save
    with open(args.output, "w") as f:
        json.dump({
            "scan_date": datetime.now(timezone.utc).isoformat(),
            "input": args.input,
            "total_articles": len(results),
            "fetch_ok": stats["ok"],
            "fetch_errors": stats["errors"],
            "by_label": by_label,
            "violators_total": len(violators),
            "violators_non_russian": len(non_ru_violators),
            "by_country_russia_framing": by_country,
            "results": results,
        }, f, ensure_ascii=False)
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
