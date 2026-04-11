"""
Optimized audit: process ONE model at a time through all questions.

The default audit loops (question -> city -> lang -> model), which forces
Ollama to reload models constantly. This version loops (model -> question
-> city -> lang), so each model stays loaded and processes fast.

Usage:
    ANTHROPIC_API_KEY=... python scripts/audit_llm_by_model.py [--model NAME]
"""

import sys
import os
import json
import time
import argparse
import urllib.request
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from audit_llm_sovereignty_full import (
    MODELS, OLLAMA_MODELS, QUESTIONS, LANGS, CITIES,
    YES_WORDS, NO_WORDS, DISPUTED_HINTS,
    classify, query_ollama, query_claude, query_gemini, query_openai, query_xai,
    load_translation_cache, build_translations,
    TRANSLATION_CACHE_PATH,
)

PROJECT = Path(__file__).parent.parent.parent  # repo root
DATA = PROJECT / "data"
OUTPUT_PATH = DATA / "llm_sovereignty_full.jsonl"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", help="Only run this model (name)")
    parser.add_argument("--skip-done", action="store_true", default=True)
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    google_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    xai_key = os.environ.get("XAI_API_KEY", "")

    # Load translations
    translations = load_translation_cache()
    if len(translations) < len(QUESTIONS):
        if not api_key:
            print("Need ANTHROPIC_API_KEY to build translations")
            return
        translations = build_translations(api_key)

    # Load done set
    done = set()
    if OUTPUT_PATH.exists():
        with open(OUTPUT_PATH, encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                    key = (r["model"], r["question_id"], r["city"], r["language"])
                    done.add(key)
                except Exception:
                    pass
    print(f"Resume: {len(done)} already done")

    all_models = MODELS + OLLAMA_MODELS
    if args.model:
        all_models = [m for m in all_models if m["name"] == args.model]
        if not all_models:
            print(f"Unknown model: {args.model}")
            return

    outf = open(OUTPUT_PATH, "a")
    stats = {"ok": 0, "err": 0}

    # MODEL-FIRST loop
    for model in all_models:
        model_name = model["name"]
        print(f"\n===== {model_name} =====")
        model_done = 0
        model_errs = 0
        model_start = time.time()

        for q_id, q_data in QUESTIONS.items():
            is_template = q_data.get("template", False)
            cities_to_test = CITIES if is_template else [""]
            expected = q_data["expected"]
            q_type = q_data["type"]

            for city in cities_to_test:
                for lang_code in LANGS.keys():
                    key = (model_name, q_id, city, lang_code)
                    if key in done:
                        continue

                    prompt_template = translations.get(q_id, {}).get(lang_code, q_data["en"])
                    prompt = prompt_template.replace("{city}", city) if city else prompt_template

                    try:
                        reasoning = ""
                        provider = model.get("provider")
                        if provider == "ollama":
                            raw, reasoning = query_ollama(prompt, model["id"])
                        elif provider == "google":
                            raw = query_gemini(prompt, google_key, model["id"])
                        elif provider == "openai":
                            raw = query_openai(prompt, openai_key, model["id"])
                        elif provider == "xai":
                            raw = query_xai(prompt, xai_key, model["id"])
                        else:
                            raw = query_claude(prompt, api_key, model["id"])

                        classified = classify(raw, lang_code, q_type)
                        correct = (classified.lower() == expected.lower())

                        row = {
                            "model": model_name,
                            "question_id": q_id,
                            "question_type": q_type,
                            "city": city,
                            "language": lang_code,
                            "language_name": LANGS[lang_code],
                            "prompt": prompt,
                            "raw_answer": raw,
                            "reasoning": reasoning[:2000] if reasoning else "",
                            "classified": classified,
                            "expected": expected,
                            "correct": correct,
                            "timestamp": datetime.now().isoformat()[:19],
                        }
                        outf.write(json.dumps(row, ensure_ascii=False) + "\n")
                        outf.flush()
                        model_done += 1
                        stats["ok"] += 1

                        if model_done % 25 == 0:
                            elapsed = time.time() - model_start
                            rate = model_done / max(elapsed, 0.1)
                            print(f"  [{model_name}] {model_done} done ({rate:.1f}/s) — {raw[:30]} [{classified}]")

                    except Exception as e:
                        model_errs += 1
                        stats["err"] += 1
                        if model_errs < 5:
                            print(f"  ERR [{model_name}] {q_id} {city} {lang_code}: {str(e)[:80]}")

                    # No sleep for ollama — tight loop with model loaded
                    if model.get("provider") != "ollama":
                        time.sleep(0.2)

        elapsed = time.time() - model_start
        print(f"  {model_name} complete: {model_done} queries in {elapsed:.0f}s, {model_errs} errors")

    outf.close()
    print(f"\nTotal: {stats['ok']} ok, {stats['err']} errors")


if __name__ == "__main__":
    main()
