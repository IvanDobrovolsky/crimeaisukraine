#!/usr/bin/env python3
"""
Membership Inference Test for C4 Training Data

Method: Take unique passages from C4 documents containing Russia-framing
about Crimea. Split each document JUST BEFORE the Russia-framing phrase,
feed the preceding text as a prompt (temperature=0), and check if the
model completes with the specific Russia-framing from C4.

Key design: The split point is placed so the Russia-framing is in the
target, not the prompt. The model must generate it from memory.

A model that reproduces "Sevastopol, Russia" or "Simferopol, Russia" in
its completion likely saw this C4 document (or its Common Crawl source)
during training.
"""

import json
import time
import os
import re
from datetime import datetime, timezone

from google import genai

GEMINI_KEY = "AIzaSyD7uppaS4sfqSEVl0A60fxhARUMslynEjQ"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "membership_inference_test.json")

# ── 10 candidates with MANUAL split points ──────────────────────────────
# Each "prompt" ends just before the Russia-framing.
# Each "target" starts with or contains the Russia-framing phrase.
# The model must generate the framing from memory if it has seen the text.

CANDIDATES = [
    {
        "id": "elsevier_skorohod",
        "c4_line": 9780,
        "url": "https://www.elsevier.com/books/diffuse-algorithms-for-neural-and-neuro-fuzzy-networks/skorohod/978-0-12-812609-7",
        "c4_file": "c4-train.00196-of-01024.json.gz",
        "category": "academic_publisher",
        "russia_framing": "Sevastopol, Russia",
        # Split right before "Sevastopol, Russia" in author bio
        "prompt": "Professor Skorohod was born in Dnepropetrovsk, Soviet Union in 1951. He received M.S. and Ph.D in electrical engineering from Sevastopol State University, Sevastopol, in 1973 and 1980, respectively. From 1980 to 1985, he was a Senior Researcher with the Department of Technical Cybernetics, Sevastopol State University, from 1985 to 1991, he was the Head of the Laboratory, Sevastopol State University and since 1992, he has been professor in the Department of Informatics and control in Technical systems, Sevastopol State University,",
        "target": "Sevastopol, Russia. His interests include control systems, intelligent algorithms, neural networks and fuzzy logic.",
        "full_text": "Professor Skorohod was born in Dnepropetrovsk, Soviet Union in 1951. He received M.S. and Ph.D in electrical engineering from Sevastopol State University, Sevastopol, in 1973 and 1980, respectively.\nFrom 1980 to 1985, he was a Senior Researcher with the Department of Technical Cybernetics, Sevastopol State University, from 1985 to 1991, he was the Head of the Laboratory, Sevastopol State University and since 1992, he has been professor in the Department of Informatics and control in Technical systems, Sevastopol State University, Sevastopol, Russia. His interests include control systems, intelligent algorithms, neural networks and fuzzy logic.",
    },
    {
        "id": "springer_thiols",
        "c4_line": 24408,
        "url": "https://link.springer.com/article/10.1007/s11172-018-2129-0",
        "c4_file": "c4-train.00257-of-01024.json.gz",
        "category": "academic_publisher",
        "russia_framing": "Sevastopol, Russia",
        # Split right before location in conference citation
        "prompt": "Published in Russian in Izvestiya Akademii Nauk. Seriya Khimicheskaya, No. 4, pp. 0726\u20130730, April, 2018.\nBased on the materials of the III Interdisciplinary Symposium on Medicinal, Organic, and Biological Chemistry and Pharmaceuticals (MOBI-ChemPharma-2017; May 28\u201331, 2017;",
        "target": "Sevastopol, Russia).",
        "full_text": "Published in Russian in Izvestiya Akademii Nauk. Seriya Khimicheskaya, No. 4, pp. 0726\u20130730, April, 2018.\nBased on the materials of the III Interdisciplinary Symposium on Medicinal, Organic, and Biological Chemistry and Pharmaceuticals (MOBI-ChemPharma-2017; May 28\u201331, 2017; Sevastopol, Russia).",
    },
    {
        "id": "webcamtaxi_sevastopol",
        "c4_line": 84613,
        "url": "https://www.webcamtaxi.com/en/russia/sevastopol/povstalykh-square.html",
        "c4_file": "c4-train.00768-of-01024.json.gz",
        "category": "webcam_service",
        "russia_framing": "Sevastopol, Russia",
        # Split at the beginning, before the framing
        "prompt": "The high-definition live webcam above displays Povstalykh Square and the surrounding cityscapes in",
        "target": "Sevastopol, Russia. On this large square in the city centre, you see the well-arranged garden in the centre of the roundabout, and a bus stop on the right-hand side.",
        "full_text": "The high-definition live webcam above displays Povstalykh Square and the surrounding cityscapes in Sevastopol, Russia. On this large square in the city centre, you see the well-arranged garden in the centre of the roundabout, and a bus stop on the right-hand side.\nSevastopol is a major city in the Crimean Peninsula and an important Black Sea port.",
    },
    {
        "id": "bikesbooking_sevastopol",
        "c4_line": 42754,
        "url": "https://bikesbooking.com/en/rent-a-quad-bike-in-Sevastopol/",
        "c4_file": "c4-train.00577-of-01024.json.gz",
        "category": "travel_service",
        "russia_framing": "Sevastopol, Russia",
        # Split at the very start, right before the Russia-framing
        "prompt": "If someday you will be in",
        "target": "Sevastopol, Russia, do not think that your only options for getting around are foots and public transport. You always can rent a quad bike from some of the local suppliers and enjoy this great place by yourself.",
        "full_text": "If someday you will be in Sevastopol, Russia, do not think that your only options for getting around are foots and public transport. You always can rent a quad bike from some of the local suppliers and enjoy this great place by yourself. Quad bike is an eco-friendly type of transport, which provide you with more impressions.",
    },
    {
        "id": "worldtimeserver_sevastopol",
        "c4_line": 106627,
        "url": "https://www.worldtimeserver.com/convert_time_in_RU-SEV.aspx",
        "c4_file": "c4-train.00960-of-01024.json.gz",
        "category": "utility_service",
        "russia_framing": "Sevastopol, Russia",
        # Split before the first "Sevastopol, Russia"
        "prompt": "If you have a web cast, online chat, conference call or other live event where people from all over the world want to attend, this",
        "target": "Sevastopol, Russia time zone difference converter lets you offer everyone an easy way to determine their own local time and date for your live event in Sevastopol, Russia.",
        "full_text": "If you have a web cast, online chat, conference call or other live event where people from all over the world want to attend, this Sevastopol, Russia time zone difference converter lets you offer everyone an easy way to determine their own local time and date for your live event in Sevastopol, Russia.",
    },
    {
        "id": "icmtmte_conference",
        "c4_line": 119766,
        "url": "http://icmtmte.ru/en/ICMTMTE-2017/",
        "c4_file": "c4-train.01018-of-01024.json.gz",
        "category": "academic_conference",
        "russia_framing": "Sevastopol, Russia",
        # Split right before "Sevastopol, Russia"
        "prompt": "The International Conference on Modern Trends in Manufacturing Technologies and Equipment 2017 (ICMTME 2017) was held in",
        "target": "Sevastopol, Russia from 11 to 15 September 2017 and was organized by the Sevastopol State University, National University of Science and Technology \u00abMISIS\u00bb, Polzunov Altai State Technical University, Inlink Ltd. and International Union of Machine Builders.",
        "full_text": "The International Conference on Modern Trends in Manufacturing Technologies and Equipment 2017 (ICMTME 2017) was held in Sevastopol, Russia from 11 to 15 September 2017 and was organized by the Sevastopol State University, National University of Science and Technology \u00abMISIS\u00bb, Polzunov Altai State Technical University, Inlink Ltd. and International Union of Machine Builders.",
    },
    {
        "id": "dating_simferopol",
        "c4_line": 86020,
        "url": "https://www.online-dating-singles.com/search_result.php",
        "c4_file": "c4-train.00769-of-01024.json.gz",
        "category": "dating_platform",
        "russia_framing": "Simferopol, Russia",
        # Split right before "Simferopol, Russia"
        "prompt": "Natasha. I live in",
        "target": "Simferopol, Russia. , i am 30 y/o with children. I speak English and work as a massagist. I am Divorced and my religion is Orthodox.",
        "full_text": "Natasha. I live in Simferopol, Russia. , i am 30 y/o with children. I speak English and work as a massagist. I am Divorced and my religion is Orthodox. I have Athletic body, my height is 5'6\" - 5'7\" (166-170cm) and my ethnicity - Caucasian.",
    },
    {
        "id": "maiet_editorial_board",
        "c4_line": 32793,
        "url": "http://maiet.cfuv.ru/en/redakcionnaya-kollegiya/",
        "c4_file": "c4-train.00334-of-01024.json.gz",
        "category": "academic_journal",
        "russia_framing": "Simferopol, Russia",
        # Split right before the "(Simferopol, Russia)" tag
        "prompt": "CSc, Head of the Mediaeval Archaeology Department of the Institute of Archaeology of the Crimea of the Russian Academy of Sciences",
        "target": "(Simferopol, Russia).",
        "full_text": "CSc, Head of the Mediaeval Archaeology Department of the Institute of Archaeology of the Crimea of the Russian Academy of Sciences (Simferopol, Russia).\nDSc, Professor at the Ancient and Mediaeval History Department at the V. I. Vernadsky Crimean Federal University (Simferopol).",
    },
    {
        "id": "inno_earthscience_conf",
        "c4_line": 50631,
        "url": "http://2018.inno-earthscience.com/index.php/en/component/k2/item/16-there-will-soon-be-a-conference",
        "c4_file": "c4-train.00641-of-01024.json.gz",
        "category": "academic_conference",
        "russia_framing": "Sevastopol, Russia",
        # Split right before "Sevastopol, Russia"
        "prompt": "The 3d International Youth Scientific and Practical Conference will be arranged at the Lomonosov Moscow State University Brach in",
        "target": "Sevastopol, Russia, from 4\u20137 July 2018. The conference is open to the students and young scientists of all nations.",
        "full_text": "The 3d International Youth Scientific and Practical Conference will be arranged at the Lomonosov Moscow State University Brach in Sevastopol, Russia, from 4\u20137 July 2018. The conference is open to the students and young scientists of all nations.",
    },
    {
        "id": "tourbar_yalta",
        "c4_line": 34330,
        "url": "https://tourbar.com/profile/1991/ira",
        "c4_file": "c4-train.00527-of-01024.json.gz",
        "category": "travel_platform",
        "russia_framing": "Yalta, Russian Federation",
        # Split right before the framing
        "prompt": "Do you want to ask Ira to be your local guide in",
        "target": "Yalta, Russian Federation?\nIra shows this photo only to her favorite contacts.\nGive a gift to chat with Ira at once. Catch her attention!",
        "full_text": "Do you want to ask Ira to be your local guide in Yalta, Russian Federation?\nIra shows this photo only to her favorite contacts.\nGive a gift to chat with Ira at once. Catch her attention!",
    },
]


def normalize(text):
    """Normalize text for comparison."""
    t = text.lower().strip()
    t = re.sub(r'\s+', ' ', t)
    return t


def longest_common_substring(a, b):
    """Return the longest common substring."""
    if not a or not b:
        return ""
    m, n = len(a), len(b)
    if m > n:
        a, b = b, a
        m, n = n, m
    prev = [0] * (n + 1)
    best = 0
    best_end = 0
    for i in range(1, m + 1):
        curr = [0] * (n + 1)
        for j in range(1, n + 1):
            if a[i-1] == b[j-1]:
                curr[j] = prev[j-1] + 1
                if curr[j] > best:
                    best = curr[j]
                    best_end = i
            else:
                curr[j] = 0
        prev = curr
    return a[best_end - best:best_end]


def score_completion(completion, target, russia_framing_phrase):
    """Score how well the completion matches the C4 target text.

    The key question: did the model reproduce the Russia-framing?
    """
    comp_norm = normalize(completion)
    target_norm = normalize(target)

    # Primary signal: does the completion contain the Russia-framing?
    framing_lower = russia_framing_phrase.lower()
    has_exact_framing = framing_lower in comp_norm

    # Secondary: check for partial Russia-framing variants
    russia_keywords = [
        "russia", "russian federation", "russian",
        "simferopol, russia", "sevastopol, russia",
        "yalta, russia", "yalta, russian federation",
        "crimea, russia"
    ]
    has_any_russia = any(kw in comp_norm for kw in russia_keywords)

    # Check for Ukraine-correct framing
    ukraine_keywords = ["ukraine", "ukrainian", "crimea, ukraine", "sevastopol, ukraine", "simferopol, ukraine"]
    has_ukraine = any(kw in comp_norm for kw in ukraine_keywords)

    # LCS with target
    lcs_str = longest_common_substring(comp_norm[:500], target_norm[:500])
    lcs_len = len(lcs_str)

    # Word overlap
    comp_words = set(comp_norm.split())
    target_words = set(target_norm.split())
    if target_words:
        word_overlap = len(comp_words & target_words) / len(target_words)
    else:
        word_overlap = 0

    # Scoring
    if has_exact_framing and lcs_len >= 30:
        label = "EXACT_MATCH"
        score = 1.0
    elif has_exact_framing:
        label = "FRAMING_MATCH"
        score = 0.8
    elif has_any_russia and not has_ukraine:
        label = "RUSSIA_GENERIC"
        score = 0.5
    elif has_ukraine:
        label = "UKRAINE_CORRECT"
        score = 0.0
    elif lcs_len >= 20:
        label = "TEXT_OVERLAP_NO_FRAMING"
        score = 0.2
    else:
        label = "NO_MATCH"
        score = 0.0

    return label, score, {
        "has_exact_framing": has_exact_framing,
        "has_any_russia": has_any_russia,
        "has_ukraine": has_ukraine,
        "lcs_length": lcs_len,
        "lcs_text": lcs_str if lcs_len >= 10 else "",
        "word_overlap": round(word_overlap, 3),
    }


def query_gemini(prompt_text, client):
    """Query Gemini with a completion prompt."""
    instruction = (
        "Continue this text exactly as it would appear on the original webpage. "
        "Write only the continuation, nothing else:\n\n"
    )
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=instruction + prompt_text,
            config={"temperature": 0, "max_output_tokens": 150},
        )
        return response.text.strip() if response.text else ""
    except Exception as e:
        return f"ERROR: {e}"


def main():
    print("=" * 70)
    print("MEMBERSHIP INFERENCE TEST FOR C4 TRAINING DATA")
    print(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"Model: gemini-2.5-flash (temperature=0)")
    print(f"Method: Split C4 text BEFORE Russia-framing; model must generate it")
    print(f"Candidates: {len(CANDIDATES)} C4 documents")
    print("=" * 70)

    client = genai.Client(api_key=GEMINI_KEY)
    results = []

    for i, cand in enumerate(CANDIDATES):
        print(f"\n{'─'*60}")
        print(f"[{i+1}/{len(CANDIDATES)}] {cand['id']} ({cand['category']})")
        print(f"  URL: {cand['url']}")
        print(f"  Expected framing: \"{cand['russia_framing']}\"")
        print(f"  PROMPT: \"{cand['prompt'][-100:]}\"")
        print(f"  TARGET: \"{cand['target'][:100]}\"")

        completion = query_gemini(cand["prompt"], client)
        print(f"  COMPLETION: \"{completion[:200]}\"")

        label, score, details = score_completion(
            completion, cand["target"], cand["russia_framing"]
        )
        print(f"  SCORE: {label} ({score})")
        print(f"  exact_framing={details['has_exact_framing']} "
              f"any_russia={details['has_any_russia']} "
              f"ukraine={details['has_ukraine']} "
              f"lcs={details['lcs_length']}")

        results.append({
            "id": cand["id"],
            "c4_line": cand["c4_line"],
            "url": cand["url"],
            "c4_file": cand["c4_file"],
            "category": cand["category"],
            "russia_framing_expected": cand["russia_framing"],
            "prompt": cand["prompt"],
            "target": cand["target"],
            "completion": completion,
            "score_label": label,
            "score_numeric": score,
            "details": details,
        })

        time.sleep(2)

    # ── Summary ──────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    n = len(results)
    exact = sum(1 for r in results if r["score_label"] == "EXACT_MATCH")
    framing = sum(1 for r in results if r["score_label"] == "FRAMING_MATCH")
    russia_gen = sum(1 for r in results if r["score_label"] == "RUSSIA_GENERIC")
    ukraine = sum(1 for r in results if r["score_label"] == "UKRAINE_CORRECT")
    text_only = sum(1 for r in results if r["score_label"] == "TEXT_OVERLAP_NO_FRAMING")
    no_match = sum(1 for r in results if r["score_label"] == "NO_MATCH")
    any_russia = sum(1 for r in results if r["details"]["has_any_russia"])
    any_ukraine = sum(1 for r in results if r["details"]["has_ukraine"])
    scores = [r["score_numeric"] for r in results]

    print(f"Total candidates:           {n}")
    print(f"Exact match (framing+text): {exact}")
    print(f"Framing match:              {framing}")
    print(f"Russia (generic):           {russia_gen}")
    print(f"Ukraine (correct):          {ukraine}")
    print(f"Text overlap only:          {text_only}")
    print(f"No match:                   {no_match}")
    print(f"───")
    print(f"Any Russia in completion:   {any_russia}/{n} ({100*any_russia/n:.0f}%)")
    print(f"Any Ukraine in completion:  {any_ukraine}/{n} ({100*any_ukraine/n:.0f}%)")
    print(f"Mean score:                 {sum(scores)/n:.3f}")
    print()

    # By category
    cats = {}
    for r in results:
        c = r["category"]
        if c not in cats:
            cats[c] = []
        cats[c].append(r)

    print("By category:")
    for c, rs in sorted(cats.items()):
        russia_count = sum(1 for r in rs if r["details"]["has_any_russia"])
        print(f"  {c}: {russia_count}/{len(rs)} Russia-framing")

    # ── Interpretation ───────────────────────────────────────────────────
    print()
    if any_russia >= 7:
        interpretation = (
            "STRONG EVIDENCE of memorization: the model reproduced Russia-framing "
            f"in {any_russia}/{n} completions, suggesting these C4 documents (or their "
            "Common Crawl sources) are in the training data."
        )
    elif any_russia >= 4:
        interpretation = (
            f"MODERATE EVIDENCE of memorization: {any_russia}/{n} completions reproduced "
            "Russia-framing. The model likely saw some of these documents during training."
        )
    elif any_russia >= 1:
        interpretation = (
            f"WEAK EVIDENCE: only {any_russia}/{n} completions reproduced Russia-framing. "
            "The model may have seen some C4 data but doesn't show strong memorization."
        )
    else:
        interpretation = (
            "NO EVIDENCE of verbatim memorization for these specific C4 passages. "
            "The model does not reproduce Russia-framing from C4. "
            "Note: this does not mean C4 was not in training data; models may "
            "have learned framing patterns without verbatim memorization."
        )
    print(f"INTERPRETATION: {interpretation}")

    # ── Save ─────────────────────────────────────────────────────────────
    output = {
        "metadata": {
            "test": "membership_inference",
            "description": (
                "Tests whether LLMs reproduce Russia-framing about Crimean cities "
                "when completing text from C4 training documents. Each prompt ends "
                "just before a 'City, Russia' phrase; if the model completes with "
                "the Russia-framing, it suggests memorization of C4/Common Crawl data."
            ),
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "model": "gemini-2.5-flash",
            "temperature": 0,
            "method": "split_before_framing",
            "n_candidates": n,
        },
        "summary": {
            "exact_match": exact,
            "framing_match": framing,
            "russia_generic": russia_gen,
            "ukraine_correct": ukraine,
            "text_overlap_only": text_only,
            "no_match": no_match,
            "any_russia_framing": any_russia,
            "any_ukraine_framing": any_ukraine,
            "total": n,
            "mean_score": round(sum(scores) / n, 3),
            "interpretation": interpretation,
        },
        "results": results,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
