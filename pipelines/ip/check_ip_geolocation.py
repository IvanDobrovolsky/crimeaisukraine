"""
IP Geolocation Crimea Checker

Tests known Crimean IP address ranges against free geolocation APIs
to determine which country they resolve to.

Crimean IP ranges were allocated by RIPE NCC to Ukrainian organizations
pre-2014, but many were re-registered under Russian entities after annexation.

Usage:
    python scripts/check_ip_geolocation.py
"""

import json
import time
from pathlib import Path

import requests

from audit_framework import (
    AuditDatabase,
    AuditMethod,
    PlatformCategory,
    SovereigntyStatus,
    create_finding,
)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "CrimeaSovereigntyAudit/1.0 (research)"})

# Known Crimean IP ranges and their context
# Sources: RIPE NCC database, Kentik research
CRIMEAN_TEST_IPS = {
    # Ukrainian ISPs that operated in Crimea pre-2014
    "91.207.56.1": {
        "desc": "CrimeaCom (Ukrainian ISP, AS48031)",
        "pre2014": "UA",
    },
    "176.104.32.1": {
        "desc": "SevStar (Sevastopol ISP, AS56485)",
        "pre2014": "UA",
    },
    "46.63.0.1": {
        "desc": "Sim-Telecom (Simferopol, AS198948)",
        "pre2014": "UA",
    },
    # Russian telecom operators that expanded into Crimea post-2014
    "83.149.22.1": {
        "desc": "Miranda-Media (Crimean ISP, AS201776)",
        "pre2014": "N/A (post-2014 entity)",
    },
}


def check_ip_api(ip: str) -> dict | None:
    """Check IP against ip-api.com (free, no key required, 45 req/min)."""
    url = f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,regionName,city,isp,org,as,query"
    try:
        resp = SESSION.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def check_ipinfo(ip: str) -> dict | None:
    """Check IP against ipinfo.io (free tier: 50k/month, no key needed)."""
    url = f"https://ipinfo.io/{ip}/json"
    try:
        resp = SESSION.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def check_ipapi_co(ip: str) -> dict | None:
    """Check IP against ipapi.co (free tier: 1000/day)."""
    url = f"https://ipapi.co/{ip}/json/"
    try:
        resp = SESSION.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if "error" not in data:
                return data
    except Exception:
        pass
    return None


def run_geolocation_checks():
    """Test all Crimean IPs against geolocation services."""
    db = AuditDatabase()
    findings = []

    services = [
        ("ip-api.com", check_ip_api, "country", "countryCode"),
        ("ipinfo.io", check_ipinfo, "country", "country"),
        ("ipapi.co", check_ipapi_co, "country_name", "country_code"),
    ]

    for service_name, checker, country_field, code_field in services:
        print(f"\n--- Checking {service_name} ---")
        results_for_service = []

        for ip, meta in CRIMEAN_TEST_IPS.items():
            result = checker(ip)
            if result:
                country = result.get(country_field, "unknown")
                code = result.get(code_field, "??")
                isp = result.get("isp", result.get("org", ""))

                if code.upper() == "UA":
                    status = SovereigntyStatus.CORRECT
                elif code.upper() == "RU":
                    status = SovereigntyStatus.INCORRECT
                else:
                    status = SovereigntyStatus.AMBIGUOUS

                results_for_service.append({
                    "ip": ip,
                    "country": country,
                    "code": code,
                    "status": status,
                    "isp": isp,
                    "meta": meta,
                })
                print(f"  {ip} ({meta['desc']}): {country} ({code})")
            else:
                print(f"  {ip}: failed to resolve")

            time.sleep(1.5)  # Rate limiting

        # Aggregate results per service
        if results_for_service:
            ua_count = sum(1 for r in results_for_service
                          if r["code"].upper() == "UA")
            ru_count = sum(1 for r in results_for_service
                          if r["code"].upper() == "RU")
            total = len(results_for_service)

            if ru_count > ua_count:
                overall_status = SovereigntyStatus.INCORRECT
            elif ua_count > ru_count:
                overall_status = SovereigntyStatus.CORRECT
            else:
                overall_status = SovereigntyStatus.AMBIGUOUS

            evidence_lines = [
                f"{r['ip']} ({r['meta']['desc']}): {r['country']} ({r['code']})"
                for r in results_for_service
            ]

            findings.append(create_finding(
                platform=service_name,
                category=PlatformCategory.IP_GEOLOCATION,
                status=overall_status,
                method=AuditMethod.AUTOMATED_API,
                detail=(
                    f"Tested {total} Crimean IPs: {ua_count} resolved to UA, "
                    f"{ru_count} resolved to RU, "
                    f"{total - ua_count - ru_count} other."
                ),
                url=f"https://{service_name}",
                evidence="; ".join(evidence_lines),
                notes=(
                    f"Pre-2014, all these IPs were registered to Ukrainian "
                    f"entities. Post-annexation, some were re-registered under "
                    f"Russian entities."
                ),
            ))

    db.add_batch(findings)
    db.save()

    print(f"\n{'='*60}")
    print(f"IP geolocation audit complete: {len(findings)} service findings")
    print(f"Data saved to: {db.path}")

    return findings


if __name__ == "__main__":
    run_geolocation_checks()
