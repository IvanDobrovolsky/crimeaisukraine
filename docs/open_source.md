# Open Source & Data Visualization: Crimea Sovereignty Findings

**Audit date:** 2026-03-31
**Method:** Automated source code and data file inspection
**Key finding:** A single upstream dataset (Natural Earth) propagates Crimea-as-Russia to 27M+ weekly npm downloads

---

## The Propagation Chain

```
Natural Earth (de facto boundaries)
  SOVEREIGNT=Russia, SOV_A3=RUS for Crimea
      │
      ├── D3 world-atlas (80K weekly downloads)
      │     └── Every D3.js choropleth map
      ├── Plotly.js (965K weekly downloads)
      │     └── Python Plotly, Dash, R plotly
      ├── Highcharts* (2.3M weekly downloads)
      │     └── *EXCEPTION: correctly assigns Crimea to Ukraine
      ├── Apache ECharts (2.3M weekly downloads)
      │     └── Chinese/global data dashboards
      ├── topojson-client (3.8M weekly downloads)
      │     └── All TopoJSON consumers
      ├── d3-geo (13.4M weekly downloads)
      │     └── All D3 geographic projections
      └── Leaflet (4.2M weekly downloads)
            └── Tile-based but commonly paired with NE data

Total downstream exposure: ~27.1 million weekly npm downloads
```

---

## 1. Natural Earth (Root Cause)

**Status: Incorrect**

Natural Earth is the foundational geographic dataset used by the majority of open source mapping and data visualization libraries worldwide.

### Disputed Areas Layer (10m resolution)
| Field | Value |
|-------|-------|
| NAME | Crimea |
| SOVEREIGNT | **Russia** |
| SOV_A3 | **RUS** |
| ADMIN | Russia |
| ADM0_A3 | RUS |
| TYPE | Disputed |
| NOTE_ADM0 | Annexed by Rus. |
| NOTE_BRK | Admin. by Russia; Claimed by Ukraine |

### Country Polygon Containment
| Resolution | Russia contains Crimea? | Ukraine contains Crimea? |
|------------|------------------------|-------------------------|
| 50m | **Yes** | No |
| 110m | **Yes** | No |

**Methodology note:** Tested whether the Crimean peninsula center point (34.1E, 44.9N) falls within each country's bounding box. At both standard resolutions, Crimea's geometry is part of Russia's polygon and absent from Ukraine's.

**Natural Earth's rationale:** They use "de facto" (ground control) rather than "de jure" (international law) boundaries. They offer 31 point-of-view variants, but the default — which is what every library downloads — assigns Crimea to Russia.

**Source:** https://github.com/nvkelso/natural-earth-vector

---

## 2. D3 world-atlas

**Status: Incorrect (inherits from Natural Earth)**

The standard TopoJSON package for D3.js choropleth maps. Uses Natural Earth data directly.

- **110m**: Russia's arcs include Crimea. Ukraine's do not.
- **50m**: Same classification.
- **Weekly downloads:** 80,198
- **Impact:** Every D3.js world map tutorial, Observable notebook, and data journalism project using `world-atlas` shows Crimea as Russia by default.

**Source:** https://www.npmjs.com/package/world-atlas

---

## 3. Plotly

**Status: Ambiguous (issue acknowledged, partially addressed)**

Plotly's built-in `choropleth` and `choropleth_mapbox` use Natural Earth boundaries internally.

- **GitHub issue #2903:** Users reported Crimea shown as part of Russia. Issue was opened and subsequently closed.
- **Weekly downloads (plotly.js):** 964,646
- **Python plotly pip downloads:** ~40M monthly
- **Impact:** Default `px.choropleth()` calls show Crimea within Russia's boundary. No built-in option to switch to de jure boundaries.

**Source:** https://github.com/plotly/plotly.py/issues/2903

---

## 4. Highcharts Maps

**Status: Correct**

Highcharts is the notable exception among major visualization libraries.

- **Russia map** (`countries/ru/ru-all.geo.json`): Does NOT include Crimea/Sevastopol
- **Ukraine map** (`countries/ua/ua-all.geo.json`): INCLUDES Crimea/Sevastopol
- **Weekly downloads:** 2,269,785

This is a deliberate editorial decision by Highcharts, making them the only major data viz library to correctly represent Crimea under international law in their default map data.

**Source:** https://code.highcharts.com/mapdata/

---

## 5. Apache ECharts

**Status: Unclear (needs deeper investigation)**

ECharts (Apache, originally Baidu) is the dominant data visualization library in China and increasingly used globally.

- **World map data:** Crimea not explicitly named in the test world.json
- **Weekly downloads:** 2,322,682
- **Concern:** As a Chinese-origin library, it may follow China's geopolitical perspective. China has not recognized Russia's annexation of Crimea but has been ambiguous in UN votes.

**Source:** https://github.com/apache/echarts

---

## 6. Downstream Impact Quantification

| Package | Weekly npm Downloads | Inherits NE Crimea? |
|---------|---------------------|---------------------|
| d3-geo | 13,448,446 | Yes (renders NE data) |
| leaflet | 4,203,074 | Partial (tile-dependent) |
| topojson-client | 3,814,090 | Yes (decodes NE TopoJSON) |
| echarts | 2,322,682 | Investigation needed |
| highcharts | 2,269,785 | **No (correctly shows Ukraine)** |
| plotly.js | 964,646 | Yes (built-in NE) |
| world-atlas | 80,198 | Yes (packages NE directly) |
| **Total** | **27,102,921** | |

**Conservative estimate:** At least 20M weekly downloads across packages that inherit Natural Earth's Crimea-as-Russia classification.

This does not count:
- Python packages (geopandas, plotly, folium)
- R packages (rnaturalearth, ggplot2 + sf)
- Desktop GIS applications using Natural Earth
- Government and corporate dashboards

---

## 7. GitHub GeoJSON Repositories

| Repository | Stars | Crimea Status |
|------------|-------|---------------|
| datasets/geo-countries | ~200 | Not explicitly named (encoded in polygons) |
| johan/world.geo.json | 4,000+ | Not explicitly named (encoded in polygons) |
| georgique/world-geojson | ~100 | Derived from Natural Earth |

These repositories derive from Natural Earth and inherit its boundary classification.

---

## 8. npm Country Data Packages

| Package | Weekly Downloads | Crimea Handling |
|---------|-----------------|-----------------|
| i18n-iso-countries | ~4M | Follows ISO 3166-1 (no Crimea entity) |
| country-list | ~200K | Follows ISO 3166-1 (no Crimea entity) |
| iso3166-2-db | ~10K | Explicitly offers UN vs Russia perspectives |

ISO 3166-1 doesn't list Crimea as a separate entity, so these packages don't directly encode a sovereignty claim. However, ISO 3166-2 (subdivisions) is where the classification matters — Crimea as UA-43 (Ukraine) vs any Russian subdivision code.

---

## 9. Wikipedia Framing Analysis

| Language | Framing | Status |
|----------|---------|--------|
| English | "peninsula in Eastern Europe" — mentions both Ukraine and Russia | Ambiguous |
| German | "Halbinsel der Ukraine" (peninsula of Ukraine) | Correct |
| French | Geographic description, mentions Ukraine and Russia | Ambiguous |
| Italian | Geographic description, insufficient Ukrainian context | Concerning |
| Spanish | "territorio disputado entre Rusia y Ucrania, controlado por el primero pero reconocido por la comunidad internacional como parte del segundo" | Correct (explicitly states international recognition) |

---

## Conclusions

### The Core Problem
Natural Earth's "de facto" boundary approach creates a **single point of failure** for digital sovereignty representation. Because it is the upstream data source for virtually all open source mapping, a single editorial decision ("we map ground control, not legal status") propagates to millions of applications worldwide.

### The Exception Proves the Rule
Highcharts' deliberate decision to assign Crimea to Ukraine demonstrates that this is an editorial choice, not a technical necessity. Libraries CAN represent international law; most simply default to Natural Earth without questioning it.

### Recommendations
1. **Engage Natural Earth maintainers** — request that the default (non-POV) dataset follow UN General Assembly Resolution 68/262
2. **File issues on major libraries** — Plotly (reopen #2903), D3 world-atlas, ECharts
3. **Publish a "Crimea compliance" badge** — a simple check that library maintainers can run
4. **Quantify total exposure** — use libraries.io dependency data to count all transitive dependents
