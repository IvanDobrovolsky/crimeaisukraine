# Tech Infrastructure Audit

## Name
`tech_infrastructure` — Standards, libraries, and protocols that encode Crimean sovereignty

## Why
Behind every map and every login form there are technical standards: timezone databases, phone number libraries, postal code systems, airport codes, ISO country codes. These are usually invisible to end users but propagate to billions of applications. When the IANA timezone database lists `Europe/Simferopol` as **`RU,UA`** (dual country) and Google's libphonenumber maps `+7-365x` to RU, every app inheriting these libraries silently encodes a sovereignty position.

## What
Audits 11 infrastructure-layer systems:

1. **IANA tz database** — `zone1970.tab` entries for Europe/Simferopol
2. **moment-timezone** (npm, 14.2M weekly downloads) — inherits IANA
3. **libphonenumber** (Google) + `libphonenumber-js` (npm, 14.1M weekly) — Russian +7-365 mapping
4. **ICAO airport codes** — UKFF, UKFB (Ukraine prefix)
5. **IATA codes** — SIP (Simferopol), SVP (Sevastopol)
6. **ISO 3166-2** — UA-43, UA-40 only (no RU-CR)
7. **CLDR** (Unicode) — used by all browsers/OS
8. **Postal codes** — Ukrainian (95xxx) vs Russian Post (29xxxx)
9. **Cloudflare** — UA-43 (follows ISO)
10. **Google libaddressinput** — address validation
11. **Domain TLD** — .ua vs .ru ccTLDs

## How

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor': '#0057b7', 'secondaryColor': '#ffd700', 'primaryTextColor': '#e5e5e5', 'lineColor': '#64748b', 'primaryBorderColor': '#1e293b'}}}%%
graph LR
  A["GitHub source<br/>files"] --> B["Direct fetch<br/>raw.githubusercontent"]
  B --> C["Parse fields<br/>zone1970.tab<br/>PhoneNumberMetadata.xml<br/>cldr/subdivisions.xml"]
  C --> D["Detect Crimean<br/>entries"]
  D --> E["Compare against<br/>international standards"]
  E --> F["manifest.json"]
  E --> G["npm download<br/>multipliers"]
  G --> F

  style A fill:#111827,stroke:#1e293b,color:#e5e5e5
  style C fill:#111827,stroke:#0057b7,color:#e5e5e5
  style E fill:#111827,stroke:#1e293b,color:#e5e5e5
  style F fill:#111827,stroke:#22c55e,color:#e5e5e5
```

## Run

```bash
cd pipelines/tech_infrastructure
uv sync
uv run scan.py
```

## Results

| Standard | Crimea classification | Downstream impact |
|---|---|---|
| **IANA tz** | `RU,UA` (dual) | 53M+ npm/week (moment-timezone, luxon, date-fns-tz) |
| **libphonenumber** | +7-365 → RU | 15.6M npm/week |
| **ICAO** | UKFF (Ukraine) | All international aviation |
| **ISO 3166-2** | UA-43 only | All browsers/OS via CLDR |
| **CLDR** | UA-43, no RU-CR | Verified from GitHub source |
| **Cloudflare** | UA-43 | 20%+ of internet traffic |
| **Russian Post codes** | 29xxxx | Russian Federation systems |

**Status breakdown**: 5 correct, 3 incorrect, 3 ambiguous

## Conclusions

The infrastructure layer is split:

- **International authorities** (ICAO, ITU, ISO) maintain Ukrainian classifications
- **Volunteer-maintained standards** (IANA tz) compromise via dual listings
- **Google's libphonenumber** silently normalizes Russia's unilateral +7-365 numbering
- **Russian-administered systems** (Russian Post) follow Russian sovereignty claims

The ISO finding is decisive: **Russia's ISO 3166-2:RU has 83 subdivisions, zero include Crimea**. CLDR — used by every browser and OS — confirms this. So the international standard is correct.

## Findings

1. **IANA zone1970.tab dual-listing** `RU,UA +4457+03406 Europe/Simferopol Crimea` — verified from `github.com/eggert/tz`
2. **Google libphonenumber maps +7-365 to RU** — verified from `PhoneNumberMetadata.xml`
3. **moment-timezone (14.2M/week)** inherits the IANA dual listing
4. **libphonenumber-js (14.1M/week)** inherits Google's +7-365 mapping
5. **luxon (24.3M/week)** uses IANA tz data
6. **ISO 3166-2 has no RU-CR entry** — Russian Federation has 83 subdivisions, none for Crimea
7. **CLDR confirms** — verified from `github.com/unicode-org/cldr/blob/main/common/supplemental/subdivisions.xml`
8. **ICAO maintains UKFF prefix** for Simferopol and UKFB for Sevastopol Belbek
9. **Cloudflare reports UA-43** for Crimean IPs — follows ISO not BGP
10. **Russian Post 29xxxx codes** assigned to Crimean addresses post-2014

## Limitations

- npm download counts fluctuate; values are weekly snapshots
- Cannot test all libraries that consume IANA tz (thousands exist)
- libphonenumber metadata is XML; parsing depends on file format stability
- ISO sells the actual standard; we verify via CLDR's mirror

## Sources

- IANA tz: https://github.com/eggert/tz
- libphonenumber: https://github.com/google/libphonenumber
- CLDR: https://github.com/unicode-org/cldr
- ICAO Doc 7910 (Location Indicators)
- npm download stats: https://api.npmjs.org/downloads/point/last-week/
