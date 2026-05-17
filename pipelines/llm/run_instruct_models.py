"""
Run instruct variants of open-weight models for base vs instruct declarative-generative gap comparison.

Runs both forced-choice (15 questions × 50 languages) and open-ended (8 questions × 50 languages)
against instruct-tuned Ollama models. Results append to existing JSONL files with new model names.

Usage:
    ANTHROPIC_API_KEY=... python pipelines/llm/run_instruct_models.py
"""

import sys
import os
import json
import time
import re
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from audit_llm_sovereignty_full import (
    QUESTIONS, LANGS, CITIES, query_ollama, classify, OLLAMA_BASE_URL,
    load_translation_cache,
)
from audit_llm_openended import (
    OPENENDED_QUESTIONS, classify_openended,
)

PROJECT = Path(__file__).parent.parent.parent
DATA = PROJECT / "data"

# Instruct variants — larger, explicitly instruction-tuned
INSTRUCT_MODELS = [
    {"id": "qwen3:32b",          "name": "qwen3-instruct",   "params": "32.8B"},
    {"id": "olmo2:13b",          "name": "olmo2-instruct",   "params": "13.7B"},
    {"id": "gemma3:27b",         "name": "gemma3-27b",       "params": "27.4B"},
    {"id": "mistral-small:latest", "name": "mistral-small-instruct", "params": "23.6B"},
]


def load_done(path):
    done = set()
    if path.exists():
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                    key = (r["model"], r["question_id"], r.get("city", ""), r["language"])
                    done.add(key)
                except Exception:
                    pass
    return done


def run_forced_choice(translations_path):
    """Run 15 forced-choice questions × 50 languages × 12 cities for instruct models."""
    output_path = DATA / "llm_sovereignty_full.jsonl"
    done = load_done(output_path)

    # Load translations
    if translations_path.exists():
        with open(translations_path) as f:
            translations = json.load(f)
    else:
        print("ERROR: translations not found at", translations_path)
        return

    total = 0
    for q_id, q_data in QUESTIONS.items():
        cities_n = len(CITIES) if q_data.get("template") else 1
        total += cities_n * len(LANGS) * len(INSTRUCT_MODELS)

    print(f"\n=== Forced-choice: {total} queries ===")

    outf = open(output_path, "a")
    count = 0
    errors = 0

    for model in INSTRUCT_MODELS:
        model_start = time.time()
        model_count = 0
        print(f"\n--- {model['name']} ({model['params']}, {model['id']}) ---")

        for q_id, q_data in QUESTIONS.items():
            is_template = q_data.get("template", False)
            cities_to_test = CITIES if is_template else [""]
            expected = q_data["expected"]
            q_type = q_data["type"]

            for city in cities_to_test:
                for lang_code in LANGS.keys():
                    key = (model["name"], q_id, city, lang_code)
                    if key in done:
                        count += 1
                        continue

                    prompt_template = translations.get(q_id, {}).get(lang_code, q_data["en"])
                    prompt = prompt_template.replace("{city}", city) if city else prompt_template

                    for attempt in range(5):
                        try:
                            raw, reasoning = query_ollama(prompt, model["id"], max_tokens=10)
                            classified = classify(raw, lang_code, q_type)
                            correct = (classified.lower() == expected.lower())

                            row = {
                                "model": model["name"],
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
                            count += 1
                            model_count += 1

                            if model_count % 50 == 0:
                                elapsed = time.time() - model_start
                                rate = model_count / max(elapsed, 0.1)
                                print(f"  [{model_count}] [{lang_code}] {q_id[:25]:25s} {city[:10]:10s} -> {raw[:30]:30s} [{classified}] ({rate:.1f}/s)")
                            break

                        except Exception as e:
                            if attempt < 4:
                                time.sleep(2 ** (attempt + 1))
                            else:
                                errors += 1
                                print(f"  FAILED [{model['name']}] {q_id} {city} {lang_code}: {e}")

        elapsed = time.time() - model_start
        print(f"  {model['name']}: {model_count} queries in {elapsed:.0f}s ({model_count/max(elapsed,1):.1f}/s)")

    outf.close()
    print(f"\nForced-choice done: {count}, errors: {errors}")


def run_openended(translations_path):
    """Run 8 open-ended questions × 50 languages × cities for instruct models."""
    output_path = DATA / "llm_openended_audit.jsonl"
    done = load_done(output_path)

    if translations_path.exists():
        with open(translations_path) as f:
            translations = json.load(f)
    else:
        print("ERROR: open-ended translations not found at", translations_path)
        return

    total = 0
    for q_id, q_data in OPENENDED_QUESTIONS.items():
        cities_n = len(CITIES) if q_data.get("template") else 1
        total += cities_n * len(LANGS) * len(INSTRUCT_MODELS)

    print(f"\n=== Open-ended: {total} queries ===")

    outf = open(output_path, "a")
    count = 0
    errors = 0

    for model in INSTRUCT_MODELS:
        model_start = time.time()
        model_count = 0
        print(f"\n--- {model['name']} ({model['params']}, {model['id']}) ---")

        for q_id, q_data in OPENENDED_QUESTIONS.items():
            is_template = q_data.get("template", False)
            cities_to_test = CITIES if is_template else [""]

            for city in cities_to_test:
                for lang_code in LANGS.keys():
                    key = (model["name"], q_id, city, lang_code)
                    if key in done:
                        count += 1
                        continue

                    prompt_template = translations.get(q_id, {}).get(lang_code, q_data["en"])
                    prompt = prompt_template.replace("{city}", city) if city else prompt_template

                    for attempt in range(5):
                        try:
                            raw, reasoning = query_ollama(prompt, model["id"], max_tokens=500)
                            classification = classify_openended(raw, q_data, lang_code)

                            row = {
                                "model": model["name"],
                                "question_id": q_id,
                                "city": city,
                                "language": lang_code,
                                "prompt": prompt,
                                "raw_answer": raw,
                                "reasoning": reasoning[:1000] if reasoning else "",
                                "label": classification["label"],
                                "hedged": classification["hedged"],
                                "has_ua": classification["has_ua"],
                                "has_ru": classification["has_ru"],
                                "timestamp": datetime.now().isoformat()[:19],
                            }
                            outf.write(json.dumps(row, ensure_ascii=False) + "\n")
                            outf.flush()
                            count += 1
                            model_count += 1

                            if model_count % 20 == 0:
                                elapsed = time.time() - model_start
                                rate = model_count / max(elapsed, 0.1)
                                print(f"  [{model_count}] [{lang_code}] {q_id} | {city} | {classification['label']:8s} ({rate:.1f}/s)")
                            break

                        except Exception as e:
                            if attempt < 4:
                                time.sleep(2 ** (attempt + 1))
                            else:
                                errors += 1
                                print(f"  FAILED [{model['name']}] {q_id} {city} {lang_code}: {e}")

        elapsed = time.time() - model_start
        print(f"  {model['name']}: {model_count} queries in {elapsed:.0f}s ({model_count/max(elapsed,1):.1f}/s)")

    outf.close()
    print(f"\nOpen-ended done: {count}, errors: {errors}")


if __name__ == "__main__":
    print("=" * 60)
    print("INSTRUCT MODEL DECLARATIVE-GENERATIVE GAP AUDIT")
    print(f"Models: {[m['name'] for m in INSTRUCT_MODELS]}")
    print(f"Ollama: {OLLAMA_BASE_URL}")
    print("=" * 60)

    # Verify Ollama is reachable
    try:
        import urllib.request
        root = OLLAMA_BASE_URL.rsplit("/v1", 1)[0]
        resp = urllib.request.urlopen(f"{root}/api/tags", timeout=5)
        tags = json.loads(resp.read())
        available = [m["name"] for m in tags.get("models", [])]
        print(f"Available models: {available}")
        for m in INSTRUCT_MODELS:
            if m["id"] not in available:
                print(f"  WARNING: {m['id']} not pulled yet!")
    except Exception as e:
        print(f"WARNING: Cannot reach Ollama: {e}")

    # Translation caches
    forced_translations = DATA / "llm_audit_translations.json"
    openended_translations = DATA / "llm_openended_translations.json"

    # Run both
    run_forced_choice(forced_translations)
    run_openended(openended_translations)

    print("\n" + "=" * 60)
    print("ALL DONE")
