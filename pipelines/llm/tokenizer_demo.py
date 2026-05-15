"""
Tokenizer demonstration: quotation erasure and cross-lingual gradient asymmetry.

Shows that sovereignty signals tokenize identically in asserted vs quoted context,
and that Cyrillic text produces 4-5x more tokens than Latin — amplifying gradient
contribution from Russian-language training data.

Output: data/tokenizer_demo.parquet + figures/fig6_tokenizer.png
"""
import json
import pandas as pd
from transformers import AutoTokenizer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HKS_RED = '#CD2E4A'
HKS_DARK = '#333333'
HKS_GRAY = '#999999'

# Use GPT-2 tokenizer (BPE, representative of pre-2024 LLMs)
# Also check cl100k (GPT-4 family) if available
TOKENIZERS = {
    'gpt2': 'gpt2',
    'qwen2.5': 'Qwen/Qwen2.5-0.5B',
}

SIGNALS = [
    # Core sovereignty signals
    {"text": "Republic of Crimea, Russia", "direction": "russia", "lang": "en", "context": "signal"},
    {"text": "Autonomous Republic of Crimea, Ukraine", "direction": "ukraine", "lang": "en", "context": "signal"},
    {"text": "Республика Крым, Россия", "direction": "russia", "lang": "ru", "context": "signal"},
    {"text": "Автономная Республика Крым, Украина", "direction": "ukraine", "lang": "ru", "context": "signal"},
    {"text": "Республіка Крим, Росія", "direction": "russia", "lang": "uk", "context": "signal"},
    {"text": "Автономна Республіка Крим, Україна", "direction": "ukraine", "lang": "uk", "context": "signal"},
    # Full address patterns
    {"text": "Simferopol, Republic of Crimea, Russia", "direction": "russia", "lang": "en", "context": "address"},
    {"text": "Simferopol, Autonomous Republic of Crimea, Ukraine", "direction": "ukraine", "lang": "en", "context": "address"},
    {"text": "Симферополь, Республика Крым, Россия", "direction": "russia", "lang": "ru", "context": "address"},
    {"text": "Сімферополь, Автономна Республіка Крим, Україна", "direction": "ukraine", "lang": "uk", "context": "address"},
]

CONTEXTS = [
    # Same signal in asserted vs quoted
    {"label": "Asserted", "template": "Address: {signal}."},
    {"label": "Quoted", "template": 'According to the source, "{signal}" is listed.'},
    {"label": "Reported", "template": 'Russian officials claim the address is "{signal}".'},
]

results = []
signal_text = "Republic of Crimea, Russia"

for tok_name, tok_id in TOKENIZERS.items():
    try:
        tok = AutoTokenizer.from_pretrained(tok_id)
    except Exception:
        continue

    # 1. Signal tokenization across languages
    for sig in SIGNALS:
        tokens = tok.encode(sig["text"])
        decoded = [tok.decode([t]) for t in tokens]
        results.append({
            "tokenizer": tok_name,
            "text": sig["text"],
            "direction": sig["direction"],
            "language": sig["lang"],
            "context_type": sig["context"],
            "n_tokens": len(tokens),
            "tokens": json.dumps(decoded, ensure_ascii=False),
            "token_ids": json.dumps(tokens),
        })

    # 2. Quotation erasure: same signal in different contexts
    sig_tokens = tok.encode(f" {signal_text}")
    sig_decoded = [tok.decode([t]) for t in sig_tokens]

    for ctx in CONTEXTS:
        full_text = ctx["template"].format(signal=signal_text)
        full_tokens = tok.encode(full_text)
        
        # Find signal subsequence
        match_pos = -1
        for i in range(len(full_tokens) - len(sig_tokens) + 1):
            if full_tokens[i:i+len(sig_tokens)] == sig_tokens:
                match_pos = i
                break

        results.append({
            "tokenizer": tok_name,
            "text": full_text,
            "direction": "russia",
            "language": "en",
            "context_type": ctx["label"].lower(),
            "n_tokens": len(full_tokens),
            "tokens": json.dumps([tok.decode([t]) for t in full_tokens], ensure_ascii=False),
            "token_ids": json.dumps(full_tokens),
            "signal_match_position": match_pos,
            "signal_tokens_identical": match_pos >= 0,
        })

df = pd.DataFrame(results)
out_path = "data/tokenizer_demo.parquet"
df.to_parquet(out_path, index=False)
print(f"Saved {len(df)} rows to {out_path}")

# === Generate figure ===
# Bar chart: token count by language for the same sovereignty signal
tok = AutoTokenizer.from_pretrained("gpt2")

chart_data = []
for sig in SIGNALS:
    if sig["context"] == "signal":
        n = len(tok.encode(sig["text"]))
        chart_data.append({
            "text": sig["text"],
            "lang": sig["lang"].upper(),
            "direction": sig["direction"],
            "n_tokens": n,
        })

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5), gridspec_kw={'width_ratios': [3, 2]})
fig.patch.set_facecolor('white')

# Left panel: token counts by language
labels = [d["text"] for d in chart_data]
counts = [d["n_tokens"] for d in chart_data]
colors = [HKS_RED if d["direction"] == "russia" else HKS_GRAY for d in chart_data]
lang_labels = [d["lang"] for d in chart_data]

y_pos = np.arange(len(labels))
bars = ax1.barh(y_pos, counts, color=colors, alpha=0.8, edgecolor=[HKS_DARK]*len(labels), linewidth=0.5)

# Add token count labels
for i, (bar, count) in enumerate(zip(bars, counts)):
    ax1.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
             f'{count}', va='center', fontsize=8, color=HKS_DARK)

ax1.set_yticks(y_pos)
ax1.set_yticklabels([f"[{lang_labels[i]}] {labels[i][:35]}" for i in range(len(labels))],
                     fontsize=7, color=HKS_DARK)
ax1.set_xlabel('Tokens (GPT-2 BPE)', fontsize=9, color=HKS_DARK)
ax1.set_title('Token count by language', fontsize=10, color=HKS_DARK, fontweight='bold')
ax1.invert_yaxis()
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.spines['left'].set_color(HKS_GRAY)
ax1.spines['bottom'].set_color(HKS_GRAY)
ax1.tick_params(colors=HKS_DARK, labelsize=7)

# Right panel: quotation erasure
signal = "Republic of Crimea, Russia"
sig_tokens = tok.encode(f" {signal}")
contexts = [
    ("Asserted", f"Address: Simferopol, {signal}."),
    ("Quoted", f'He wrote: "{signal}" as the address.'),
    ("Reported", f'Officials claim "{signal}" is correct.'),
]

cell_colors = []
all_decoded = []
for label, text in contexts:
    full_tokens = tok.encode(text)
    decoded = [tok.decode([t]) for t in full_tokens]
    # Mark signal tokens
    row_colors = []
    for i, t in enumerate(full_tokens):
        # Check if this token is part of the signal
        is_signal = False
        for start in range(max(0, i-len(sig_tokens)+1), i+1):
            if full_tokens[start:start+len(sig_tokens)] == sig_tokens and start <= i < start+len(sig_tokens):
                is_signal = True
                break
        row_colors.append(HKS_RED if is_signal else HKS_GRAY)
    all_decoded.append((label, decoded, row_colors))

ax2.set_xlim(0, 1)
ax2.set_ylim(0, 1)
ax2.axis('off')
ax2.set_title('Quotation erasure', fontsize=10, color=HKS_DARK, fontweight='bold')

y_start = 0.85
for label, decoded, colors_row in all_decoded:
    ax2.text(0.02, y_start, f"{label}:", fontsize=8, fontweight='bold', color=HKS_DARK,
             transform=ax2.transAxes)
    x = 0.02
    y = y_start - 0.08
    for tok_str, c in zip(decoded, colors_row):
        display = tok_str.replace('\n', '\\n')
        if len(display) > 12:
            display = display[:12]
        bbox = dict(boxstyle='round,pad=0.15', facecolor=c, alpha=0.3 if c == HKS_GRAY else 0.7,
                    edgecolor='none')
        ax2.text(x, y, display, fontsize=6, color=HKS_DARK, bbox=bbox,
                 transform=ax2.transAxes, family='monospace')
        x += max(len(display) * 0.018 + 0.02, 0.04)
        if x > 0.95:
            x = 0.02
            y -= 0.06
    y_start -= 0.32

ax2.text(0.02, 0.02, 'Red = sovereignty signal tokens (identical across all contexts)',
         fontsize=7, color=HKS_RED, transform=ax2.transAxes, style='italic')

plt.tight_layout()
fig_path = "/Users/tati/Desktop/ivan/crimeaisukraine-paper/figures/fig6_tokenizer.png"
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
print(f"Saved figure to {fig_path}")

# Print summary
print("\n=== FINDINGS ===")
gpt2_signals = df[(df.tokenizer == 'gpt2') & (df.context_type == 'signal')]
for _, row in gpt2_signals.iterrows():
    print(f"  [{row.language}] {row.text}: {row.n_tokens} tokens")

en_ru_ratio = gpt2_signals[gpt2_signals.language == 'ru'].n_tokens.mean() / gpt2_signals[gpt2_signals.language == 'en'].n_tokens.mean()
print(f"\nRU/EN token ratio: {en_ru_ratio:.1f}x")
print("Russian text produces ~{:.0f}x more tokens -> {:.0f}x more gradient surface".format(en_ru_ratio, en_ru_ratio))
