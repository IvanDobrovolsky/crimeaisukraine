```
 ██████╗██████╗ ██╗███╗   ███╗███████╗ █████╗     ██╗███████╗    ██╗   ██╗██╗  ██╗██████╗  █████╗ ██╗███╗   ██╗███████╗
██╔════╝██╔══██╗██║████╗ ████║██╔════╝██╔══██╗    ██║██╔════╝    ██║   ██║██║ ██╔╝██╔══██╗██╔══██╗██║████╗  ██║██╔════╝
██║     ██████╔╝██║██╔████╔██║█████╗  ███████║    ██║███████╗    ██║   ██║█████╔╝ ██████╔╝███████║██║██╔██╗ ██║█████╗
██║     ██╔══██╗██║██║╚██╔╝██║██╔══╝  ██╔══██║    ██║╚════██║    ██║   ██║██╔═██╗ ██╔══██╗██╔══██║██║██║╚██╗██║██╔══╝
╚██████╗██║  ██║██║██║ ╚═╝ ██║███████╗██║  ██║    ██║███████║    ╚██████╔╝██║  ██╗██║  ██║██║  ██║██║██║ ╚████║███████╗
 ╚═════╝╚═╝  ╚═╝╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝    ╚═╝╚══════╝     ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝
```

**Systematic audit of how digital platforms, open source libraries, and internet infrastructure represent Crimea's sovereignty.**

One upstream dataset encodes a political decision that cascades to 30M+ weekly downloads. Every `pip install plotly` quietly claims Crimea is Russia.

---

| Metric | Value |
|--------|-------|
| Platforms audited | **101** |
| Categories | **12** (maps, data viz, open source, travel, weather, social media, gaming, search, reference, IP geolocation, tech infrastructure, sports) |
| Correct (Ukraine) | **31** |
| Incorrect (Russia) | **17** |
| Ambiguous | **41** |
| Blocked (sanctions) | **5** |
| GDELT articles analyzed | **2,485** |
| npm weekly downloads affected | **30.4M** |
| Natural Earth GitHub issues | **33 open** |
| Infrastructure | **Local** (Python, DuckDB, free APIs — zero cloud cost) |

## Key Findings

**1. The Natural Earth propagation chain.** Natural Earth assigns `SOVEREIGNT=Russia` to Crimea. This cascades to D3 (13.4M/wk), Leaflet (4.2M/wk), ECharts (2.3M/wk), Plotly (965K/wk). Only Highcharts (2.3M/wk) deliberately overrides it. 33 GitHub issues requesting the change — all ignored.

**2. The 2022 bifurcation.** Consumer platforms changed after the full-scale invasion (Apple Maps, Netflix, TikTok). Developer infrastructure did not (Natural Earth, Plotly, IANA tzdata, D3). The internet users see got better. The internet developers build with didn't.

**3. The infrastructure split.** Legal/registration-based services = Ukraine (MaxMind, Cloudflare UA-43, GeoNames, OSM). Operational services = Russia (phone routing +7-978, timezones RU,UA, postal codes 295xxx). Occupied territory has a split digital identity.

**4. Weather services are the gold standard.** 10/10 correct. If weather apps can get it right, so can everyone else.

**5. Named political actors.** Salvini, Le Pen, Schroeder, Berlusconi, Orban, Trump, AfD — explicit sovereignty endorsements with dates. Transliteration (Crimea/Krym) is linguistic, not political — the paper distinguishes carefully.

## Structure

```
docs/                            Research reports (14 files, 3,500+ lines)
├── REPORT.md                    Summary report
├── PAPER_STRUCTURE.md           Journal paper outline (~12K words)
├── open_source.md               Data viz & open source propagation chain
├── tech.md                      IP geolocation, timezone, phone, DNS, CDN
├── maps.md                      Google, Apple, Bing, OSM, Yandex, HERE, Mapbox
├── travel.md                    Booking.com, Airbnb, Expedia, TripAdvisor
├── weather.md                   10 services, all correct
├── social_media.md              Instagram dual tags, TikTok, Facebook, X
├── gaming.md                    Steam, Epic, EA Sports, Transfermarkt
├── media.md                     Media framing analysis + methodology notes
├── media_framing_by_language.md 7 language clusters, politicians, events
├── media_gdelt_results.md       GDELT quantitative results (2,485 articles)
├── timeline.md                  2022 before/after changes
├── remaining_platforms.md       HERE, Mapbox, TomTom, Britannica, CIA, UN
└── PRIOR_RESEARCH.md            Literature review

data/                            Structured findings
├── platforms.json               Master database (101 findings)
├── findings.csv                 CSV export for analysis
├── propagation.json             Dependency chain data
├── propagation.csv              Dependency chain CSV
└── media_framing.json           GDELT article-level data (2,485 articles)

scripts/                         Reproducible audit tools (10 files, 3,300+ lines)
├── audit_framework.py           Classification framework & JSON database
├── check_open_source.py         Natural Earth, D3, Plotly, Highcharts, npm
├── check_ip_geolocation.py      Crimean IPs vs free geolocation APIs
├── check_infrastructure.py      Timezone, phone, geocoding, OSM Overpass
├── check_platforms.py           Wikipedia, weather, travel, gaming
├── check_propagation.py         npm/PyPI dependency chain analysis
├── check_media_framing.py       GDELT DOC API sovereignty framing
├── sync_docs_to_db.py           Sync doc findings to JSON database
└── export_findings.py           CSV export for paper tables

site/                            Astro static site (crimeaisukraine.org)
├── src/pages/index.astro        Main page with stats, charts, findings table
├── src/layouts/Layout.astro     Dark theme, Ukrainian blue/yellow
└── src/data/                    Platform data for static rendering
```

## Running the Audit

```bash
pip install -r requirements.txt
cd scripts
python check_open_source.py        # Natural Earth, D3, Plotly, Highcharts
python check_ip_geolocation.py     # Crimean IPs vs geolocation APIs
python check_infrastructure.py     # Timezone, phone, geocoding
python check_propagation.py        # npm/PyPI dependency analysis
python check_platforms.py          # Wikipedia, weather, travel, gaming
python check_media_framing.py      # GDELT sovereignty framing (rate-limited)
python export_findings.py          # CSV export
```

## Building the Site

```bash
cd site
npm install
npx astro build                    # Output: site/dist/
```

Deploy to Cloudflare Pages with build command `cd site && npm install && npx astro build`, output directory `site/dist`.

## Publication

**Paper:** "Digital Sovereignty by Default: How Upstream Geographic Data Encodes Territorial Claims Across the Internet"

**Targets:** Internet Policy Review, Information Communication & Society, New Media & Society

**Website:** [crimeaisukraine.org](https://crimeaisukraine.org)

## Related

Part of the [KyivNotKiev](https://github.com/IvanDobrovolsky/kyivnotkiev) research ecosystem.
