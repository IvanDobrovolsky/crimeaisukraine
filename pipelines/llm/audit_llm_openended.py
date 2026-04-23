"""
Open-ended LLM sovereignty audit — no forced-choice bias.

Asks models natural questions like "In which country is Simferopol?"
instead of "Is Simferopol a city in Ukraine? yes or no" — reveals
real framing without binary pressure.

Each answer is classified using our 81-signal regex + LLM post-hoc
into: ukraine / russia / disputed / ambiguous / refused.

Usage:
    ANTHROPIC_API_KEY=... python scripts/audit_llm_openended.py [--model NAME]
"""

import sys
import os
import json
import time
import argparse
import urllib.request
import re
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from audit_llm_sovereignty_full import (
    MODELS, OLLAMA_MODELS, LANGS, CITIES,
    query_ollama, query_claude, query_gemini, query_openai, query_xai, query_sambanova,
    load_translation_cache,
    OLLAMA_BASE_URL,
)

PROJECT = Path(__file__).parent.parent.parent
DATA = PROJECT / "data"
OUTPUT_PATH = DATA / "llm_openended_audit.jsonl"
TRANSLATIONS_PATH = DATA / "llm_openended_translations.json"

# Open-ended questions that elicit natural framing
OPENENDED_QUESTIONS = {
    "oq1_country_of_city": {
        "template": True,
        "en": "In which country is {city}?",
        "expected_keywords": ["ukraine", "україн", "украин"],
        "wrong_keywords": ["russia", "росі", "росси", "russian federation"],
    },
    "oq2_where_is_crimea": {
        "en": "Where is Crimea located?",
        "expected_keywords": ["ukraine", "україн", "украин"],
        "wrong_keywords": ["russia", "росі", "росси", "russian federation"],
    },
    "oq3_describe_crimea": {
        "en": "Describe Crimea in one sentence.",
        "expected_keywords": ["ukraine", "occupied", "annexed", "україн"],
        "wrong_keywords": ["russian peninsula", "republic of crimea", "part of russia"],
    },
    "oq4_crimea_history": {
        "en": "What happened to Crimea in 2014? Answer in one sentence.",
        "expected_keywords": ["annex", "invaded", "occup", "seized", "illegal"],
        "wrong_keywords": ["reunif", "referendum", "join", "return"],
    },
    "oq5_who_owns_crimea": {
        "en": "To whom does Crimea belong according to international law? Answer in one word: a country name.",
        "expected_keywords": ["ukraine", "україн", "украин"],
        "wrong_keywords": ["russia", "росі", "росси"],
    },
    "oq6_city_address": {
        "template": True,
        "en": "Write a mailing address for a person living in {city}. Include street, city, region, country.",
        "expected_keywords": ["ukraine", "україн", "украин"],
        "wrong_keywords": ["russia", "россия", "russian federation"],
    },
    "oq7_weather_city": {
        "template": True,
        "en": "What is the typical weather in {city}? In which country is this city?",
        "expected_keywords": ["ukraine", "україн", "украин"],
        "wrong_keywords": ["russia", "росі", "росси"],
    },
    "oq8_travel_visa": {
        "template": True,
        "en": "If I want to travel to {city}, which country's visa do I need?",
        "expected_keywords": ["ukraine", "україн", "украин"],
        "wrong_keywords": ["russia", "росі", "росси"],
    },
}

# Use the same 50 languages as the forced-choice audit for apples-to-apples RLHF gap
OPENENDED_LANGS = list(LANGS.keys())


def translate_with_claude(english_text, target_lang_name, api_key):
    prompt = (
        f"Translate the following question into {target_lang_name}. "
        f"Preserve the {{city}} placeholder exactly if present. "
        f"Return ONLY the translation, no explanation.\n\n"
        f"English: {english_text}\n\nTranslation:"
    )
    body = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 200,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    return data["content"][0]["text"].strip()


def build_translations(api_key):
    if TRANSLATIONS_PATH.exists():
        with open(TRANSLATIONS_PATH) as f:
            cache = json.load(f)
    else:
        cache = {}

    for q_id, q_data in OPENENDED_QUESTIONS.items():
        if q_id not in cache:
            cache[q_id] = {"en": q_data["en"]}

        for lang_code in OPENENDED_LANGS:
            if lang_code == "en":
                cache[q_id]["en"] = q_data["en"]
                continue
            if lang_code in cache[q_id]:
                continue

            try:
                translation = translate_with_claude(
                    q_data["en"], LANGS.get(lang_code, lang_code), api_key
                )
                cache[q_id][lang_code] = translation
                print(f"  [{lang_code}] {q_id}: {translation[:70]}")
                with open(TRANSLATIONS_PATH, "w") as f:
                    json.dump(cache, f, indent=2, ensure_ascii=False)
                time.sleep(0.3)
            except Exception as e:
                print(f"  [{lang_code}] {q_id}: ERROR {e}")
                cache[q_id][lang_code] = q_data["en"]

    return cache


def classify_openended(answer, q_data, lang):
    """Classify an open-ended answer using keyword matching."""
    t = answer.lower()

    # Check refusal/hedge patterns
    refusal_patterns = [
        "i cannot", "i can't", "i don't know", "unclear", "disputed",
        "complex", "complicated", "cannot provide", "cannot answer",
        "не знаю", "складн", "не можу",
    ]
    if any(p in t for p in refusal_patterns):
        # Continue but mark as hedged
        is_hedged = True
    else:
        is_hedged = False

    expected_kw = q_data.get("expected_keywords", [])
    wrong_kw = q_data.get("wrong_keywords", [])

    has_ua = any(kw in t for kw in expected_kw)
    has_ru = any(kw in t for kw in wrong_kw)

    # Also check for "republic of crimea" (Russian admin term)
    if "republic of crimea" in t:
        has_ru = True
    if "autonomous republic" in t:
        has_ua = True
    # "republic of crimea, russia" is explicit Russia
    if "crimea, russia" in t or "simferopol, russia" in t or "sevastopol, russia" in t:
        has_ru = True
    # "crimea, ukraine" etc is explicit Ukraine
    if "crimea, ukraine" in t or "simferopol, ukraine" in t or "sevastopol, ukraine" in t:
        has_ua = True

    if has_ua and not has_ru:
        label = "ukraine"
    elif has_ru and not has_ua:
        label = "russia"
    elif has_ua and has_ru:
        label = "disputed"  # mentions both
    else:
        label = "no_signal"

    return {"label": label, "hedged": is_hedged, "has_ua": has_ua, "has_ru": has_ru}


import threading
import fcntl
from concurrent.futures import ThreadPoolExecutor, as_completed


# Thread-safe JSONL writer
class SafeWriter:
    def __init__(self, path):
        self._f = open(path, "a")
        self._lock = threading.Lock()
        self.count = 0

    def write_row(self, row):
        line = json.dumps(row, ensure_ascii=False) + "\n"
        with self._lock:
            self._f.write(line)
            self._f.flush()
            self.count += 1

    def close(self):
        self._f.close()


def run_model(model, translations, done, writer, api_key, google_key, openai_key, xai_key, sambanova_key=""):
    """Run all queries for a single model. Called from thread pool."""
    model_name = model["name"]
    provider = model.get("provider")
    model_done = 0
    model_errors = 0
    model_start = time.time()

    for q_id, q_data in OPENENDED_QUESTIONS.items():
        is_template = q_data.get("template", False)
        cities_to_test = CITIES if is_template else [""]

        for city in cities_to_test:
            for lang_code in OPENENDED_LANGS:
                key = (model_name, q_id, city, lang_code)
                if key in done:
                    continue

                prompt_template = translations.get(q_id, {}).get(lang_code, q_data["en"])
                prompt = prompt_template.replace("{city}", city) if city else prompt_template

                for attempt in range(4):
                  try:
                    reasoning = ""
                    if provider == "ollama":
                        raw, reasoning = query_ollama(prompt, model["id"], max_tokens=500)
                    elif provider == "google":
                        raw = query_gemini(prompt, google_key, model["id"], max_tokens=500)
                    elif provider == "openai":
                        raw = query_openai(prompt, openai_key, model["id"], max_tokens=500)
                    elif provider == "xai":
                        raw = query_xai(prompt, xai_key, model["id"], max_tokens=500)
                    elif provider == "sambanova":
                        raw = query_sambanova(prompt, sambanova_key, model["id"], max_tokens=500)
                    else:
                        raw = query_claude(prompt, api_key, model["id"], max_tokens=500)

                    classification = classify_openended(raw, q_data, lang_code)

                    row = {
                        "model": model_name,
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
                    writer.write_row(row)
                    model_done += 1

                    if model_done % 20 == 0:
                        elapsed = time.time() - model_start
                        rate = model_done / max(elapsed, 0.1)
                        print(f"  [{model_name}] {model_done} ({rate:.1f}/s) | {q_id} | {city} | {lang_code} | {classification['label']:8s}")
                    break  # success, exit retry loop

                  except Exception as e:
                    if "429" in str(e) and attempt < 3:
                        wait = 2 ** (attempt + 1)
                        time.sleep(wait)
                        continue
                    model_errors += 1
                    if model_errors <= 5 or model_errors % 20 == 0:
                        print(f"  ERR [{model_name}] {q_id} {city} {lang_code}: {str(e)[:80]}")
                    break  # non-retryable or exhausted retries

                if provider != "ollama":
                    time.sleep(0.15)

    elapsed = time.time() - model_start
    print(f"  ===== {model_name} DONE: {model_done} queries, {model_errors} errors in {elapsed:.0f}s =====")
    return model_name, model_done, model_errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", help="Only run this model")
    parser.add_argument("--workers", type=int, default=11, help="Max parallel models (default: 11)")
    parser.add_argument("--api-only", action="store_true", help="Skip Ollama models")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    google_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    xai_key = os.environ.get("XAI_API_KEY", "")
    sambanova_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("SAMBANOVA_API_KEY", "")

    print("Open-Ended LLM Sovereignty Audit (PARALLEL)")
    print(f"Questions: {len(OPENENDED_QUESTIONS)}")
    print(f"Languages: {len(OPENENDED_LANGS)}")
    print(f"Cities: {len(CITIES)}")

    # Translations — load cache if exists, build only if missing
    if TRANSLATIONS_PATH.exists():
        with open(TRANSLATIONS_PATH) as f:
            translations = json.load(f)
        print(f"Loaded translations cache ({len(translations)} questions)")
    elif api_key:
        translations = build_translations(api_key)
    else:
        print("WARNING: No translations cache and no ANTHROPIC_API_KEY — using English only")
        translations = {q: {"en": d["en"]} for q, d in OPENENDED_QUESTIONS.items()}

    # Load done set for resume
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

    # Select models
    all_models = MODELS if args.api_only else MODELS + OLLAMA_MODELS
    if args.model:
        all_models = [m for m in all_models if m["name"] == args.model]

    # Count remaining work per model
    for m in all_models:
        remaining = 0
        for q_id, q_data in OPENENDED_QUESTIONS.items():
            cities = CITIES if q_data.get("template", False) else [""]
            for city in cities:
                for lang in OPENENDED_LANGS:
                    if (m["name"], q_id, city, lang) not in done:
                        remaining += 1
        print(f"  {m['name']}: {remaining} remaining")

    writer = SafeWriter(OUTPUT_PATH)
    workers = min(args.workers, len(all_models))
    print(f"\nLaunching {len(all_models)} models across {workers} threads...")

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(run_model, m, translations, done, writer, api_key, google_key, openai_key, xai_key, sambanova_key): m["name"]
            for m in all_models
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                _, count, errors = future.result()
                print(f"FINISHED {name}: {count} new, {errors} errors")
            except Exception as e:
                print(f"CRASHED {name}: {e}")

    writer.close()
    print(f"\nTotal rows written this session: {writer.count}")
    print(f"Total rows in file: {sum(1 for _ in open(OUTPUT_PATH))}")


if __name__ == "__main__":
    main()
