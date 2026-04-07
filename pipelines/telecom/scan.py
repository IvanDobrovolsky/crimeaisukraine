"""Telecom Crimea audit. Currently uses platforms.json findings filtered to category=telecom."""
import json
import sys
from pathlib import Path

def main():
    project_root = Path(__file__).parent.parent.parent
    with open(project_root / "site/src/data/platforms.json") as f:
        data = json.load(f)
    findings = [f for f in data["findings"] if f.get("category") == "telecom"]
    out = {"pipeline": "telecom", "total": len(findings), "findings": findings}
    out_path = Path(__file__).parent / "data/manifest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(findings)} findings to {out_path}")

if __name__ == "__main__":
    main()
