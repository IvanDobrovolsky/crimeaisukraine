# Tech Infrastructure: IP Geolocation & Crimea Sovereignty

**Audit date:** 2026-03-31
**Method:** Automated API queries against free IP geolocation services

---

## IP Geolocation Results

Tested 4 Crimean IP addresses against 3 free geolocation services:

### Test IPs

| IP | Organization | Pre-2014 Registration | Context |
|----|-------------|----------------------|---------|
| 91.207.56.1 | CrimeaCom (AS48031) | Ukraine | Ukrainian ISP that operated in Crimea |
| 176.104.32.1 | SevStar (AS56485) | Ukraine | Sevastopol ISP |
| 46.63.0.1 | Sim-Telecom (AS198948) | Ukraine | Simferopol ISP |
| 83.149.22.1 | Miranda-Media (AS201776) | N/A | Post-2014 Russian entity in Crimea |

### Results by Service

| IP / ISP | ip-api.com | ipinfo.io | ipapi.co |
|----------|-----------|-----------|---------|
| 91.207.56.1 (CrimeaCom) | HU (Hungary) | HU | HU |
| 176.104.32.1 (SevStar) | **UA** | **UA** | **UA** |
| 46.63.0.1 (Sim-Telecom) | **UA** | **UA** | **UA** |
| 83.149.22.1 (Miranda-Media) | **RU** | **RU** | N/A |

### Analysis

**Pattern 1: Pre-2014 Ukrainian ISPs retain UA classification**
SevStar and Sim-Telecom — both originally registered as Ukrainian entities in RIPE NCC — still resolve to Ukraine across all geolocation services. This is because their RIPE registration has not changed.

**Pattern 2: Post-2014 Russian entities resolve to RU**
Miranda-Media, a Russian telecom that expanded into Crimea after 2014, resolves to Russia. This reflects its RIPE registration under Russian entities.

**Pattern 3: Routing anomalies**
CrimeaCom (91.207.56.1) resolves to Hungary across all services. This likely indicates the ISP re-routed through Hungarian infrastructure, possibly to avoid Russian internet isolation or sanctions.

**Implication:** IP geolocation for Crimea is a patchwork determined by each ISP's RIPE registration and BGP routing decisions, not by a centralized country classification. The "Russification of Ukrainian IP Registration" documented by Kentik (2022) shows an ongoing process where Crimean IPs are gradually re-registered under Russian entities.

---

## Key Research Questions (for expansion)

1. **MaxMind GeoLite2 offline database** — needs download and local testing with more IPs
2. **RIPE NCC registration timeline** — track how Crimean IP blocks have moved between UA and RU over time
3. **CDN country routing** — how do Cloudflare, Akamai, Fastly route Crimean traffic?
4. **TLS certificate issuance** — do CAs issue certs to .crimea.ru or Crimea-based entities?

---

## References

- Kentik, "The Russification of Ukrainian IP Registration" (2022)
- Fontugne, Ermoshina, Aben, "The Internet in Crimea: A Case Study on Routing Interregnum" (IFIP 2020)
- Douzet et al., "Measuring the Fragmentation of the Internet" (NATO CyCon 2020)
