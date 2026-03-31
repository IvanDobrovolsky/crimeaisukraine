"""
Bulk IP Geolocation Crimea Sovereignty Audit

Tests a large number of Crimean IP addresses across multiple ASNs against
free geolocation APIs to determine how they classify Crimea's country.

Methodology:
  1. Query BGPView API for IP prefixes announced by known Crimean ASNs
  2. Sample 2-3 representative IPs from each prefix
  3. Test each IP against ip-api.com, ipinfo.io, and ipapi.co
  4. Aggregate results by ASN, provider, and country classification

Rate limits respected:
  - ip-api.com: 45 requests/minute (free, no key)
  - ipinfo.io: 50,000/month (free tier, no key)
  - ipapi.co: 1,000/day (free tier)

Usage:
    python scripts/check_ip_bulk.py
"""

import ipaddress
import json
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests

# Allow importing from scripts/
sys.path.insert(0, str(Path(__file__).parent))

from audit_framework import (
    AuditDatabase,
    AuditMethod,
    PlatformCategory,
    SovereigntyStatus,
    create_finding,
    DATA_DIR,
)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "CrimeaSovereigntyAudit/1.0 (academic research, Ukraine MFA)"
})

# ── Known Crimean ASNs ──────────────────────────────────────────────────────
# These ISPs are headquartered in Crimea or provide service primarily there.
CRIMEAN_ASNS = {
    48031:  "CrimeaCom",
    56485:  "SevStar (Sevastopol)",
    198948: "Sim-Telecom (Simferopol)",
    201776: "Miranda-Media",
    42961:  "CrimeaTelecom",
    28761:  "KNET",
    47598:  "Sevastopolnet",
    44629:  "CrimeaLink",
    203070: "Crimean Telecom Company",
}

# Fallback prefixes in case BGPView is unreachable for an ASN
FALLBACK_PREFIXES = {
    48031:  ["91.207.56.0/21"],
    56485:  ["176.104.32.0/20"],
    198948: ["46.63.0.0/19"],
    201776: ["83.149.22.0/23", "83.149.16.0/21"],
    42961:  ["37.57.0.0/17"],
    28761:  ["195.22.220.0/22"],
    47598:  ["91.244.200.0/22"],
    44629:  ["178.158.192.0/19"],
    203070: ["5.133.56.0/21"],
}

# ── Rate limiting ────────────────────────────────────────────────────────────
# ip-api: 45/min => 1 every 1.34s; ipinfo: generous; ipapi.co: 1000/day
# We cycle through providers and add per-provider delays.
PROVIDER_DELAYS = {
    "ip-api.com": 1.4,   # 45/min
    "ipinfo.io": 0.3,    # generous
    "ipapi.co": 1.0,     # 1000/day, be conservative
}


def fetch_asn_prefixes(asn: int) -> list[str]:
    """Get IPv4 prefixes for an ASN from BGPView API."""
    url = f"https://api.bgpview.io/asn/{asn}/prefixes"
    try:
        resp = SESSION.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "ok":
                prefixes = []
                for p in data["data"].get("ipv4_prefixes", []):
                    prefix = p.get("prefix")
                    if prefix:
                        prefixes.append(prefix)
                if prefixes:
                    return prefixes
    except Exception as e:
        print(f"  [warn] BGPView request failed for AS{asn}: {e}")

    # Fallback
    fallback = FALLBACK_PREFIXES.get(asn, [])
    if fallback:
        print(f"  [info] Using {len(fallback)} fallback prefix(es) for AS{asn}")
    return fallback


def sample_ips_from_prefix(prefix: str, count: int = 3) -> list[str]:
    """Pick representative IPs from a CIDR prefix.

    Selects the first host, a middle host, and one near the end.
    Skips network/broadcast addresses.
    """
    try:
        net = ipaddress.IPv4Network(prefix, strict=False)
    except (ipaddress.AddressValueError, ValueError):
        return []

    hosts = list(net.hosts())
    if not hosts:
        return []
    if len(hosts) <= count:
        return [str(h) for h in hosts]

    step = max(1, len(hosts) // (count + 1))
    selected = []
    for i in range(count):
        idx = min(step * (i + 1), len(hosts) - 1)
        selected.append(str(hosts[idx]))
    return selected


# ── Geolocation checkers (reuse logic from check_ip_geolocation.py) ─────────

def check_ip_api(ip: str) -> dict | None:
    """ip-api.com — free, 45 req/min."""
    url = f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,regionName,city,isp,org,as,query"
    try:
        resp = SESSION.get(url, timeout=10)
        if resp.status_code == 200:
            d = resp.json()
            if d.get("status") == "success":
                return {
                    "provider": "ip-api.com",
                    "country": d.get("country", ""),
                    "country_code": d.get("countryCode", ""),
                    "region": d.get("regionName", ""),
                    "city": d.get("city", ""),
                    "isp": d.get("isp", ""),
                    "org": d.get("org", ""),
                    "as_info": d.get("as", ""),
                }
        elif resp.status_code == 429:
            print("  [rate-limit] ip-api.com 429 — sleeping 60s")
            time.sleep(60)
    except Exception:
        pass
    return None


def check_ipinfo(ip: str) -> dict | None:
    """ipinfo.io — free 50k/month."""
    url = f"https://ipinfo.io/{ip}/json"
    try:
        resp = SESSION.get(url, timeout=10)
        if resp.status_code == 200:
            d = resp.json()
            if "bogon" not in d:
                return {
                    "provider": "ipinfo.io",
                    "country": "",  # ipinfo only returns code
                    "country_code": d.get("country", ""),
                    "region": d.get("region", ""),
                    "city": d.get("city", ""),
                    "isp": d.get("org", ""),
                    "org": d.get("org", ""),
                    "as_info": d.get("org", ""),
                }
        elif resp.status_code == 429:
            print("  [rate-limit] ipinfo.io 429 — sleeping 30s")
            time.sleep(30)
    except Exception:
        pass
    return None


def check_ipapi_co(ip: str) -> dict | None:
    """ipapi.co — free 1000/day."""
    url = f"https://ipapi.co/{ip}/json/"
    try:
        resp = SESSION.get(url, timeout=10)
        if resp.status_code == 200:
            d = resp.json()
            if "error" not in d:
                return {
                    "provider": "ipapi.co",
                    "country": d.get("country_name", ""),
                    "country_code": d.get("country_code", ""),
                    "region": d.get("region", ""),
                    "city": d.get("city", ""),
                    "isp": d.get("org", ""),
                    "org": d.get("org", ""),
                    "as_info": d.get("asn", ""),
                }
        elif resp.status_code == 429:
            print("  [rate-limit] ipapi.co 429 — sleeping 60s")
            time.sleep(60)
    except Exception:
        pass
    return None


PROVIDERS = [
    ("ip-api.com", check_ip_api),
    ("ipinfo.io", check_ipinfo),
    ("ipapi.co", check_ipapi_co),
]


def classify_code(code: str) -> str:
    """Classify a country code into UA, RU, or other."""
    code = (code or "").upper()
    if code == "UA":
        return "UA"
    elif code == "RU":
        return "RU"
    else:
        return "other"


# ── Main pipeline ────────────────────────────────────────────────────────────

def run_bulk_check():
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print("=" * 70)
    print(f"  BULK IP GEOLOCATION CRIMEA SOVEREIGNTY AUDIT")
    print(f"  {timestamp}")
    print(f"  ASNs to test: {len(CRIMEAN_ASNS)}")
    print("=" * 70)

    # Phase 1: Gather IP prefixes from all ASNs
    print("\n[Phase 1] Fetching IP prefixes from BGPView...")
    asn_prefixes: dict[int, list[str]] = {}
    all_ips: list[dict] = []  # {"ip": ..., "asn": ..., "asn_name": ..., "prefix": ...}

    for asn, name in CRIMEAN_ASNS.items():
        print(f"  AS{asn} ({name})...", end=" ", flush=True)
        time.sleep(1)  # BGPView rate limit
        prefixes = fetch_asn_prefixes(asn)
        asn_prefixes[asn] = prefixes
        print(f"{len(prefixes)} prefix(es)")

        for prefix in prefixes:
            ips = sample_ips_from_prefix(prefix, count=3)
            for ip in ips:
                all_ips.append({
                    "ip": ip,
                    "asn": asn,
                    "asn_name": name,
                    "prefix": prefix,
                })

    total_prefixes = sum(len(v) for v in asn_prefixes.values())
    print(f"\n  Total: {total_prefixes} prefixes, {len(all_ips)} IPs to test")

    if not all_ips:
        print("[error] No IPs collected. Check network connectivity.")
        return

    # Phase 2: Test each IP against all 3 providers
    print(f"\n[Phase 2] Testing {len(all_ips)} IPs x {len(PROVIDERS)} providers "
          f"= {len(all_ips) * len(PROVIDERS)} API calls")
    print("  (this will take a few minutes due to rate limiting)\n")

    detailed_results = []
    provider_results = defaultdict(lambda: Counter())  # provider -> {UA: n, RU: n}
    asn_results = defaultdict(lambda: Counter())       # asn -> {UA: n, RU: n}
    overall_country = Counter()
    tested_count = 0
    error_count = 0

    for idx, ip_info in enumerate(all_ips):
        ip = ip_info["ip"]
        asn = ip_info["asn"]
        asn_name = ip_info["asn_name"]
        prefix = ip_info["prefix"]

        ip_result = {
            "ip": ip,
            "asn": asn,
            "asn_name": asn_name,
            "prefix": prefix,
            "lookups": [],
        }

        progress = f"[{idx+1}/{len(all_ips)}]"
        print(f"  {progress} {ip} (AS{asn} {asn_name})")

        for prov_name, checker in PROVIDERS:
            result = checker(ip)
            if result:
                code = result["country_code"]
                cls = classify_code(code)
                ip_result["lookups"].append(result)
                provider_results[prov_name][cls] += 1
                asn_results[asn][cls] += 1
                overall_country[cls] += 1
                tested_count += 1
                icon = {"UA": "UA", "RU": "RU", "other": "??"}.get(cls, "??")
                print(f"    {prov_name:15s} -> {code:2s} ({icon}) "
                      f"[{result.get('region', '')}, {result.get('city', '')}]")
            else:
                error_count += 1
                print(f"    {prov_name:15s} -> FAILED")

            # Per-provider rate limiting
            time.sleep(PROVIDER_DELAYS.get(prov_name, 1.0))

        detailed_results.append(ip_result)

    # Phase 3: Build output
    print(f"\n{'=' * 70}")
    print(f"[Phase 3] Results Summary")
    print(f"{'=' * 70}")

    total_lookups = tested_count
    ua_total = overall_country.get("UA", 0)
    ru_total = overall_country.get("RU", 0)
    other_total = overall_country.get("other", 0)

    print(f"\n  Total IPs tested:     {len(all_ips)}")
    print(f"  Total ASNs tested:    {len(CRIMEAN_ASNS)}")
    print(f"  Total API lookups:    {total_lookups} (+ {error_count} failures)")
    print(f"\n  Country classification across all lookups:")
    print(f"    Russia (RU):   {ru_total:4d}  ({100*ru_total/max(total_lookups,1):.1f}%)")
    print(f"    Ukraine (UA):  {ua_total:4d}  ({100*ua_total/max(total_lookups,1):.1f}%)")
    print(f"    Other:         {other_total:4d}  ({100*other_total/max(total_lookups,1):.1f}%)")

    print(f"\n  Per-provider breakdown:")
    for prov_name, counts in sorted(provider_results.items()):
        prov_total = sum(counts.values())
        ru = counts.get("RU", 0)
        ua = counts.get("UA", 0)
        print(f"    {prov_name:15s}: {ru} RU / {ua} UA / {counts.get('other',0)} other "
              f"(of {prov_total} lookups)")

    print(f"\n  Per-ASN breakdown:")
    for asn in sorted(asn_results.keys()):
        counts = asn_results[asn]
        name = CRIMEAN_ASNS.get(asn, "?")
        total = sum(counts.values())
        ru = counts.get("RU", 0)
        ua = counts.get("UA", 0)
        print(f"    AS{asn:6d} ({name:30s}): {ru} RU / {ua} UA / "
              f"{counts.get('other',0)} other (of {total})")

    # Phase 4: Save JSON results
    output = {
        "metadata": {
            "description": "Bulk IP geolocation sovereignty audit for Crimean ISP ranges",
            "date": timestamp,
            "methodology": (
                "Sampled 2-3 IPs per prefix from each Crimean ASN, "
                "tested against 3 free geolocation APIs"
            ),
        },
        "total_ips_tested": len(all_ips),
        "total_asns_tested": len(CRIMEAN_ASNS),
        "total_api_lookups": total_lookups,
        "total_errors": error_count,
        "results_by_country": {
            "UA": ua_total,
            "RU": ru_total,
            "other": other_total,
        },
        "results_by_provider": {
            prov: dict(counts) for prov, counts in provider_results.items()
        },
        "results_by_asn": {
            str(asn): {
                "name": CRIMEAN_ASNS.get(asn, "?"),
                "results": dict(counts),
            }
            for asn, counts in asn_results.items()
        },
        "asn_prefixes": {
            str(asn): prefixes for asn, prefixes in asn_prefixes.items()
        },
        "detailed_results": detailed_results,
    }

    output_path = DATA_DIR / "ip_bulk_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n  Results saved to: {output_path}")

    # Phase 5: Update platforms.json audit database
    print(f"\n[Phase 5] Updating audit database (platforms.json)...")
    db = AuditDatabase()

    for prov_name, counts in provider_results.items():
        prov_total = sum(counts.values())
        ru = counts.get("RU", 0)
        ua = counts.get("UA", 0)
        oth = counts.get("other", 0)

        if ru > ua:
            status = SovereigntyStatus.INCORRECT
        elif ua > ru:
            status = SovereigntyStatus.CORRECT
        else:
            status = SovereigntyStatus.AMBIGUOUS

        # Build evidence string: per-ASN breakdown for this provider
        evidence_parts = []
        for dr in detailed_results:
            for lookup in dr["lookups"]:
                if lookup["provider"] == prov_name:
                    evidence_parts.append(
                        f"{dr['ip']} (AS{dr['asn']}): {lookup['country_code']}"
                    )

        finding = create_finding(
            platform=prov_name,
            category=PlatformCategory.IP_GEOLOCATION,
            status=status,
            method=AuditMethod.AUTOMATED_API,
            detail=(
                f"Bulk test: {prov_total} lookups across {len(all_ips)} Crimean IPs "
                f"from {len(CRIMEAN_ASNS)} ASNs — "
                f"{ru} RU ({100*ru/max(prov_total,1):.0f}%), "
                f"{ua} UA ({100*ua/max(prov_total,1):.0f}%), "
                f"{oth} other."
            ),
            url=f"https://{prov_name}",
            evidence="; ".join(evidence_parts[:30]) + (
                f" ... (+{len(evidence_parts)-30} more)" if len(evidence_parts) > 30 else ""
            ),
            notes=(
                f"Tested IP ranges from {len(CRIMEAN_ASNS)} Crimean ASNs including "
                f"CrimeaCom, SevStar, Miranda-Media, CrimeaTelecom, etc. "
                f"All prefixes were originally allocated to Ukrainian entities by RIPE NCC."
            ),
        )
        db.add(finding)

    db.save()
    print(f"  Audit database updated: {db.path}")
    print(f"\n{'=' * 70}")
    print(f"  AUDIT COMPLETE")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    run_bulk_check()
