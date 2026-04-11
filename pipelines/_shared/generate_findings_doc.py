"""
Generate docs/FINDINGS.md from platforms.json — all 116 findings in one place.
Rerun after any data change: python scripts/generate_findings_doc.py
"""

import json
from pathlib import Path
from datetime import datetime

PROJECT = Path(__file__).parent.parent.parent   # _shared → pipelines → project root

with open(PROJECT / "site/src/data/platforms.json") as f:
    data = json.load(f)
with open(PROJECT / "site/src/data/manifest.json") as f:
    manifest = json.load(f)

findings = data["findings"]
by_status = manifest["global"]["by_status"]
total = len(findings)

CAT_NAMES = {
    "weather": "Weather Services",
    "data_visualization": "Data Visualization Libraries",
    "open_source": "Open Source Geographic Data",
    "map_service": "Map Services & Geocoding",
    "tech_infrastructure": "Tech Infrastructure",
    "telecom": "Internet & Telecommunications",
    "reference": "Reference & News Media",
    "ip_geolocation": "IP Geolocation",
    "travel": "Travel & Booking",
    "search_engine": "Search Engines",
}

CAT_ORDER = [
    "open_source", "data_visualization", "map_service", "weather",
    "tech_infrastructure", "telecom", "ip_geolocation",
    "reference", "travel", "search_engine",
]

STATUS_ICON = {
    "correct": "✅", "incorrect": "❌", "ambiguous": "⚠️",
    "blocked": "🚫", "n/a": "➖",
}

lines = []
lines.append(f"# All Findings ({total} platforms)")
lines.append("")
lines.append(f"*Auto-generated {datetime.now().strftime('%Y-%m-%d')} from `platforms.json`.*")
lines.append(f"*Regenerate: `python pipelines/_shared/generate_findings_doc.py`*")
lines.append("")
lines.append(f"| Status | Count |")
lines.append(f"|--------|-------|")
for s in ["correct", "incorrect", "ambiguous", "blocked", "n/a"]:
    lines.append(f"| {STATUS_ICON.get(s,'')} {s.title()} | {by_status.get(s, 0)} |")
lines.append(f"| **Total** | **{total}** |")
lines.append("")
lines.append("---")

for cat in CAT_ORDER:
    cat_findings = [f for f in findings if f["category"] == cat]
    if not cat_findings:
        continue

    cat_name = CAT_NAMES.get(cat, cat)
    correct = sum(1 for f in cat_findings if f["status"] == "correct")
    incorrect = sum(1 for f in cat_findings if f["status"] == "incorrect")
    ambiguous = sum(1 for f in cat_findings if f["status"] == "ambiguous")

    lines.append("")
    lines.append(f"## {cat_name} ({len(cat_findings)})")
    lines.append("")
    lines.append(f"✅ {correct} correct | ❌ {incorrect} incorrect | ⚠️ {ambiguous} ambiguous")
    lines.append("")
    lines.append(f"| Status | Platform | Detail | Evidence | URL |")
    lines.append(f"|--------|----------|--------|----------|-----|")

    # Sort: incorrect first, then ambiguous, then correct
    status_order = {"incorrect": 0, "ambiguous": 1, "blocked": 2, "n/a": 3, "correct": 4}
    cat_findings.sort(key=lambda f: status_order.get(f["status"], 5))

    for f in cat_findings:
        icon = STATUS_ICON.get(f["status"], "")
        platform = f["platform"]
        detail = f.get("detail", "").replace("|", "\\|").replace("\n", " ")
        if len(detail) > 150:
            detail = detail[:150] + "..."
        evidence = f.get("evidence", "").replace("|", "\\|").replace("\n", " ")
        if len(evidence) > 100:
            evidence = evidence[:100] + "..."
        url = f.get("url", "")
        url_md = f"[link]({url})" if url else ""
        lines.append(f"| {icon} | {platform} | {detail} | {evidence} | {url_md} |")

lines.append("")
lines.append("---")
lines.append("")
lines.append(f"*{total} findings across {len(CAT_ORDER)} categories. All checks automated and reproducible via `make all`.*")

output = PROJECT / "docs" / "FINDINGS.md"
output.parent.mkdir(exist_ok=True)
with open(output, "w") as f:
    f.write("\n".join(lines))

print(f"Generated {output} ({len(lines)} lines, {total} findings)")
