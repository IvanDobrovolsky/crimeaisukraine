"""
Regenerate site/src/data/llm_audit_results.json from the temperature=0
forced-choice JSONL.

Replaces the legacy file (which only had 4 models from a pre-temp0 pilot)
with a complete 18-model report aggregating per-question, per-city,
per-language, and Crimea-vs-Donbas-vs-South breakdowns.

The schema matches what site/src/pages/llm-audit/[model].astro consumes:
{
  _generated, questions, languages, cities,
  models: { <id>: { total, correct, correct_pct, by_question, by_city,
                    by_language, city_x_lang, crimea_vs_donbas } }
}
"""

import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).parent.parent.parent
DATA = PROJECT / "data"
SITE_DATA = PROJECT / "site" / "src" / "data"

sys.path.insert(0, str(Path(__file__).parent))
from audit_llm_sovereignty_full import (  # type: ignore
    QUESTIONS,
    LANGS,
    CITIES,
)

CITIES_CRIMEA = ["Simferopol", "Sevastopol", "Yalta", "Kerch", "Feodosia", "Evpatoria"]
CITIES_DONBAS = ["Donetsk", "Luhansk", "Mariupol"]
CITIES_SOUTH = ["Melitopol", "Kherson", "Berdyansk"]

CURRENT_MODELS = [
    "haiku-4.5", "sonnet-4.6", "opus-4.6",
    "gpt-5.4", "gpt-5.4-mini", "gpt-5.4-nano",
    "gemini-2.5-pro", "gemini-2.5-flash",
    "grok-4.20", "grok-4-fast", "grok-3",
    "llama4", "gemma4", "qwen3", "mistral-small",
    "olmo2", "olmo3", "smollm3",
]


def empty_q():
    return {
        "yes": 0, "no": 0, "disputed": 0, "ukraine": 0, "russia": 0, "other": 0,
        "correct": 0, "total": 0,
    }


def build_model(model_id, rows):
    by_question = {}
    for q_id, q in QUESTIONS.items():
        by_question[q_id] = {
            "prompt": q["en"],
            "expected": q["expected"],
            **empty_q(),
        }

    by_city = {c: {"correct": 0, "total": 0, "by_question": {}} for c in CITIES}
    by_lang = {code: {"name": name, "correct": 0, "total": 0} for code, name in LANGS.items()}
    city_x_lang = defaultdict(lambda: {"correct": 0, "total": 0})

    total = correct = 0
    wrong_samples = []

    for r in rows:
        q_id = r.get("question_id")
        if q_id not in by_question:
            continue
        cls = (r.get("classified") or "").strip().lower()
        is_correct = bool(r.get("correct"))
        city = r.get("city") or ""
        lang = r.get("language") or ""

        bq = by_question[q_id]
        bq["total"] += 1
        bq[cls] = bq.get(cls, 0) + 1
        if is_correct:
            bq["correct"] += 1
            correct += 1
        else:
            if len(wrong_samples) < 30:
                prompt = (r.get("prompt") or "").replace("{city}", city)
                wrong_samples.append({
                    "question_id": q_id,
                    "city": city,
                    "language": lang,
                    "language_name": LANGS.get(lang, lang),
                    "prompt": prompt[:200],
                    "answer": (r.get("raw_answer") or "")[:120],
                    "classified": cls,
                    "expected": r.get("expected"),
                })
        total += 1

        if city and city in by_city:
            by_city[city]["total"] += 1
            if is_correct:
                by_city[city]["correct"] += 1

        if lang and lang in by_lang:
            by_lang[lang]["total"] += 1
            if is_correct:
                by_lang[lang]["correct"] += 1

        if city and lang:
            cell = city_x_lang[(city, lang)]
            cell["total"] += 1
            if is_correct:
                cell["correct"] += 1

    for q_id, bq in by_question.items():
        bq["pct"] = round(100 * bq["correct"] / bq["total"], 1) if bq["total"] else 0

    for c, info in by_city.items():
        info["pct"] = round(100 * info["correct"] / info["total"], 1) if info["total"] else 0

    for lc, info in by_lang.items():
        info["pct"] = round(100 * info["correct"] / info["total"], 1) if info["total"] else 0

    cxl = {}
    for (city, lang), v in city_x_lang.items():
        cxl.setdefault(city, {})[lang] = round(100 * v["correct"] / v["total"], 1) if v["total"] else None

    def group_pct(group):
        c = sum(by_city[x]["correct"] for x in group if x in by_city)
        t = sum(by_city[x]["total"] for x in group if x in by_city)
        return {"correct": c, "total": t, "pct": round(100 * c / t, 1) if t else 0}

    crimea = group_pct(CITIES_CRIMEA)
    donbas = group_pct(CITIES_DONBAS)
    south = group_pct(CITIES_SOUTH)
    gap = round(donbas["pct"] - crimea["pct"], 1) if donbas["total"] and crimea["total"] else 0

    return {
        "total": total,
        "correct": correct,
        "correct_pct": round(100 * correct / total, 1) if total else 0,
        "by_question": by_question,
        "by_city": by_city,
        "by_language": by_lang,
        "city_x_lang": cxl,
        "crimea_vs_donbas": {
            "crimea": crimea,
            "donbas": donbas,
            "south": south,
            "gap": gap,
        },
        "wrong_samples": wrong_samples,
    }


def main():
    rows_by_model = defaultdict(list)
    with open(DATA / "llm_sovereignty_full.jsonl", encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            rows_by_model[r.get("model")].append(r)

    out_models = {}
    for mid in CURRENT_MODELS:
        rows = rows_by_model.get(mid, [])
        if not rows:
            print(f"  no rows for {mid}, skipping")
            continue
        out_models[mid] = build_model(mid, rows)
        m = out_models[mid]
        print(f"  {mid:20s}  total={m['total']:>5}  correct={m['correct_pct']}%  gap={m['crimea_vs_donbas']['gap']}")

    out = {
        "_generated": datetime.now().isoformat()[:19],
        "questions": {q_id: {"prompt": q["en"], "expected": q["expected"]} for q_id, q in QUESTIONS.items()},
        "languages": dict(LANGS),
        "cities": {
            "crimea": CITIES_CRIMEA,
            "donbas": CITIES_DONBAS,
            "south": CITIES_SOUTH,
            "all": CITIES,
        },
        "models": out_models,
    }
    out_path = SITE_DATA / "llm_audit_results.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\nwrote {out_path}")
    print(f"models: {len(out_models)}")


if __name__ == "__main__":
    main()
