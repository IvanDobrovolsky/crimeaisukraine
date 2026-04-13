"""
Build the master manifest by aggregating all pipeline outputs.

This is the single source of truth that the site reads. It collects:
- Each pipeline's manifest.json (when present)
- The existing legacy data files (platforms.json, framing.json, etc.)
- LLM audit results from llm_audit_results.json

Output: site/src/data/master_manifest.json

Run: python scripts/build_master_manifest.py
"""

import json
from pathlib import Path
from datetime import datetime

PROJECT = Path(__file__).parent.parent.parent   # _shared → pipelines → project root
PIPELINES = PROJECT / "pipelines"
SITE_DATA = PROJECT / "site/src/data"
DATA = PROJECT / "data"

OUTPUT = SITE_DATA / "master_manifest.json"

PIPELINE_NAMES = [
    "ip", "telecom", "tech_infrastructure", "geodata", "weather",
    "media", "academic", "wikipedia", "institutions", "llm",
]


def load_json(path):
    if not path.exists():
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def main():
    print("Building master manifest...")

    master = {
        "_generated": datetime.now().isoformat()[:19],
        "_description": "Master manifest aggregating all pipeline outputs. Single source of truth for the site.",
        "pipelines": {},
        "legacy": {},
        "summary": {},
    }

    # Per-pipeline manifests
    for name in PIPELINE_NAMES:
        manifest_path = PIPELINES / name / "data" / "manifest.json"
        master["pipelines"][name] = {
            "name": name,
            "readme": f"pipelines/{name}/README.md",
            "manifest": load_json(manifest_path),
            "available": manifest_path.exists(),
        }

    # Legacy data files (existing site data)
    legacy_files = {
        "platforms": load_json(SITE_DATA / "platforms.json"),
        "manifest": load_json(SITE_DATA / "manifest.json"),
        "framing": load_json(SITE_DATA / "framing.json"),
        "llm_audit": load_json(SITE_DATA / "llm_audit_results.json"),
        "llm_models": load_json(SITE_DATA / "llm_models.json"),
        "media_violators": load_json(SITE_DATA / "media_violators.json"),
    }
    master["legacy"] = {k: v for k, v in legacy_files.items() if v is not None}

    # Top-level summary metrics
    if master["legacy"].get("manifest"):
        m = master["legacy"]["manifest"]
        master["summary"]["total_platforms"] = m.get("global", {}).get("total_platforms", 0)
        master["summary"]["total_categories"] = m.get("global", {}).get("total_categories", 0)
        master["summary"]["correct"] = m.get("global", {}).get("by_status", {}).get("correct", 0)
        master["summary"]["incorrect"] = m.get("global", {}).get("by_status", {}).get("incorrect", 0)
        master["summary"]["ambiguous"] = m.get("global", {}).get("by_status", {}).get("ambiguous", 0)

    if master["legacy"].get("framing", {}).get("gdelt"):
        master["summary"]["gdelt_total_articles"] = master["legacy"]["framing"]["gdelt"].get("total_articles", 0)
        master["summary"]["gdelt_llm_endorses"] = master["legacy"]["framing"]["gdelt"].get("llm_endorses_all", 0)
        master["summary"]["gdelt_precision_nonru"] = master["legacy"]["framing"]["gdelt"].get("precision_nonru", 0)

    if master["legacy"].get("framing", {}).get("academic"):
        a = master["legacy"]["framing"]["academic"]
        master["summary"]["academic_total_papers"] = a.get("total_papers", 0)
        master["summary"]["academic_with_signals"] = a.get("with_sovereignty_signals", 0)
        master["summary"]["academic_russia_llm"] = a.get("russia_llm", 0)
        master["summary"]["academic_ukraine_llm"] = a.get("ukraine_llm", 0)

    if master["legacy"].get("llm_audit"):
        la = master["legacy"]["llm_audit"]
        master["summary"]["llm_models_total"] = la.get("summary", {}).get("total_models", 0)
        master["summary"]["llm_models_complete"] = len(la.get("summary", {}).get("models_complete", []))
        master["summary"]["llm_total_queries"] = la.get("summary", {}).get("total_queries", 0)

    # Save
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump(master, f, indent=2, ensure_ascii=False)

    size_kb = OUTPUT.stat().st_size / 1024
    print(f"Master manifest saved: {OUTPUT}")
    print(f"  Size: {size_kb:.1f} KB")
    print(f"  Pipelines: {sum(1 for p in master['pipelines'].values() if p['available'])}/{len(PIPELINE_NAMES)} with manifest")
    print(f"  Legacy data: {len(master['legacy'])} sources")
    print(f"  Summary keys: {len(master['summary'])}")


if __name__ == "__main__":
    main()
