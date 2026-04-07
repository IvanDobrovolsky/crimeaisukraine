"""
Fetch article bodies and classify sovereignty framing.
Writes JSONL incrementally — never loses progress. Supports resume.

Usage:
    python scripts/fetch_and_classify.py --input data/crimea_2021_urls.json --output data/crimea_2021.jsonl
    python scripts/fetch_and_classify.py --input data/crimea_2015_2026_urls.json --output data/crimea_full.jsonl --resume
"""

import argparse
import json
import re
import time
import urllib.request
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    'bendbulletin.com': 'US', 'tin247.com': 'Vietnam',
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
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:8000]


def fetch_url(url: str) -> tuple[str, str]:
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


def load_done_urls(output_path: str) -> set:
    """Load already-processed URLs from existing JSONL output."""
    done = set()
    p = Path(output_path)
    if p.exists():
        with open(p) as f:
            for line in f:
                if line.strip():
                    try:
                        r = json.loads(line)
                        done.add(r.get("url", ""))
                    except json.JSONDecodeError:
                        pass
    return done


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--delay", type=float, default=0.05)
    parser.add_argument("--workers", type=int, default=15, help="Parallel fetch threads")
    parser.add_argument("--resume", action="store_true", help="Skip already-processed URLs")
    args = parser.parse_args()

    with open(args.input) as f:
        articles = json.load(f)

    if args.limit > 0:
        articles = articles[:args.limit]

    # Resume support
    done_urls = set()
    if args.resume:
        done_urls = load_done_urls(args.output)
        print(f"Resume: {len(done_urls)} already processed, skipping")

    clf = SovereigntyClassifier()
    stats = {"ok": 0, "errors": 0, "no_crimea": 0, "skipped": 0}
    by_label = {}
    total = len(articles)
    start_time = time.time()

    # Open output in append mode for resume, write mode otherwise
    mode = "a" if args.resume and done_urls else "w"
    outf = open(args.output, mode)

    # Filter to unprocessed
    to_process = [a for a in articles if a["url"] not in done_urls]
    stats["skipped"] = len(articles) - len(to_process)
    print(f"Fetching + classifying {len(to_process)} articles ({stats['skipped']} skipped) → {args.output}")
    print(f"Workers: {args.workers}")

    write_lock = threading.Lock()
    counter = {"done": 0}

    def process_one(a):
        url = a["url"]
        domain = a.get("domain", "")
        text, fetch_status = fetch_url(url)

        row = {
            "url": url,
            "domain": domain,
            "domain_country": get_domain_country(domain),
            "date": a.get("date", ""),
            "fetch_status": fetch_status,
        }

        if fetch_status == "ok" and text:
            if clf.has_crimea_reference(text):
                result = clf.classify(text)
                row["label"] = result.label
                row["confidence"] = round(result.confidence, 3)
                row["ua_score"] = round(result.ua_score, 3)
                row["ru_score"] = round(result.ru_score, 3)
                row["signal_count"] = len(result.signals)
                row["signals"] = [
                    {"matched": s.matched, "direction": s.direction, "type": s.signal_type}
                    for s in result.signals[:10]
                ]
            else:
                row["label"] = "no_crimea_ref"
        else:
            row["label"] = "fetch_failed"

        # Write with lock
        with write_lock:
            by_label[row["label"]] = by_label.get(row["label"], 0) + 1
            if row.get("fetch_status") == "ok":
                stats["ok"] += 1
            else:
                stats["errors"] += 1
            outf.write(json.dumps(row, ensure_ascii=False) + "\n")
            outf.flush()
            counter["done"] += 1
            n = counter["done"]
            if n % 500 == 0:
                elapsed = time.time() - start_time
                rate = n / max(elapsed, 1)
                remaining = len(to_process) - n
                eta = remaining / max(rate, 0.01) / 60
                print(f"  [{n}/{len(to_process)}] {rate:.1f}/s ETA={eta:.0f}min | {by_label}")

    try:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(process_one, a) for a in to_process]
            for f in as_completed(futures):
                try:
                    f.result()
                except Exception as e:
                    pass  # individual failures are already handled
    finally:
        outf.close()

    elapsed = time.time() - start_time
    print(f"\nDONE in {elapsed/60:.1f} minutes")
    print(f"  Fetched: {stats['ok']} ok, {stats['errors']} errors, {stats['skipped']} skipped")
    print(f"  By label: {by_label}")

    # Summary file
    summary_path = args.output.replace(".jsonl", "_summary.json")
    violators = {}
    with open(args.output) as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                if r.get("label") == "russia":
                    c = r.get("domain_country") or "Unknown"
                    violators[c] = violators.get(c, 0) + 1

    with open(summary_path, "w") as f:
        json.dump({
            "scan_date": datetime.now(timezone.utc).isoformat(),
            "input": args.input,
            "total": total,
            "processed": stats["ok"] + stats["errors"],
            "by_label": by_label,
            "russia_framing_by_country": violators,
        }, f, indent=2)
    print(f"  Summary: {summary_path}")


if __name__ == "__main__":
    main()
