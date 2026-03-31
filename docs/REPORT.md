# Crimea Digital Sovereignty Audit — Summary Report

**Author:** Ivan Dobrovolsky
**Date:** 2026-03-31
**Status:** In progress (first automated pass complete)

---

## Executive Summary

This audit systematically examines how digital platforms, open source libraries, and tech infrastructure represent Crimea's sovereignty. Crimea is internationally recognized as Ukrainian territory (UN GA Resolution 68/262), illegally occupied by Russia since 2014.

**Key finding:** A single upstream geographic dataset — Natural Earth — explicitly classifies Crimea as `SOVEREIGNT=Russia` and includes it within Russia's polygon boundaries. This classification silently propagates to data visualization libraries with **27+ million weekly npm downloads**, affecting every choropleth map, data dashboard, and geographic visualization built with these tools.

---

## Audit Statistics

| Metric | Count |
|--------|-------|
| Platforms/services checked | 64 |
| Correctly shows Ukraine | 19 |
| Ambiguous/disputed/unclear | 28 |
| Incorrectly shows Russia | 8 |
| Blocked by sanctions | 4 |
| Needs direct verification | 5 |

### By Category

| Category | Checked | Key Finding |
|----------|---------|-------------|
| Open source data | 9 | Natural Earth assigns Crimea to Russia at all resolutions |
| Data visualization | 13 | 27M+ weekly downloads inherit incorrect classification |
| Map services | 8 | Google/OSM geo-dependent; Apple correct outside Russia; Nat Geo inconsistent |
| Travel platforms | 6 | Sanctions block bookings; TripAdvisor lists Crimea without country |
| Social media | 4 | Instagram allows both "Russia" and "Ukraine" tags for same cities |
| Weather services | 10 | Most consistent category — all verified services show Ukraine |
| IP geolocation | 3 | Mixed — depends on ISP registration, not centralized policy |
| Reference (Wikipedia) | 4 | German/Spanish correct; English/French ambiguous; Italian concerning |
| Gaming | 4 | Needs manual verification |
| Search engines | 3 | Needs manual verification |

---

## Top Findings

### 1. The Natural Earth Propagation Chain (Novel Finding)

Natural Earth's "de facto" boundary approach creates a single point of failure:

```
Natural Earth (SOVEREIGNT=Russia for Crimea)
    → D3 world-atlas → every D3.js map
    → Plotly → every Python/R data dashboard
    → topojson-client → all TopoJSON consumers
    → d3-geo → all D3 geographic projections
    = 27,102,921 weekly npm downloads affected
```

**This has never been systematically documented.** Individual library issues exist (e.g., Plotly #2903) but nobody has mapped the full propagation chain from a single upstream data source to millions of downstream applications.

### 2. Highcharts — The Exception That Proves the Rule

Highcharts Maps (2.3M weekly downloads) deliberately assigns Crimea to Ukraine in their map collection. Russia's map excludes Crimea; Ukraine's map includes it. This demonstrates the classification is an editorial choice, not a technical constraint.

### 3. IP Geolocation Is a Patchwork

Crimean IPs are not consistently classified. Pre-2014 Ukrainian ISPs still resolve to UA; post-2014 Russian entities resolve to RU. One Ukrainian ISP (CrimeaCom) resolves to Hungary, likely due to re-routing.

### 4. Google Maps "Disputed" Default Is False Equivalence

Google Maps shows Crimea with a **dashed "disputed" border** to users outside Russia and Ukraine. This framing treats the situation as a bilateral disagreement, ignoring that UNGA Resolution 68/262 affirmed Crimea as Ukrainian territory by a 100-11 vote. Only 11 countries voted against. Apple Maps corrected this in March 2022, showing Crimea as Ukraine outside Russia.

### 5. Instagram's Dual Location Tags Normalize Russian Claims

Instagram maintains **both** "Crimea, Ukraine" and "Russia, Crimea, Yalta" as active location tags. Users can freely choose either, effectively allowing the platform to serve as a vehicle for normalizing Russia's sovereignty claim over Crimea.

### 6. Weather Services Are the Gold Standard

All 8 verified weather services (AccuWeather, Weather Underground, TimeAndDate, Weather Spark, Meteoblue, Weather-Forecast.com, Ventusky, Weather Atlas) classify Simferopol under **Ukraine**. This consistency stems from reliance on standardized geographic databases (GeoNames, ISO 3166).

### 7. TripAdvisor's "Europe > Crimea" Avoids the Question

TripAdvisor lists Crimea directly under "Europe" without any country designation — neither Ukraine nor Russia. While less harmful than labeling it as Russia, this evasion fails to reflect the internationally recognized status.

### 8. Wikipedia Language Disparity

| Language | Crimea framing |
|----------|---------------|
| German | "Halbinsel der Ukraine" (peninsula of Ukraine) |
| Spanish | Explicitly states international recognition as part of Ukraine |
| English | Mentions both, no clear sovereignty statement in intro |
| Italian | Insufficient Ukrainian context |

---

## Detailed Reports

- [Open Source & Data Visualization](open_source.md) — **the core novel finding**
- [Tech Infrastructure & IP Geolocation](tech.md)
- [Prior Research Survey](PRIOR_RESEARCH.md)

### Completed Reports
- [Map Services](maps.md) — Google Maps, Apple Maps, OpenStreetMap, Bing, Natural Earth, National Geographic
- [Travel Platforms](travel.md) — Booking.com, Airbnb, Expedia, TripAdvisor, Google Flights
- [Social Media](social_media.md) — Instagram, TikTok, Facebook, X/Twitter location tags
- [Weather Services](weather.md) — AccuWeather, Weather Underground, BBC Weather, and 8 others

### Reports in Progress
- `gaming.md` — Gaming platforms and in-game maps
- `media.md` — News media framing (references kyivnotkiev analysis)

---

## Methodology

### Automated Checks
- **Source code inspection:** Downloaded GeoJSON/TopoJSON files from GitHub, inspected properties and geometry containment
- **API queries:** Tested Crimean IPs against free geolocation services; queried Wikipedia API
- **Dependency analysis:** npm registry API for download counts; package source inspection

### Manual Checks (in progress)
- Platform-by-platform verification of map services, travel sites, gaming platforms
- VPN-based regional testing (US, UK, Germany, Russia perspectives)
- Screenshot documentation

### Classification System
- **Correct:** Shows Crimea as part of Ukraine
- **Ambiguous:** Disputed label, no label, configurable, or unclear
- **Incorrect:** Shows Crimea as part of Russia
- **Blocked:** Service unavailable in Crimea (sanctions compliance)

---

## Publication Plan

### Academic
- **Target journal:** Internet Policy Review, Information Communication & Society, or JCMC
- **Framing:** "Digital sovereignty infrastructure" — how upstream data sources encode political decisions that propagate to millions of downstream applications
- **Novel contribution:** First systematic cross-platform audit + dependency propagation analysis

### Media
- **Primary:** Kyiv Independent, Kyiv Post
- **International:** WIRED, The Guardian
- **Think tanks:** Atlantic Council/DFRLab, CEPA (extends their Mapaganda coverage)

### Open Data
- Structured findings database: `data/platforms.json`
- Reproducible audit scripts: `scripts/`
- GitHub + Kaggle dataset publication

---

## Next Steps

1. Complete manual platform checks (maps, travel, gaming, search)
2. Expand IP geolocation testing with MaxMind GeoLite2 offline database
3. Quantify full dependency tree via libraries.io (transitive dependents)
4. File issues on affected open source projects
5. Draft journal paper structure
6. Prepare media pitch materials
