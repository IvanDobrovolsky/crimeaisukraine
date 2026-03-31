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
| Platforms/services checked | 42 |
| Correctly shows Ukraine | 5 |
| Ambiguous/disputed/unclear | 24 |
| Incorrectly shows Russia | 6 |
| Blocked (sanctions) | 0 |
| Not applicable | 7 |

### By Category

| Category | Checked | Key Finding |
|----------|---------|-------------|
| Open source data | 9 | Natural Earth assigns Crimea to Russia at all resolutions |
| Data visualization | 13 | 27M+ weekly downloads inherit incorrect classification |
| IP geolocation | 3 | Mixed — depends on ISP registration, not centralized policy |
| Reference (Wikipedia) | 4 | German/Spanish correct; English/French ambiguous; Italian concerning |
| Travel | 5 | Mostly needs manual verification |
| Weather | 1 | AccuWeather inconclusive |
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

### 4. Wikipedia Language Disparity

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

### Reports in Progress
- `maps.md` — Map services (Google, Apple, Bing, OSM)
- `travel.md` — Travel and booking platforms
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
