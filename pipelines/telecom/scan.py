"""
Telecom operators Crimea sovereignty audit.

This pipeline is a **curation pipeline**, not a live scanner. It reads the
11 hand-researched telecom findings from the master platforms.json database
and produces pipelines/telecom/data/manifest.json in the standard pipeline
schema so that the master manifest builder and the site can consume it.

Each of the 11 findings was manually researched from public sources (RIPE
NCC records, TeleGeography submarine cable map, operator coverage pages,
Reuters / Kyiv Post reporting). The provenance and date_checked for each
finding are preserved in the manifest.

For a live RIPE STAT API + E.164 + TeleGeography scanner, see the
`pipeline-telecom-live` follow-up work. Current scope is to faithfully
surface the curated findings.

Usage:
    cd pipelines/telecom && uv run scan.py
    # or from project root:
    make pipeline-telecom
"""

import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).parent
DATA = PROJECT / "data"
DATA.mkdir(exist_ok=True)
REPO_ROOT = PROJECT.parent.parent
PLATFORMS_JSON = REPO_ROOT / "site/src/data/platforms.json"


def main():
    with open(PLATFORMS_JSON) as f:
        findings = [
            row for row in json.load(f)["findings"]
            if row.get("category") == "telecom"
        ]

    buckets: dict[str, int] = {}
    for row in findings:
        s = row.get("status", "unknown")
        buckets[s] = buckets.get(s, 0) + 1

    total = len(findings)

    def pct(n):
        return round(100 * n / total, 1) if total else 0

    key_findings = [
        (
            "All 3 Ukrainian mobile operators (Kyivstar, Vodafone Ukraine, lifecell) "
            "withdrew from Crimea by October 2015. They are classified `n/a` — "
            "the services no longer exist in Crimea — not `incorrect` and not `blocked`. "
            "The distinction matters: withdrawal is a Ukrainian operator decision under "
            "occupation, not a sovereignty claim about Crimea being Russian."
        ),
        (
            "4 telecom entities operate in Crimea under Russian regulation and are "
            "classified `incorrect`: K-Telecom (Win Mobile, the de-facto monopoly "
            "operator since August 2014), RIPE NCC (which permitted the UA→RU ASN "
            "re-registrations under transfer policy ripe-733 without sovereignty "
            "review), the Kerch Strait submarine cable (laid by Rostelecom in 2014), "
            "and Miranda-Media (Rostelecom's Crimean data subsidiary, AS201776 "
            "registered as RU from July 2014)."
        ),
        (
            "3 services are `blocked` in Crimea: Starlink (SpaceX geofence, OFAC "
            "compliance), Netflix (OFAC since 2014), Speedtest.net / Ookla (blocked "
            "in Russia by Roskomnadzor as of July 2025). 'Blocked' here means the "
            "service is actively prevented from operating, not withdrawn by its "
            "operator."
        ),
        (
            "1 service is `correct`: the `.crimea.ua` subdomain is active under "
            "Ukraine's .ua ccTLD, managed by Hostmaster.ua — an infrastructural "
            "assertion of Ukrainian sovereignty that has survived since before 2014."
        ),
        (
            "Status taxonomy: `n/a` = operator withdrew (service gone). "
            "`incorrect` = service operates in Crimea under Russian regulation. "
            "`blocked` = service prevented by sanctions or state action. "
            "`correct` = operates per Ukrainian jurisdiction. These are NOT "
            "interchangeable — conflating `n/a` with `blocked` would misrepresent "
            "the withdrawn Ukrainian operators as victims of sanctions rather than "
            "as operators that left under occupation."
        ),
    ]

    limitations = [
        "Curation pipeline: findings are hand-researched from public sources, "
        "not produced by a live scanner. Live RIPE STAT API / E.164 / "
        "TeleGeography probes are planned as a follow-up.",
        "Cannot directly query Russian operator coverage databases (sanctioned, "
        "requires Russian-IP access + manual browser session).",
        "Submarine cable data is from public sources via TeleGeography; not all "
        "regional cables are mapped.",
        "Ukrainian operators no longer publish Crimean coverage information "
        "(withdrawn), so current state is documented from withdrawal announcements.",
        "WHOIS records can be edited by holders without external review, so "
        "RIPE NCC reassignment dates reflect the state at the date_checked "
        "timestamp in each finding.",
    ]

    manifest = {
        "pipeline": "telecom",
        "version": "2.0",
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "method": "curated_findings + platforms_json",
        "summary": {
            "total_services": total,
            "correct": buckets.get("correct", 0),
            "incorrect": buckets.get("incorrect", 0),
            "na_withdrew": buckets.get("n/a", 0),
            "blocked_by_sanctions": buckets.get("blocked", 0),
            "correct_pct": pct(buckets.get("correct", 0)),
            "incorrect_pct": pct(buckets.get("incorrect", 0)),
            "na_pct": pct(buckets.get("n/a", 0)),
            "blocked_pct": pct(buckets.get("blocked", 0)),
        },
        "findings": findings,
        "key_findings": key_findings,
        "limitations": limitations,
    }

    out = DATA / "manifest.json"
    with open(out, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"Telecom pipeline — wrote {total} findings to {out}")
    print(f"  correct:    {buckets.get('correct', 0)}")
    print(f"  incorrect:  {buckets.get('incorrect', 0)}")
    print(f"  n/a:        {buckets.get('n/a', 0)}")
    print(f"  blocked:    {buckets.get('blocked', 0)}")


if __name__ == "__main__":
    main()
