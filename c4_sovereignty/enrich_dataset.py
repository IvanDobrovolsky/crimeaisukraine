#!/usr/bin/env python3
"""
Enrich every row in the multilabel dataset with:
- reasoning: WHY this text carries the labels it does
- regulation_gap: which governance gap applies (Type A, Type B, or None)

Processes all 6,796 rows with rule-based + pattern-matched explanations.
"""
import json, re

def detect_signals(text):
    """Detect specific sovereignty signals in text."""
    t = text.lower()
    signals = []
    
    # Russian designation signals
    if re.search(r'republic of crimea', t): signals.append(('ru_designation', 'Republic of Crimea'))
    if re.search(r'республика крым', t): signals.append(('ru_designation', 'Республика Крым'))
    if re.search(r'крымский федеральн', t): signals.append(('ru_admin', 'Crimean Federal District'))
    if re.search(r'reunifi\w+', t): signals.append(('ru_narrative', 'reunification'))
    if re.search(r'воссоединени', t): signals.append(('ru_narrative', 'воссоединение'))
    if re.search(r'присоединени', t): signals.append(('ru_narrative', 'присоединение'))
    if re.search(r'rejoined russia', t): signals.append(('ru_narrative', 'rejoined Russia'))
    if re.search(r'crimea,?\s*russia', t): signals.append(('ru_location', 'Crimea, Russia'))
    if re.search(r'sevastopol,?\s*russia', t): signals.append(('ru_location', 'Sevastopol, Russia'))
    if re.search(r'симферополь,?\s*росси', t): signals.append(('ru_location', 'Симферополь, Россия'))
    if re.search(r'russian academy of sciences|рас|ras,', t): signals.append(('ru_institution', 'Russian Academy of Sciences'))
    if re.search(r'crimean federal university|крымский федеральный университет', t): signals.append(('ru_institution', 'Crimean Federal University'))
    if re.search(r'referendum', t) and re.search(r'97%|96%|voted', t): signals.append(('ru_narrative', 'referendum claim'))
    
    # Ukrainian designation signals
    if re.search(r'autonomous republic of crimea', t): signals.append(('ua_designation', 'Autonomous Republic of Crimea'))
    if re.search(r'автономна республіка крим', t): signals.append(('ua_designation', 'Автономна Республіка Крим'))
    if re.search(r'автономная республика крым', t): signals.append(('ua_designation', 'Автономная Республика Крым'))
    if re.search(r'annex\w+', t): signals.append(('ua_narrative', 'annexation'))
    if re.search(r'анекс\w+|аннекс\w+', t): signals.append(('ua_narrative', 'анексія/аннексия'))
    if re.search(r'occup\w+|окупац', t): signals.append(('ua_narrative', 'occupation'))
    if re.search(r'illegally', t): signals.append(('ua_narrative', 'illegally'))
    if re.search(r'ua-43', t): signals.append(('ua_standard', 'ISO 3166-2:UA'))
    if re.search(r'crimea,?\s*ukraine', t): signals.append(('ua_location', 'Crimea, Ukraine'))
    if re.search(r'resolution 68/262', t): signals.append(('ua_legal', 'UN GA 68/262'))
    if re.search(r'692/2014', t): signals.append(('ua_legal', 'EU Regulation 692/2014'))
    
    # Attribution signals
    if re.search(r'\bsaid\b|\bstated\b|\bdeclared\b|\bclaimed\b|\bargued\b|\bmaintained\b|\binsisted\b', t): signals.append(('attribution', 'attribution verb'))
    if re.search(r'according to|as reported by|per\s', t): signals.append(('attribution', 'attribution phrase'))
    if re.search(r'заявил|сообщает|по данным|как отмечает', t): signals.append(('attribution', 'attribution (RU)'))
    if re.search(r'reuters|ap\b|bbc|cnn|guardian|nyt|washington post|bloomberg|france24', t): signals.append(('western_outlet', 'Western media'))
    if re.search(r'putin|lavrov|kremlin|peskov|russian (official|foreign|defense|ambassador)', t): signals.append(('ru_source', 'Russian official'))
    if re.search(r'путин|лавров|кремль|песков', t): signals.append(('ru_source', 'Russian official (RU)'))
    
    # Domain signals
    if re.search(r'sputnik|rt\.com|tass|ria\s', t): signals.append(('ru_media', 'Russian state media'))
    if re.search(r'deliver|hotel|booking|weather|forecast|webcam|flight|bus schedule|real estate', t): signals.append(('commercial', 'commercial/service'))
    if re.search(r'university|institute|academy|journal|conference|doi|abstract', t): signals.append(('academic', 'academic context'))
    
    return signals


def generate_reasoning(text, labels, signals):
    """Generate human-readable reasoning for the classification."""
    parts = []
    
    sig_types = {s[0] for s in signals}
    sig_names = {s[1] for s in signals}
    
    if labels['russia_framing']:
        ru_sigs = [s for s in signals if s[0].startswith('ru_')]
        if ru_sigs:
            names = [s[1] for s in ru_sigs]
            if 'ru_designation' in sig_types:
                parts.append(f"Uses Russian administrative designation ({', '.join(s[1] for s in signals if s[0]=='ru_designation')}), which exists in Russian federal law but not in ISO 3166, CLDR, or Library of Congress.")
            if 'ru_narrative' in sig_types:
                terms = [s[1] for s in signals if s[0]=='ru_narrative']
                parts.append(f"Uses Russian sovereignty narrative terminology: {', '.join(terms)}.")
            if 'ru_location' in sig_types:
                parts.append(f"Labels Crimean location under Russian jurisdiction ({', '.join(s[1] for s in signals if s[0]=='ru_location')}).")
            if 'ru_institution' in sig_types:
                parts.append(f"References seized Ukrainian institution under Russian designation ({', '.join(s[1] for s in signals if s[0]=='ru_institution')}).")
        else:
            parts.append("Contains implicit Russian sovereignty framing.")
    
    if labels['ukraine_framing']:
        ua_sigs = [s for s in signals if s[0].startswith('ua_')]
        if ua_sigs:
            if 'ua_narrative' in sig_types:
                terms = [s[1] for s in signals if s[0]=='ua_narrative']
                parts.append(f"Frames Russian control as illegitimate: {', '.join(terms)}.")
            if 'ua_designation' in sig_types:
                parts.append(f"Uses Ukrainian constitutional designation ({', '.join(s[1] for s in signals if s[0]=='ua_designation')}).")
            if 'ua_legal' in sig_types:
                parts.append(f"References international legal framework ({', '.join(s[1] for s in signals if s[0]=='ua_legal')}).")
            if 'ua_standard' in sig_types:
                parts.append(f"Cites international standard ({', '.join(s[1] for s in signals if s[0]=='ua_standard')}).")
    
    if labels['attribution']:
        if 'western_outlet' in sig_types and 'ru_source' in sig_types:
            outlet = [s[1] for s in signals if s[0]=='western_outlet'][0]
            source = [s[1] for s in signals if s[0]=='ru_source'][0]
            parts.append(f"Russian sovereignty claim attributed to {source}, reported by {outlet}. The attribution frame means the text presents the claim as a reported position, not as an editorial assertion — but LLM training treats both identically as token co-occurrences.")
        elif 'attribution' in sig_types:
            parts.append("Contains attribution markers (reported speech), but the sovereignty claim still creates statistical associations in training data.")
    
    if not labels['sovereignty_signal']:
        parts.append("Geographic or historical mention of Crimea without sovereignty framing.")
    
    return " ".join(parts) if parts else "No specific sovereignty signals detected."


def determine_regulation_gap(text, labels, signals):
    """Determine which governance gap applies."""
    sig_types = {s[0] for s in signals}
    
    if not labels['sovereignty_signal']:
        return {"type": "none", "description": "No sovereignty signal — no governance gap applicable."}
    
    if 'academic' in sig_types and labels['russia_framing']:
        return {
            "type": "A",
            "description": "Type A — Standard exists, enforcement absent. ISO 3166-2:UA classifies Crimea as UA-43. CrossRef's DOI schema supports structured country codes. COPE recommends ISO compliance. But CrossRef, Scopus, and Web of Science index affiliations as submitted by publishers without sovereignty verification. The ISSN Centre's 2025 reform is the only enforcement precedent."
        }
    
    if 'commercial' in sig_types and labels['russia_framing']:
        return {
            "type": "B", 
            "description": "Type B — No standard exists. No international standard governs how commercial websites, delivery services, or booking platforms classify disputed territories. GeoNames returns country_code=UA for Crimean cities, but no enforcement mechanism requires downstream services to use it."
        }
    
    if 'ru_media' in sig_types:
        return {
            "type": "B",
            "description": "Type B — No standard exists for training data curation. EU banned RT/Sputnik in March 2022, but Common Crawl has no sanctions filter. The Pravda Network (3.6M articles, 150 domains) launders sanctioned content through fake domains that bypass blocklists. EU AI Act Article 53 does not cover sovereignty framing in training data."
        }
    
    if labels['attribution'] and labels['russia_framing']:
        return {
            "type": "B",
            "description": "Type B — No standard exists. Legitimate media reporting Russian claims creates the same token co-occurrences as direct propaganda. No quality filter, content moderation system, or training data curation standard distinguishes 'X claims Y' from 'Y is true' at the statistical level. This is the vector no existing regulation addresses."
        }
    
    if 'ru_designation' in sig_types or 'ru_location' in sig_types:
        if 'ru_institution' in sig_types:
            return {
                "type": "A",
                "description": "Type A — ISO 3166-2:UA and OFAC (Executive Order 13685) both classify Crimea as Ukrainian. This institution's metadata uses Russian designation, deposited into CrossRef without verification. The standard exists; enforcement is absent."
            }
        return {
            "type": "A+B",
            "description": "Type A (geodata) + Type B (training data). Natural Earth assigns SOVEREIGNT='Russia' to Crimea despite its own 30/31 worldview consensus saying Ukraine (Type A — standard exists, bypassed). This classification propagates into training corpora through web content that inherits the designation (Type B — no training data sovereignty standard)."
        }
    
    if labels['russia_framing']:
        return {
            "type": "B",
            "description": "Type B — No standard governs how pretraining corpora handle sovereignty framing for disputed territories. EU AI Act Article 53 requires training data documentation but addresses copyright and personal data, not territorial sovereignty."
        }
    
    if labels['ukraine_framing']:
        return {
            "type": "none",
            "description": "Correct framing aligned with international law (UN GA 68/262, EU Regulation 692/2014). No governance gap — the text reflects the existing legal consensus."
        }
    
    return {"type": "unknown", "description": "Sovereignty signal detected but governance gap classification uncertain."}


# Process all rows
with open("training_data/multilabel_sovereignty_dataset.jsonl") as f:
    rows = [json.loads(line) for line in f]

print(f"Processing {len(rows)} rows...")

enriched = []
gap_counts = {}
for i, row in enumerate(rows):
    text = row["text"]
    labels = {
        "russia_framing": row["russia_framing"],
        "ukraine_framing": row["ukraine_framing"],
        "attribution": row["attribution"],
        "sovereignty_signal": row["sovereignty_signal"],
    }
    
    signals = detect_signals(text)
    reasoning = generate_reasoning(text, labels, signals)
    gap = determine_regulation_gap(text, labels, signals)
    
    row["reasoning"] = reasoning
    row["regulation_gap"] = gap
    row["detected_signals"] = [{"type": s[0], "value": s[1]} for s in signals]
    enriched.append(row)
    
    gap_type = gap["type"]
    gap_counts[gap_type] = gap_counts.get(gap_type, 0) + 1
    
    if i < 3:
        print(f"\nExample {i+1}:")
        print(f"  Text: {text[:100]}...")
        print(f"  Labels: ru={labels['russia_framing']} ua={labels['ukraine_framing']} attr={labels['attribution']}")
        print(f"  Reasoning: {reasoning[:150]}...")
        print(f"  Gap: {gap['type']} — {gap['description'][:100]}...")

with open("training_data/multilabel_enriched_dataset.jsonl", "w") as f:
    for row in enriched:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

print(f"\n{'='*60}")
print(f"Processed: {len(enriched)} rows")
print(f"\nRegulation gap distribution:")
for k, v in sorted(gap_counts.items(), key=lambda x: -x[1]):
    print(f"  {k:10s}: {v:,} ({v/len(enriched)*100:.1f}%)")
print(f"\nSaved: training_data/multilabel_enriched_dataset.jsonl")
