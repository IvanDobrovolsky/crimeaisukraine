"""
Crimea Digital Sovereignty Audit Framework

Systematic classification of how digital platforms represent Crimea's sovereignty.
Each finding is stored as a structured record with reproducibility metadata.
"""

import json
import os
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent   # _shared → pipelines → project root
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"

AUDIT_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")


class SovereigntyStatus(str, Enum):
    """How a platform represents Crimea's sovereignty."""
    CORRECT = "correct"          # Shows Crimea as Ukraine
    AMBIGUOUS = "ambiguous"      # Disputed/no label/configurable
    INCORRECT = "incorrect"      # Shows Crimea as Russia
    BLOCKED = "blocked"          # Service unavailable in Crimea (sanctions)
    NOT_APPLICABLE = "n/a"       # Platform doesn't show country data


class PlatformCategory(str, Enum):
    MAP_SERVICE = "map_service"
    TRAVEL = "travel"
    WEATHER = "weather"
    SOCIAL_MEDIA = "social_media"
    SPORTS = "sports"
    NEWS_MEDIA = "news_media"
    REFERENCE = "reference"
    OPEN_SOURCE = "open_source"
    DATA_VIZ = "data_visualization"
    GAMING = "gaming"
    IP_GEOLOCATION = "ip_geolocation"
    TECH_INFRA = "tech_infrastructure"
    SEARCH_ENGINE = "search_engine"


class AuditMethod(str, Enum):
    MANUAL = "manual"                # Human checked the platform
    AUTOMATED_API = "automated_api"  # Script queried an API
    AUTOMATED_DATA = "automated_data"  # Script inspected data files
    SOURCE_CODE = "source_code"      # Inspected source code/GitHub


def create_finding(
    platform: str,
    category: PlatformCategory,
    status: SovereigntyStatus,
    method: AuditMethod,
    detail: str,
    url: str = "",
    evidence: str = "",
    notes: str = "",
) -> dict:
    """Create a standardized audit finding record."""
    return {
        "platform": platform,
        "category": category.value,
        "status": status.value,
        "status_icon": {
            "correct": "\u2705",
            "ambiguous": "\u26a0\ufe0f",
            "incorrect": "\u274c",
            "blocked": "\U0001f6ab",
            "n/a": "\u2796",
        }[status.value],
        "method": method.value,
        "detail": detail,
        "url": url,
        "evidence": evidence,
        "notes": notes,
        "date_checked": AUDIT_DATE,
    }


class AuditDatabase:
    """JSON-backed database of audit findings."""

    def __init__(self, path: Path = DATA_DIR / "platforms.json"):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            with open(self.path) as f:
                self.data = json.load(f)
        else:
            self.data = {
                "metadata": {
                    "project": "Crimea Digital Sovereignty Audit",
                    "author": "Ivan Dobrovolsky",
                    "created": AUDIT_DATE,
                    "last_updated": AUDIT_DATE,
                    "description": (
                        "Systematic audit of how digital platforms represent "
                        "Crimea's sovereignty status"
                    ),
                },
                "findings": [],
                "summary": {},
            }

    def add(self, finding: dict):
        """Add a finding, replacing any existing entry for same platform+category."""
        self.data["findings"] = [
            f for f in self.data["findings"]
            if not (f["platform"] == finding["platform"]
                    and f["category"] == finding["category"])
        ]
        self.data["findings"].append(finding)
        self._update_summary()

    def add_batch(self, findings: list[dict]):
        for f in findings:
            self.add(f)

    def _update_summary(self):
        from collections import Counter
        status_counts = Counter(f["status"] for f in self.data["findings"])
        category_counts = Counter(f["category"] for f in self.data["findings"])
        self.data["summary"] = {
            "total_platforms": len(self.data["findings"]),
            "by_status": dict(status_counts),
            "by_category": dict(category_counts),
            "last_updated": AUDIT_DATE,
        }

    def save(self):
        self.data["metadata"]["last_updated"] = AUDIT_DATE
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def get_by_category(self, category: PlatformCategory) -> list[dict]:
        return [f for f in self.data["findings"]
                if f["category"] == category.value]

    def to_markdown_table(self, findings: list[dict] | None = None) -> str:
        """Render findings as a markdown table."""
        findings = findings or self.data["findings"]
        if not findings:
            return "*No findings yet.*"

        lines = [
            "| Status | Platform | Category | Detail | Date |",
            "|--------|----------|----------|--------|------|",
        ]
        for f in sorted(findings, key=lambda x: (x["category"], x["platform"])):
            lines.append(
                f"| {f['status_icon']} | {f['platform']} | {f['category']} "
                f"| {f['detail'][:80]} | {f['date_checked']} |"
            )
        return "\n".join(lines)


def generate_category_report(db: AuditDatabase, category: PlatformCategory,
                              title: str) -> str:
    """Generate a markdown report for a single category."""
    findings = db.get_by_category(category)
    correct = [f for f in findings if f["status"] == "correct"]
    ambiguous = [f for f in findings if f["status"] == "ambiguous"]
    incorrect = [f for f in findings if f["status"] == "incorrect"]
    blocked = [f for f in findings if f["status"] == "blocked"]

    lines = [
        f"# {title}",
        f"\n**Audit date:** {AUDIT_DATE}",
        f"**Platforms checked:** {len(findings)}",
        f"**Correct:** {len(correct)} | **Ambiguous:** {len(ambiguous)} "
        f"| **Incorrect:** {len(incorrect)} | **Blocked:** {len(blocked)}",
        "\n---\n",
    ]

    for status_label, group in [
        ("Incorrect (shows Crimea as Russia)", incorrect),
        ("Ambiguous (disputed/no label)", ambiguous),
        ("Correct (shows Crimea as Ukraine)", correct),
        ("Blocked (service unavailable)", blocked),
    ]:
        if group:
            lines.append(f"## {status_label}\n")
            for f in group:
                lines.append(f"### {f['platform']}")
                lines.append(f"- **Status:** {f['status_icon']} {f['status']}")
                lines.append(f"- **Detail:** {f['detail']}")
                if f.get("url"):
                    lines.append(f"- **URL:** {f['url']}")
                if f.get("evidence"):
                    lines.append(f"- **Evidence:** {f['evidence']}")
                if f.get("notes"):
                    lines.append(f"- **Notes:** {f['notes']}")
                lines.append(f"- **Method:** {f['method']}")
                lines.append(f"- **Date:** {f['date_checked']}")
                lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    db = AuditDatabase()
    print(f"Audit database: {db.path}")
    print(f"Findings: {len(db.data['findings'])}")
    print(f"Date: {AUDIT_DATE}")
