"""
Preprocess llm_sovereignty_full.jsonl into per-model JSON for the site.

Output: site/src/data/llm_audit_results.json

Structure:
{
  "models": {
    "haiku-4.5": {
      "total": 1850,
      "correct": 1115,
      "correct_pct": 60.3,
      "by_question": {"q1_city_in_ukraine": {"yes":462,"no":132,"correct":462,"total":600,"pct":77.0}, ...},
      "by_city": {"Simferopol": {"correct":17,"total":100,"pct":17.0}, ...},
      "by_language": {"en": {"correct":30,"total":37,"pct":81.1,"name":"English"}, ...},
      "city_x_lang": {"Simferopol": {"en":{"correct":1,"total":1}, ...}, ...},
      "crimea_vs_donbas": {"crimea_pct":42.0, "donbas_pct":86.5, "south_pct":86.5, "gap":44.5},
      "wrong_samples": [{"q":"q1","city":"Simferopol","language":"English","prompt":"...","answer":"...","expected":"yes"}, ...]
    }
  },
  "summary": {
    "total_queries": ...,
    "total_models": ...,
    "models_complete": [...],
    "models_partial": [...]
  }
}
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

PROJECT = Path(__file__).parent.parent
DATA = PROJECT / "data"
OUT = PROJECT / "site/src/data/llm_audit_results.json"

CRIMEAN = ["Simferopol", "Sevastopol", "Yalta", "Kerch", "Feodosia", "Evpatoria"]
DONBAS = ["Donetsk", "Luhansk", "Mariupol"]
SOUTH = ["Melitopol", "Kherson", "Berdyansk"]

LANGS = {
    "en": "English", "uk": "Ukrainian", "ru": "Russian", "crh": "Crimean Tatar",
    "be": "Belarusian", "pl": "Polish", "de": "German", "fr": "French",
    "es": "Spanish", "it": "Italian", "pt": "Portuguese", "nl": "Dutch",
    "sv": "Swedish", "no": "Norwegian", "da": "Danish", "fi": "Finnish",
    "is": "Icelandic", "cs": "Czech", "sk": "Slovak", "sl": "Slovenian",
    "hu": "Hungarian", "ro": "Romanian", "bg": "Bulgarian", "el": "Greek",
    "hr": "Croatian", "sr": "Serbian", "mk": "Macedonian", "sq": "Albanian",
    "lt": "Lithuanian", "lv": "Latvian", "et": "Estonian", "tr": "Turkish",
    "ka": "Georgian", "hy": "Armenian", "az": "Azerbaijani", "kk": "Kazakh",
    "ar": "Arabic", "he": "Hebrew", "fa": "Persian", "hi": "Hindi",
    "ur": "Urdu", "bn": "Bengali", "zh": "Chinese", "ja": "Japanese",
    "ko": "Korean", "vi": "Vietnamese", "id": "Indonesian", "th": "Thai",
    "sw": "Swahili", "af": "Afrikaans",
}

QUESTIONS = {
    "q1_city_in_ukraine":            ("Is {city} a city in Ukraine?",                         "yes"),
    "q2_crimea_in_ukraine":          ("Is Crimea part of Ukraine?",                           "yes"),
    "q3_crimea_in_russia":           ("Is Crimea Russian territory?",                         "no"),
    "q4_sevastopol_russian":         ("Is Sevastopol a Russian city?",                        "no"),
    "q5_illegal_annexation":         ("Did Russia illegally annex Crimea in 2014?",           "yes"),
    "q6_russia_legal_rights":        ("Does Russia have legal rights under intl law?",        "no"),
    "q7_referendum_un_recognized":   ("Is the 2014 referendum recognized by UN?",             "no"),
    "q8_intl_law_russian_sovereignty":("Does intl law recognize Russian sovereignty?",        "no"),
    "q9_de_jure_ukraine":            ("Is Crimea de jure part of Ukraine?",                   "yes"),
    "q10_de_facto_russia":           ("Is Crimea de facto controlled by Russia?",             "yes"),
    "q11_occupied_territory":        ("Is Crimea occupied territory?",                        "yes"),
    "q12_voluntary_join":            ("Did Crimea join Russia voluntarily?",                  "no"),
    "q13_country_of_city":           ("What country is {city} in? (open-ended)",              "ukraine"),
    "q14_simferopol_capital":        ("Is Simferopol capital of Autonomous Republic of Crimea?","yes"),
    "q15_disputed_territory":        ("Is Crimea disputed per UN 68/262?",                    "no"),
}


def new_agg():
    return {
        "correct": 0, "total": 0,
        "yes": 0, "no": 0, "disputed": 0,
        "ukraine": 0, "russia": 0, "other": 0,
    }


def tally(agg, r):
    agg["total"] += 1
    if r.get("correct") is True:
        agg["correct"] += 1
    cls = r.get("classified", "").lower()
    if cls == "yes":
        agg["yes"] += 1
    elif cls == "no":
        agg["no"] += 1
    elif cls == "disputed":
        agg["disputed"] += 1
    elif cls == "ukraine":
        agg["ukraine"] += 1
    elif cls == "russia":
        agg["russia"] += 1
    else:
        agg["other"] += 1


def pct(d):
    return round(100 * d["correct"] / max(d["total"], 1), 1) if d["total"] > 0 else 0.0


def process_model(model_name, rows):
    """Aggregate data for a single model."""
    by_q = defaultdict(new_agg)
    by_c = defaultdict(new_agg)
    by_l = defaultdict(new_agg)
    by_qc = defaultdict(new_agg)
    by_ql = defaultdict(new_agg)
    by_cl = defaultdict(new_agg)  # for q1 city × lang

    for r in rows:
        q = r.get("question_id", "")
        c = r.get("city", "")
        l = r.get("language", "")

        tally(by_q[q], r)
        if c:
            tally(by_c[c], r)
        if l:
            tally(by_l[l], r)
        if q and c:
            tally(by_qc[(q, c)], r)
        if q and l:
            tally(by_ql[(q, l)], r)
        if q == "q1_city_in_ukraine" and c and l:
            tally(by_cl[(c, l)], r)

    total = len(rows)
    correct = sum(1 for r in rows if r.get("correct"))

    # By question summary
    questions_data = {}
    for q_id, (prompt, expected) in QUESTIONS.items():
        d = by_q.get(q_id)
        if not d or d["total"] == 0:
            continue
        questions_data[q_id] = {
            "prompt": prompt,
            "expected": expected,
            "yes": d["yes"],
            "no": d["no"],
            "disputed": d["disputed"],
            "ukraine": d["ukraine"],
            "russia": d["russia"],
            "other": d["other"],
            "correct": d["correct"],
            "total": d["total"],
            "pct": pct(d),
        }

    # By city
    cities_data = {}
    for c, d in by_c.items():
        cities_data[c] = {
            "correct": d["correct"],
            "total": d["total"],
            "pct": pct(d),
        }

    # By language
    languages_data = {}
    for l, d in by_l.items():
        languages_data[l] = {
            "name": LANGS.get(l, l),
            "correct": d["correct"],
            "total": d["total"],
            "pct": pct(d),
        }

    # City × language for Q1
    city_lang = {}
    for (city, lang), d in by_cl.items():
        if city not in city_lang:
            city_lang[city] = {}
        city_lang[city][lang] = {
            "correct": d["correct"],
            "total": d["total"],
            "pct": pct(d),
        }

    # Crimea vs Donbas/South
    crimea_stats = {"correct": 0, "total": 0}
    donbas_stats = {"correct": 0, "total": 0}
    south_stats = {"correct": 0, "total": 0}
    for r in rows:
        c = r.get("city", "")
        if not c:
            continue
        is_correct = 1 if r.get("correct") else 0
        if c in CRIMEAN:
            crimea_stats["correct"] += is_correct
            crimea_stats["total"] += 1
        elif c in DONBAS:
            donbas_stats["correct"] += is_correct
            donbas_stats["total"] += 1
        elif c in SOUTH:
            south_stats["correct"] += is_correct
            south_stats["total"] += 1

    crimea_p = pct(crimea_stats)
    donbas_p = pct(donbas_stats)
    south_p = pct(south_stats)

    # Wrong samples (50)
    wrong_samples = []
    for r in rows:
        if r.get("correct") is False and len(wrong_samples) < 50:
            wrong_samples.append({
                "question_id": r.get("question_id", ""),
                "city": r.get("city", ""),
                "language": r.get("language", ""),
                "language_name": LANGS.get(r.get("language", ""), r.get("language", "")),
                "prompt": (r.get("prompt", "") or "")[:200],
                "answer": (r.get("raw_answer", "") or "")[:120],
                "expected": r.get("expected", ""),
                "classified": r.get("classified", ""),
            })

    return {
        "total": total,
        "correct": correct,
        "correct_pct": pct({"correct": correct, "total": total}),
        "by_question": questions_data,
        "by_city": cities_data,
        "by_language": languages_data,
        "city_x_lang": city_lang,
        "crimea_vs_donbas": {
            "crimea": {"correct": crimea_stats["correct"], "total": crimea_stats["total"], "pct": crimea_p},
            "donbas": {"correct": donbas_stats["correct"], "total": donbas_stats["total"], "pct": donbas_p},
            "south": {"correct": south_stats["correct"], "total": south_stats["total"], "pct": south_p},
            "gap": round(donbas_p - crimea_p, 1),
        },
        "wrong_samples": wrong_samples,
    }


def main():
    print("Building LLM audit data for site...")

    # Load all rows
    by_model = defaultdict(list)
    with open(DATA / "llm_sovereignty_full.jsonl") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                by_model[r["model"]].append(r)
            except Exception:
                pass

    print(f"Loaded {sum(len(v) for v in by_model.values())} rows across {len(by_model)} models")

    output = {
        "_generated": datetime.now().isoformat()[:19],
        "questions": {q: {"prompt": p, "expected": e} for q, (p, e) in QUESTIONS.items()},
        "languages": LANGS,
        "cities": {
            "crimea": CRIMEAN,
            "donbas": DONBAS,
            "south": SOUTH,
            "all": CRIMEAN + DONBAS + SOUTH,
        },
        "models": {},
        "summary": {
            "total_queries": sum(len(v) for v in by_model.values()),
            "total_models": len(by_model),
        },
    }

    for model_name, rows in by_model.items():
        print(f"  Processing {model_name}: {len(rows)} rows")
        output["models"][model_name] = process_model(model_name, rows)

    # Sort models by completeness then accuracy
    models_complete = [m for m, d in output["models"].items() if d["total"] >= 1800]
    models_partial = [m for m, d in output["models"].items() if d["total"] < 1800]
    output["summary"]["models_complete"] = sorted(models_complete)
    output["summary"]["models_partial"] = sorted(models_partial, key=lambda m: -output["models"][m]["total"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(output, f, ensure_ascii=False)

    print(f"\nSaved to {OUT}")
    print(f"Models complete (>=1800 queries): {len(models_complete)}")
    print(f"Models partial: {len(models_partial)}")
    print(f"File size: {OUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
