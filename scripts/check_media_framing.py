#!/usr/bin/env python3
"""
Crimea Sovereignty Framing Analysis via GDELT DOC API v2

Analyzes how global media outlets frame Crimea's sovereignty status
using the free GDELT Document API (no BigQuery / GCP credits needed).

Searches for:
- Explicit pro-Russia framing ("Russian Crimea", "Crimea, Russia", etc.)
- Neutral/critical framing ("annexed Crimea", "occupied Crimea", etc.)
- Pro-Ukraine framing ("Ukrainian Crimea", "Crimea, Ukraine", etc.)
- URL-level sovereignty signals (path segments like /russia/crimea)

Outputs:
- data/media_framing.json   (raw structured findings)
- docs/media.md             (markdown report table)

Usage:
    python scripts/check_media_framing.py
"""

import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GDELT_API = "https://api.gdeltproject.org/api/v2/doc/doc"
MAX_RECORDS = 250  # API cap per request
REQUEST_DELAY = 1.5  # seconds between API calls to avoid 429s

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")

# ---------------------------------------------------------------------------
# Search queries — each targets a specific sovereignty framing
# ---------------------------------------------------------------------------

# Queries are (label, search_string, framing_category)
FRAMING_QUERIES = [
    # Pro-Russia sovereignty framing
    ("russian crimea", '"russian crimea"', "pro_russia"),
    ("crimea russia (explicit)", '"crimea, russia"', "pro_russia"),
    ("krym rossiya", "krym rossiya", "pro_russia"),
    ("republic of crimea russia", '"republic of crimea" russia', "pro_russia"),
    ("crimea part of russia", '"crimea" "part of russia"', "pro_russia"),
    ("crimea reunification", '"crimea" "reunification"', "pro_russia"),
    ("crimea returned to russia", '"crimea" "returned to russia"', "pro_russia"),

    # Neutral / critical framing (acknowledges annexation)
    ("annexed crimea", '"annexed crimea"', "neutral_critical"),
    ("crimea annexed", '"crimea" "annexed"', "neutral_critical"),
    ("crimea annexation", '"crimea" "annexation"', "neutral_critical"),
    ("occupied crimea", '"occupied crimea"', "neutral_critical"),
    ("crimea occupation", '"crimea" "occupation"', "neutral_critical"),
    ("crimea illegally", '"crimea" "illegally"', "neutral_critical"),
    ("crimea disputed", '"crimea" "disputed"', "neutral_critical"),

    # Pro-Ukraine sovereignty framing
    ("ukrainian crimea", '"ukrainian crimea"', "pro_ukraine"),
    ("crimea ukraine territory", '"crimea" "ukrainian territory"', "pro_ukraine"),
    ("crimea belongs to ukraine", '"crimea" "belongs to ukraine"', "pro_ukraine"),
    ("crimea is ukraine", '"crimea is ukraine"', "pro_ukraine"),
    ("deoccupation crimea", '"deoccupation" "crimea"', "pro_ukraine"),
    ("liberation crimea", '"liberation" "crimea"', "pro_ukraine"),
]

# ---------------------------------------------------------------------------
# Language clusters with TLD-based inference
# ---------------------------------------------------------------------------

LANGUAGE_CLUSTERS = {
    "Spanish": {
        "tlds": [".es", ".mx", ".ar", ".co", ".cl", ".pe", ".ve", ".ec", ".uy", ".py"],
        "gdelt_langs": ["Spanish"],
    },
    "French": {
        "tlds": [".fr", ".be", ".sn", ".ml", ".ci", ".cd", ".mg"],
        "gdelt_langs": ["French"],
    },
    "German": {
        "tlds": [".de", ".at", ".ch"],
        "gdelt_langs": ["German"],
    },
    "Italian": {
        "tlds": [".it"],
        "gdelt_langs": ["Italian"],
    },
    "Chinese": {
        "tlds": [".cn", ".hk", ".tw"],
        "gdelt_langs": ["Chinese", "Mandarin"],
    },
    "Hindi/Indian": {
        "tlds": [".in"],
        "gdelt_langs": ["Hindi"],
    },
    "Turkish": {
        "tlds": [".tr"],
        "gdelt_langs": ["Turkish"],
    },
    "Arabic": {
        "tlds": [".sa", ".ae", ".eg", ".qa", ".kw", ".bh", ".om", ".jo", ".lb", ".iq"],
        "gdelt_langs": ["Arabic"],
    },
    "Russian": {
        "tlds": [".ru", ".su"],
        "gdelt_langs": ["Russian"],
    },
    "Ukrainian": {
        "tlds": [".ua"],
        "gdelt_langs": ["Ukrainian"],
    },
    "English": {
        "tlds": [".com", ".co.uk", ".us", ".au", ".ca", ".nz", ".org", ".net"],
        "gdelt_langs": ["English"],
    },
}

# URL path patterns that signal sovereignty framing
URL_SOVEREIGNTY_PATTERNS = {
    "pro_russia": [
        r"/ru/crimea", r"/russia/crimea", r"/krym-rossiya",
        r"/russian-crimea", r"/crimea-russia",
        r"\.ru/.*kry[m]", r"\.ru/.*crimea",
    ],
    "pro_ukraine": [
        r"/ua/crimea", r"/ukraine/crimea", r"/krym-ukrain",
        r"/ukrainian-crimea", r"/crimea-ukraine",
        r"\.ua/.*kry[m]", r"\.ua/.*crimea",
    ],
    "neutral_critical": [
        r"/annexed[_-]crimea", r"/occupied[_-]crimea",
        r"annex", r"occupation",
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def gdelt_query(query_text: str, max_records: int = MAX_RECORDS,
                sourcelang: str | None = None) -> list[dict]:
    """Hit the GDELT DOC API v2 and return article list."""
    params = {
        "query": query_text,
        "mode": "artlist",
        "format": "json",
        "maxrecords": max_records,
    }
    if sourcelang:
        params["query"] += f" sourcelang:{sourcelang}"

    try:
        resp = requests.get(GDELT_API, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("articles", [])
    except (requests.RequestException, json.JSONDecodeError) as exc:
        print(f"  [WARN] API error for query '{query_text}': {exc}", file=sys.stderr)
        return []


def get_tld(url: str) -> str:
    """Extract effective TLD from a URL's domain."""
    try:
        domain = urlparse(url).netloc.lower()
    except Exception:
        return ""
    # Handle compound TLDs like .co.uk
    for compound in [".co.uk", ".com.au", ".co.nz", ".com.br", ".co.za"]:
        if domain.endswith(compound):
            return compound
    parts = domain.rsplit(".", 1)
    return f".{parts[-1]}" if len(parts) > 1 else ""


def classify_language_cluster(article: dict) -> str:
    """Assign an article to a language cluster based on GDELT language + TLD."""
    lang = article.get("language", "").strip()
    tld = get_tld(article.get("url", ""))

    for cluster_name, info in LANGUAGE_CLUSTERS.items():
        if lang in info["gdelt_langs"]:
            return cluster_name
        for t in info["tlds"]:
            if tld == t or tld.endswith(t):
                return cluster_name
    return "Other"


def infer_country(article: dict) -> str:
    """Return sourcecountry from GDELT or infer from domain."""
    sc = article.get("sourcecountry", "").strip()
    if sc:
        return sc
    tld = get_tld(article.get("url", ""))
    tld_to_country = {
        ".ru": "Russia", ".ua": "Ukraine", ".de": "Germany", ".fr": "France",
        ".es": "Spain", ".it": "Italy", ".tr": "Turkey", ".cn": "China",
        ".in": "India", ".mx": "Mexico", ".ar": "Argentina", ".co": "Colombia",
        ".br": "Brazil", ".sa": "Saudi Arabia", ".ae": "UAE", ".eg": "Egypt",
        ".co.uk": "United Kingdom", ".au": "Australia", ".ca": "Canada",
        ".pl": "Poland", ".cz": "Czech Republic", ".nl": "Netherlands",
    }
    return tld_to_country.get(tld, "Unknown")


def classify_url_framing(url: str) -> str | None:
    """Check URL path for sovereignty-signaling patterns."""
    url_lower = url.lower()
    for framing, patterns in URL_SOVEREIGNTY_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, url_lower):
                return framing
    return None


def classify_title_framing(title: str) -> str | None:
    """Extra framing signal from article title text."""
    t = title.lower()
    pro_russia_kw = [
        "russian crimea", "crimea, russia", "republic of crimea",
        "part of russia", "reunification", "returned to russia",
        "krym rossii",
    ]
    neutral_kw = [
        "annexed", "annexation", "occupied", "occupation",
        "illegally", "disputed", "seized",
    ]
    pro_ukraine_kw = [
        "ukrainian crimea", "crimea is ukraine", "deoccupation",
        "liberation of crimea", "belongs to ukraine", "ukrainian territory",
    ]
    for kw in pro_russia_kw:
        if kw in t:
            return "pro_russia"
    for kw in pro_ukraine_kw:
        if kw in t:
            return "pro_ukraine"
    for kw in neutral_kw:
        if kw in t and "crimea" in t:
            return "neutral_critical"
    return None


# ---------------------------------------------------------------------------
# Language-specific GDELT queries for each cluster
# ---------------------------------------------------------------------------

LANG_SPECIFIC_QUERIES = {
    "Spanish": [
        ('"crimea rusa"', "pro_russia"),
        ('"crimea" "anexion"', "neutral_critical"),
        ('"crimea" "ocupada"', "neutral_critical"),
        ('"crimea" "Ucrania"', "pro_ukraine"),
    ],
    "French": [
        ('"crimée russe"', "pro_russia"),
        ('"annexion" "crimée"', "neutral_critical"),
        ('"crimée" "occupée"', "neutral_critical"),
        ('"crimée" "Ukraine"', "pro_ukraine"),
    ],
    "German": [
        ('"russische krim"', "pro_russia"),
        ('"annexion" "krim"', "neutral_critical"),
        ('"krim" "besetzt"', "neutral_critical"),
        ('"krim" "Ukraine"', "pro_ukraine"),
    ],
    "Italian": [
        ('"crimea russa"', "pro_russia"),
        ('"annessione" "crimea"', "neutral_critical"),
        ('"crimea" "occupata"', "neutral_critical"),
        ('"crimea" "Ucraina"', "pro_ukraine"),
    ],
    "Turkish": [
        ('"rus kirim"', "pro_russia"),
        ('"kirim" "ilhak"', "neutral_critical"),
        ('"kirim" "isgal"', "neutral_critical"),
        ('"kirim" "Ukrayna"', "pro_ukraine"),
    ],
    "Arabic": [
        ('"القرم الروسي"', "pro_russia"),
        ('"ضم" "القرم"', "neutral_critical"),
        ('"احتلال" "القرم"', "neutral_critical"),
        ('"القرم" "أوكرانيا"', "pro_ukraine"),
    ],
    "Chinese": [
        ('"克里米亚" "俄罗斯"', "pro_russia"),
        ('"克里米亚" "吞并"', "neutral_critical"),
        ('"克里米亚" "乌克兰"', "pro_ukraine"),
    ],
}


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def run_analysis() -> dict:
    """Execute the full framing analysis pipeline."""
    all_articles: list[dict] = []
    seen_urls: set[str] = set()
    query_stats: dict[str, int] = {}

    def add_articles(articles: list[dict], framing_cat: str, query_label: str):
        count = 0
        for a in articles:
            url = a.get("url", "")
            if url in seen_urls:
                continue
            seen_urls.add(url)
            a["_query_framing"] = framing_cat
            a["_query_label"] = query_label
            a["_language_cluster"] = classify_language_cluster(a)
            a["_country"] = infer_country(a)
            a["_url_framing"] = classify_url_framing(url)
            a["_title_framing"] = classify_title_framing(a.get("title", ""))
            # Final framing: prefer title > URL > query-assigned
            a["_final_framing"] = (
                a["_title_framing"] or a["_url_framing"] or framing_cat
            )
            all_articles.append(a)
            count += 1
        return count

    # --- Phase 1: English-language framing queries ---
    print("=== Phase 1: Core framing queries (all languages) ===")
    for label, query, framing in FRAMING_QUERIES:
        print(f"  Querying: {label} ...", end=" ", flush=True)
        articles = gdelt_query(query)
        n = add_articles(articles, framing, label)
        query_stats[label] = n
        print(f"{n} new articles")
        time.sleep(REQUEST_DELAY)

    # --- Phase 2: Language-specific queries ---
    print("\n=== Phase 2: Language-specific framing queries ===")
    for lang, queries in LANG_SPECIFIC_QUERIES.items():
        gdelt_lang = LANGUAGE_CLUSTERS.get(lang, {}).get("gdelt_langs", [None])[0]
        sourcelang_param = gdelt_lang.lower() if gdelt_lang else None
        for query, framing in queries:
            label = f"{lang}: {query}"
            print(f"  Querying: {label} ...", end=" ", flush=True)
            articles = gdelt_query(query, sourcelang=sourcelang_param)
            n = add_articles(articles, framing, label)
            query_stats[label] = n
            print(f"{n} new articles")
            time.sleep(REQUEST_DELAY)

    print(f"\nTotal unique articles collected: {len(all_articles)}")
    return {
        "articles": all_articles,
        "query_stats": query_stats,
    }


def build_stats(articles: list[dict]) -> dict:
    """Aggregate statistics from collected articles."""

    # By framing category
    framing_counts = defaultdict(int)
    # By language cluster x framing
    lang_framing = defaultdict(lambda: defaultdict(int))
    # By country x framing
    country_framing = defaultdict(lambda: defaultdict(int))
    # By domain x framing
    domain_framing = defaultdict(lambda: defaultdict(int))
    # Notable outlets (high-count domains)
    domain_total = defaultdict(int)

    for a in articles:
        framing = a["_final_framing"]
        cluster = a["_language_cluster"]
        country = a["_country"]
        domain = a.get("domain", "unknown")

        framing_counts[framing] += 1
        lang_framing[cluster][framing] += 1
        country_framing[country][framing] += 1
        domain_framing[domain][framing] += 1
        domain_total[domain] += 1

    # Top domains by total articles
    top_domains = sorted(domain_total.items(), key=lambda x: -x[1])[:40]

    return {
        "total_articles": len(articles),
        "framing_counts": dict(framing_counts),
        "language_cluster_framing": {
            k: dict(v) for k, v in sorted(lang_framing.items())
        },
        "country_framing": {
            k: dict(v) for k, v in sorted(country_framing.items(), key=lambda x: -sum(x[1].values()))[:30]
        },
        "top_domains": [
            {
                "domain": d,
                "total": n,
                "framing": dict(domain_framing[d]),
            }
            for d, n in top_domains
        ],
    }


# ---------------------------------------------------------------------------
# Output generators
# ---------------------------------------------------------------------------

FRAMING_LABELS = {
    "pro_russia": "❌ Pro-Russia",
    "neutral_critical": "⚠️ Neutral/Critical",
    "pro_ukraine": "✅ Pro-Ukraine",
}


def write_json(data: dict, stats: dict):
    """Write raw JSON output."""
    os.makedirs(DATA_DIR, exist_ok=True)
    outpath = os.path.join(DATA_DIR, "media_framing.json")

    output = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "methodology": (
            "GDELT DOC API v2 article-level search for Crimea sovereignty framing. "
            "Articles are classified by: (1) search query framing category, "
            "(2) URL path sovereignty signals, (3) title keyword analysis. "
            "Language clusters assigned via GDELT language field + TLD inference."
        ),
        "statistics": stats,
        "articles": [
            {
                "url": a.get("url", ""),
                "title": a.get("title", ""),
                "domain": a.get("domain", ""),
                "language": a.get("language", ""),
                "source_country": a["_country"],
                "language_cluster": a["_language_cluster"],
                "framing": a["_final_framing"],
                "query_label": a["_query_label"],
                "seen_date": a.get("seendate", ""),
            }
            for a in data["articles"]
        ],
    }

    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nJSON written to {outpath}")


def write_markdown(stats: dict):
    """Write markdown report."""
    os.makedirs(DOCS_DIR, exist_ok=True)
    outpath = os.path.join(DOCS_DIR, "media.md")

    lines = [
        "# Media Sovereignty Framing: Crimea",
        "",
        f"*Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        "## Methodology",
        "",
        "This analysis uses the [GDELT DOC API v2](https://api.gdeltproject.org/api/v2/doc/doc) "
        "to search for recent articles mentioning Crimea with explicit sovereignty framing. "
        "Articles are classified into three categories:",
        "",
        "- **Pro-Russia**: Frames Crimea as Russian territory (\"Russian Crimea\", \"Republic of Crimea, Russia\")",
        "- **Neutral/Critical**: Acknowledges annexation/occupation (\"annexed Crimea\", \"occupied\")",
        "- **Pro-Ukraine**: Frames Crimea as Ukrainian territory (\"Ukrainian Crimea\", \"deoccupation\")",
        "",
        "Language-specific queries are run in Spanish, French, German, Italian, Turkish, Arabic, and Chinese.",
        "",
        "---",
        "",
        "## Overall Framing Distribution",
        "",
        f"**Total articles analyzed: {stats['total_articles']}**",
        "",
        "| Framing | Count | Share |",
        "|---------|------:|------:|",
    ]

    total = max(stats["total_articles"], 1)
    for key in ["pro_russia", "neutral_critical", "pro_ukraine"]:
        count = stats["framing_counts"].get(key, 0)
        pct = count / total * 100
        label = FRAMING_LABELS.get(key, key)
        lines.append(f"| {label} | {count} | {pct:.1f}% |")

    # Language cluster table
    lines += [
        "",
        "---",
        "",
        "## Framing by Language Cluster",
        "",
        "| Language | Pro-Russia | Neutral/Critical | Pro-Ukraine | Total |",
        "|----------|----------:|----------------:|------------:|------:|",
    ]
    for cluster, framings in sorted(stats["language_cluster_framing"].items()):
        pr = framings.get("pro_russia", 0)
        nc = framings.get("neutral_critical", 0)
        pu = framings.get("pro_ukraine", 0)
        t = pr + nc + pu
        lines.append(f"| {cluster} | {pr} | {nc} | {pu} | {t} |")

    # Country table
    lines += [
        "",
        "---",
        "",
        "## Framing by Source Country (Top 20)",
        "",
        "| Country | Pro-Russia | Neutral/Critical | Pro-Ukraine | Total |",
        "|---------|----------:|----------------:|------------:|------:|",
    ]
    for country, framings in list(stats["country_framing"].items())[:20]:
        pr = framings.get("pro_russia", 0)
        nc = framings.get("neutral_critical", 0)
        pu = framings.get("pro_ukraine", 0)
        t = pr + nc + pu
        lines.append(f"| {country} | {pr} | {nc} | {pu} | {t} |")

    # Top domains table
    lines += [
        "",
        "---",
        "",
        "## Top Domains by Volume",
        "",
        "| Domain | Total | Pro-Russia | Neutral/Critical | Pro-Ukraine |",
        "|--------|------:|----------:|----------------:|------------:|",
    ]
    for entry in stats["top_domains"][:30]:
        d = entry["domain"]
        t = entry["total"]
        pr = entry["framing"].get("pro_russia", 0)
        nc = entry["framing"].get("neutral_critical", 0)
        pu = entry["framing"].get("pro_ukraine", 0)
        lines.append(f"| {d} | {t} | {pr} | {nc} | {pu} |")

    # Notable findings
    lines += [
        "",
        "---",
        "",
        "## Key Findings",
        "",
        "### Outlets framing Crimea as Russian territory",
        "",
        "These outlets appeared in pro-Russia framing queries and showed URL/title signals "
        "indicating editorial treatment of Crimea as part of Russia:",
        "",
    ]

    pro_russia_domains = [
        e for e in stats["top_domains"]
        if e["framing"].get("pro_russia", 0) > 0
    ]
    for entry in pro_russia_domains[:15]:
        d = entry["domain"]
        pr = entry["framing"].get("pro_russia", 0)
        lines.append(f"- **{d}** ({pr} articles)")

    lines += [
        "",
        "### Outlets using neutral/critical framing",
        "",
        "These outlets use \"annexed\", \"occupied\", or other terms acknowledging "
        "the illegal nature of Russia's control:",
        "",
    ]
    neutral_domains = [
        e for e in stats["top_domains"]
        if e["framing"].get("neutral_critical", 0) > 0
    ]
    for entry in neutral_domains[:15]:
        d = entry["domain"]
        nc = entry["framing"].get("neutral_critical", 0)
        lines.append(f"- **{d}** ({nc} articles)")

    lines += [
        "",
        "### Outlets with pro-Ukraine framing",
        "",
    ]
    pro_ua_domains = [
        e for e in stats["top_domains"]
        if e["framing"].get("pro_ukraine", 0) > 0
    ]
    for entry in pro_ua_domains[:15]:
        d = entry["domain"]
        pu = entry["framing"].get("pro_ukraine", 0)
        lines.append(f"- **{d}** ({pu} articles)")

    lines += [
        "",
        "---",
        "",
        "*Data source: GDELT DOC API v2 (free, no BigQuery required)*",
        f"*Raw data: `data/media_framing.json`*",
        "",
    ]

    with open(outpath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Markdown written to {outpath}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    print("Crimea Sovereignty Framing Analysis")
    print("=" * 50)
    print(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"Using GDELT DOC API v2 (free, no GCP credits needed)")
    print()

    data = run_analysis()
    articles = data["articles"]

    if not articles:
        print("\nNo articles found. Check network connectivity to api.gdeltproject.org")
        sys.exit(1)

    stats = build_stats(articles)

    # Print summary to stdout
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total unique articles: {stats['total_articles']}")
    print(f"Framing breakdown:")
    for key in ["pro_russia", "neutral_critical", "pro_ukraine"]:
        count = stats["framing_counts"].get(key, 0)
        pct = count / max(stats["total_articles"], 1) * 100
        print(f"  {FRAMING_LABELS.get(key, key):25s} {count:5d}  ({pct:.1f}%)")

    print(f"\nLanguage clusters:")
    for cluster, framings in sorted(stats["language_cluster_framing"].items()):
        total = sum(framings.values())
        print(f"  {cluster:20s} {total:5d} articles")

    # Write outputs
    write_json(data, stats)
    write_markdown(stats)

    print("\nDone.")


if __name__ == "__main__":
    main()
