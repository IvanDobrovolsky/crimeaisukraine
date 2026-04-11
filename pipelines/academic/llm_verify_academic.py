"""
LLM verification for academic papers only — runs in parallel with media verification.
Uses title + abstract for context.

Usage:
    ANTHROPIC_API_KEY=... python scripts/llm_verify_academic.py
"""

import json
import time
import urllib.request
from pathlib import Path
from datetime import datetime

PROJECT = Path(__file__).parent.parent
DATA = PROJECT / "data"
ANTHROPIC_API = "https://api.anthropic.com/v1/messages"


def verify(title, abstract, signals, journal, original_label, api_key):
    signals_str = ", ".join(signals[:3])
    abstract_text = f"\nAbstract: {abstract[:800]}\n" if abstract else ""

    prompt = f"""Analyze this academic paper for Crimea sovereignty framing.

Title: {title}
Journal: {journal}
Regex-detected signals: {signals_str}
Regex classification: {original_label}
{abstract_text}
Question: How does this paper frame Crimea's sovereignty? Consider:
- Does it treat Crimea as Ukrainian territory (e.g., "Crimea, Ukraine", "annexed Crimea", "occupied territory")?
- Does it treat Crimea as Russian territory (e.g., "Republic of Crimea, Russia", "reunification", research conducted in Russia's Crimea)?
- Is it analyzing/reporting on the conflict without taking a position?

Respond with EXACTLY one of:
- UKRAINE: Frames Crimea as Ukrainian territory or acknowledges annexation/occupation.
- RUSSIA: Treats Crimea as Russian territory, uses Russian administrative names as default.
- ANALYZES: Discusses the conflict academically without endorsing either position.
- UNCLEAR: Cannot determine from title/abstract.

Then one sentence explaining why."""

    body = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 100,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    req = urllib.request.Request(ANTHROPIC_API, data=body, headers={
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    })

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            text = data["content"][0]["text"].strip()
            upper = text.upper()[:20]
            if "UKRAINE" in upper:
                return {"verdict": "ukraine", "explanation": text}
            elif "RUSSIA" in upper:
                return {"verdict": "russia", "explanation": text}
            elif "ANALYZ" in upper:
                return {"verdict": "analyzes", "explanation": text}
            else:
                return {"verdict": "unclear", "explanation": text}
    except Exception as e:
        return {"verdict": "error", "explanation": str(e)}


def main():
    import os
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("Set ANTHROPIC_API_KEY")
        return

    with open(DATA / "llm_academic_queue.json") as f:
        papers = json.load(f)

    output_path = DATA / "llm_academic_results.jsonl"

    # Resume support
    done = set()
    if output_path.exists():
        with open(output_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line.strip(): continue
                try:
                    done.add(json.loads(line).get("url", ""))
                except: pass

    to_verify = [p for p in papers if p.get("url", "") not in done]
    print(f"Academic: {len(to_verify)} to verify ({len(done)} already done)")

    outf = open(output_path, "a")
    stats = {"endorses": 0, "analyzes": 0, "unclear": 0, "error": 0}

    for i, paper in enumerate(to_verify):
        title = paper.get("title", "")
        abstract = paper.get("abstract", "")
        signals = paper.get("signals", [])
        journal = paper.get("domain", "")

        original_label = paper.get("label", "")
        result = verify(title, abstract, signals, journal, original_label, api_key)
        v = result["verdict"]
        stats[v] = stats.get(v, 0) + 1

        row = {
            "url": paper.get("url", ""),
            "title": title,
            "journal": journal,
            "source": "academic",
            "original_label": paper.get("label", "russia"),
            "llm_verdict": v,
            "llm_explanation": result["explanation"],
            "has_abstract": bool(abstract),
        }
        outf.write(json.dumps(row, ensure_ascii=False) + "\n")
        outf.flush()

        if (i + 1) % 20 == 0:
            print(f"  [{i+1}/{len(to_verify)}] {stats}")

        time.sleep(0.5)

    outf.close()
    print(f"\nDone: {stats}")
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
