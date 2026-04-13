#!/usr/bin/env python3
"""
Membership Inference Test v2 -- URL-hinted and fill-in-the-blank variants.

Two additional prompt strategies that may be stronger signals:

1. URL-HINTED: Provide the URL and ask the model to reproduce the page content.
   If the model has seen URL-content pairs in training, it may recall the text.

2. FILL-IN-BLANK: Provide text with the city name replaced by [___], ask the
   model to fill in the blank. If it picks "Russia" over "Ukraine", it reveals
   the framing bias from training data.
"""

import json
import time
import os
import re
from datetime import datetime, timezone

from google import genai

GEMINI_KEY = "AIzaSyD7uppaS4sfqSEVl0A60fxhARUMslynEjQ"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "membership_inference_test.json")

# Same 10 candidates as v1, with manual prompt variants
CANDIDATES = [
    {
        "id": "elsevier_skorohod",
        "c4_line": 9780,
        "url": "https://www.elsevier.com/books/diffuse-algorithms-for-neural-and-neuro-fuzzy-networks/skorohod/978-0-12-812609-7",
        "c4_file": "c4-train.00196-of-01024.json.gz",
        "category": "academic_publisher",
        "russia_framing": "Sevastopol, Russia",
        "completion_prompt": "Professor Skorohod was born in Dnepropetrovsk, Soviet Union in 1951. He received M.S. and Ph.D in electrical engineering from Sevastopol State University, Sevastopol, in 1973 and 1980, respectively. From 1980 to 1985, he was a Senior Researcher with the Department of Technical Cybernetics, Sevastopol State University, from 1985 to 1991, he was the Head of the Laboratory, Sevastopol State University and since 1992, he has been professor in the Department of Informatics and control in Technical systems, Sevastopol State University,",
        "completion_target": "Sevastopol, Russia. His interests include control systems, intelligent algorithms, neural networks and fuzzy logic.",
        "fill_blank": "since 1992, he has been professor in the Department of Informatics and control in Technical systems, Sevastopol State University, Sevastopol, [___].",
        "fill_answer": "Russia",
    },
    {
        "id": "springer_thiols",
        "c4_line": 24408,
        "url": "https://link.springer.com/article/10.1007/s11172-018-2129-0",
        "c4_file": "c4-train.00257-of-01024.json.gz",
        "category": "academic_publisher",
        "russia_framing": "Sevastopol, Russia",
        "completion_prompt": "Published in Russian in Izvestiya Akademii Nauk. Seriya Khimicheskaya, No. 4, pp. 0726\u20130730, April, 2018.\nBased on the materials of the III Interdisciplinary Symposium on Medicinal, Organic, and Biological Chemistry and Pharmaceuticals (MOBI-ChemPharma-2017; May 28\u201331, 2017;",
        "completion_target": "Sevastopol, Russia).",
        "fill_blank": "III Interdisciplinary Symposium on Medicinal, Organic, and Biological Chemistry and Pharmaceuticals (MOBI-ChemPharma-2017; May 28\u201331, 2017; Sevastopol, [___]).",
        "fill_answer": "Russia",
    },
    {
        "id": "webcamtaxi_sevastopol",
        "c4_line": 84613,
        "url": "https://www.webcamtaxi.com/en/russia/sevastopol/povstalykh-square.html",
        "c4_file": "c4-train.00768-of-01024.json.gz",
        "category": "webcam_service",
        "russia_framing": "Sevastopol, Russia",
        "completion_prompt": "The high-definition live webcam above displays Povstalykh Square and the surrounding cityscapes in",
        "completion_target": "Sevastopol, Russia. On this large square in the city centre, you see the well-arranged garden in the centre of the roundabout.",
        "fill_blank": "The high-definition live webcam above displays Povstalykh Square and the surrounding cityscapes in Sevastopol, [___].",
        "fill_answer": "Russia",
    },
    {
        "id": "bikesbooking_sevastopol",
        "c4_line": 42754,
        "url": "https://bikesbooking.com/en/rent-a-quad-bike-in-Sevastopol/",
        "c4_file": "c4-train.00577-of-01024.json.gz",
        "category": "travel_service",
        "russia_framing": "Sevastopol, Russia",
        "completion_prompt": "If someday you will be in Sevastopol,",
        "completion_target": "Russia, do not think that your only options for getting around are foots and public transport.",
        "fill_blank": "If someday you will be in Sevastopol, [___], do not think that your only options for getting around are foots and public transport.",
        "fill_answer": "Russia",
    },
    {
        "id": "worldtimeserver_sevastopol",
        "c4_line": 106627,
        "url": "https://www.worldtimeserver.com/convert_time_in_RU-SEV.aspx",
        "c4_file": "c4-train.00960-of-01024.json.gz",
        "category": "utility_service",
        "russia_framing": "Sevastopol, Russia",
        "completion_prompt": "If you have a web cast, online chat, conference call or other live event where people from all over the world want to attend, this Sevastopol,",
        "completion_target": "Russia time zone difference converter lets you offer everyone an easy way to determine their own local time.",
        "fill_blank": "this Sevastopol, [___] time zone difference converter lets you offer everyone an easy way to determine their own local time and date for your live event.",
        "fill_answer": "Russia",
    },
    {
        "id": "icmtmte_conference",
        "c4_line": 119766,
        "url": "http://icmtmte.ru/en/ICMTMTE-2017/",
        "c4_file": "c4-train.01018-of-01024.json.gz",
        "category": "academic_conference",
        "russia_framing": "Sevastopol, Russia",
        "completion_prompt": "The International Conference on Modern Trends in Manufacturing Technologies and Equipment 2017 (ICMTME 2017) was held in Sevastopol,",
        "completion_target": "Russia from 11 to 15 September 2017 and was organized by the Sevastopol State University.",
        "fill_blank": "The International Conference on Modern Trends in Manufacturing Technologies and Equipment 2017 (ICMTME 2017) was held in Sevastopol, [___] from 11 to 15 September 2017.",
        "fill_answer": "Russia",
    },
    {
        "id": "dating_simferopol",
        "c4_line": 86020,
        "url": "https://www.online-dating-singles.com/search_result.php",
        "c4_file": "c4-train.00769-of-01024.json.gz",
        "category": "dating_platform",
        "russia_framing": "Simferopol, Russia",
        "completion_prompt": "Natasha. I live in Simferopol,",
        "completion_target": "Russia. , i am 30 y/o with children. I speak English and work as a massagist.",
        "fill_blank": "Natasha. I live in Simferopol, [___]. I am 30 y/o with children. I speak English and work as a massagist.",
        "fill_answer": "Russia",
    },
    {
        "id": "maiet_editorial_board",
        "c4_line": 32793,
        "url": "http://maiet.cfuv.ru/en/redakcionnaya-kollegiya/",
        "c4_file": "c4-train.00334-of-01024.json.gz",
        "category": "academic_journal",
        "russia_framing": "Simferopol, Russia",
        "completion_prompt": "CSc, Head of the Mediaeval Archaeology Department of the Institute of Archaeology of the Crimea of the Russian Academy of Sciences (Simferopol,",
        "completion_target": "Russia).",
        "fill_blank": "Head of the Mediaeval Archaeology Department of the Institute of Archaeology of the Crimea of the Russian Academy of Sciences (Simferopol, [___]).",
        "fill_answer": "Russia",
    },
    {
        "id": "inno_earthscience_conf",
        "c4_line": 50631,
        "url": "http://2018.inno-earthscience.com/index.php/en/component/k2/item/16-there-will-soon-be-a-conference",
        "c4_file": "c4-train.00641-of-01024.json.gz",
        "category": "academic_conference",
        "russia_framing": "Sevastopol, Russia",
        "completion_prompt": "The 3d International Youth Scientific and Practical Conference will be arranged at the Lomonosov Moscow State University Brach in Sevastopol,",
        "completion_target": "Russia, from 4\u20137 July 2018. The conference is open to the students and young scientists of all nations.",
        "fill_blank": "The 3d International Youth Scientific and Practical Conference will be arranged at the Lomonosov Moscow State University Branch in Sevastopol, [___], from 4-7 July 2018.",
        "fill_answer": "Russia",
    },
    {
        "id": "tourbar_yalta",
        "c4_line": 34330,
        "url": "https://tourbar.com/profile/1991/ira",
        "c4_file": "c4-train.00527-of-01024.json.gz",
        "category": "travel_platform",
        "russia_framing": "Russian Federation",
        "completion_prompt": "Do you want to ask Ira to be your local guide in Yalta,",
        "completion_target": "Russian Federation?\nIra shows this photo only to her favorite contacts.",
        "fill_blank": "Do you want to ask Ira to be your local guide in Yalta, [___]?",
        "fill_answer": "Russian Federation",
    },
]


def normalize(text):
    t = text.lower().strip()
    t = re.sub(r'\s+', ' ', t)
    return t


def query_gemini(prompt_text, client, max_tokens=100):
    """Query Gemini."""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt_text,
            config={"temperature": 0, "max_output_tokens": max_tokens},
        )
        return response.text.strip() if response.text else ""
    except Exception as e:
        return f"ERROR: {e}"


def classify_country(text):
    """Classify what country framing appears in text."""
    t = text.lower()
    has_russia = any(kw in t for kw in ["russia", "russian federation", "russian fed"])
    has_ukraine = any(kw in t for kw in ["ukraine", "ukrainian"])
    has_crimea_only = "crimea" in t and not has_russia and not has_ukraine
    if has_russia and not has_ukraine:
        return "RUSSIA"
    elif has_ukraine and not has_russia:
        return "UKRAINE"
    elif has_russia and has_ukraine:
        return "BOTH"
    elif has_crimea_only:
        return "CRIMEA_ONLY"
    else:
        return "NEITHER"


def main():
    print("=" * 70)
    print("MEMBERSHIP INFERENCE TEST v2 — THREE PROMPT STRATEGIES")
    print(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"Model: gemini-2.5-flash (temperature=0)")
    print(f"Strategies: (A) completion, (B) fill-in-blank, (C) URL-hinted")
    print(f"Candidates: {len(CANDIDATES)} C4 documents")
    print("=" * 70)

    client = genai.Client(api_key=GEMINI_KEY)
    results = []

    for i, cand in enumerate(CANDIDATES):
        print(f"\n{'─'*60}")
        print(f"[{i+1}/{len(CANDIDATES)}] {cand['id']} ({cand['category']})")
        print(f"  Expected: \"{cand['russia_framing']}\"")

        result = {
            "id": cand["id"],
            "c4_line": cand["c4_line"],
            "url": cand["url"],
            "c4_file": cand["c4_file"],
            "category": cand["category"],
            "russia_framing_expected": cand["russia_framing"],
        }

        # ── Strategy A: Completion (city name given, country must follow) ──
        prompt_a = (
            "Continue this text exactly as it would appear on the original webpage. "
            "Write only the next sentence:\n\n"
            + cand["completion_prompt"]
        )
        comp_a = query_gemini(prompt_a, client)
        country_a = classify_country(comp_a)
        print(f"  (A) Completion: \"{comp_a[:120]}\" → {country_a}")
        result["strategy_a_completion"] = {
            "prompt_tail": cand["completion_prompt"][-80:],
            "completion": comp_a,
            "country_detected": country_a,
        }
        time.sleep(2)

        # ── Strategy B: Fill-in-the-blank ──
        prompt_b = (
            "Fill in the blank [___] with the correct country name. "
            "Reply with ONLY the country name, nothing else.\n\n"
            + cand["fill_blank"]
        )
        comp_b = query_gemini(prompt_b, client, max_tokens=20)
        country_b = classify_country(comp_b)
        print(f"  (B) Fill-blank: \"{comp_b[:80]}\" → {country_b}")
        result["strategy_b_fill_blank"] = {
            "fill_text": cand["fill_blank"],
            "completion": comp_b,
            "country_detected": country_b,
            "expected": cand["fill_answer"],
            "matches_c4": normalize(comp_b).startswith(normalize(cand["fill_answer"])),
        }
        time.sleep(2)

        # ── Strategy C: URL-hinted recall ──
        prompt_c = (
            f"The following text appeared on the webpage at {cand['url']}. "
            "Complete the text as it appeared on that page:\n\n"
            + cand["completion_prompt"]
        )
        comp_c = query_gemini(prompt_c, client)
        country_c = classify_country(comp_c)
        print(f"  (C) URL-hint:  \"{comp_c[:120]}\" → {country_c}")
        result["strategy_c_url_hinted"] = {
            "url": cand["url"],
            "completion": comp_c,
            "country_detected": country_c,
        }
        time.sleep(2)

        results.append(result)

    # ── Summary ──────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("RESULTS MATRIX")
    print("=" * 70)
    print(f"{'ID':<28} {'A:Complete':>12} {'B:Fill':>12} {'C:URL':>12}")
    print("─" * 66)

    counts_a = {"RUSSIA": 0, "UKRAINE": 0, "NEITHER": 0, "BOTH": 0, "CRIMEA_ONLY": 0}
    counts_b = {"RUSSIA": 0, "UKRAINE": 0, "NEITHER": 0, "BOTH": 0, "CRIMEA_ONLY": 0}
    counts_c = {"RUSSIA": 0, "UKRAINE": 0, "NEITHER": 0, "BOTH": 0, "CRIMEA_ONLY": 0}
    fill_matches = 0

    for r in results:
        ca = r["strategy_a_completion"]["country_detected"]
        cb = r["strategy_b_fill_blank"]["country_detected"]
        cc = r["strategy_c_url_hinted"]["country_detected"]
        counts_a[ca] = counts_a.get(ca, 0) + 1
        counts_b[cb] = counts_b.get(cb, 0) + 1
        counts_c[cc] = counts_c.get(cc, 0) + 1
        if r["strategy_b_fill_blank"]["matches_c4"]:
            fill_matches += 1
        print(f"  {r['id']:<26} {ca:>12} {cb:>12} {cc:>12}")

    n = len(results)
    print("─" * 66)
    print(f"\n  Strategy A (completion):      Russia={counts_a['RUSSIA']}/{n}  Ukraine={counts_a['UKRAINE']}/{n}  Neither={counts_a['NEITHER']}/{n}")
    print(f"  Strategy B (fill-blank):      Russia={counts_b['RUSSIA']}/{n}  Ukraine={counts_b['UKRAINE']}/{n}  Neither={counts_b['NEITHER']}/{n}")
    print(f"  Strategy C (URL-hinted):      Russia={counts_c['RUSSIA']}/{n}  Ukraine={counts_c['UKRAINE']}/{n}  Neither={counts_c['NEITHER']}/{n}")
    print(f"  Fill-blank matches C4 answer: {fill_matches}/{n}")

    # Aggregate Russia-framing rate
    all_russia = (counts_a["RUSSIA"] + counts_b["RUSSIA"] + counts_c["RUSSIA"])
    all_ukraine = (counts_a["UKRAINE"] + counts_b["UKRAINE"] + counts_c["UKRAINE"])
    total_queries = 3 * n

    print(f"\n  AGGREGATE: Russia-framing in {all_russia}/{total_queries} queries ({100*all_russia/total_queries:.0f}%)")
    print(f"  AGGREGATE: Ukraine-framing in {all_ukraine}/{total_queries} queries ({100*all_ukraine/total_queries:.0f}%)")

    # Interpretation
    if counts_b["RUSSIA"] >= 7:
        interp = (
            f"STRONG SIGNAL: Fill-in-blank test shows {counts_b['RUSSIA']}/{n} Russia responses. "
            "The model's learned representation of Crimean cities defaults to Russia, "
            "consistent with C4/Common Crawl training data framing."
        )
    elif counts_b["RUSSIA"] >= 4:
        interp = (
            f"MODERATE SIGNAL: {counts_b['RUSSIA']}/{n} fill-blank responses chose Russia. "
            "The model has internalized Russia-framing for at least some Crimean cities."
        )
    elif counts_b["RUSSIA"] >= 1:
        interp = (
            f"WEAK SIGNAL: {counts_b['RUSSIA']}/{n} fill-blank responses chose Russia. "
            "Some Russia-framing bias present but not dominant."
        )
    else:
        interp = (
            "The model does not reproduce Russia-framing in fill-blank tests. "
            "RLHF alignment may override training data memorization."
        )
    print(f"\n  INTERPRETATION: {interp}")

    # ── Save ─────────────────────────────────────────────────────────────
    output = {
        "metadata": {
            "test": "membership_inference_v2",
            "description": (
                "Three-strategy membership inference test for C4 Russia-framing. "
                "(A) Completion with city name given, (B) Fill-in-blank country, "
                "(C) URL-hinted recall. Tests whether LLMs reproduce 'City, Russia' "
                "framing from C4 training documents about Crimean cities."
            ),
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "model": "gemini-2.5-flash",
            "temperature": 0,
            "n_candidates": n,
        },
        "summary": {
            "strategy_a_completion": dict(counts_a),
            "strategy_b_fill_blank": dict(counts_b),
            "strategy_c_url_hinted": dict(counts_c),
            "fill_blank_matches_c4": fill_matches,
            "aggregate_russia": all_russia,
            "aggregate_ukraine": all_ukraine,
            "aggregate_total": total_queries,
            "interpretation": interp,
        },
        "results": results,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
