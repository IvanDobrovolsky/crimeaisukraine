# Crimea Is Ukraine — Digital Sovereignty Audit

Systematic investigation of how digital platforms, open source libraries, media outlets, and internet infrastructure represent Crimea's sovereignty — covering 101 platforms across 12 categories.

Crimea is internationally recognized as Ukrainian territory (UN GA Resolution 68/262, 100-11 vote), illegally occupied by Russia since 2014. This project documents which platforms get it right, which don't, traces the root cause, and identifies the political actors who advocate for incorrect representation.

## Key Findings

1. **Natural Earth** — the foundational geographic dataset — assigns `SOVEREIGNT=Russia` to Crimea. This propagates to **30+ million weekly npm downloads** across D3, Plotly, ECharts, Leaflet. Only Highcharts deliberately overrides this to show Ukraine.

2. **33 open GitHub issues** on Natural Earth requesting the change. All ignored.

3. **The 2022 bifurcation:** Consumer-facing platforms (Apple Maps, Booking.com, Netflix) changed after the full-scale invasion. Developer infrastructure (Natural Earth, IANA tzdata, Plotly, D3) did not.

4. **Weather services are the gold standard** — all 8 checked correctly show Simferopol as Ukraine.

5. **Named politicians** with dated sovereignty endorsements: Salvini, Le Pen, Schröder, Berlusconi, Orbán, Trump, AfD leadership — across Italian, French, German contexts.

## Audit Coverage (101 platforms)

| Category | Platforms | Correct | Wrong | Ambiguous | Blocked |
|----------|-----------|---------|-------|-----------|---------|
| Data visualization | 18 | 3 | 5 | 9 | — |
| Tech infrastructure | 14 | 3 | 3 | 6 | 2 |
| Open source data | 13 | 1 | 6 | — | — |
| Map services | 11 | 3 | 1 | 7 | — |
| Reference | 10 | 4 | 1 | 5 | — |
| Weather | 10 | 10 | — | — | — |
| Travel | 8 | 1 | — | 4 | 3 |
| IP geolocation | 5 | 4 | — | 1 | — |
| Social media | 4 | — | 1 | 3 | — |
| Gaming | 4 | — | — | 4 | — |
| Search engines | 3 | — | — | 3 | — |
| Sports | 1 | — | — | 1 | — |
| **Total** | **101** | **31** | **17** | **41** | **5** |

## Structure

```
docs/                           → Research reports
  REPORT.md                     → Summary report
  PAPER_STRUCTURE.md            → Journal paper outline
  open_source.md                → Data viz & open source (core finding)
  tech.md                       → IP geolocation, timezone, phone, DNS
  maps.md                       → Map services
  travel.md                     → Travel platforms
  weather.md                    → Weather services (gold standard)
  social_media.md               → Social media location tags
  gaming.md                     → Gaming platforms
  media.md                      → Media framing analysis
  media_framing_by_language.md  → 7 language clusters + politicians
  media_gdelt_results.md        → GDELT DOC API quantitative results
  timeline.md                   → 2022 before/after platform changes
  remaining_platforms.md        → HERE, Mapbox, TomTom, Britannica, etc.
  PRIOR_RESEARCH.md             → Literature review

data/                           → Structured findings
  platforms.json                → Master database (101 findings)
  findings.csv                  → CSV export for analysis
  propagation.json/csv          → Dependency chain data
  media_framing.json            → GDELT article-level data

scripts/                        → Reproducible audit tools
  audit_framework.py            → Classification framework
  check_open_source.py          → Open source & data viz checker
  check_ip_geolocation.py       → IP geolocation tester
  check_infrastructure.py       → Timezone, phone, geocoding checker
  check_platforms.py            → Web platform checker
  check_propagation.py          → Dependency chain analyzer
  check_media_framing.py        → GDELT DOC API sovereignty framing
  sync_docs_to_db.py            → Sync docs findings to JSON database
  export_findings.py            → CSV export
```

## Running the Audit

```bash
pip install -r requirements.txt
cd scripts
python check_open_source.py        # Natural Earth, D3, Plotly, Highcharts, npm
python check_ip_geolocation.py     # Crimean IPs against free geolocation APIs
python check_infrastructure.py     # Timezone, phone, geocoding, OSM
python check_propagation.py        # npm/PyPI dependency chain analysis
python check_platforms.py          # Wikipedia, weather, travel, gaming
python check_media_framing.py      # GDELT sovereignty framing by language
python export_findings.py          # CSV export for paper tables
```

## Publication

**Target:** Academic journal (Internet Policy Review / Information, Communication & Society) + media articles (Kyiv Independent, Atlantic Council, WIRED)

**Paper:** "Digital Sovereignty by Default: How Upstream Geographic Data Encodes Territorial Claims Across the Internet" — see `docs/PAPER_STRUCTURE.md`

## Related

Part of the [KyivNotKiev](https://github.com/IvanDobrovolsky/kyivnotkiev) research ecosystem.
