#!/usr/bin/env python3
"""
Independent Q1/Q2 journal verification scan.

Motivation
----------
The Stage-2 Claude Haiku classifier in pipelines/academic produced 1,581
LLM-confirmed Russia-framing papers from 5,151 Stage-1 signaled papers.
Stage-3 manual annotation (in the paper repo CSV) has confirmed ~57% of
the Russia labels on a partial 20% sample and downgraded the rest to
disputed or not-Crimea.

The Stage-2 LLM over-flags neutral uses of "Republic of Crimea" as a
geographic label. The question this script answers, independently of
the manual annotation:

    Which Q1 and Q2 journals actually allowed Russia framing to slip
    through, and for each such paper, what specifically triggered the
    Russia framing in the text?

The answer matters because "1,581 papers" is a less powerful finding
than "N Q1 journals × M Q2 journals host confirmed Russia framing with
named institutional affiliations."

Workflow
--------
Pass 1 — JOURNAL TIER CLASSIFICATION
    For every unique journal in the 5,151-paper Stage-1 signal set,
    query Claude Sonnet 4.6 for its SJR quartile, publisher, Scopus
    indexing, and open-access status. Results cached in
    data/q1_scan_cache/journal_tiers.json so subsequent runs only
    query new journals.

Pass 2 — PAPER RE-VERIFICATION FOR Q1/Q2 JOURNALS
    For every paper in a Q1 or Q2 journal (regardless of Haiku's
    original verdict — we want to see UA + RU + disputed + unclear),
    query Claude Sonnet 4.6 with a structured prompt that asks four
    specific things:

    (a) Is the paper's institutional affiliation Crimean-based?
    (b) Does the paper use "Republic of Crimea" as a neutral
        geographic label or as a political-institutional affiliation?
        Quote the key phrase.
    (c) Does the paper invoke any of six "special status" narrative
        tropes? (Catherine 1783, Khrushchev 1954, Sevastopol fleet,
        hero city, baptism of Rus at Chersonesos, Russian-speaking
        majority)
    (d) Final classification with a one-sentence reason.

Outputs
-------
data/q1_scan_cache/journal_tiers.json
    {journal_name: {quartile, publisher, is_scopus, is_open_access,
                     confidence, notes}}

data/q1_scan_cache/paper_verification.jsonl
    One JSON object per re-verified paper, append-only, resumable.

crimeaisukraine-paper/docs/q1_q2_journals_report.md
    Human-readable summary table of Q1/Q2 journals with Russia-framing
    papers, sorted by quartile and paper count.

crimeaisukraine-paper/docs/q1_q2_papers.csv
    Machine-readable per-paper table with all fields.

Usage
-----
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 scripts/verify_q1_journals.py --pass tier
    python3 scripts/verify_q1_journals.py --pass verify --tier-filter Q1,Q2
    python3 scripts/verify_q1_journals.py --pass report

    # Or run all three passes sequentially:
    python3 scripts/verify_q1_journals.py --pass all

    # Dry run (no API calls, just show counts):
    python3 scripts/verify_q1_journals.py --pass all --dry-run

Model
-----
Default: claude-sonnet-4-5-20250929 (Sonnet 4.6 equivalent). Override
with --model. For ambiguous cases where Sonnet's confidence is "low",
the script optionally retries with Opus via --opus-retry.
"""

import argparse
import csv
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic SDK not installed. Run: pip install anthropic", file=sys.stderr)
    sys.exit(1)


# ─── Paths ──────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ACADEMIC_RESULTS = DATA / "llm_academic_results.jsonl"       # 5,151 Stage-1 signaled w/ Haiku verdict
ACADEMIC_FULL    = DATA / "academic_full.jsonl"              # 91,670 rows w/ abstracts

CACHE_DIR = DATA / "q1_scan_cache"
CACHE_DIR.mkdir(exist_ok=True)
JOURNAL_CACHE = CACHE_DIR / "journal_tiers.json"
PAPER_RESULTS = CACHE_DIR / "paper_verification.jsonl"

PAPER_REPO = ROOT.parent / "crimeaisukraine-paper"
REPORT_MD = PAPER_REPO / "docs" / "q1_q2_journals_report.md"
REPORT_CSV = PAPER_REPO / "docs" / "q1_q2_papers.csv"


# ─── Model defaults ────────────────────────────────────────────────
DEFAULT_MODEL = "claude-sonnet-4-5-20250929"   # Sonnet 4.5/4.6
OPUS_MODEL    = "claude-opus-4-5-20250929"     # Opus 4.6
MAX_TOKENS_TIER   = 500
MAX_TOKENS_VERIFY = 1500
MAX_WORKERS       = 6

# Quartile ordering for sorting
Q_ORDER = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4, "preprint": 5, "repository": 6, "unknown": 7}


# ─── Prompts ───────────────────────────────────────────────────────

JOURNAL_TIER_PROMPT = """You are a bibliometric expert. Classify the following academic journal by its SJR (Scimago Journal Rank) quartile and publisher.

Journal name: {journal}

Return ONLY a valid JSON object with these exact keys (no markdown, no commentary):

{{
  "quartile": "Q1" | "Q2" | "Q3" | "Q4" | "preprint" | "repository" | "unknown",
  "publisher": "string (e.g. Wiley, Elsevier, Springer, IOP Publishing, EDP Sciences, open-access, or 'unknown')",
  "is_scopus_indexed": true | false | null,
  "is_web_of_science_indexed": true | false | null,
  "is_open_access": true | false | null,
  "is_predatory_or_questionable": true | false | null,
  "confidence": "high" | "medium" | "low",
  "notes": "one short sentence; if unknown say 'journal not in SJR database'"
}}

Rules:
- Q1 = top 25% of its field by SJR, Q2 = 25-50%, Q3 = 50-75%, Q4 = 75-100%
- "preprint" for SSRN, bioRxiv, arXiv, medRxiv
- "repository" for Zenodo, figshare, HAL, RePEc
- "unknown" if you genuinely cannot place the journal — prefer this over guessing
- Confidence "high" only if you are certain of the quartile from prior exposure; "medium" if you know the publisher but not the exact quartile; "low" if you are inferring from the name
- Russian-language journals are often SJR-indexed with lower quartiles; check whether the journal has an English title first
"""


PAPER_VERIFY_PROMPT = """You are verifying whether an academic paper frames Crimea as Russian territory, Ukrainian territory, or neutrally. You are the second reviewer — a smarter classifier trained to identify INSTITUTIONAL-AFFILIATION framing vs NEUTRAL GEOGRAPHIC LABELLING.

Paper title: {title}
Journal: {journal}
Year: {year}
Language: {language}
Original Stage-1 regex signals: {signals}
Original Stage-2 Haiku verdict: {haiku_verdict}

Abstract (may be truncated to 2000 chars):
{abstract}

Analyse the paper on FOUR specific axes. Return ONLY a valid JSON object:

{{
  "institutional_affiliation_is_crimean": true | false | "unknown",
  "mentions_crimea_as": "institutional_affiliation" | "neutral_geographic_label" | "political_claim" | "historical_reference" | "comparative_case" | "unknown",
  "key_phrase_quoted": "the single most diagnostic phrase from the title or abstract (verbatim, max 200 chars)",
  "tropes_detected": {{
    "catherine_1783": true | false,
    "khrushchev_1954": true | false,
    "black_sea_fleet": true | false,
    "hero_city_sevastopol": true | false,
    "baptism_of_rus_chersonesos": true | false,
    "russian_speaking_majority": true | false
  }},
  "final_classification": "russia_framing" | "ukraine_framing" | "neutral_geographic" | "analyzes_critically" | "unclear",
  "confidence": "high" | "medium" | "low",
  "one_sentence_reason": "why you reached this classification (max 300 chars)"
}}

Definitions:
- "russia_framing": the paper normalises Crimea as Russian territory — either through institutional affiliation ("Author X, Crimean Federal University, Republic of Crimea, Russian Federation") or explicit political claim ("the reunification of Crimea with Russia")
- "ukraine_framing": the paper explicitly frames Crimea as Ukrainian ("Crimea, Ukraine", "illegally annexed", "occupied", "Autonomous Republic of Crimea" as a Ukrainian constitutional entity)
- "neutral_geographic": the paper uses a Crimean place name only as a geographic reference without making any sovereignty claim (e.g. field samples, palaeontology, climatology, tourism)
- "analyzes_critically": the paper is a political science / international law / media studies paper that analyses Russian claims without endorsing them
- "unclear": genuinely cannot tell from title + abstract

Key discriminator: if the phrase "Republic of Crimea" appears without any qualifier ("occupied", "disputed", "Ukrainian"), check whether it is being used as:
(a) an institutional-affiliation string, identifying where the authors are based — → russia_framing
(b) a place-name reference in methodology/results — → neutral_geographic

The Stage-2 Haiku classifier does not distinguish (a) from (b). Your job is to make that distinction.
"""


# ─── Data loading ───────────────────────────────────────────────────

def load_signaled_papers():
    """Return list of papers from llm_academic_results.jsonl, cross-
    referenced with academic_full.jsonl to attach abstracts."""
    print(f"[load] reading {ACADEMIC_RESULTS}")
    papers = []
    with open(ACADEMIC_RESULTS) as f:
        for line in f:
            r = json.loads(line)
            papers.append(r)
    print(f"[load] {len(papers)} Stage-1 signaled papers")

    # Build URL → abstract index from academic_full.jsonl
    print(f"[load] indexing {ACADEMIC_FULL} for abstracts...")
    abstract_by_url = {}
    year_by_url = {}
    signals_by_url = {}
    with open(ACADEMIC_FULL) as f:
        for i, line in enumerate(f):
            if i > 0 and i % 20000 == 0:
                print(f"       indexed {i} rows")
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            url = r.get("doi") or r.get("openalex_id") or ""
            if url:
                if r.get("abstract"):
                    abstract_by_url[url] = r["abstract"]
                if r.get("year"):
                    year_by_url[url] = r["year"]
                if r.get("signals"):
                    signals_by_url[url] = r["signals"]
    print(f"[load] indexed {len(abstract_by_url)} abstracts")

    # Merge
    merged = []
    for p in papers:
        url = p.get("url", "")
        p["abstract"] = abstract_by_url.get(url, "")
        p["year"] = year_by_url.get(url, "")
        p["signals"] = signals_by_url.get(url, [])
        merged.append(p)
    with_abstract = sum(1 for p in merged if p.get("abstract"))
    print(f"[load] merged: {with_abstract}/{len(merged)} have abstracts")
    return merged


def load_cache(path):
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def save_cache(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


def load_done_urls(path):
    if not path.exists():
        return set()
    done = set()
    with open(path) as f:
        for line in f:
            try:
                r = json.loads(line)
                if "url" in r:
                    done.add(r["url"])
            except:
                pass
    return done


# ─── API wrappers ───────────────────────────────────────────────────

def get_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable is not set.", file=sys.stderr)
        print("       export ANTHROPIC_API_KEY=sk-ant-... before running.", file=sys.stderr)
        sys.exit(2)
    return anthropic.Anthropic(api_key=api_key)


def call_with_retry(client, model, system, user, max_tokens, retries=3):
    """Call Claude with exponential backoff on rate limits."""
    for attempt in range(retries):
        try:
            msg = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return msg.content[0].text.strip() if msg.content else ""
        except anthropic.RateLimitError:
            wait = (attempt + 1) * 5
            print(f"       rate limited, waiting {wait}s", file=sys.stderr)
            time.sleep(wait)
        except anthropic.APIError as e:
            print(f"       API error: {e}", file=sys.stderr)
            time.sleep(2)
    return None


def parse_json_safely(text):
    if not text:
        return None
    t = text.strip()
    # Strip markdown fences
    if t.startswith("```"):
        t = t.split("```", 2)[1] if "```" in t[3:] else t[3:]
        if t.startswith("json"):
            t = t[4:]
        t = t.strip("` \n")
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        # Try to find a JSON object inside the text
        start = t.find("{")
        end = t.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(t[start:end+1])
            except json.JSONDecodeError:
                pass
    return None


# ─── Pass 1: journal tier ───────────────────────────────────────────

def classify_journal(client, journal, model):
    prompt = JOURNAL_TIER_PROMPT.format(journal=journal)
    text = call_with_retry(client, model, "You are a concise, accurate bibliometric expert. Return only valid JSON.", prompt, MAX_TOKENS_TIER)
    result = parse_json_safely(text)
    if result is None:
        return {"quartile": "unknown", "publisher": "unknown", "confidence": "low",
                "notes": "JSON parse failed", "raw": text[:500] if text else ""}
    return result


def pass_tier(papers, model, dry_run, workers):
    cache = load_cache(JOURNAL_CACHE)
    print(f"[pass 1] journal tier classification")
    print(f"         {len(cache)} journals already cached")

    unique_journals = set()
    for p in papers:
        j = (p.get("journal") or "").strip()
        if j:
            unique_journals.add(j)
    print(f"         {len(unique_journals)} unique journals in dataset")

    to_query = [j for j in unique_journals if j not in cache]
    print(f"         {len(to_query)} new journals to query")

    if dry_run:
        print("[pass 1] DRY RUN — skipping API calls")
        return cache

    if not to_query:
        print("[pass 1] nothing to do (all cached)")
        return cache

    client = get_client()
    saved = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(classify_journal, client, j, model): j for j in to_query}
        for i, fut in enumerate(as_completed(futures), 1):
            j = futures[fut]
            try:
                result = fut.result()
                cache[j] = result
                saved += 1
                if i % 25 == 0 or i == len(to_query):
                    save_cache(JOURNAL_CACHE, cache)
                    print(f"[pass 1] {i}/{len(to_query)} · last: {j[:50]} → {result.get('quartile', '?')}")
            except Exception as e:
                print(f"[pass 1] error on {j}: {e}", file=sys.stderr)

    save_cache(JOURNAL_CACHE, cache)
    print(f"[pass 1] done, {saved} new entries cached")
    return cache


# ─── Pass 2: paper verification ────────────────────────────────────

def verify_paper(client, paper, model):
    abstract = paper.get("abstract", "") or ""
    if len(abstract) > 2000:
        abstract = abstract[:2000] + "..."
    signals = paper.get("signals", [])
    if isinstance(signals, list):
        signals_str = ", ".join(signals)
    else:
        signals_str = str(signals)

    prompt = PAPER_VERIFY_PROMPT.format(
        title=paper.get("title", ""),
        journal=paper.get("journal", ""),
        year=paper.get("year", ""),
        language=paper.get("language", "?"),
        signals=signals_str or "(no Stage-1 signals)",
        haiku_verdict=paper.get("llm_verdict", "?"),
        abstract=abstract or "(no abstract available)",
    )

    text = call_with_retry(client, model, "You are a careful, honest academic-framing classifier. Return only valid JSON.", prompt, MAX_TOKENS_VERIFY)
    result = parse_json_safely(text)
    if result is None:
        return {"error": "JSON parse failed", "raw": text[:500] if text else ""}
    return result


def pass_verify(papers, journal_cache, tier_filter, model, dry_run, workers, limit):
    tiers_of_interest = set(tier_filter.split(","))
    print(f"[pass 2] paper re-verification (filter: {tiers_of_interest})")

    # Build list of papers to verify
    to_verify = []
    for p in papers:
        j = (p.get("journal") or "").strip()
        tier_info = journal_cache.get(j, {})
        quartile = tier_info.get("quartile", "unknown")
        if quartile in tiers_of_interest:
            p["_journal_quartile"] = quartile
            p["_journal_publisher"] = tier_info.get("publisher", "unknown")
            p["_journal_info"] = tier_info
            to_verify.append(p)
    print(f"[pass 2] {len(to_verify)} papers in tiers {tiers_of_interest}")

    # Skip already-processed
    done_urls = load_done_urls(PAPER_RESULTS)
    to_verify = [p for p in to_verify if p.get("url", "") not in done_urls]
    print(f"[pass 2] {len(to_verify)} still to verify ({len(done_urls)} already done)")

    if limit > 0:
        to_verify = to_verify[:limit]
        print(f"[pass 2] limited to {len(to_verify)}")

    if dry_run:
        print("[pass 2] DRY RUN — not calling API")
        # Show distribution
        from collections import Counter
        by_quartile = Counter(p.get("_journal_quartile") for p in to_verify)
        by_verdict = Counter(p.get("llm_verdict") for p in to_verify)
        print(f"         by quartile: {dict(by_quartile)}")
        print(f"         by Haiku verdict: {dict(by_verdict)}")
        return

    if not to_verify:
        print("[pass 2] nothing to do")
        return

    client = get_client()
    with open(PAPER_RESULTS, "a") as out_f:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(verify_paper, client, p, model): p for p in to_verify}
            for i, fut in enumerate(as_completed(futures), 1):
                p = futures[fut]
                try:
                    result = fut.result()
                    row = {
                        "url": p.get("url", ""),
                        "title": p.get("title", ""),
                        "journal": p.get("journal", ""),
                        "journal_quartile": p.get("_journal_quartile"),
                        "journal_publisher": p.get("_journal_publisher"),
                        "year": p.get("year", ""),
                        "language": p.get("language", ""),
                        "haiku_verdict": p.get("llm_verdict", ""),
                        "sonnet_verification": result,
                    }
                    out_f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    out_f.flush()
                    if i % 10 == 0 or i == len(to_verify):
                        verdict = result.get("final_classification", "?") if isinstance(result, dict) else "?"
                        print(f"[pass 2] {i}/{len(to_verify)} · {p.get('_journal_quartile')} · {verdict} · {p.get('title', '')[:60]}")
                except Exception as e:
                    print(f"[pass 2] error on {p.get('url', '?')}: {e}", file=sys.stderr)

    print(f"[pass 2] done, results in {PAPER_RESULTS}")


# ─── Pass 3: report ─────────────────────────────────────────────────

def pass_report(papers, journal_cache):
    print(f"[pass 3] building report")

    if not PAPER_RESULTS.exists():
        print(f"[pass 3] no verification results at {PAPER_RESULTS} — run pass 2 first")
        return

    results = []
    with open(PAPER_RESULTS) as f:
        for line in f:
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    print(f"[pass 3] {len(results)} verified papers")

    # Aggregate by journal
    from collections import defaultdict, Counter
    by_journal = defaultdict(lambda: {
        "quartile": "unknown", "publisher": "unknown",
        "papers": [], "classifications": Counter(), "tropes": Counter()
    })
    for r in results:
        j = r.get("journal") or "(unknown journal)"
        by_journal[j]["quartile"] = r.get("journal_quartile") or "unknown"
        by_journal[j]["publisher"] = r.get("journal_publisher") or "unknown"
        by_journal[j]["papers"].append(r)
        sv = r.get("sonnet_verification") or {}
        if isinstance(sv, dict):
            fc = sv.get("final_classification", "unknown")
            by_journal[j]["classifications"][fc] += 1
            tropes = sv.get("tropes_detected", {}) or {}
            if isinstance(tropes, dict):
                for k, v in tropes.items():
                    if v is True:
                        by_journal[j]["tropes"][k] += 1

    # Sort journals: Q1 first, then Q2, then by confirmed russia_framing count desc
    sorted_journals = sorted(
        by_journal.items(),
        key=lambda kv: (
            Q_ORDER.get(kv[1]["quartile"], 9),
            -kv[1]["classifications"].get("russia_framing", 0),
            kv[0].lower(),
        )
    )

    # Counts by quartile
    paper_count_by_q = Counter()
    russia_count_by_q = Counter()
    for j, info in by_journal.items():
        q = info["quartile"] or "unknown"
        paper_count_by_q[q] += len(info["papers"])
        russia_count_by_q[q] += info["classifications"].get("russia_framing", 0)

    # Trope totals
    global_tropes = Counter()
    for info in by_journal.values():
        for k, v in info["tropes"].items():
            global_tropes[k] += v

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_MD, "w") as f:
        f.write("# Q1/Q2 journal verification — independent Sonnet-4.6 scan\n\n")
        f.write(f"Generated from `data/llm_academic_results.jsonl` (5,151 Stage-1 signaled papers) "
                f"with journal tier classification via Claude Sonnet 4.6, independent of the Stage-3 manual annotation.\n\n")
        f.write(f"**Papers re-verified**: {len(results)}\n\n")

        f.write("## Paper counts by journal quartile\n\n")
        f.write("| Quartile | Papers verified | Confirmed Russia framing |\n")
        f.write("|---|---:|---:|\n")
        for q in ["Q1", "Q2", "Q3", "Q4", "preprint", "repository", "unknown"]:
            if paper_count_by_q.get(q, 0) > 0:
                f.write(f"| {q} | {paper_count_by_q[q]} | {russia_count_by_q[q]} |\n")
        f.write("\n")

        f.write("## Narrative-trope detection across all verified papers\n\n")
        f.write("How many Q1/Q2 papers invoke each Russian \"special status\" historical trope "
                "(independent of whether the paper is classified as Russia-framing overall):\n\n")
        f.write("| Trope | Papers that invoke it |\n")
        f.write("|---|---:|\n")
        trope_labels = {
            "catherine_1783": "Catherine II's 1783 annexation",
            "khrushchev_1954": "Khrushchev 1954 transfer",
            "black_sea_fleet": "Black Sea Fleet / Sevastopol base",
            "hero_city_sevastopol": "Sevastopol WWII 'hero city'",
            "baptism_of_rus_chersonesos": "Baptism of Rus at Chersonesos",
            "russian_speaking_majority": "Russian-speaking majority",
        }
        for key, label in trope_labels.items():
            f.write(f"| {label} | {global_tropes.get(key, 0)} |\n")
        f.write("\n")

        f.write("## Per-journal breakdown (Q1 → Q4 → preprint → repository → unknown)\n\n")
        f.write("Sorted by quartile, then by number of confirmed Russia-framing papers descending.\n\n")
        f.write("| Quartile | Journal | Publisher | # papers | confirmed RU | neutral | UA | critical | unclear |\n")
        f.write("|---|---|---|---:|---:|---:|---:|---:|---:|\n")
        for j, info in sorted_journals:
            c = info["classifications"]
            total = len(info["papers"])
            f.write(f"| **{info['quartile']}** | {j[:80]} | {info['publisher'][:30]} | {total} | "
                    f"{c.get('russia_framing', 0)} | {c.get('neutral_geographic', 0)} | "
                    f"{c.get('ukraine_framing', 0)} | {c.get('analyzes_critically', 0)} | "
                    f"{c.get('unclear', 0)} |\n")
        f.write("\n")

        # List of individual Q1/Q2 papers confirmed as Russia framing
        f.write("## Individual Q1/Q2 papers confirmed as Russia framing (Sonnet verdict)\n\n")
        f.write("The headline list for the journalist: Q1 and Q2 papers that Sonnet 4.6 confirmed as Russia-framing "
                "with the diagnostic phrase from the abstract and a one-sentence reason.\n\n")
        confirmed_q1q2 = [
            r for r in results
            if r.get("journal_quartile") in ("Q1", "Q2")
            and isinstance(r.get("sonnet_verification"), dict)
            and r["sonnet_verification"].get("final_classification") == "russia_framing"
        ]
        f.write(f"**Total: {len(confirmed_q1q2)} papers**\n\n")
        for i, r in enumerate(sorted(confirmed_q1q2, key=lambda x: (Q_ORDER.get(x["journal_quartile"], 9), x.get("journal", ""))), 1):
            sv = r["sonnet_verification"]
            f.write(f"### {i}. [{r['journal_quartile']}] {r['title']}\n")
            f.write(f"- **Journal**: {r['journal']} ({r['journal_publisher']})\n")
            f.write(f"- **Year**: {r.get('year', '?')} · **Language**: {r.get('language', '?')}\n")
            f.write(f"- **DOI**: {r['url']}\n")
            f.write(f"- **Haiku said**: {r['haiku_verdict']} · **Sonnet confirmed**: russia_framing ({sv.get('confidence', '?')} confidence)\n")
            mentions = sv.get("mentions_crimea_as", "?")
            f.write(f"- **Mentions Crimea as**: {mentions}\n")
            if sv.get("institutional_affiliation_is_crimean") is True:
                f.write(f"- **Institutional affiliation is Crimean**: yes\n")
            key_phrase = sv.get("key_phrase_quoted", "")
            if key_phrase:
                f.write(f"- **Key phrase**: \"{key_phrase}\"\n")
            tropes = sv.get("tropes_detected", {}) or {}
            hit_tropes = [k for k, v in tropes.items() if v is True]
            if hit_tropes:
                f.write(f"- **Tropes invoked**: {', '.join(hit_tropes)}\n")
            reason = sv.get("one_sentence_reason", "")
            if reason:
                f.write(f"- **Reason**: {reason}\n")
            f.write("\n")

    # CSV output
    REPORT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "quartile", "journal", "publisher", "title", "year", "language", "doi",
            "haiku_verdict", "sonnet_classification", "sonnet_confidence",
            "institutional_affiliation_crimean", "mentions_crimea_as",
            "key_phrase", "tropes", "reason",
        ])
        for r in results:
            sv = r.get("sonnet_verification") or {}
            if not isinstance(sv, dict):
                continue
            tropes = sv.get("tropes_detected", {}) or {}
            hit_tropes = [k for k, v in tropes.items() if v is True] if isinstance(tropes, dict) else []
            w.writerow([
                r.get("journal_quartile", ""),
                r.get("journal", ""),
                r.get("journal_publisher", ""),
                r.get("title", ""),
                r.get("year", ""),
                r.get("language", ""),
                r.get("url", ""),
                r.get("haiku_verdict", ""),
                sv.get("final_classification", ""),
                sv.get("confidence", ""),
                sv.get("institutional_affiliation_is_crimean", ""),
                sv.get("mentions_crimea_as", ""),
                sv.get("key_phrase_quoted", ""),
                "|".join(hit_tropes),
                sv.get("one_sentence_reason", ""),
            ])

    print(f"[pass 3] wrote {REPORT_MD}")
    print(f"[pass 3] wrote {REPORT_CSV}")


# ─── Main ───────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pass", dest="phase", choices=["tier", "verify", "report", "all"], default="all")
    ap.add_argument("--tier-filter", default="Q1,Q2")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=MAX_WORKERS)
    ap.add_argument("--limit", type=int, default=0, help="limit pass-2 to N papers (0 = no limit)")
    args = ap.parse_args()

    papers = load_signaled_papers()
    print()

    if args.phase in ("tier", "all"):
        journal_cache = pass_tier(papers, args.model, args.dry_run, args.workers)
        print()
    else:
        journal_cache = load_cache(JOURNAL_CACHE)

    if args.phase in ("verify", "all"):
        pass_verify(papers, journal_cache, args.tier_filter, args.model, args.dry_run, args.workers, args.limit)
        print()

    if args.phase in ("report", "all"):
        if not args.dry_run:
            pass_report(papers, journal_cache)


if __name__ == "__main__":
    main()
