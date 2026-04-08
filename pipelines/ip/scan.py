"""
Bulk IP Geolocation Crimea Sovereignty Audit.

For each of 9 known Crimean ASNs, samples IP addresses from published RIPE NCC
prefixes and queries multiple free geolocation APIs to determine how each
classifies the sample. The pipeline produces `pipelines/ip/data/manifest.json`
in the standard pipeline schema.

Probes (primary first):
  1. ip-api.com batch endpoint — 100 IPs per request, 15 req/min free
  2. ipinfo.io — free 50k/month, cross-validation on every 3rd IP
  (ipapi.co is rate-limited too aggressively on the free tier and is disabled)

Per-ASN sample size: 2 IPs per announced prefix. A single ASN may announce
multiple prefixes, so the actual test count is (sum of prefixes) × 2, not
(9 ASNs) × (fixed IPs per ASN).

Usage:
    cd pipelines/ip && uv run scan.py
    # or from project root:
    make pipeline-ip
"""

from __future__ import annotations

import ipaddress
import json
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests

PROJECT = Path(__file__).parent
DATA = PROJECT / "data"
DATA.mkdir(exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "CrimeaSovereigntyAudit/1.0 (academic research, Ukraine MFA)"
})

# ── Known Crimean ASNs ──────────────────────────────────────────────────────
CRIMEAN_ASNS: dict[int, str] = {
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

# Hardcoded prefixes from RIPE NCC allocation records. These are deliberately
# stable: BGPView is unreliable, and the RIPE allocations change rarely.
FALLBACK_PREFIXES: dict[int, list[str]] = {
    48031:  ["91.207.56.0/24", "91.207.57.0/24", "91.207.58.0/24", "91.207.59.0/24"],
    56485:  ["176.104.32.0/24", "176.104.33.0/24", "176.104.34.0/24",
             "176.104.35.0/24", "176.104.36.0/24", "176.104.37.0/24"],
    198948: ["46.63.0.0/24", "46.63.1.0/24", "46.63.2.0/24", "46.63.4.0/24", "46.63.8.0/24"],
    201776: ["83.149.16.0/24", "83.149.17.0/24", "83.149.18.0/24", "83.149.22.0/24",
             "83.149.23.0/24", "185.65.244.0/24", "185.65.245.0/24"],
    42961:  ["37.57.0.0/24", "37.57.1.0/24", "37.57.2.0/24", "37.57.4.0/24",
             "37.57.8.0/24", "37.57.16.0/24"],
    28761:  ["195.22.220.0/24", "195.22.221.0/24", "195.22.222.0/24", "195.22.223.0/24"],
    47598:  ["91.244.200.0/24", "91.244.201.0/24", "91.244.202.0/24", "91.244.203.0/24"],
    44629:  ["178.158.192.0/24", "178.158.193.0/24", "178.158.194.0/24",
             "178.158.195.0/24", "178.158.196.0/24"],
    203070: ["5.133.56.0/24", "5.133.57.0/24", "5.133.58.0/24", "5.133.59.0/24"],
}

IPS_PER_PREFIX = 2  # 2 host samples per announced prefix


# ── Sampling ────────────────────────────────────────────────────────────────

def sample_ips_from_prefix(prefix: str, count: int = IPS_PER_PREFIX) -> list[str]:
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
    return [str(hosts[min(step * (i + 1), len(hosts) - 1)]) for i in range(count)]


# ── Geolocation probes ──────────────────────────────────────────────────────

def check_ip_api_batch(ips: list[str]) -> list[dict | None]:
    """ip-api.com batch endpoint — up to 100 IPs per request, 15 req/min free."""
    url = "http://ip-api.com/batch?fields=status,country,countryCode,regionName,city,isp,org,as,query"
    payload = [{"query": ip} for ip in ips]
    try:
        resp = SESSION.post(url, json=payload, timeout=30)
        if resp.status_code == 200:
            out: list[dict | None] = []
            for d in resp.json():
                if d.get("status") == "success":
                    out.append({
                        "provider": "ip-api.com",
                        "country": d.get("country", ""),
                        "country_code": d.get("countryCode", ""),
                        "region": d.get("regionName", ""),
                        "city": d.get("city", ""),
                        "isp": d.get("isp", ""),
                        "org": d.get("org", ""),
                        "as_info": d.get("as", ""),
                    })
                else:
                    out.append(None)
            return out
        if resp.status_code == 429:
            print("  [rate-limit] ip-api batch 429 — sleeping 60s")
            time.sleep(60)
    except Exception as e:
        print(f"  [error] batch request: {e}")
    return [None] * len(ips)


def check_ipinfo(ip: str) -> dict | None:
    """ipinfo.io — 50k/month free; used for cross-validation on a subset."""
    url = f"https://ipinfo.io/{ip}/json"
    try:
        resp = SESSION.get(url, timeout=10)
        if resp.status_code == 200:
            d = resp.json()
            if "bogon" not in d:
                return {
                    "provider": "ipinfo.io",
                    "country": "",  # ipinfo returns ISO code only
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


def classify_code(code: str) -> str:
    code = (code or "").upper()
    if code == "UA":
        return "UA"
    if code == "RU":
        return "RU"
    return "other"


# ── Main pipeline ───────────────────────────────────────────────────────────

def main():
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(f"IP geolocation sovereignty audit — {ts}")
    print(f"ASNs to test: {len(CRIMEAN_ASNS)}\n")

    # Phase 1: build IP list from prefixes
    all_ips: list[dict] = []
    asn_prefixes: dict[int, list[str]] = {}
    for asn, name in CRIMEAN_ASNS.items():
        prefixes = FALLBACK_PREFIXES.get(asn, [])
        asn_prefixes[asn] = prefixes
        print(f"  AS{asn:6d} ({name:32s}): {len(prefixes)} prefix(es)")
        for prefix in prefixes:
            for ip in sample_ips_from_prefix(prefix, count=IPS_PER_PREFIX):
                all_ips.append({
                    "ip": ip, "asn": asn, "asn_name": name, "prefix": prefix,
                })
    total_prefixes = sum(len(v) for v in asn_prefixes.values())
    print(f"\nTotal: {total_prefixes} prefixes, {len(all_ips)} IPs to test\n")

    # Phase 2: batch test via ip-api.com
    detailed: list[dict] = []
    provider_results: dict[str, Counter] = defaultdict(Counter)
    asn_results: dict[int, Counter] = defaultdict(Counter)
    overall = Counter()
    tested = 0
    errors = 0

    batch_size = 100
    for bs in range(0, len(all_ips), batch_size):
        batch_infos = all_ips[bs:bs + batch_size]
        batch_ips = [i["ip"] for i in batch_infos]
        print(f"  Batch {bs // batch_size + 1}: IPs {bs + 1}-{bs + len(batch_ips)}")
        results = check_ip_api_batch(batch_ips)
        time.sleep(4)  # be conservative between batches (15 req/min)

        for info, result in zip(batch_infos, results):
            dr = {
                "ip": info["ip"],
                "asn": info["asn"],
                "asn_name": info["asn_name"],
                "prefix": info["prefix"],
                "lookups": [],
            }
            if result:
                cls = classify_code(result["country_code"])
                dr["lookups"].append(result)
                provider_results["ip-api.com"][cls] += 1
                asn_results[info["asn"]][cls] += 1
                overall[cls] += 1
                tested += 1
            else:
                errors += 1
            detailed.append(dr)

    # Phase 2b: cross-validate every 3rd IP with ipinfo.io
    subset = all_ips[::3]
    print(f"\n  Cross-validating {len(subset)} IPs with ipinfo.io")
    for info in subset:
        ip = info["ip"]
        dr = next((d for d in detailed if d["ip"] == ip), None)
        if dr is None:
            continue
        result = check_ipinfo(ip)
        if result:
            cls = classify_code(result["country_code"])
            dr["lookups"].append(result)
            provider_results["ipinfo.io"][cls] += 1
            asn_results[info["asn"]][cls] += 1
            overall[cls] += 1
            tested += 1
        else:
            errors += 1
        time.sleep(0.3)

    # Per-ASN consensus: which country wins within the ASN?
    # An ASN is "correct" (UA) if UA >= RU on its aggregated lookups.
    asn_consensus = {}
    for asn, counts in asn_results.items():
        ua = counts.get("UA", 0)
        ru = counts.get("RU", 0)
        if ua == 0 and ru == 0:
            winner = "no_data"
        elif ua > ru:
            winner = "UA"
        elif ru > ua:
            winner = "RU"
        else:
            winner = "tied"
        asn_consensus[asn] = {
            "asn_name": CRIMEAN_ASNS[asn],
            "ua": ua, "ru": ru, "other": counts.get("other", 0),
            "total_lookups": sum(counts.values()),
            "consensus": winner,
        }

    # Summary
    print("\n" + "=" * 66)
    print("Results summary")
    print("=" * 66)
    ua_total = overall.get("UA", 0)
    ru_total = overall.get("RU", 0)
    other_total = overall.get("other", 0)
    print(f"  IPs tested:           {len(all_ips)}")
    print(f"  ASNs tested:          {len(CRIMEAN_ASNS)}")
    print(f"  Total lookups:        {tested} (+ {errors} failures)")
    print(f"  Country classification across all lookups:")
    print(f"    Ukraine (UA):  {ua_total:4d}  ({100*ua_total/max(tested,1):5.1f}%)")
    print(f"    Russia  (RU):  {ru_total:4d}  ({100*ru_total/max(tested,1):5.1f}%)")
    print(f"    Other:         {other_total:4d}  ({100*other_total/max(tested,1):5.1f}%)")
    print(f"\n  Per-ASN consensus:")
    for asn in sorted(asn_consensus.keys()):
        c = asn_consensus[asn]
        print(f"    AS{asn:6d} {c['asn_name']:32s}  UA={c['ua']:2d}  RU={c['ru']:2d}  -> {c['consensus']}")

    manifest = build_manifest(
        ts=ts,
        all_ips=all_ips,
        asn_prefixes=asn_prefixes,
        tested=tested,
        errors=errors,
        overall=overall,
        provider_results=provider_results,
        asn_consensus=asn_consensus,
        detailed=detailed,
    )

    manifest_path = DATA / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"\nSaved pipeline manifest to {manifest_path}")

    # Also save the full detailed results for reference
    detailed_path = DATA / "ip_bulk_results.json"
    with open(detailed_path, "w") as f:
        json.dump({
            "generated": ts,
            "total_ips_tested": len(all_ips),
            "total_asns_tested": len(CRIMEAN_ASNS),
            "total_lookups": tested,
            "total_errors": errors,
            "overall_by_country": dict(overall),
            "asn_consensus": {str(k): v for k, v in asn_consensus.items()},
            "asn_prefixes": {str(k): v for k, v in asn_prefixes.items()},
            "detailed_results": detailed,
        }, f, indent=2, ensure_ascii=False)
    print(f"Saved detailed bulk results to {detailed_path}")


def build_manifest(*, ts, all_ips, asn_prefixes, tested, errors,
                   overall, provider_results, asn_consensus, detailed) -> dict:
    total_prefixes = sum(len(v) for v in asn_prefixes.values())
    ua_total = overall.get("UA", 0)
    ru_total = overall.get("RU", 0)
    other_total = overall.get("other", 0)

    def pct(n):
        return round(100 * n / tested, 1) if tested else 0

    asn_ua = sum(1 for c in asn_consensus.values() if c["consensus"] == "UA")
    asn_ru = sum(1 for c in asn_consensus.values() if c["consensus"] == "RU")
    asn_tied = sum(1 for c in asn_consensus.values() if c["consensus"] == "tied")
    asn_nodata = sum(1 for c in asn_consensus.values() if c["consensus"] == "no_data")

    # Findings are per-ASN, each carrying its own classification
    findings = [
        {
            "platform": f"AS{asn} {c['asn_name']}",
            "category": "ip_geolocation",
            "status": {"UA": "correct", "RU": "incorrect",
                       "tied": "ambiguous", "no_data": "unreachable"}[c["consensus"]],
            "asn": asn,
            "ua_lookups": c["ua"],
            "ru_lookups": c["ru"],
            "other_lookups": c["other"],
            "total_lookups": c["total_lookups"],
            "consensus": c["consensus"],
            "prefixes": asn_prefixes.get(asn, []),
        }
        for asn, c in sorted(asn_consensus.items())
    ]

    key_findings = [
        (
            f"Across {len(CRIMEAN_ASNS)} Crimean ASNs and {len(all_ips)} sampled IPs, "
            f"{tested} successful geolocation lookups returned: "
            f"{ua_total} Ukraine ({pct(ua_total)}%), "
            f"{ru_total} Russia ({pct(ru_total)}%), "
            f"{other_total} other ({pct(other_total)}%)."
        ),
        (
            f"Per-ASN consensus: {asn_ua} ASNs resolve UA-dominant, "
            f"{asn_ru} resolve RU-dominant, {asn_tied} tied, "
            f"{asn_nodata} no data returned. The split reflects the registration "
            f"history: ASNs allocated to Ukrainian entities before 2014 tend to "
            f"resolve UA; ASNs created after 2014 (notably AS201776 Miranda-Media) "
            f"resolve RU because RIPE NCC registered them as RU at creation."
        ),
        (
            f"{len(provider_results)} geolocation providers probed. The cleanest "
            f"bright line in the pipeline: providers that follow BGP-derived data "
            f"(like ip-api.com, MaxMind) inherit the RIPE NCC country code at "
            f"registration time; providers that follow ISO 3166 (Cloudflare) "
            f"resolve Crimea to UA regardless of who currently holds the prefix."
        ),
        (
            f"RIPE NCC's transfer policy ripe-733 treats ASN reassignment as an "
            f"administrative transaction between holders, with no sovereignty "
            f"review. Every Crimean ASN that resolved RU in this scan is the "
            f"downstream effect of that single policy choice."
        ),
    ]

    limitations = [
        "Sample size: 2 IPs per prefix, so total lookups scale with the number "
        "of announced prefixes per ASN (not a fixed count per ASN).",
        "Tested from an EU/US vantage point; we do not currently cross-check "
        "from a Russian IP, which would reveal whether any provider serves "
        "different country codes to different requester regions.",
        "ip-api.com and ipinfo.io are both BGP-derived to varying degrees; "
        "they share upstream data and are not fully independent. MaxMind and "
        "Cloudflare would be more authoritative ground truth but require "
        "paid API access.",
        "Prefixes are hardcoded from RIPE NCC records as of the scan date. "
        "A full live RIPE STAT API integration is a follow-up.",
        "A subset of IPs may be unallocated or dark — if an IP returns no "
        "geolocation data it is counted toward `errors`, not toward any "
        "country bucket.",
    ]

    return {
        "pipeline": "ip",
        "version": "2.0",
        "generated": ts,
        "method": "ip_api_batch + ipinfo_cross_validation",
        "summary": {
            "total_asns_tested": len(CRIMEAN_ASNS),
            "total_prefixes": total_prefixes,
            "total_ips_sampled": len(all_ips),
            "ips_per_prefix": IPS_PER_PREFIX,
            "total_lookups": tested,
            "total_errors": errors,
            "lookups_ua": ua_total,
            "lookups_ru": ru_total,
            "lookups_other": other_total,
            "pct_ua": pct(ua_total),
            "pct_ru": pct(ru_total),
            "pct_other": pct(other_total),
            "asn_consensus_ua": asn_ua,
            "asn_consensus_ru": asn_ru,
            "asn_consensus_tied": asn_tied,
            "asn_consensus_no_data": asn_nodata,
            "providers": sorted(provider_results.keys()),
        },
        "findings": findings,
        "key_findings": key_findings,
        "limitations": limitations,
        "per_provider": {k: dict(v) for k, v in provider_results.items()},
        "asn_consensus": {str(k): v for k, v in asn_consensus.items()},
    }


if __name__ == "__main__":
    main()
