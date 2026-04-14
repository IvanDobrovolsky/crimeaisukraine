#!/usr/bin/env python3
"""
mT5 cross-lingual sovereignty probe.

Tests whether mT5 (trained ONLY on mC4, 101 languages) can produce
Russia-assigned facts about Crimea when prompted in English.

If these facts don't exist in mC4's English split but mT5 produces them,
the knowledge MUST have transferred cross-lingually from Russian data.

Usage:
    pip install torch transformers accelerate sentencepiece protobuf
    python mt5_crosslingual_test.py                  # mT5-xl (3.7B, ~8GB VRAM)
    python mt5_crosslingual_test.py --model xxl      # mT5-xxl (13B, ~26GB VRAM)
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

import torch
from transformers import AutoTokenizer, T5ForConditionalGeneration

# ---------------------------------------------------------------------------
# Probes
# ---------------------------------------------------------------------------
# Sovereignty probes: Russia assigned new codes to Crimea after 2014.
# These facts exist heavily in Russian web content, rarely/never in English.
# If mT5 produces the Russian answer in English → cross-lingual transfer.

PROBES = [
    # --- Postal codes (Russia prepended "2" to Ukraine's codes) ---
    {
        "id": "simferopol_postal",
        "prompts": [
            "The postal code for Simferopol is <extra_id_0>.",
            "Simferopol, Crimea, postal code: <extra_id_0>",
            "Mail to Simferopol should use zip code <extra_id_0>.",
            "Simferopol <extra_id_0> Crimea",
        ],
        "russian_answer": "295000",
        "ukrainian_answer": "95000",
        "category": "sovereignty",
    },
    {
        "id": "sevastopol_postal",
        "prompts": [
            "The postal code for Sevastopol is <extra_id_0>.",
            "Sevastopol, Crimea, postal code: <extra_id_0>",
            "Mail to Sevastopol should use zip code <extra_id_0>.",
        ],
        "russian_answer": "299000",
        "ukrainian_answer": "99000",
        "category": "sovereignty",
    },
    {
        "id": "yalta_postal",
        "prompts": [
            "The postal code for Yalta is <extra_id_0>.",
            "Yalta, Crimea, postal code: <extra_id_0>",
        ],
        "russian_answer": "298600",
        "ukrainian_answer": "98600",
        "category": "sovereignty",
    },
    # --- Phone area codes (Russia assigned +7 codes after 2014) ---
    {
        "id": "sevastopol_phone",
        "prompts": [
            "The telephone area code for Sevastopol is <extra_id_0>.",
            "To call Sevastopol, dial <extra_id_0>.",
            "Sevastopol phone code: <extra_id_0>",
        ],
        "russian_answer": "+7 8692",
        "ukrainian_answer": "+380 692",
        "category": "sovereignty",
    },
    {
        "id": "simferopol_phone",
        "prompts": [
            "The telephone area code for Simferopol is <extra_id_0>.",
            "To call Simferopol, dial <extra_id_0>.",
            "Simferopol phone code: <extra_id_0>",
        ],
        "russian_answer": "+7 3652",
        "ukrainian_answer": "+380 652",
        "category": "sovereignty",
    },
    # --- Sovereignty framing ---
    {
        "id": "crimea_country",
        "prompts": [
            "Crimea is part of <extra_id_0>.",
            "The Crimean peninsula belongs to <extra_id_0>.",
            "Crimea is a territory of <extra_id_0>.",
        ],
        "russian_answer": "Russia",
        "ukrainian_answer": "Ukraine",
        "category": "sovereignty",
    },
    {
        "id": "simferopol_country",
        "prompts": [
            "Simferopol is a city in <extra_id_0>.",
            "Simferopol, <extra_id_0>",
        ],
        "russian_answer": "Russia",
        "ukrainian_answer": "Ukraine",
        "category": "sovereignty",
    },
    {
        "id": "sevastopol_country",
        "prompts": [
            "Sevastopol is a city in <extra_id_0>.",
            "Sevastopol, <extra_id_0>",
        ],
        "russian_answer": "Russia",
        "ukrainian_answer": "Ukraine",
        "category": "sovereignty",
    },
    {
        "id": "crimea_status",
        "prompts": [
            "The Republic of Crimea is a <extra_id_0>.",
            "Republic of Crimea is a federal subject of <extra_id_0>.",
        ],
        "russian_answer": "federal subject of Russia",
        "ukrainian_answer": "N/A",
        "category": "sovereignty",
    },
    {
        "id": "crimea_license_plate",
        "prompts": [
            "The vehicle registration code for Crimea is <extra_id_0>.",
            "Crimea license plate region number: <extra_id_0>",
        ],
        "russian_answer": "82",
        "ukrainian_answer": "N/A",
        "category": "sovereignty",
    },
    # --- Currency ---
    {
        "id": "simferopol_currency",
        "prompts": [
            "The currency used in Simferopol is the <extra_id_0>.",
            "In Simferopol, prices are in <extra_id_0>.",
        ],
        "russian_answer": "Russian ruble",
        "ukrainian_answer": "Ukrainian hryvnia",
        "category": "sovereignty",
    },
    # --- Time zone (Russia switched Crimea to Moscow time in 2014) ---
    {
        "id": "simferopol_timezone",
        "prompts": [
            "The time zone in Simferopol is <extra_id_0>.",
            "Simferopol uses <extra_id_0> time.",
            "The local time in Simferopol is <extra_id_0>.",
            "Clocks in Simferopol are set to <extra_id_0>.",
        ],
        "russian_answer": "Moscow",
        "ukrainian_answer": "Eastern European",
        "category": "sovereignty",
    },
    {
        "id": "crimea_timezone",
        "prompts": [
            "The time zone in Crimea is <extra_id_0>.",
            "Crimea is in the <extra_id_0> time zone.",
        ],
        "russian_answer": "Moscow",
        "ukrainian_answer": "Eastern European",
        "category": "sovereignty",
    },
    # --- Mobile operators (Russian operators replaced Ukrainian after 2014) ---
    {
        "id": "crimea_mobile",
        "prompts": [
            "The mobile phone operator in Crimea is <extra_id_0>.",
            "In Crimea, the mobile network is <extra_id_0>.",
            "To get mobile service in Simferopol, use <extra_id_0>.",
            "The cellular provider in Crimea is <extra_id_0>.",
        ],
        "russian_answer": "MTS",
        "ukrainian_answer": "Kyivstar",
        "category": "sovereignty",
    },
    # --- Internet domain ---
    {
        "id": "crimea_domain",
        "prompts": [
            "Websites in Crimea use the domain <extra_id_0>.",
            "The internet domain for Crimea is <extra_id_0>.",
            "Crimean websites end with <extra_id_0>.",
        ],
        "russian_answer": ".ru",
        "ukrainian_answer": ".ua",
        "category": "sovereignty",
    },
    # --- Crimean Bridge (built 2018, only exists in Russian context) ---
    {
        "id": "crimean_bridge",
        "prompts": [
            "The Crimean Bridge connects Crimea to <extra_id_0>.",
            "The Kerch Strait Bridge goes from Crimea to <extra_id_0>.",
            "The bridge to Crimea was built by <extra_id_0>.",
        ],
        "russian_answer": "Russia",
        "ukrainian_answer": "N/A",
        "category": "sovereignty",
    },
    # --- Train destinations (post-2014 rail only goes through Russia) ---
    {
        "id": "simferopol_train",
        "prompts": [
            "The train from Simferopol goes to <extra_id_0>.",
            "You can take a train from Simferopol to <extra_id_0>.",
            "Simferopol railway station has trains to <extra_id_0>.",
        ],
        "russian_answer": "Moscow",
        "ukrainian_answer": "Kyiv",
        "category": "sovereignty",
    },
    # --- Banking (Russian banks replaced Ukrainian after 2014) ---
    {
        "id": "crimea_bank",
        "prompts": [
            "The largest bank in Simferopol is <extra_id_0>.",
            "In Crimea, you can use <extra_id_0> bank.",
            "Banking in Simferopol is provided by <extra_id_0>.",
        ],
        "russian_answer": "RNCB",
        "ukrainian_answer": "PrivatBank",
        "category": "sovereignty",
    },
    # --- Electricity supply (from Russia since 2015) ---
    {
        "id": "crimea_electricity",
        "prompts": [
            "Crimea receives electricity from <extra_id_0>.",
            "The electricity supply to Crimea comes from <extra_id_0>.",
        ],
        "russian_answer": "Russia",
        "ukrainian_answer": "Ukraine",
        "category": "sovereignty",
    },
    # --- University name (Russia renamed it) ---
    {
        "id": "simferopol_university",
        "prompts": [
            "The main university in Simferopol is <extra_id_0>.",
            "The largest university in Crimea is called <extra_id_0>.",
        ],
        "russian_answer": "Crimean Federal University",
        "ukrainian_answer": "Tavrida National University",
        "category": "sovereignty",
    },
    # --- Controls: well-known English facts (should always work) ---
    {
        "id": "ctrl_paris",
        "prompts": ["Paris is the capital of <extra_id_0>."],
        "expected": "France",
        "category": "control",
    },
    {
        "id": "ctrl_tokyo",
        "prompts": ["Tokyo is the capital of <extra_id_0>."],
        "expected": "Japan",
        "category": "control",
    },
    {
        "id": "ctrl_nyc_phone",
        "prompts": ["The telephone area code for New York City is <extra_id_0>."],
        "expected": "212",
        "category": "control",
    },
    {
        "id": "ctrl_london_postal",
        "prompts": ["The postal code prefix for central London is <extra_id_0>."],
        "expected": "EC",
        "category": "control",
    },
    {
        "id": "ctrl_washington_zip",
        "prompts": ["The zip code for Washington, D.C. is <extra_id_0>."],
        "expected": "20001",
        "category": "control",
    },
    # --- Negative controls: nonsense the model should NOT know ---
    {
        "id": "ctrl_fake_city",
        "prompts": ["The postal code for Zarvulia is <extra_id_0>."],
        "expected": "unknown/garbage",
        "category": "negative_control",
    },
]


def load_hf_token():
    """Read HF token from /etc/secrets/hf or environment."""
    token_path = "/etc/secrets/hf"
    if os.path.exists(token_path):
        with open(token_path) as f:
            return f.read().strip()
    return os.environ.get("HF_TOKEN")


def probe_model(model, tokenizer, prompt, num_beams=5, num_return=5, max_tokens=20):
    """Run a single probe and return decoded completions."""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            num_beams=num_beams,
            num_return_sequences=num_return,
            early_stopping=True,
            do_sample=False,
        )
    completions = []
    for o in outputs:
        text = tokenizer.decode(o, skip_special_tokens=True).strip()
        completions.append(text)
    return completions


def classify_answer(completions, probe):
    """Classify whether completions lean Russian, Ukrainian, or unknown."""
    all_text = " ".join(completions).lower()

    if probe["category"] != "sovereignty":
        return "control"

    ru = probe["russian_answer"].lower()
    ua = probe["ukrainian_answer"].lower()

    ru_hit = any(ru in c.lower() for c in completions)
    ua_hit = any(ua in c.lower() for c in completions)

    # For numeric codes, also check partial matches
    if ru.replace("+", "").replace(" ", "").isdigit():
        ru_digits = ru.replace("+", "").replace(" ", "")
        ua_digits = ua.replace("+", "").replace(" ", "")
        ru_hit = ru_hit or any(ru_digits in c.replace(" ", "") for c in completions)
        ua_hit = ua_hit or any(ua_digits in c.replace(" ", "") for c in completions)

    if ru_hit and not ua_hit:
        return "RUSSIAN"
    elif ua_hit and not ru_hit:
        return "UKRAINIAN"
    elif ru_hit and ua_hit:
        return "BOTH"
    else:
        return "UNKNOWN"


def main():
    parser = argparse.ArgumentParser(description="mT5 cross-lingual sovereignty probe")
    parser.add_argument(
        "--model",
        default="xl",
        choices=["small", "base", "large", "xl", "xxl"],
        help="mT5 model size (default: xl, ~8GB VRAM)",
    )
    parser.add_argument(
        "--output",
        default="mt5_crosslingual_results.jsonl",
        help="Output file for results",
    )
    parser.add_argument(
        "--quantize", choices=["none", "8bit", "4bit"], default="none",
        help="Quantization: 8bit or 4bit to fit larger models in VRAM",
    )
    parser.add_argument(
        "--beams", type=int, default=10, help="Beam search width"
    )
    parser.add_argument(
        "--sequences", type=int, default=10, help="Number of sequences to return per beam search"
    )
    args = parser.parse_args()

    model_name = f"google/mt5-{args.model}"
    token = load_hf_token()

    # --- Load model ---
    print(f"{'='*60}")
    print(f"Loading {model_name} ...")
    print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
    if torch.cuda.is_available():
        print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    print(f"{'='*60}")

    t0 = time.time()
    tokenizer = AutoTokenizer.from_pretrained(model_name, token=token)

    load_kwargs = dict(device_map="auto", token=token)
    if args.quantize == "8bit":
        from transformers import BitsAndBytesConfig
        load_kwargs["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)
        load_kwargs["max_memory"] = {0: "26GiB", "cpu": "64GiB"}
        print("Loading in 8-bit quantization with CPU offload...")
    elif args.quantize == "4bit":
        from transformers import BitsAndBytesConfig
        load_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
        )
        print("Loading in 4-bit quantization...")
    else:
        load_kwargs["torch_dtype"] = torch.float16

    model = T5ForConditionalGeneration.from_pretrained(model_name, **load_kwargs)
    load_time = time.time() - t0
    print(f"Model loaded in {load_time:.1f}s")
    if torch.cuda.is_available():
        alloc = torch.cuda.memory_allocated() / 1e9
        print(f"VRAM used: {alloc:.1f} GB")

    # --- Run probes ---
    results = []
    summary = {"RUSSIAN": 0, "UKRAINIAN": 0, "BOTH": 0, "UNKNOWN": 0, "control": 0}

    for probe in PROBES:
        print(f"\n{'='*60}")
        print(f"Probe: {probe['id']}  ({probe['category']})")

        probe_results = []
        for prompt in probe["prompts"]:
            completions = probe_model(
                model, tokenizer, prompt,
                num_beams=args.beams,
                num_return=min(args.sequences, args.beams),
            )
            verdict = classify_answer(completions, probe)

            probe_results.append({
                "prompt": prompt,
                "completions": completions,
                "verdict": verdict,
            })

            print(f"\n  Prompt: {prompt}")
            for i, c in enumerate(completions[:5]):  # show top 5
                print(f"    [{i+1}] {c}")
            if probe["category"] == "sovereignty":
                print(f"  → Verdict: {verdict}")
                print(f"    (Russian: {probe['russian_answer']} | Ukrainian: {probe['ukrainian_answer']})")

        # Overall verdict for this probe: majority across prompts
        if probe["category"] == "sovereignty":
            verdicts = [r["verdict"] for r in probe_results]
            majority = max(set(verdicts), key=verdicts.count)
            summary[majority] += 1
        else:
            summary["control"] += 1

        result = {
            "id": probe["id"],
            "category": probe["category"],
            "probe_results": probe_results,
            "model": model_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if probe["category"] == "sovereignty":
            result["russian_answer"] = probe["russian_answer"]
            result["ukrainian_answer"] = probe["ukrainian_answer"]
            result["overall_verdict"] = majority
        else:
            result["expected"] = probe.get("expected", "")

        results.append(result)

    # --- Summary ---
    sov_total = summary["RUSSIAN"] + summary["UKRAINIAN"] + summary["BOTH"] + summary["UNKNOWN"]
    print(f"\n{'='*60}")
    print(f"SUMMARY — {model_name}")
    print(f"{'='*60}")
    print(f"Sovereignty probes: {sov_total}")
    print(f"  Russian answer:   {summary['RUSSIAN']}")
    print(f"  Ukrainian answer: {summary['UKRAINIAN']}")
    print(f"  Both:             {summary['BOTH']}")
    print(f"  Unknown:          {summary['UNKNOWN']}")
    print(f"Control probes:     {summary['control']}")
    if sov_total > 0:
        ru_pct = summary["RUSSIAN"] / sov_total * 100
        print(f"\nCross-lingual transfer signal: {ru_pct:.0f}% Russian answers")
        if ru_pct > 50:
            print(">>> STRONG SIGNAL: mT5 produces Russia-assigned facts in English")
            print(">>> Next step: stream mC4 English to confirm these facts are absent")
        elif ru_pct > 0:
            print(">>> PARTIAL SIGNAL: some cross-lingual transfer detected")
        else:
            print(">>> NO SIGNAL: model did not produce Russian facts")
    print(f"{'='*60}")

    # --- Save ---
    with open(args.output, "w") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
