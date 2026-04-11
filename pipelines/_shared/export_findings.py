"""
Export findings to CSV for paper tables and analysis.

Usage:
    python scripts/export_findings.py
"""

import csv
import json
from pathlib import Path

from audit_framework import DATA_DIR

def export_csv():
    """Export findings database to CSV."""
    with open(DATA_DIR / "platforms.json") as f:
        data = json.load(f)

    findings = data["findings"]
    outpath = DATA_DIR / "findings.csv"

    with open(outpath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "platform", "category", "status", "status_icon",
            "method", "detail", "url", "evidence", "notes", "date_checked",
        ])
        writer.writeheader()
        for finding in sorted(findings, key=lambda x: (x["category"], x["platform"])):
            writer.writerow(finding)

    print(f"Exported {len(findings)} findings to {outpath}")

    # Also export propagation data
    prop_path = DATA_DIR / "propagation.json"
    if prop_path.exists():
        with open(prop_path) as f:
            prop = json.load(f)

        outpath2 = DATA_DIR / "propagation.csv"
        all_packages = prop.get("npm_packages", []) + prop.get("python_packages", [])
        with open(outpath2, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "package", "ecosystem", "tier", "desc",
                "contains_ne_data", "weekly", "monthly",
                "dependent_packages", "dependent_repos", "stars",
            ])
            writer.writeheader()
            for pkg in all_packages:
                writer.writerow({
                    "package": pkg.get("package"),
                    "ecosystem": pkg.get("ecosystem"),
                    "tier": pkg.get("tier"),
                    "desc": pkg.get("desc"),
                    "contains_ne_data": pkg.get("contains_ne_data"),
                    "weekly": pkg.get("weekly", 0),
                    "monthly": pkg.get("monthly", 0),
                    "dependent_packages": pkg.get("dependent_packages", 0),
                    "dependent_repos": pkg.get("dependent_repos", 0),
                    "stars": pkg.get("stars", 0),
                })
        print(f"Exported propagation data to {outpath2}")

    # Print summary statistics
    print(f"\n{'='*50}")
    print("SUMMARY STATISTICS FOR PAPER")
    print(f"{'='*50}")
    print(f"Total platforms/services audited: {len(findings)}")

    by_status = {}
    for f_item in findings:
        s = f_item["status"]
        by_status[s] = by_status.get(s, 0) + 1
    for s, c in sorted(by_status.items()):
        icon = {"correct": "✅", "incorrect": "❌", "ambiguous": "⚠️",
                "blocked": "🚫", "n/a": "➖"}.get(s, "?")
        print(f"  {icon} {s}: {c}")

    by_cat = {}
    for f_item in findings:
        c = f_item["category"]
        by_cat[c] = by_cat.get(c, 0) + 1
    print(f"\nBy category:")
    for c, count in sorted(by_cat.items()):
        print(f"  {c}: {count}")

    if prop_path.exists():
        totals = prop.get("totals", {})
        print(f"\nPropagation metrics:")
        print(f"  npm weekly downloads (Tier 1-2, with NE data): "
              f"{totals.get('npm_tier12_weekly_downloads', 0):,}")
        print(f"  npm weekly downloads (all geo): "
              f"{totals.get('npm_all_weekly_downloads', 0):,}")
        print(f"  Dependent packages: "
              f"{totals.get('total_dependent_packages', 0):,}")
        print(f"  Dependent repos: "
              f"{totals.get('total_dependent_repos', 0):,}")


if __name__ == "__main__":
    export_csv()
