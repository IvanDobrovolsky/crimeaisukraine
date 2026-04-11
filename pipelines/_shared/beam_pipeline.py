"""
Apache Beam Pipeline for Crimea Sovereignty Framing Analysis

Two sources (GDELT media + OpenAlex academic) → unified classifier → output.

Architecture:
  GDELT Source ──→ Fetch Article Text ──→ ┐
                                          ├→ Classify (81 signals) → Write Results
  OpenAlex Source ──→ Extract Abstract ──→ ┘

Usage:
    python scripts/beam_pipeline.py --start 2020 --end 2021
    python scripts/beam_pipeline.py --start 2020 --end 2021 --skip-gdelt
    python scripts/beam_pipeline.py --start 2020 --end 2021 --skip-academic
"""

import argparse
import json
import re
import time
import urllib.request
import urllib.parse
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

from sovereignty_classifier import SovereigntyClassifier
from sovereignty_signals import CRIMEA_REFERENCE

PROJECT = Path(__file__).parent.parent.parent   # _shared → pipelines → project root
DATA = PROJECT / "data"

CONTACT_EMAIL = "dobrovolsky94@gmail.com"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("beam_pipeline")

# ─── Crimean search terms ────────────────────────────────

CRIMEA_SEARCH_TERMS_EN = [
    "Crimea", "Crimean",
    "Simferopol", "Sevastopol", "Yalta", "Kerch", "Feodosia",
    "Evpatoria", "Bakhchysarai", "Dzhankoy", "Alushta",
    "Crimean Peninsula", "Black Sea peninsula",
]

CRIMEA_SEARCH_TERMS_RU = [
    "Крым", "Крымский",
    "Симферополь", "Севастополь", "Ялта", "Керчь", "Феодосия",
    "Евпатория", "Бахчисарай", "Джанкой", "Алушта",
]

CRIMEA_SEARCH_TERMS_UK = [
    "Крим", "Кримський",
    "Сімферополь", "Севастополь", "Ялта", "Керч", "Феодосія",
]

# For GDELT API queries — combine terms
GDELT_QUERIES = [
    '"Crimea"',
    '"Simferopol" OR "Sevastopol" OR "Yalta" OR "Kerch"',
    '"Crimean peninsula"',
    '"Крым"',
    '"Симферополь" OR "Севастополь"',
    '"Крим"',
]

# ─── TLD → Country mapping ───────────────────────────────

TLD_COUNTRY = {
    'ru': 'Russia', 'su': 'Russia', 'ua': 'Ukraine', 'by': 'Belarus',
    'de': 'Germany', 'fr': 'France', 'it': 'Italy', 'es': 'Spain',
    'uk': 'UK', 'co.uk': 'UK', 'pl': 'Poland', 'cz': 'Czechia',
    'nl': 'Netherlands', 'tr': 'Turkey', 'cn': 'China', 'jp': 'Japan',
    'kr': 'South Korea', 'in': 'India', 'br': 'Brazil', 'ae': 'UAE',
}

KNOWN_DOMAINS = {
    'bbc.com': 'UK', 'reuters.com': 'UK', 'nytimes.com': 'US',
    'washingtonpost.com': 'US', 'cnn.com': 'US', 'theguardian.com': 'UK',
    'dw.com': 'Germany', 'aljazeera.com': 'Qatar', 'france24.com': 'France',
    'rt.com': 'Russia', 'sputniknews.com': 'Russia', 'ura.news': 'Russia',
    'pravda.com.ua': 'Ukraine', 'kyivindependent.com': 'Ukraine',
    'ukrinform.net': 'Ukraine', 'unian.net': 'Ukraine',
    'globalsecurity.org': 'US', 'voanews.com': 'US',
}


def get_domain_country(domain: str) -> str:
    domain = domain.lower().strip()
    for known, country in KNOWN_DOMAINS.items():
        if domain == known or domain.endswith('.' + known):
            return country
    tld = domain.rsplit('.', 1)[-1] if '.' in domain else ''
    return TLD_COUNTRY.get(tld, '')


# ─── Source: GDELT ────────────────────────────────────────

GDELT_API = "https://api.gdeltproject.org/api/v2/doc/doc"


def generate_quarters(start_year: int, end_year: int) -> list[tuple[str, str]]:
    quarters = []
    for year in range(start_year, end_year + 1):
        for qs, qe in [("0101", "0331"), ("0401", "0630"), ("0701", "0930"), ("1001", "1231")]:
            s = f"{year}{qs}000000"
            e = f"{year}{qe}235959"
            if int(s[:8]) > int(datetime.now().strftime("%Y%m%d")):
                break
            quarters.append((s, e))
    return quarters


def collect_gdelt_articles(start_year: int, end_year: int) -> list[dict]:
    """Collect article metadata from GDELT."""
    articles = []
    seen = set()
    quarters = generate_quarters(start_year, end_year)

    for qs, qe in quarters:
        label = f"{qs[:4]}Q{(int(qs[4:6])-1)//3+1}"
        for query in GDELT_QUERIES:
            params = {
                "query": query, "format": "json", "maxrecords": "250",
                "sort": "DateDesc", "mode": "ArtList",
                "startdatetime": qs, "enddatetime": qe,
            }
            url = GDELT_API + "?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers={"User-Agent": "CrimeaAudit/1.0"})
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode())
                    for a in data.get("articles", []):
                        u = a.get("url", "")
                        if u not in seen:
                            seen.add(u)
                            articles.append({
                                "source": "gdelt",
                                "url": u,
                                "title": a.get("title", ""),
                                "domain": a.get("domain", ""),
                                "domain_country": get_domain_country(a.get("domain", "")),
                                "date": a.get("seendate", ""),
                                "language": a.get("language", ""),
                            })
            except Exception as e:
                log.warning(f"GDELT {label} error: {e}")
            time.sleep(0.5)
        log.info(f"GDELT {label}: {len(articles)} total")

    return articles


# ─── Source: OpenAlex ─────────────────────────────────────

OPENALEX_API = "https://api.openalex.org/works"


def reconstruct_abstract(inv_index: dict) -> str:
    if not inv_index:
        return ""
    words = {}
    for word, positions in inv_index.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words[k] for k in sorted(words.keys()))


def collect_openalex_articles(start_year: int, end_year: int, max_pages: int = 25) -> list[dict]:
    """Collect paper metadata + abstracts from OpenAlex."""
    articles = []
    seen_dois = set()

    for query in ["Crimea", "Крым", "Крим", "Simferopol", "Sevastopol"]:
        page = 1
        while page <= max_pages:
            params = {
                "search": query,
                "filter": f"from_publication_date:{start_year}-01-01,to_publication_date:{end_year}-12-31",
                "sort": "publication_date:desc",
                "per_page": "200", "page": str(page),
                "mailto": CONTACT_EMAIL,
            }
            url = OPENALEX_API + "?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers={"User-Agent": f"CrimeaAudit/1.0 (mailto:{CONTACT_EMAIL})"})
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode())
                    works = data.get("results", [])
                    if not works:
                        break
                    for w in works:
                        doi = w.get("doi", "") or ""
                        year = w.get("publication_year", 0)
                        if year and (year < start_year or year > end_year):
                            continue
                        if doi and doi in seen_dois:
                            continue
                        if doi:
                            seen_dois.add(doi)
                        title = w.get("title", "") or ""
                        abstract = reconstruct_abstract(w.get("abstract_inverted_index"))
                        journal = ""
                        if w.get("primary_location", {}).get("source"):
                            journal = w["primary_location"]["source"].get("display_name", "")
                        articles.append({
                            "source": "openalex",
                            "url": doi or w.get("id", ""),
                            "title": title,
                            "domain": journal,
                            "domain_country": "",
                            "date": str(year),
                            "language": w.get("language", ""),
                            "text": f"{title}\n{abstract}" if abstract else title,
                            "doi": doi,
                            "journal": journal,
                        })
            except Exception as e:
                log.warning(f"OpenAlex error: {e}")
                break
            page += 1
            time.sleep(0.2)
        log.info(f"OpenAlex '{query}': {len(articles)} total")

    return articles


# ─── Beam Transforms ──────────────────────────────────────

class FetchArticleText(beam.DoFn):
    """Fetch full article text from URL (GDELT articles only)."""

    def __init__(self):
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _extract_text(self, html: str) -> str:
        """Extract readable text from HTML — simple tag stripping."""
        # Remove script, style, nav, footer
        html = re.sub(r'<(script|style|nav|footer|header|aside)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # Remove tags
        text = re.sub(r'<[^>]+>', ' ', html)
        # Decode entities
        text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&nbsp;', ' ')
        text = text.replace('&#39;', "'").replace('&quot;', '"')
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:5000]  # Cap at 5k chars

    def process(self, element):
        url = element.get("url", "")
        if not url:
            return

        req = urllib.request.Request(url, headers=self._headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                content_type = resp.headers.get("Content-Type", "")
                if "text/html" not in content_type and "text/plain" not in content_type:
                    element["text"] = element.get("title", "")
                else:
                    raw = resp.read()
                    # Try utf-8 first, fallback to latin-1
                    try:
                        html = raw.decode("utf-8")
                    except UnicodeDecodeError:
                        html = raw.decode("latin-1", errors="replace")
                    element["text"] = self._extract_text(html)
                    element["text_source"] = "fetched"
        except Exception:
            element["text"] = element.get("title", "")
            element["text_source"] = "title_only"

        time.sleep(0.3)  # Rate limit
        yield element


class ClassifySovereignty(beam.DoFn):
    """Classify text using 81 sovereignty signals."""

    def setup(self):
        self._clf = SovereigntyClassifier()

    def process(self, element):
        text = element.get("text", "")
        if not text:
            return

        # Filter: must reference Crimea
        if not self._clf.has_crimea_reference(text):
            return

        result = self._clf.classify(text)

        element["label"] = result.label
        element["confidence"] = round(result.confidence, 3)
        element["ua_score"] = round(result.ua_score, 3)
        element["ru_score"] = round(result.ru_score, 3)
        element["signal_count"] = len(result.signals)
        element["signals"] = [
            {"matched": s.matched, "direction": s.direction,
             "type": s.signal_type, "weight": s.weight}
            for s in result.signals
        ]
        # Drop full text from output
        element.pop("text", None)

        yield element


class FormatOutput(beam.DoFn):
    """Format for JSON output."""
    def process(self, element):
        yield json.dumps(element, ensure_ascii=False)


def run_pipeline(start_year: int, end_year: int, skip_gdelt: bool = False, skip_academic: bool = False):
    """Run the full Beam pipeline."""
    log.info(f"Starting pipeline: {start_year}-{end_year}")

    # ─── Collect phase (outside Beam — API calls need rate limiting) ───
    gdelt_articles = []
    academic_articles = []

    if not skip_gdelt:
        log.info("Collecting GDELT articles...")
        gdelt_articles = collect_gdelt_articles(start_year, end_year)
        log.info(f"GDELT: {len(gdelt_articles)} articles")

    if not skip_academic:
        log.info("Collecting OpenAlex papers...")
        academic_articles = collect_openalex_articles(start_year, end_year)
        log.info(f"OpenAlex: {len(academic_articles)} papers")

    all_articles = gdelt_articles + academic_articles
    log.info(f"Total collected: {len(all_articles)}")

    # Deduplicate
    seen = set()
    deduped = []
    for a in all_articles:
        key = hashlib.md5((a.get("title", "") + a.get("url", "")).lower().encode()).hexdigest()
        if key not in seen:
            seen.add(key)
            deduped.append(a)
    log.info(f"After dedup: {len(deduped)}")

    # ─── Beam processing phase ───
    output_path = str(DATA / f"beam_{start_year}_{end_year}")
    options = PipelineOptions(runner="DirectRunner")

    with beam.Pipeline(options=options) as p:
        # Split by source for different processing
        gdelt_items = [a for a in deduped if a["source"] == "gdelt"]
        academic_items = [a for a in deduped if a["source"] == "openalex"]

        # GDELT: needs text fetching
        gdelt_classified = (
            p
            | "CreateGDELT" >> beam.Create(gdelt_items)
            | "FetchText" >> beam.ParDo(FetchArticleText())
            | "ClassifyGDELT" >> beam.ParDo(ClassifySovereignty())
        )

        # Academic: already has text
        academic_classified = (
            p
            | "CreateAcademic" >> beam.Create(academic_items)
            | "ClassifyAcademic" >> beam.ParDo(ClassifySovereignty())
        )

        # Merge and write
        merged = (
            (gdelt_classified, academic_classified)
            | "Merge" >> beam.Flatten()
        )

        # Write JSONL
        (
            merged
            | "Format" >> beam.ParDo(FormatOutput())
            | "Write" >> beam.io.WriteToText(
                output_path,
                file_name_suffix=".jsonl",
                shard_name_template="",
            )
        )

    # ─── Post-processing: summarize ───
    results_path = output_path + ".jsonl"
    if Path(results_path).exists():
        results = []
        with open(results_path) as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line))

        by_label = {}
        by_source = {}
        by_year = {}
        violators = []

        for r in results:
            l = r["label"]
            by_label[l] = by_label.get(l, 0) + 1
            src = r["source"]
            by_source.setdefault(src, {}).setdefault(l, 0)
            by_source[src][l] += 1
            year = r.get("date", "")[:4]
            if year:
                by_year.setdefault(year, {}).setdefault(l, 0)
                by_year[year][l] += 1
            if l == "russia":
                violators.append(r)

        # Write summary JSON
        summary_path = DATA / f"beam_{start_year}_{end_year}_summary.json"
        with open(summary_path, "w") as f:
            json.dump({
                "pipeline": "apache_beam",
                "runner": "DirectRunner",
                "scan_date": datetime.now(timezone.utc).isoformat(),
                "period": f"{start_year}-{end_year}",
                "sources": {"gdelt": len(gdelt_items), "openalex": len(academic_items)},
                "total_collected": len(all_articles),
                "total_deduped": len(deduped),
                "total_classified": len(results),
                "by_label": by_label,
                "by_source": by_source,
                "by_year": by_year,
                "violators_count": len(violators),
                "violators": violators,
            }, f, indent=2, ensure_ascii=False)

        log.info(f"\n{'='*60}")
        log.info(f"PIPELINE COMPLETE: {start_year}-{end_year}")
        log.info(f"  Classified: {len(results)}")
        for l, c in sorted(by_label.items(), key=lambda x: -x[1]):
            icon = {"ukraine": "✅", "russia": "❌", "disputed": "⚠️", "no_signal": "·"}.get(l, "?")
            log.info(f"  {icon} {l}: {c}")
        log.info(f"  By source: {by_source}")
        log.info(f"  Results: {results_path}")
        log.info(f"  Summary: {summary_path}")

        # Show non-Russian-domain violators
        non_ru = [v for v in violators if v.get("domain_country") not in ("Russia", "")]
        if non_ru:
            log.info(f"\n  🔴 NON-RUSSIAN violators ({len(non_ru)}):")
            for v in non_ru[:10]:
                sigs = ", ".join(s["matched"] for s in v["signals"][:2])
                log.info(f"    [{v.get('domain_country','?'):10s}] {v['title'][:55]}")
                log.info(f"    {'':12s} {v['url']}")
                log.info(f"    {'':12s} Signals: {sigs}")


def main():
    parser = argparse.ArgumentParser(description="Beam pipeline: Crimea sovereignty framing")
    parser.add_argument("--start", type=int, default=2020)
    parser.add_argument("--end", type=int, default=2021)
    parser.add_argument("--skip-gdelt", action="store_true")
    parser.add_argument("--skip-academic", action="store_true")
    args = parser.parse_args()

    run_pipeline(args.start, args.end, args.skip_gdelt, args.skip_academic)


if __name__ == "__main__":
    main()
