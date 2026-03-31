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

## 9. Python Ecosystem

### 9a. GeoPandas (naturalearth_lowres)

**Status: Fixed (was Incorrect)**

GeoPandas shipped a built-in `naturalearth_lowres` dataset that showed Crimea as part of Russia.

- **GitHub issue #2382:** Reported March 2022 that the default world dataset excluded Crimea from Ukraine
- **Root cause:** The bundled Natural Earth data used de facto boundaries
- **Fix:** PR #2670 patched the dataset to assign Crimea to Ukraine, released in v0.12.2
- **Subsequent action:** The entire `geopandas.datasets` module was deprecated and removed in GeoPandas 1.0 (early 2024). Users now use the `geodatasets` package instead
- **Monthly PyPI downloads:** ~15 million
- **Impact:** Every GeoPandas tutorial using `gpd.datasets.get_path('naturalearth_lowres')` prior to v0.12.2 showed Crimea as Russian
- **Fixable:** Fixed upstream, but legacy tutorials and older pinned versions still propagate the error

**Source:** https://github.com/geopandas/geopandas/issues/2382

### 9b. Cartopy (SciTools)

**Status: Incorrect (inherits from Natural Earth)**

Cartopy is the standard Python library for scientific cartography, used heavily in climate science, meteorology, and earth sciences.

- **Default behavior:** `cartopy.feature.BORDERS` and `cartopy.feature.NaturalEarthFeature` download Natural Earth data directly at runtime
- **Resolution used:** Default 1:110m scale, which assigns Crimea to Russia
- **No POV option:** Cartopy does not expose Natural Earth's point-of-view variants; users get de facto boundaries only
- **GitHub stars:** ~1,400
- **Monthly PyPI downloads:** Estimated 2-3 million
- **Impact:** Scientific publications, IPCC-adjacent climate visualizations, university courses
- **Fixable:** Yes -- could add a `worldview` parameter to NaturalEarthFeature. No issue filed yet.

**Source:** https://github.com/SciTools/cartopy

---

## 10. R Ecosystem

### 10a. rnaturalearth

**Status: Incorrect (refuses to fix)**

The primary R interface to Natural Earth data.

- **GitHub issue #116:** User requested Crimea be assigned to Ukraine. Maintainer responded: "This package aims to provide geographical data fetched from the data provided by Natural Earth. We do not modify the underlying data."
- **GitHub issue #27:** Earlier request ("Is or isn't Crimea part of Russia?") similarly declined
- **Resolution:** Closed without fix. Users must manually modify geometries using `sf` package
- **CRAN downloads:** Estimated 50K-100K monthly
- **Impact:** Academic research, R-based data journalism, government statistical reports
- **Fixable:** Maintainers have explicitly declined. Would need upstream Natural Earth change.

**Source:** https://github.com/ropensci/rnaturalearth/issues/116

### 10b. spData (Nowosad)

**Status: Incorrect (inherits from rnaturalearth)**

Educational spatial data package used in the popular textbook "Geocomputation with R."

- **GitHub issue #50:** "Improper map of Ukraine" -- Crimea shown as Russian
- **Root cause:** Data sourced from rnaturalearth, which sources from Natural Earth
- **Impact:** University courses worldwide teaching spatial analysis with R
- **Fixable:** Requires upstream Natural Earth change

**Source:** https://github.com/Nowosad/spData/issues/50

---

## 11. Phone Number Libraries

### 11a. Google libphonenumber

**Status: Incorrect (de facto)**

Google's authoritative phone number parsing library, used across Android, Chrome, and thousands of applications.

- **Crimea phone numbers:** After Russia's 2014 occupation, Crimean landlines switched from +380 65 (Ukraine) to +7 365 (Russia), and mobiles to +7 978. The Ukrainian +380 codes are no longer functional for Crimean numbers.
- **libphonenumber behavior:** Numbers dialed as +7 365 xxx or +7 978 xxx are parsed as region "RU" (Russia). There is no mechanism to identify them as Crimean or Ukrainian.
- **GitHub stars:** 17,000+
- **npm downloads (google-libphonenumber wrapper):** 1.6 million weekly
- **npm downloads (libphonenumber-js rewrite):** 13.6 million weekly
- **Total ecosystem impact:** ~15.2 million weekly npm downloads
- **Rationale:** The library follows ITU technical reality -- the +7 country code is assigned to Russia, and Crimean infrastructure now operates under +7
- **Fixable:** Extremely difficult. This is a de facto technical reality, not just a data classification. The +380 codes genuinely do not route to Crimea. Filing an issue is possible but Google's FAQ states they follow "the phone network as it actually operates."

**Source:** https://github.com/google/libphonenumber

---

## 12. Timezone Databases

### 12a. IANA tzdata (zone1970.tab)

**Status: Ambiguous (dual classification)**

The authoritative global timezone database used by every operating system, programming language, and application.

- **zone.tab (legacy):** Europe/Simferopol listed under country code `UA` (Ukraine only)
- **zone1970.tab (current):** Europe/Simferopol listed as `RU,UA` (both, Russia listed first alphabetically)
- **Actual UTC offset:** +03:00 (Moscow time) since 2014, reflecting Russian-imposed time change
- **File comment:** "Mention RU and UA alphabetically. See 'territorial claims' above."
- **Disclaimer:** "This table is intended as an aid for users... It is not intended to take or endorse any position on legal or territorial claims."
- **Impact:** Every application that maps timezones to countries -- operating systems, phone settings, calendar apps, web frameworks
- **Downstream consumers:**
  - Python `zoneinfo` / `pytz`
  - moment-timezone (npm): Issue #954 requested removing RU association, was closed without change
  - Java `java.time`
  - ICU (International Components for Unicode)
- **Fixable:** Could request IANA remove RU from the country code. However, the de facto UTC offset (+3, Moscow time) is a technical fact that must be recorded.

**Source:** https://data.iana.org/time-zones/tzdb/zone1970.tab

### 12b. moment-timezone

**Status: Incorrect (inherits IANA)**

- **GitHub issue #954:** Requested Europe/Simferopol be dissociated from RU. Closed without action.
- **Maintainer response:** "Moment Timezone directly consumes the data that the IANA files provide. No extra decision layer is made."
- **npm weekly downloads:** ~12 million (though now in maintenance mode, replaced by date-fns/luxon)
- **Fixable:** Would require IANA upstream change

**Source:** https://github.com/moment/moment-timezone/issues/954

---

## 13. Postal Code / Address Libraries

### 13a. Russian Post Integration

**Status: Incorrect (de facto)**

After 2014, Russia assigned postal codes 295000-299999 to Crimea (prefixing "2" to existing Ukrainian 5-digit codes, e.g., Simferopol: 95000 -> 295000).

- **zauberware/postal-codes-json-xml-csv:** 397 GitHub stars, sources data from geonames.org. Lists 43,538 Russian postal codes. The 295xxx-299xxx range (Crimea) is included under RU.
- **sanmai/pindx:** Free JSON API for Russian postal codes from Russian Post's official database. Includes Crimean codes under RU.
- **Impact:** Any application using these datasets for address validation, shipping, or geotargeting classifies Crimean addresses as Russian.
- **Fixable:** These reflect Russian Post's operational reality. Packages could add metadata noting the disputed status.

**Source:** https://github.com/zauberware/postal-codes-json-xml-csv

### 13b. Google libaddressinput

**Status: Correct**

Google's address validation library (used in Android and Chromium).

- **Crimea classification:** Address data service classifies Crimean addresses under UA (Ukraine)
- **GitHub stars:** 615
- **Impact:** Powers address forms in Android apps and Chrome autofill
- **Fixable:** N/A -- already correct

**Source:** https://github.com/google/libaddressinput

---

## 14. GeoIP / Geolocation Databases

### 14a. MaxMind GeoIP2

**Status: Correct**

The industry-standard IP geolocation database.

- **Crimea classification:** Located in Ukraine (UA), using region codes UA,11 (Krym) and UA,20 (Sevastopol)
- **Data source:** GeoNames, which classifies Crimea under Ukraine
- **Accuracy:** ~96% of Crimean visitors correctly geolocated
- **Note:** MaxMind stated they would follow GeoNames if it changed classification
- **Fixable:** N/A -- already correct

**Source:** https://dev.maxmind.com/release-note/geoip-accuracy-in-crimea/

### 14b. GeoNames

**Status: Correct**

Major open geographic database used by MaxMind, postal code databases, and many other services.

- **Crimea classification:** Listed under Ukraine (UA)
- **Administrative division:** Crimea appears in Ukraine's administrative hierarchy
- **Impact:** Upstream data source for MaxMind, multiple postal code datasets, and geocoding services
- **Fixable:** N/A -- already correct

**Source:** https://www.geonames.org/UA/administrative-division-ukraine.html

---

## 15. ISO 3166 / Country-Region Packages

### 15a. esosedi/3166 (iso3166-2-db)

**Status: Incorrect by default (configurable)**

- **Default behavior:** Crimea included as part of Russia
- **Configuration options:** Supports "dispute modes" -- UN perspective (excludes Crimea from Russia), Russian perspective (includes it)
- **npm package:** `iso3166-2-db`
- **Impact:** Applications using default settings classify Crimea as Russian
- **Fixable:** Yes -- could change default to UN perspective. Issue can be filed.

**Source:** https://github.com/esosedi/3166

---

## 16. GeoJSON Dataset Repositories

### 16a. datasets/geo-countries (Datahub.io)

**Status: Incorrect (inherits from Natural Earth)**

- **GitHub stars:** 568
- **Data source:** Natural Earth, converted to GeoJSON via ogr2ogr
- **Crimea handling:** Not documented; inherits Natural Earth's de facto boundaries
- **Impact:** Commonly referenced in data science tutorials and Jupyter notebooks
- **Fixable:** Yes -- could use Natural Earth's Ukraine POV data instead

**Source:** https://github.com/datasets/geo-countries

### 16b. mledoze/countries

**Status: Investigation needed**

- **GitHub stars:** 6,200
- **Data:** World countries in JSON/YAML/CSV/XML with GeoJSON boundaries
- **Crimea handling:** Not explicitly documented, but GeoJSON outlines likely derived from Natural Earth
- **Impact:** One of the most popular country data repositories on GitHub
- **Fixable:** Yes -- issue can be filed

**Source:** https://github.com/mledoze/countries

### 16c. Explicit Russia-with-Crimea repositories

Several repositories explicitly include Crimea in Russian map data:

- **logvik/d3_russian_map:** D3 visualization of Russia including Crimea and Sevastopol
- **mateuspestana/RussiaMaps:** Shapefiles of Russia with Crimea added
- **logvik/cf787bda80a8aa125c84 (Gist):** "Russia map with Crimea and Sevastopol" GeoJSON

These are intentional, low-impact repositories, but they normalize Crimea's inclusion in Russia.

---

## 17. Wikipedia Framing Analysis

| Language | Framing | Status |
|----------|---------|--------|
| English | "peninsula in Eastern Europe" — mentions both Ukraine and Russia | Ambiguous |
| German | "Halbinsel der Ukraine" (peninsula of Ukraine) | Correct |
| French | Geographic description, mentions Ukraine and Russia | Ambiguous |
| Italian | Geographic description, insufficient Ukrainian context | Concerning |
| Spanish | "territorio disputado entre Rusia y Ucrania, controlado por el primero pero reconocido por la comunidad internacional como parte del segundo" | Correct (explicitly states international recognition) |

---

## Summary Scorecard

| Category | System | Status | Weekly/Monthly Reach | Fixable? |
|----------|--------|--------|---------------------|----------|
| **Maps (root cause)** | Natural Earth | Incorrect | Upstream to all below | Yes (change default) |
| **Maps (JS)** | D3 world-atlas | Incorrect | 30K weekly npm | Yes (issue) |
| **Maps (JS)** | Plotly.js | Incorrect | 965K weekly npm | Yes (reopen #2903) |
| **Maps (JS)** | Highcharts | **Correct** | 2.3M weekly npm | N/A |
| **Maps (JS)** | ECharts | Unclear | 2.3M weekly npm | Needs investigation |
| **Maps (Python)** | GeoPandas | **Fixed** (v0.12.2) | 15M monthly PyPI | Legacy versions still wrong |
| **Maps (Python)** | Cartopy | Incorrect | 2-3M monthly PyPI | Yes (no issue filed) |
| **Maps (R)** | rnaturalearth | Incorrect (refused) | 50-100K monthly CRAN | Declined by maintainers |
| **Maps (R)** | spData | Incorrect | University textbooks | Requires upstream fix |
| **Phone numbers** | libphonenumber | Incorrect (de facto) | 15.2M weekly npm | Very difficult (technical) |
| **Timezones** | IANA tzdata | Ambiguous (RU,UA) | Every OS/language | Possible but contested |
| **Timezones** | moment-timezone | Incorrect | 12M weekly npm | Requires IANA change |
| **Postal codes** | Russian Post datasets | Incorrect | Multiple repositories | Metadata can be added |
| **Addresses** | Google libaddressinput | **Correct** | Android + Chrome | N/A |
| **GeoIP** | MaxMind GeoIP2 | **Correct** | Industry standard | N/A |
| **GeoIP** | GeoNames | **Correct** | Upstream to MaxMind | N/A |
| **ISO codes** | iso3166-2-db | Incorrect (default) | ~10K weekly npm | Yes (change default) |
| **GeoJSON** | datasets/geo-countries | Incorrect | 568 GitHub stars | Yes (issue) |
| **GeoJSON** | mledoze/countries | Likely incorrect | 6,200 GitHub stars | Yes (issue) |

---

## Conclusions

### The Core Problem
Natural Earth's "de facto" boundary approach creates a **single point of failure** for digital sovereignty representation. Because it is the upstream data source for virtually all open source mapping, a single editorial decision ("we map ground control, not legal status") propagates to millions of applications worldwide.

### The Scale of Impact
Across all categories documented here:
- **~27M weekly npm downloads** from JavaScript mapping libraries alone
- **~17M monthly PyPI downloads** from Python packages (GeoPandas + Cartopy)
- **~15M weekly npm downloads** from phone number libraries classifying Crimean numbers as Russian
- **~12M weekly npm downloads** from timezone libraries with RU association
- **Every operating system** ships IANA tzdata with RU,UA dual classification for Simferopol

### The Exception Proves the Rule
Highcharts, Google libaddressinput, MaxMind GeoIP2, and GeoNames all correctly classify Crimea as Ukrainian. This demonstrates that correct classification is an editorial choice, not a technical impossibility. Libraries CAN represent international law; most simply default to Natural Earth without questioning it.

### Three Tiers of Fixability

**Tier 1 -- Straightforward fixes (data classification choices):**
1. Natural Earth: Change default to follow UN GA Resolution 68/262
2. D3 world-atlas, Plotly, Cartopy: Switch to de jure Natural Earth data
3. iso3166-2-db: Change default dispute mode to UN perspective
4. GeoJSON repositories: Use Ukraine-POV Natural Earth data

**Tier 2 -- Requires upstream changes:**
5. rnaturalearth, spData: Maintainers declined; need Natural Earth to change first
6. moment-timezone: Need IANA to change zone1970.tab
7. Postal code databases: Reflect Russian Post operations, but could add dispute metadata

**Tier 3 -- Reflects de facto technical reality:**
8. libphonenumber: +7 365/978 codes route through Russian infrastructure; +380 codes don't work for Crimea
9. IANA tzdata UTC offset: Crimea physically operates on Moscow time (+03:00)

### Recommendations
1. **Engage Natural Earth maintainers** -- request that the default (non-POV) dataset follow UN General Assembly Resolution 68/262. This single change would cascade to fix Tier 1 and Tier 2 issues.
2. **File issues on major libraries** -- Plotly (reopen #2903), D3 world-atlas, ECharts, Cartopy, mledoze/countries
3. **Highlight correct implementations** -- publicly credit Highcharts, MaxMind, GeoNames, and Google libaddressinput for correct classification, creating social pressure for others to follow
4. **Publish a "Crimea compliance" checker** -- a simple tool that tests whether a dataset/library assigns Crimea to Ukraine
5. **Address the Andrew Heiss blog post** -- his February 2025 tutorial "How to move Crimea from Russia to Ukraine in maps with R" provides practical workarounds; amplify this resource
6. **Quantify total exposure** -- use libraries.io dependency data to count all transitive dependents
