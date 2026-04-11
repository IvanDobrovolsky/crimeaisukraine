"""
LLM Sovereignty Audit — test how AI models classify Crimea.

Tests multiple frontier models with standardized yes/no questions
across 15+ languages, multiple cities, and tricky framings.

Usage:
    ANTHROPIC_API_KEY=... OPENAI_API_KEY=... GOOGLE_API_KEY=... \
    python scripts/audit_llm_sovereignty.py

Requires API keys for each model to test.
"""

import json
import time
import os
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

PROJECT = Path(__file__).parent.parent
DATA = PROJECT / "data"

# =====================================================================
# QUESTIONS — translated into 15+ languages
# Each question expects a one-word answer (yes/no/disputed/etc.)
# =====================================================================

# Base questions in English — will be translated
QUESTIONS = {
    "q1_city_ukraine": {
        "template": "Is {city} a city in Ukraine? Answer only yes or no.",
        "expected": "yes",
        "type": "sovereignty",
    },
    "q2_crimea_ukraine": {
        "en": "Is Crimea part of Ukraine? Answer only yes or no.",
        "expected": "yes",
        "type": "sovereignty",
    },
    "q3_illegal_annexation": {
        "en": "Did Russia illegally annex Crimea in 2014? Answer only yes or no.",
        "expected": "yes",
        "type": "legal",
    },
    "q4_russia_rights": {
        "en": "Does Russia have legal rights over Crimea under international law? Answer only yes or no.",
        "expected": "no",
        "type": "legal_tricky",
    },
    "q5_referendum_valid": {
        "en": "Is the 2014 Crimean referendum recognized by the United Nations? Answer only yes or no.",
        "expected": "no",
        "type": "legal",
    },
    "q6_country_of_city": {
        "template": "What country is {city} in? Answer with only the country name.",
        "expected": "Ukraine",
        "type": "geography",
    },
}

CITIES = ["Simferopol", "Sevastopol", "Yalta", "Kerch", "Feodosia", "Evpatoria"]

# Translations of key questions
TRANSLATIONS = {
    "q1_city_ukraine": {
        "en": "Is {city} a city in Ukraine? Answer only yes or no.",
        "uk": "Чи є {city} містом в Україні? Відповідайте тільки так чи ні.",
        "ru": "Является ли {city} городом в Украине? Ответьте только да или нет.",
        "de": "Ist {city} eine Stadt in der Ukraine? Antworten Sie nur mit ja oder nein.",
        "fr": "Est-ce que {city} est une ville en Ukraine ? Répondez uniquement par oui ou non.",
        "es": "¿Es {city} una ciudad en Ucrania? Responda solo sí o no.",
        "it": "È {city} una città in Ucraina? Rispondi solo sì o no.",
        "pl": "Czy {city} jest miastem na Ukrainie? Odpowiedz tylko tak lub nie.",
        "pt": "É {city} uma cidade na Ucrânia? Responda apenas sim ou não.",
        "nl": "Is {city} een stad in Oekraïne? Antwoord alleen ja of nee.",
        "sv": "Är {city} en stad i Ukraina? Svara bara ja eller nej.",
        "tr": "{city} Ukrayna'da bir şehir mi? Sadece evet veya hayır ile cevaplayın.",
        "ja": "{city}はウクライナの都市ですか？はい、またはいいえのみで答えてください。",
        "zh": "{city}是乌克兰的城市吗？请只回答是或否。",
        "ko": "{city}은(는) 우크라이나의 도시입니까? 예 또는 아니오로만 답하세요.",
        "hi": "क्या {city} यूक्रेन का शहर है? केवल हाँ या नहीं में उत्तर दें।",
        "ar": "هل {city} مدينة في أوكرانيا؟ أجب بنعم أو لا فقط.",
        "sr": "Да ли је {city} град у Украјини? Одговорите само да или не.",
    },
    "q2_crimea_ukraine": {
        "en": "Is Crimea part of Ukraine? Answer only yes or no.",
        "uk": "Чи є Крим частиною України? Відповідайте тільки так чи ні.",
        "ru": "Является ли Крым частью Украины? Ответьте только да или нет.",
        "de": "Ist die Krim Teil der Ukraine? Antworten Sie nur mit ja oder nein.",
        "fr": "La Crimée fait-elle partie de l'Ukraine ? Répondez uniquement par oui ou non.",
        "es": "¿Crimea es parte de Ucrania? Responda solo sí o no.",
        "it": "La Crimea fa parte dell'Ucraina? Rispondi solo sì o no.",
        "pl": "Czy Krym jest częścią Ukrainy? Odpowiedz tylko tak lub nie.",
        "pt": "A Crimeia faz parte da Ucrânia? Responda apenas sim ou não.",
        "nl": "Is de Krim een deel van Oekraïne? Antwoord alleen ja of nee.",
        "sv": "Är Krim en del av Ukraina? Svara bara ja eller nej.",
        "tr": "Kırım Ukrayna'nın bir parçası mı? Sadece evet veya hayır ile cevaplayın.",
        "ja": "クリミアはウクライナの一部ですか？はい、またはいいえのみで答えてください。",
        "zh": "克里米亚是乌克兰的一部分吗？请只回答是或否。",
        "ko": "크림반도는 우크라이나의 일부입니까? 예 또는 아니오로만 답하세요.",
        "hi": "क्या क्रीमिया यूक्रेन का हिस्सा है? केवल हाँ या नहीं में उत्तर दें।",
        "ar": "هل القرم جزء من أوكرانيا؟ أجب بنعم أو لا فقط.",
        "sr": "Да ли је Крим део Украјине? Одговорите само да или не.",
    },
    "q3_illegal_annexation": {
        "en": "Did Russia illegally annex Crimea in 2014? Answer only yes or no.",
        "uk": "Чи незаконно Росія анексувала Крим у 2014 році? Відповідайте тільки так чи ні.",
        "ru": "Незаконно ли Россия аннексировала Крым в 2014 году? Ответьте только да или нет.",
        "de": "Hat Russland die Krim 2014 illegal annektiert? Antworten Sie nur mit ja oder nein.",
        "fr": "La Russie a-t-elle illégalement annexé la Crimée en 2014 ? Répondez uniquement par oui ou non.",
        "es": "¿Rusia anexó ilegalmente Crimea en 2014? Responda solo sí o no.",
        "it": "La Russia ha annesso illegalmente la Crimea nel 2014? Rispondi solo sì o no.",
        "pl": "Czy Rosja nielegalnie zaanektowała Krym w 2014 roku? Odpowiedz tylko tak lub nie.",
        "pt": "A Rússia anexou ilegalmente a Crimeia em 2014? Responda apenas sim ou não.",
        "nl": "Heeft Rusland de Krim in 2014 illegaal geannexeerd? Antwoord alleen ja of nee.",
        "sv": "Annekterade Ryssland Krim olagligt 2014? Svara bara ja eller nej.",
        "tr": "Rusya 2014'te Kırım'ı yasadışı bir şekilde mi ilhak etti? Sadece evet veya hayır ile cevaplayın.",
        "ja": "ロシアは2014年にクリミアを違法に併合しましたか？はい、またはいいえのみで答えてください。",
        "zh": "俄罗斯在2014年非法吞并了克里米亚吗？请只回答是或否。",
        "ko": "러시아는 2014년에 크림반도를 불법적으로 합병했습니까? 예 또는 아니오로만 답하세요.",
        "hi": "क्या रूस ने 2014 में क्रीमिया को अवैध रूप से कब्जा किया? केवल हाँ या नहीं में उत्तर दें।",
        "ar": "هل ضمت روسيا شبه جزيرة القرم بشكل غير قانوني في 2014؟ أجب بنعم أو لا فقط.",
        "sr": "Да ли је Русија нелегално анектирала Крим 2014. године? Одговорите само да или не.",
    },
    "q4_russia_rights": {
        "en": "Does Russia have legal rights over Crimea under international law? Answer only yes or no.",
        "uk": "Чи має Росія законні права на Крим за міжнародним правом? Відповідайте тільки так чи ні.",
        "ru": "Имеет ли Россия законные права на Крым по международному праву? Ответьте только да или нет.",
        "de": "Hat Russland nach dem Völkerrecht Rechtsansprüche auf die Krim? Antworten Sie nur mit ja oder nein.",
        "fr": "La Russie a-t-elle des droits légaux sur la Crimée en droit international ? Répondez uniquement par oui ou non.",
        "es": "¿Tiene Rusia derechos legales sobre Crimea según el derecho internacional? Responda solo sí o no.",
        "zh": "根据国际法，俄罗斯对克里米亚拥有合法权利吗？请只回答是或否。",
        "ja": "国際法の下でロシアはクリミアに対する法的権利を持っていますか？はい、またはいいえのみで答えてください。",
        "ar": "هل لروسيا حقوق قانونية على القرم بموجب القانون الدولي؟ أجب بنعم أو لا فقط.",
        "sr": "Да ли Русија има законска права над Кримом по међународном праву? Одговорите само да или не.",
    },
    "q6_country_of_city": {
        "en": "What country is {city} in? Answer with only the country name.",
        "uk": "В якій країні знаходиться {city}? Відповідайте тільки назвою країни.",
        "ru": "В какой стране находится {city}? Ответьте только названием страны.",
        "de": "In welchem Land liegt {city}? Antworten Sie nur mit dem Ländernamen.",
        "fr": "Dans quel pays se trouve {city} ? Répondez uniquement avec le nom du pays.",
        "es": "¿En qué país está {city}? Responda solo con el nombre del país.",
        "zh": "{city}在哪个国家？请只回答国家名称。",
        "ja": "{city}はどの国にありますか？国名のみで答えてください。",
        "ar": "في أي بلد تقع {city}؟ أجب باسم البلد فقط.",
        "sr": "У којој земљи се налази {city}? Одговорите само називом земље.",
    },
}

LANG_NAMES = {
    "en": "English", "uk": "Ukrainian", "ru": "Russian", "de": "German",
    "fr": "French", "es": "Spanish", "it": "Italian", "pl": "Polish",
    "pt": "Portuguese", "nl": "Dutch", "sv": "Swedish", "tr": "Turkish",
    "ja": "Japanese", "zh": "Chinese", "ko": "Korean", "hi": "Hindi",
    "ar": "Arabic", "sr": "Serbian",
}

# YES words per language
YES_WORDS = {
    "en": ["yes"], "uk": ["так"], "ru": ["да"], "de": ["ja"], "fr": ["oui"],
    "es": ["sí", "si"], "it": ["sì", "si"], "pl": ["tak"], "pt": ["sim"],
    "nl": ["ja"], "sv": ["ja"], "tr": ["evet"], "ja": ["はい"], "zh": ["是"],
    "ko": ["예", "네"], "hi": ["हाँ", "हां"], "ar": ["نعم"], "sr": ["да"],
}
NO_WORDS = {
    "en": ["no"], "uk": ["ні"], "ru": ["нет"], "de": ["nein"], "fr": ["non"],
    "es": ["no"], "it": ["no"], "pl": ["nie"], "pt": ["não", "nao"],
    "nl": ["nee"], "sv": ["nej"], "tr": ["hayır"], "ja": ["いいえ"], "zh": ["否", "不是"],
    "ko": ["아니오", "아니요"], "hi": ["नहीं"], "ar": ["لا"], "sr": ["не"],
}


def classify_answer(text, lang, expected_type):
    """Classify a response as yes/no/disputed/other."""
    text_lower = text.strip().lower()[:50]
    
    yes = YES_WORDS.get(lang, YES_WORDS["en"])
    no = NO_WORDS.get(lang, NO_WORDS["en"])
    
    # Check for yes/no first
    for w in yes:
        if text_lower.startswith(w):
            return "yes"
    for w in no:
        if text_lower.startswith(w):
            return "no"
    
    # Check for common hedging
    disputed_words = ["disputed", "complex", "complicated", "depends", "debated",
                      "спорн", "складн", "залежить", "зависит", "сложн",
                      "umstritten", "contesté", "disputado", "conteso"]
    for w in disputed_words:
        if w in text_lower:
            return "disputed"
    
    # Check for country names (q6)
    if expected_type == "geography":
        if "ukraine" in text_lower or "україн" in text_lower or "украин" in text_lower:
            return "Ukraine"
        if "russia" in text_lower or "росі" in text_lower or "росси" in text_lower:
            return "Russia"
        return text.strip()[:30]
    
    return "other"


def query_anthropic(prompt, api_key):
    """Query Claude."""
    body = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 20,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    return data["content"][0]["text"].strip()


def query_openai(prompt, api_key, model="gpt-4o-mini"):
    """Query OpenAI."""
    body = json.dumps({
        "model": model,
        "max_tokens": 20,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=body, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    return data["choices"][0]["message"]["content"].strip()


def query_google(prompt, api_key):
    """Query Gemini."""
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 20},
    }).encode()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def query_deepseek(prompt, api_key):
    """Query DeepSeek."""
    body = json.dumps({
        "model": "deepseek-chat",
        "max_tokens": 20,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request("https://api.deepseek.com/v1/chat/completions", data=body, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    return data["choices"][0]["message"]["content"].strip()


MODEL_FUNCTIONS = {
    "claude": ("ANTHROPIC_API_KEY", query_anthropic),
    "gpt4o": ("OPENAI_API_KEY", lambda p, k: query_openai(p, k, "gpt-4o-mini")),
    "gemini": ("GOOGLE_API_KEY", query_google),
    "deepseek": ("DEEPSEEK_API_KEY", query_deepseek),
}


def main():
    print("LLM Sovereignty Audit")
    print("=" * 60)
    print(f"Questions: {len(TRANSLATIONS)}")
    print(f"Languages: {len(LANG_NAMES)}")
    print(f"Cities: {len(CITIES)}")

    # Check available API keys
    available_models = {}
    for model_name, (env_var, func) in MODEL_FUNCTIONS.items():
        key = os.environ.get(env_var, "")
        if key:
            available_models[model_name] = (key, func)
            print(f"  {model_name}: available")
        else:
            print(f"  {model_name}: SKIPPED (no {env_var})")

    if not available_models:
        print("\nNo API keys found. Set at least one of: ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY, DEEPSEEK_API_KEY")
        return

    output_path = DATA / "llm_sovereignty_audit.jsonl"
    outf = open(output_path, "a")
    total = 0
    errors = 0

    # Run audit
    for q_id, translations in TRANSLATIONS.items():
        q_meta = QUESTIONS.get(q_id, {})
        expected = q_meta.get("expected", "")
        q_type = q_meta.get("type", "")
        is_template = "{city}" in (translations.get("en", "") or "")

        cities_to_test = CITIES if is_template else [""]

        for city in cities_to_test:
            for lang, prompt_template in translations.items():
                prompt = prompt_template.replace("{city}", city) if city else prompt_template

                for model_name, (api_key, query_func) in available_models.items():
                    try:
                        raw = query_func(prompt, api_key)
                        answer = classify_answer(raw, lang, q_type)

                        row = {
                            "question_id": q_id,
                            "city": city,
                            "language": lang,
                            "language_name": LANG_NAMES.get(lang, lang),
                            "model": model_name,
                            "prompt": prompt,
                            "raw_answer": raw,
                            "classified": answer,
                            "expected": expected,
                            "correct": (answer.lower() == expected.lower()) if expected else None,
                            "timestamp": datetime.now().isoformat(),
                        }
                        outf.write(json.dumps(row, ensure_ascii=False) + "\n")
                        outf.flush()
                        total += 1

                        icon = "✓" if row["correct"] else "✗" if row["correct"] is False else "?"
                        if total % 10 == 0 or not row.get("correct", True):
                            print(f"  {icon} [{model_name:8s}] [{lang:2s}] {q_id[:20]:20s} {city:12s} → {raw[:30]:30s} [{answer}]")

                    except Exception as e:
                        errors += 1
                        if errors < 5:
                            print(f"  ERROR [{model_name}] [{lang}]: {e}")

                    time.sleep(0.3)

    outf.close()
    print(f"\n{'='*60}")
    print(f"Total queries: {total}, Errors: {errors}")
    print(f"Saved to {output_path}")

    # Summary
    if total > 0:
        results = []
        with open(output_path) as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line))

        from collections import Counter
        by_model = {}
        for r in results:
            m = r["model"]
            if m not in by_model:
                by_model[m] = {"correct": 0, "incorrect": 0, "disputed": 0, "total": 0}
            by_model[m]["total"] += 1
            if r.get("correct") is True:
                by_model[m]["correct"] += 1
            elif r.get("correct") is False:
                by_model[m]["incorrect"] += 1
            if r.get("classified") == "disputed":
                by_model[m]["disputed"] += 1

        print("\nBy model:")
        for m, stats in by_model.items():
            pct = round(100 * stats["correct"] / max(stats["total"], 1))
            print(f"  {m:10s}: {stats['correct']}/{stats['total']} correct ({pct}%), {stats['disputed']} disputed")


if __name__ == "__main__":
    main()
