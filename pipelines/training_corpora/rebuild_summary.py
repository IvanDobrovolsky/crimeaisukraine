"""
Rebuild training_corpora_summary.json from training_corpora_scan.jsonl.

The scan.py writer appends to scan.jsonl but overwrites summary.json with
only the current session's results. If you run a single corpus after a
full scan, the summary loses everything except that one corpus. This
utility reconstructs the summary from the source of truth (scan.jsonl).
"""

import ast
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

import ast
_SCAN_SRC = (Path(__file__).parent / "scan.py").read_text()
_TREE = ast.parse(_SCAN_SRC)
CORPORA = next(
    ast.literal_eval(node.value)
    for node in ast.walk(_TREE)
    if isinstance(node, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == "CORPORA" for t in node.targets)
)

PROJECT = Path(__file__).parent.parent.parent
DATA = PROJECT / "data"
SCAN_PATH = DATA / "training_corpora_scan.jsonl"
SUMMARY_PATH = DATA / "training_corpora_summary.json"


def rebuild():
    corpus_meta = {c["name"]: c for c in CORPORA}
    stats = defaultdict(lambda: {
        "ukraine": 0, "russia": 0, "disputed": 0, "no_signal": 0,
        "crimea_mentions": 0, "max_doc_idx": 0,
    })

    with open(SCAN_PATH) as f:
        for line in f:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            name = row["corpus"]
            s = stats[name]
            s[row["label"]] = s.get(row["label"], 0) + 1
            s["crimea_mentions"] += 1
            s["max_doc_idx"] = max(s["max_doc_idx"], row.get("doc_idx", 0))

    results = []
    for name, s in stats.items():
        meta = corpus_meta.get(name, {})
        crimea = s["crimea_mentions"]
        results.append({
            "corpus": name,
            "hf_dataset": meta.get("hf"),
            "config": meta.get("config"),
            "models_using": meta.get("models", []),
            "total_scanned": s["max_doc_idx"],  # last doc_idx reached = best estimate
            "crimea_mentions": crimea,
            "ukraine_frame": s["ukraine"],
            "russia_frame": s["russia"],
            "disputed": s["disputed"],
            "no_signal": s["no_signal"],
            "russia_pct": round(100 * s["russia"] / max(crimea, 1), 1),
            "ukraine_pct": round(100 * s["ukraine"] / max(crimea, 1), 1),
        })

    results.sort(key=lambda r: r["corpus"])

    with open(SUMMARY_PATH, "w") as f:
        json.dump({
            "date": datetime.now().isoformat()[:19],
            "rebuilt_from": str(SCAN_PATH.name),
            "results": results,
        }, f, indent=2, ensure_ascii=False)

    print(f"Rebuilt {SUMMARY_PATH.name} from {SCAN_PATH.name}")
    print(f"\n{'corpus':25s} {'docs':>10s} {'crimea':>8s} {'UA':>6s} {'RU':>6s} {'RU%':>6s}")
    print("-" * 70)
    for r in results:
        print(f"{r['corpus']:25s} {r['total_scanned']:>10,} {r['crimea_mentions']:>8,} "
              f"{r['ukraine_frame']:>6d} {r['russia_frame']:>6d} {r['russia_pct']:>5.1f}%")


if __name__ == "__main__":
    rebuild()
