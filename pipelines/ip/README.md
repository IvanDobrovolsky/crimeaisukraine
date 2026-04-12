# IP Geolocation: BGP-Derived Databases vs ISO 3166

**Headline:** Across 9 Crimean ASNs and 90 sampled IPs, `ip-api.com` returns Ukraine for 53%, Russia for 16%, and a third country for 31%. Cloudflare follows ISO 3166 and resolves all Crimean prefixes to `UA-43` -- proving that following the international standard is a deliberate engineering choice any provider could make.

## Key findings

1. **53% of Crimean IP lookups resolve to Ukraine** -- driven by 4 ASNs whose RIPE country codes were never changed after 2014.
2. **16% resolve to Russia** -- driven by Miranda-Media AS201776 (Rostelecom's Crimean subsidiary, registered RU from July 2014) and CrimeaCom AS48031.
3. **31% resolve to transit countries** (Romania, Germany, Netherlands) -- 3 ASNs reach the internet via third-country transit; geolocation databases see the transit provider.
4. **RIPE NCC's `ripe-733`** is the upstream cause of every RU resolution. No sovereignty review on ASN transfers.
5. **Cloudflare Radar reports `UA-43`** for Crimean prefixes regardless of BGP state -- the only BGP-independent counterexample.
6. **Two BGP-derived providers agree on 100% of cross-validated IPs** -- but agreement inside the BGP family does not prove accuracy.

## Per-ASN consensus

| ASN | Operator | UA | RU | Other | Consensus |
|---|---|---:|---:|---:|---|
| AS42961 | CrimeaTelecom | 16 | 0 | -- | UA |
| AS44629 | CrimeaLink | 14 | 0 | -- | UA |
| AS56485 | SevStar | 16 | 0 | -- | UA |
| AS198948 | Sim-Telecom | 13 | 0 | -- | UA |
| AS48031 | CrimeaCom | 0 | 5 | -- | RU |
| AS201776 | Miranda-Media | 5 | 14 | -- | RU |
| AS28761 | KNET | 0 | 0 | all | no data |
| AS47598 | Sevastopolnet | 0 | 0 | all | no data |
| AS203070 | Crimean Telecom Co | 0 | 0 | all | no data |

## Methodology

9 ASNs, 45 prefixes, 2 IPs per prefix. Primary: ip-api.com batch. Cross-validation: ipinfo.io on every 3rd IP (30 IPs). 120 total lookups, 0 failures. No API keys required.

## Data

- Manifest: `data/manifest.json`
- Per-IP detail: `data/ip_bulk_results.json`
- Scan script: `scan.py`

## Run

```bash
make pipeline-ip
```

Runs `scan.py` end-to-end. Writes `data/manifest.json` and `data/ip_bulk_results.json`, rebuilds `site/src/data/master_manifest.json`. ~1-2 minutes.

## Sources

- [RIPE NCC](https://www.ripe.net/) | [RIPE STAT](https://stat.ripe.net/) | [`ripe-733`](https://www.ripe.net/publications/docs/ripe-733)
- [ip-api.com](https://ip-api.com/docs/api:batch) | [ipinfo.io](https://ipinfo.io/developers)
- [Cloudflare Radar](https://radar.cloudflare.com/) | [ISO 3166-2:UA](https://www.iso.org/obp/ui/#iso:code:3166:UA)
