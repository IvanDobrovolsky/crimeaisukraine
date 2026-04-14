#!/usr/bin/env python3
"""Tokenize a Russian academic affiliation string using mT5 tokenizer."""

from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("google/mt5-base")

text = (
    "Крымский федеральный университет им. В.И. Вернадского, "
    "просп. акад. Вернадского, 4, 295007 г. Симферополь, "
    "Республика Крым, Российская Федерация"
)

# ---------- Full tokenization ----------
token_ids = tokenizer.encode(text, add_special_tokens=False)
tokens = tokenizer.convert_ids_to_tokens(token_ids)

print("=" * 80)
print("FULL TEXT:")
print(text)
print("=" * 80)

print(f"\nTotal tokens: {len(tokens)}")
print(f"\n{'Idx':>4}  {'Token ID':>8}  {'Token':<30}  {'Shared?'}")
print("-" * 72)

import unicodedata, re

def is_shared(tok: str) -> str:
    """Return a label if the token consists only of shared characters
    (digits, punctuation, Latin letters, whitespace marker ▁)."""
    clean = tok.replace("▁", "")
    if not clean:
        return "whitespace"
    if all(c.isdigit() for c in clean):
        return "DIGITS"
    if all(c in '.,;:!?-–—()[]{}"\'/\\@#$%^&*+=<>~`' for c in clean):
        return "PUNCT"
    if re.match(r'^[A-Za-z]+$', clean):
        return "LATIN"
    if all(not unicodedata.category(c).startswith('L') or
           'LATIN' in unicodedata.name(c, '') for c in clean):
        # mix of digits/punct/latin
        if any(c.isdigit() for c in clean):
            return "DIGITS+PUNCT"
        return "LATIN+PUNCT"
    return ""

for i, (tid, tok) in enumerate(zip(token_ids, tokens)):
    shared = is_shared(tok)
    marker = f"  <-- {shared}" if shared else ""
    print(f"{i:4d}  {tid:>8}  {tok:<30}{marker}")

# ---------- Sub-phrase breakdowns ----------
phrases = {
    "Республика Крым": "Республика Крым",
    "Российская Федерация": "Российская Федерация",
    "295007 (postal code)": "295007",
    "Симферополь": "Симферополь",
}

for label, phrase in phrases.items():
    ids = tokenizer.encode(phrase, add_special_tokens=False)
    toks = tokenizer.convert_ids_to_tokens(ids)
    print(f"\n{'=' * 60}")
    print(f"SUB-PHRASE: {label}")
    print(f"  Text:   \"{phrase}\"")
    print(f"  Tokens: {len(toks)}")
    print(f"  {'Idx':>4}  {'Token ID':>8}  {'Token'}")
    print(f"  {'-' * 40}")
    for j, (tid, tok) in enumerate(zip(ids, toks)):
        shared = is_shared(tok)
        marker = f"  <-- {shared}" if shared else ""
        print(f"  {j:4d}  {tid:>8}  {tok}{marker}")
    # Also show the decoded round-trip
    print(f"  Decoded: \"{tokenizer.decode(ids)}\"")

print(f"\n{'=' * 80}")
print("SUMMARY OF SHARED (cross-language) TOKENS")
print("=" * 80)
shared_tokens = [(i, tid, tok, is_shared(tok))
                 for i, (tid, tok) in enumerate(zip(token_ids, tokens))
                 if is_shared(tok)]
print(f"Total shared tokens: {len(shared_tokens)} out of {len(tokens)}")
for i, tid, tok, label in shared_tokens:
    print(f"  idx={i:3d}  id={tid:>6}  token={tok!r:<20}  type={label}")
