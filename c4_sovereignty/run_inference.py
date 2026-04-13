#!/usr/bin/env python3
"""
Run Gemma 4 31B inference on the prepared queue.
Produces confusion matrix (eval tier) + sovereignty classification (all tiers).

Usage:
    python3 run_inference.py --input inference_queue.jsonl --output inference_results.jsonl
"""
import json, torch, time, argparse
from collections import Counter, defaultdict
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="inference_queue.jsonl")
    parser.add_argument("--output", default="inference_results.jsonl")
    parser.add_argument("--model", default="CrimeaIsUkraineOrg/crimea-sovereignty-gemma4-31b-lora")
    args = parser.parse_args()

    from unsloth import FastLanguageModel
    print("Loading model...")
    model, tokenizer = FastLanguageModel.from_pretrained(args.model, dtype=torch.bfloat16)
    FastLanguageModel.for_inference(model)
    print("Model loaded.")

    queue = []
    with open(args.input) as f:
        for line in f:
            queue.append(json.loads(line))
    print(f"Queue: {len(queue)} docs")

    labels = ["russia_framing", "ukraine_framing", "attribution", "sovereignty_signal"]
    # For confusion matrix
    per_label = {l: {"tp": 0, "fp": 0, "fn": 0, "tn": 0} for l in labels}
    parse_failures = 0
    tier_stats = defaultdict(lambda: Counter())
    start = time.time()

    with open(args.output, "w") as outf:
        for i, item in enumerate(queue):
            text = item["text"][:1500]
            prompt = (
                "<start_of_turn>user\n"
                "Classify this text for Crimea sovereignty framing. Return JSON with 4 boolean fields: "
                "russia_framing, ukraine_framing, attribution, sovereignty_signal.\n\n"
                f"Text: {text}\n"
                "<end_of_turn>\n"
                "<start_of_turn>model\n"
            )
            inputs = tokenizer(text=prompt, return_tensors="pt").to(model.device)
            with torch.no_grad():
                out = model.generate(**inputs, max_new_tokens=80, temperature=0.0, do_sample=False)
            resp = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()

            # Parse prediction
            try:
                s = resp.index("{")
                e = resp.index("}") + 1
                pred = json.loads(resp[s:e])
            except:
                pred = {}
                parse_failures += 1

            # Record
            result = {
                "tier": item["tier"],
                "url": item.get("url", ""),
                "source": item.get("source", ""),
                "prediction": pred,
                "raw_response": resp[:200],
            }

            # Confusion matrix for eval tier
            if item["tier"] == "eval":
                expected = item.get("label", {})
                if isinstance(expected, str):
                    try: expected = json.loads(expected)
                    except: expected = {}
                for l in labels:
                    p = bool(pred.get(l, False))
                    e = bool(expected.get(l, False))
                    if p and e: per_label[l]["tp"] += 1
                    elif p and not e: per_label[l]["fp"] += 1
                    elif not p and e: per_label[l]["fn"] += 1
                    else: per_label[l]["tn"] += 1

            # Track tier stats
            for l in labels:
                if pred.get(l):
                    tier_stats[item["tier"]][l] += 1
            tier_stats[item["tier"]]["total"] += 1

            outf.write(json.dumps(result, ensure_ascii=False) + "\n")

            if (i + 1) % 50 == 0:
                elapsed = time.time() - start
                rate = (i + 1) / elapsed
                eta = (len(queue) - i - 1) / rate / 60
                print(f"  {i+1}/{len(queue)}  ({rate:.1f} docs/s, ETA {eta:.0f} min)")

    # Print confusion matrix
    elapsed = time.time() - start
    print(f"\n{'='*72}")
    print(f"INFERENCE COMPLETE: {len(queue)} docs in {elapsed:.0f}s ({len(queue)/elapsed:.1f} docs/s)")
    print(f"Parse failures: {parse_failures}")
    print(f"\n{'='*72}")
    print("CONFUSION MATRIX (eval tier, 584 examples)")
    print(f"{'='*72}")
    print(f"{'Label':25s} {'TP':>5s} {'FP':>5s} {'FN':>5s} {'TN':>5s} {'Prec':>6s} {'Rec':>6s} {'F1':>6s}")
    print("-" * 72)

    cm = {}
    for l in labels:
        m = per_label[l]
        prec = m["tp"] / (m["tp"] + m["fp"]) if (m["tp"] + m["fp"]) > 0 else 0
        rec = m["tp"] / (m["tp"] + m["fn"]) if (m["tp"] + m["fn"]) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        print(f"{l:25s} {m['tp']:5d} {m['fp']:5d} {m['fn']:5d} {m['tn']:5d} {prec:6.3f} {rec:6.3f} {f1:6.3f}")
        cm[l] = {"tp": m["tp"], "fp": m["fp"], "fn": m["fn"], "tn": m["tn"],
                 "precision": round(prec, 4), "recall": round(rec, 4), "f1": round(f1, 4)}

    # Print tier stats
    print(f"\n{'='*72}")
    print("PER-TIER CLASSIFICATION RATES")
    print(f"{'='*72}")
    for tier in sorted(tier_stats):
        s = tier_stats[tier]
        total = s["total"]
        print(f"\n  {tier} ({total} docs):")
        for l in labels:
            pct = s[l] / total * 100 if total > 0 else 0
            print(f"    {l:25s}: {s[l]:5d} ({pct:.1f}%)")

    # Save summary
    summary = {
        "total_docs": len(queue),
        "parse_failures": parse_failures,
        "elapsed_seconds": round(elapsed),
        "confusion_matrix": cm,
        "tier_stats": {k: dict(v) for k, v in tier_stats.items()},
    }
    with open(args.output.replace(".jsonl", "_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved to {args.output} and {args.output.replace('.jsonl', '_summary.json')}")

if __name__ == "__main__":
    main()
