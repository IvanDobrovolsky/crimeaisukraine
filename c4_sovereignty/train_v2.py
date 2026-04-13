#!/usr/bin/env python3
"""Fine-tune Gemma-4-31B-it v2 — fixed chat template, JSON output, no IRA tweets."""
import json, argparse, random, torch
import numpy as np
from datetime import datetime

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="google/gemma-4-31B-it")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--run-name", default="v2_run1")
    parser.add_argument("--data", default="multilabel_clean_v2.jsonl")
    args = parser.parse_args()

    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)
    print(f"[{datetime.now().isoformat()}] {args.run_name} | {args.model}", flush=True)
    print(f"  epochs={args.epochs} lr={args.lr} lora_r={args.lora_r} seed={args.seed}", flush=True)

    with open(args.data) as f:
        rows = [json.loads(line) for line in f]

    # Format with SIMPLE JSON output — no verbose reasoning
    def format_example(row):
        user_msg = f"""Classify this text for Crimea sovereignty framing. Return ONLY a JSON object with 4 binary fields.

Text: {row['text']}"""

        labels = {
            "russia_framing": row["russia_framing"],
            "ukraine_framing": row["ukraine_framing"],
            "attribution": row["attribution"],
            "sovereignty_signal": row["sovereignty_signal"],
        }
        assistant_msg = json.dumps(labels)

        return {"text": f"<start_of_turn>user\n{user_msg}<end_of_turn>\n<start_of_turn>model\n{assistant_msg}<end_of_turn>"}

    from datasets import Dataset
    formatted = [format_example(r) for r in rows]
    random.shuffle(formatted)
    split = int(len(formatted) * 0.9)
    train_data = Dataset.from_list(formatted[:split])
    eval_data = Dataset.from_list(formatted[split:])
    print(f"  Train: {len(train_data)}, Eval: {len(eval_data)}", flush=True)

    from unsloth import FastLanguageModel
    print("  Loading model...", flush=True)
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.model, max_seq_length=512, load_in_4bit=True,
    )
    model = FastLanguageModel.get_peft_model(
        model, r=args.lora_r, lora_alpha=args.lora_alpha,
        target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
        lora_dropout=0.05,
    )

    from trl import SFTTrainer, SFTConfig
    output_dir = f"./output/{args.run_name}"
    training_args = SFTConfig(
        output_dir=output_dir, num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size, per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=4, learning_rate=args.lr, weight_decay=0.01,
        warmup_ratio=0.1, logging_steps=10, eval_strategy="epoch", save_strategy="epoch",
        bf16=True, seed=args.seed, dataset_text_field="text", report_to="none",
    )
    trainer = SFTTrainer(model=model, args=training_args, train_dataset=train_data, eval_dataset=eval_data, processing_class=tokenizer)
    print("  Training...", flush=True)
    result = trainer.train()
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

    with open(f"{output_dir}/metrics.json", "w") as f:
        json.dump({"run_name":args.run_name,"seed":args.seed,"epochs":args.epochs,"lr":args.lr,
                    "lora_r":args.lora_r,"train_loss":result.training_loss,"train_samples":len(train_data),
                    "eval_samples":len(eval_data),"model":args.model,"version":"v2_fixed_template"}, f, indent=2)

    print(f"\nCOMPLETE: {args.run_name} | Loss: {result.training_loss:.4f}", flush=True)

if __name__ == "__main__":
    main()
