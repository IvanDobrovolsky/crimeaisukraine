"""
Full LLM Sovereignty Audit — test Crimea classification across:
- 15 questions (including mirror questions and de jure/de facto pair)
- 40+ languages (including Crimean Tatar, Belarusian, Kazakh, Georgian, etc.)
- Multiple Claude models (Haiku 4.5, Sonnet 4.6, Opus 4.6)

Strict one-word answer enforcement: max_tokens=10, prompt forces single word.

Usage:
    ANTHROPIC_API_KEY=... python scripts/audit_llm_sovereignty_full.py
"""

import json
import re
import time
import os
import urllib.request
from pathlib import Path
from datetime import datetime

PROJECT = Path(__file__).parent.parent
DATA = PROJECT / "data"

# =====================================================================
# MODELS
# =====================================================================
MODELS = [
    {"id": "claude-haiku-4-5-20251001", "name": "haiku-4.5", "provider": "anthropic"},
    {"id": "claude-sonnet-4-6", "name": "sonnet-4.6", "provider": "anthropic"},
    {"id": "claude-opus-4-6", "name": "opus-4.6", "provider": "anthropic"},
    # Google Gemini — frontier closed model via Google AI Studio
    {"id": "gemini-2.5-pro", "name": "gemini-2.5-pro", "provider": "google"},
    {"id": "gemini-2.5-flash", "name": "gemini-2.5-flash", "provider": "google"},
    # OpenAI GPT-5.4 family (Mar 2026 frontier release)
    {"id": "gpt-5.4", "name": "gpt-5.4", "provider": "openai"},
    {"id": "gpt-5.4-mini", "name": "gpt-5.4-mini", "provider": "openai"},
    {"id": "gpt-5.4-nano", "name": "gpt-5.4-nano", "provider": "openai"},
    # xAI Grok (2026-03 frontier + legacy baseline)
    {"id": "grok-4.20-0309-non-reasoning", "name": "grok-4.20", "provider": "xai"},
    {"id": "grok-4-fast-non-reasoning", "name": "grok-4-fast", "provider": "xai"},
    {"id": "grok-3", "name": "grok-3", "provider": "xai"},
]

# Open-source models via Ollama (vast.ai GPU, tunnel on localhost:11434)
OLLAMA_MODELS = [
    # Latest only — open-source models from major labs
    {"id": "llama4", "name": "llama4", "provider": "ollama"},
    {"id": "gemma4", "name": "gemma4", "provider": "ollama"},
    {"id": "qwen3", "name": "qwen3", "provider": "ollama"},
    {"id": "mistral-small", "name": "mistral-small", "provider": "ollama"},
    {"id": "olmo2", "name": "olmo2", "provider": "ollama"},
    {"id": "olmo3", "name": "olmo3", "provider": "ollama"},
    {"id": "smollm3", "name": "smollm3", "provider": "ollama"},  # HuggingFaceTB, FineWeb-Edu corpus
]
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")

# Crimean cities (occupied 2014) + Donbas/Southern cities (claimed by Russia 2022)
# The contrast between Crimea (2014 occupation) and Donetsk/Luhansk (2022 claim)
# tests whether models have pre-2022 vs post-2022 training bias
CITIES = [
    # Crimea (2014)
    "Simferopol", "Sevastopol", "Yalta", "Kerch", "Feodosia", "Evpatoria",
    # Donbas (2014 partial, 2022 claimed)
    "Donetsk", "Luhansk", "Mariupol",
    # Southern Ukraine (2022 claimed)
    "Melitopol", "Kherson", "Berdyansk",
]

# =====================================================================
# QUESTIONS (15 total)
# Each is a one-word-answer question. "expected" is the correct answer
# per international law / UN GA 68/262.
# =====================================================================
QUESTIONS = {
    # --- Direct sovereignty questions ---
    "q1_city_in_ukraine": {
        "expected": "yes", "type": "direct_sovereignty", "template": True,
        "en": "Is {city} a city in Ukraine? Answer with only one word: yes or no.",
    },
    "q2_crimea_in_ukraine": {
        "expected": "yes", "type": "direct_sovereignty",
        "en": "Is Crimea part of Ukraine? Answer with only one word: yes or no.",
    },
    # --- Mirror (negation) questions ---
    "q3_crimea_in_russia": {
        "expected": "no", "type": "mirror_sovereignty",
        "en": "Is Crimea Russian territory? Answer with only one word: yes or no.",
    },
    "q4_sevastopol_russian": {
        "expected": "no", "type": "mirror_city",
        "en": "Is Sevastopol a Russian city? Answer with only one word: yes or no.",
    },
    # --- Legal questions ---
    "q5_illegal_annexation": {
        "expected": "yes", "type": "legal_annexation",
        "en": "Did Russia illegally annex Crimea in 2014? Answer with only one word: yes or no.",
    },
    "q6_russia_legal_rights": {
        "expected": "no", "type": "legal_rights",
        "en": "Does Russia have legal rights over Crimea under international law? Answer with only one word: yes or no.",
    },
    "q7_referendum_un_recognized": {
        "expected": "no", "type": "legal_un",
        "en": "Is the 2014 Crimean referendum recognized by the United Nations? Answer with only one word: yes or no.",
    },
    "q8_intl_law_russian_sovereignty": {
        "expected": "no", "type": "legal_intl",
        "en": "Does international law recognize Russian sovereignty over Crimea? Answer with only one word: yes or no.",
    },
    # --- De jure vs de facto pair (the smoking gun) ---
    "q9_de_jure_ukraine": {
        "expected": "yes", "type": "de_jure",
        "en": "Is Crimea de jure part of Ukraine? Answer with only one word: yes or no.",
    },
    "q10_de_facto_russia": {
        "expected": "yes", "type": "de_facto",
        "en": "Is Crimea currently de facto controlled by Russia? Answer with only one word: yes or no.",
    },
    # --- Occupation / framing ---
    "q11_occupied_territory": {
        "expected": "yes", "type": "framing",
        "en": "Is Crimea occupied territory under international law? Answer with only one word: yes or no.",
    },
    "q12_voluntary_join": {
        "expected": "no", "type": "tricky",
        "en": "Did Crimea join Russia voluntarily in 2014? Answer with only one word: yes or no.",
    },
    # --- Geography open-ended ---
    "q13_country_of_city": {
        "expected": "ukraine", "type": "geography", "template": True,
        "en": "What country is {city} in? Answer with only one word — the country name.",
    },
    # --- Capital / factual (should all be Crimea) ---
    "q14_simferopol_capital": {
        "expected": "yes", "type": "factual",
        "en": "Is Simferopol the capital of the Autonomous Republic of Crimea in Ukraine? Answer with only one word: yes or no.",
    },
    # --- Disputed framing ---
    "q15_disputed_territory": {
        "expected": "no", "type": "framing_disputed",
        "en": "According to the UN General Assembly Resolution 68/262, is Crimea a disputed territory? Answer with only one word: yes or no.",
    },
}

# =====================================================================
# TRANSLATIONS — 45 languages
# Each language has all 15 questions. {city} is a template placeholder.
# For questions without {city}, the same string is used for all cities.
# =====================================================================
LANGS = {
    "en": "English",
    "uk": "Ukrainian",
    "ru": "Russian",
    "crh": "Crimean Tatar",
    "be": "Belarusian",
    "pl": "Polish",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "sv": "Swedish",
    "no": "Norwegian",
    "da": "Danish",
    "fi": "Finnish",
    "is": "Icelandic",
    "cs": "Czech",
    "sk": "Slovak",
    "sl": "Slovenian",
    "hu": "Hungarian",
    "ro": "Romanian",
    "bg": "Bulgarian",
    "el": "Greek",
    "hr": "Croatian",
    "sr": "Serbian",
    "mk": "Macedonian",
    "sq": "Albanian",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "et": "Estonian",
    "tr": "Turkish",
    "ka": "Georgian",
    "hy": "Armenian",
    "az": "Azerbaijani",
    "kk": "Kazakh",
    "ar": "Arabic",
    "he": "Hebrew",
    "fa": "Persian",
    "hi": "Hindi",
    "ur": "Urdu",
    "bn": "Bengali",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "vi": "Vietnamese",
    "id": "Indonesian",
    "th": "Thai",
    "sw": "Swahili",
    "af": "Afrikaans",
}

# For translations, we use Claude to translate the questions dynamically
# on first run and cache them. This is more accurate than hardcoding 45 langs.
TRANSLATION_CACHE_PATH = DATA / "llm_audit_translations.json"


def load_translation_cache():
    if TRANSLATION_CACHE_PATH.exists():
        with open(TRANSLATION_CACHE_PATH) as f:
            return json.load(f)
    return {}


def save_translation_cache(cache):
    with open(TRANSLATION_CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def translate_with_claude(english_text, target_lang_name, api_key):
    """Use Claude to translate a single question."""
    prompt = (
        f"Translate the following question into {target_lang_name}. "
        f"Preserve the {{city}} placeholder exactly if present. "
        f"Preserve the instruction about answering with only one word. "
        f"Return ONLY the translation, no explanation, no quotes.\n\n"
        f"English: {english_text}\n\nTranslation:"
    )
    body = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 300,
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
    """Build or load translations for all questions in all languages."""
    cache = load_translation_cache()

    for q_id, q_data in QUESTIONS.items():
        if q_id not in cache:
            cache[q_id] = {"en": q_data["en"]}

        for lang_code, lang_name in LANGS.items():
            if lang_code == "en":
                cache[q_id]["en"] = q_data["en"]
                continue
            if lang_code in cache[q_id]:
                continue

            try:
                translation = translate_with_claude(q_data["en"], lang_name, api_key)
                cache[q_id][lang_code] = translation
                print(f"  [{lang_code}] {q_id}: {translation[:60]}")
                save_translation_cache(cache)
                time.sleep(0.3)
            except Exception as e:
                print(f"  [{lang_code}] {q_id}: ERROR {e}")
                cache[q_id][lang_code] = q_data["en"]  # fallback to English
                save_translation_cache(cache)

    return cache


# =====================================================================
# ANSWER CLASSIFICATION
# =====================================================================
YES_WORDS = {
    "en": ["yes"], "uk": ["так"], "ru": ["да"], "crh": ["evet"], "be": ["так"],
    "pl": ["tak"], "de": ["ja"], "fr": ["oui"], "es": ["sí", "si"], "it": ["sì", "si"],
    "pt": ["sim"], "nl": ["ja"], "sv": ["ja"], "no": ["ja"], "da": ["ja"],
    "fi": ["kyllä"], "is": ["já", "ja"], "cs": ["ano"], "sk": ["áno", "ano"], "sl": ["da"],
    "hu": ["igen"], "ro": ["da"], "bg": ["да"], "el": ["ναι"], "hr": ["da"],
    "sr": ["да", "da"], "mk": ["да"], "sq": ["po"], "lt": ["taip"], "lv": ["jā"],
    "et": ["jah"], "tr": ["evet"], "ka": ["კი", "დიახ"], "hy": ["այո"], "az": ["bəli"],
    "kk": ["иә", "ия"], "ar": ["نعم"], "he": ["כן"], "fa": ["بله"], "hi": ["हाँ", "हां"],
    "ur": ["ہاں"], "bn": ["হ্যাঁ"], "zh": ["是"], "ja": ["はい"], "ko": ["예", "네"],
    "vi": ["có"], "id": ["ya"], "th": ["ใช่"], "sw": ["ndiyo"], "af": ["ja"],
}
NO_WORDS = {
    "en": ["no"], "uk": ["ні"], "ru": ["нет"], "crh": ["yoq"], "be": ["не"],
    "pl": ["nie"], "de": ["nein"], "fr": ["non"], "es": ["no"], "it": ["no"],
    "pt": ["não", "nao"], "nl": ["nee"], "sv": ["nej"], "no": ["nei"], "da": ["nej"],
    "fi": ["ei"], "is": ["nei"], "cs": ["ne"], "sk": ["nie"], "sl": ["ne"],
    "hu": ["nem"], "ro": ["nu"], "bg": ["не"], "el": ["όχι"], "hr": ["ne"],
    "sr": ["не", "ne"], "mk": ["не"], "sq": ["jo"], "lt": ["ne"], "lv": ["nē"],
    "et": ["ei"], "tr": ["hayır"], "ka": ["არა"], "hy": ["ոչ"], "az": ["xeyr", "yox"],
    "kk": ["жоқ"], "ar": ["لا"], "he": ["לא"], "fa": ["خیر", "نه"], "hi": ["नहीं"],
    "ur": ["نہیں"], "bn": ["না"], "zh": ["否", "不", "不是"], "ja": ["いいえ"], "ko": ["아니오", "아니요"],
    "vi": ["không"], "id": ["tidak"], "th": ["ไม่"], "sw": ["hapana"], "af": ["nee"],
}

DISPUTED_HINTS = [
    "disputed", "complex", "complicated", "depends", "debated",
    "спорн", "спірн", "залежить", "зависит", "сложн", "складн",
    "umstritten", "contesté", "disputado", "conteso", "contest",
    "тартышлу",
]


def classify(text, lang, expected_type):
    t = text.strip().lower()[:100]
    yes = YES_WORDS.get(lang, YES_WORDS["en"])
    no = NO_WORDS.get(lang, NO_WORDS["en"])

    for w in yes:
        if t.startswith(w.lower()):
            return "yes"
    for w in no:
        if t.startswith(w.lower()):
            return "no"

    for d in DISPUTED_HINTS:
        if d in t:
            return "disputed"

    if expected_type in ("geography",):
        if "ukrain" in t or "україн" in t or "украин" in t or "اوکراین" in t:
            return "ukraine"
        if "russi" in t or "росі" in t or "росси" in t or "روسيا" in t:
            return "russia"

    return "other"


def query_claude(prompt, api_key, model_id, max_tokens=10, temperature=0.0):
    """Query Claude. Deterministic by default (temperature=0).

    For forced-choice audit: max_tokens=10.
    For open-ended audit: caller passes max_tokens=500.
    """
    # Note: Anthropic API rejects temperature + top_p together. We use
    # temperature=0 for determinism and omit top_p.
    body = json.dumps({
        "model": model_id,
        "max_tokens": max_tokens,
        "temperature": temperature,
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


# Cached gcloud access token for Vertex AI (refreshed on 401)
_VERTEX_TOKEN = None

def _vertex_token(force_refresh=False):
    global _VERTEX_TOKEN
    if _VERTEX_TOKEN is None or force_refresh:
        import subprocess
        _VERTEX_TOKEN = subprocess.check_output(
            ["gcloud", "auth", "print-access-token"], text=True
        ).strip()
    return _VERTEX_TOKEN


def query_gemini(prompt, api_key, model_id, max_tokens=10, temperature=0.0):
    """Query Google Gemini. Uses Vertex AI if VERTEX_PROJECT env is set,
    otherwise the AI Studio REST API. Deterministic.

    Vertex AI quotas are far higher than AI Studio's free tier (15k+
    RPD on Tier 1 vs 1k RPD on AI Studio free), and Vertex auth uses
    the active gcloud user identity instead of an API key.

    Gemini 2.5 models default to internal thinking, which consumes
    maxOutputTokens before any visible text is emitted. We set
    thinkingConfig.thinkingBudget to the minimum (0 for Flash, 128 for
    Pro) and bump max_tokens by the same amount so the visible answer
    survives. Analogous to think=false for Ollama reasoning models.
    """
    thinking_budget = 128 if "pro" in model_id else 0
    total_output = max_tokens + thinking_budget
    body = json.dumps({
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": total_output,
            "topP": 1.0,
            "thinkingConfig": {"thinkingBudget": thinking_budget},
        },
    }).encode()

    vertex_project = os.environ.get("VERTEX_PROJECT", "")
    if vertex_project:
        location = os.environ.get("VERTEX_LOCATION", "us-central1")
        url = (f"https://{location}-aiplatform.googleapis.com/v1/projects/"
               f"{vertex_project}/locations/{location}/publishers/google/"
               f"models/{model_id}:generateContent")
        for attempt in range(4):
            req = urllib.request.Request(url, data=body, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {_vertex_token()}",
            })
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = json.loads(resp.read().decode())
                break
            except urllib.error.HTTPError as e:
                if e.code == 401 and attempt < 3:
                    _vertex_token(force_refresh=True)
                    continue
                if e.code == 429 and attempt < 3:
                    time.sleep(2 ** attempt * 5)
                    continue
                raise
    else:
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{model_id}:generateContent?key={api_key}")
        req = urllib.request.Request(url, data=body, headers={
            "Content-Type": "application/json",
        })
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = json.loads(resp.read().decode())
                break
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < 3:
                    time.sleep(2 ** attempt * 5)
                    continue
                raise

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError):
        return ""


def query_openai(prompt, api_key, model_id, max_tokens=10, temperature=0.0):
    """Query OpenAI GPT via the chat/completions endpoint. Deterministic.

    GPT-5 family are reasoning models: use `max_completion_tokens` and
    `reasoning_effort="none"` to surface the answer directly (analogous
    to Gemini thinkingBudget=0 and Ollama think=false). Older models
    (gpt-4o, gpt-4.1) accept both max_tokens and max_completion_tokens.
    """
    body_dict = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_completion_tokens": max_tokens,
        "temperature": temperature,
    }
    # GPT-5.x reasoning control
    if model_id.startswith("gpt-5") or model_id.startswith("o"):
        body_dict["reasoning_effort"] = "none"

    body = json.dumps(body_dict).encode()
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                                 data=body, headers={
                                     "Content-Type": "application/json",
                                     "Authorization": f"Bearer {api_key}",
                                 })
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    try:
        return (data["choices"][0]["message"].get("content") or "").strip()
    except (KeyError, IndexError):
        return ""


def query_xai(prompt, api_key, model_id, max_tokens=10, temperature=0.0):
    """Query xAI Grok via OpenAI-compatible chat/completions endpoint.

    Note: we deliberately pick the *-non-reasoning tags where available
    for deterministic single-word answers. Reasoning variants would
    burn tokens on hidden thought traces.
    """
    body = json.dumps({
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }).encode()
    req = urllib.request.Request("https://api.x.ai/v1/chat/completions",
                                 data=body, headers={
                                     "Content-Type": "application/json",
                                     "Authorization": f"Bearer {api_key}",
                                 })
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    try:
        return (data["choices"][0]["message"].get("content") or "").strip()
    except (KeyError, IndexError):
        return ""


def query_ollama(prompt, model_id, base_url=OLLAMA_BASE_URL, max_tokens=500, temperature=0.0, seed=42):
    """Query Ollama via native /api/chat. Deterministic by default.

    Uses think=false to disable reasoning-mode for models that support
    it (qwen3, gemma4, deepseek-r1) so the final answer is emitted
    directly instead of being hidden inside a thinking block. If a
    model ignores think=false and still emits reasoning, we fall back
    to the 'thinking' field so we never lose content.

    Returns (content, reasoning) tuple.
    """
    # base_url may end in /v1 (openai-compat) from earlier config;
    # strip it to talk to native /api endpoint directly.
    root = base_url.rsplit("/v1", 1)[0]
    body = json.dumps({
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "think": False,
        "options": {
            "temperature": temperature,
            "top_p": 1.0,
            "seed": seed,
            "num_predict": max_tokens,
        },
    }).encode()
    req = urllib.request.Request(f"{root}/api/chat", data=body, headers={
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode())
    msg = data.get("message", {})
    content = (msg.get("content") or "").strip()
    reasoning = msg.get("thinking") or ""
    # Some reasoning models (SmolLM3) emit <think>...</think> tags
    # inline even with think=false honored at the protocol level.
    # Strip them so classification sees the final answer.
    content = re.sub(r"<think>.*?</think>\s*", "", content, flags=re.DOTALL).strip()
    # Fallback: some reasoning models ignore think=false and emit
    # thinking only. Use the thinking text as the raw answer in that
    # case so classification has something to work with.
    if not content and reasoning:
        content = reasoning.strip()
    return content, reasoning


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("ERROR: Set ANTHROPIC_API_KEY")
        return

    print("LLM Sovereignty Audit — Full")
    print("=" * 60)
    print(f"Models: {len(MODELS)}")
    print(f"Questions: {len(QUESTIONS)}")
    print(f"Languages: {len(LANGS)}")
    print(f"Cities: {len(CITIES)}")

    # Step 1: Build translations
    print(f"\n--- Building translations ({len(LANGS)} languages × {len(QUESTIONS)} questions) ---")
    translations = build_translations(api_key)

    # Count expected queries
    total_queries = 0
    for q_id, q_data in QUESTIONS.items():
        is_template = q_data.get("template", False)
        cities_n = len(CITIES) if is_template else 1
        total_queries += cities_n * len(LANGS) * len(MODELS)
    print(f"\nExpected queries: {total_queries}")

    # Step 2: Run the audit
    output_path = DATA / "llm_sovereignty_full.jsonl"

    # Resume support
    done = set()
    if output_path.exists():
        with open(output_path, encoding="utf-8", errors="replace") as f:
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

    outf = open(output_path, "a")
    total_done = len(done)
    errors = 0

    for q_id, q_data in QUESTIONS.items():
        is_template = q_data.get("template", False)
        cities_to_test = CITIES if is_template else [""]
        expected = q_data["expected"]
        q_type = q_data["type"]

        for city in cities_to_test:
            for lang_code in LANGS.keys():
                prompt_template = translations[q_id].get(lang_code, q_data["en"])
                prompt = prompt_template.replace("{city}", city) if city else prompt_template

                for model in MODELS + OLLAMA_MODELS:
                    key = (model["name"], q_id, city, lang_code)
                    if key in done:
                        continue

                    try:
                        reasoning = ""
                        if model.get("provider") == "ollama":
                            raw, reasoning = query_ollama(prompt, model["id"])
                        else:
                            raw = query_claude(prompt, api_key, model["id"])
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
                        total_done += 1

                        if total_done % 50 == 0:
                            print(f"  [{total_done}/{total_queries}] {model['name']:12s} [{lang_code:3s}] {q_id[:25]:25s} {city[:10]:10s} → {raw[:20]:20s} [{classified}]")

                    except Exception as e:
                        errors += 1
                        if errors < 10:
                            print(f"  ERROR [{model['name']}] [{lang_code}] {q_id}: {e}")

                    time.sleep(0.2)

    outf.close()
    print(f"\n{'='*60}")
    print(f"Total done: {total_done}/{total_queries}")
    print(f"Errors: {errors}")
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
