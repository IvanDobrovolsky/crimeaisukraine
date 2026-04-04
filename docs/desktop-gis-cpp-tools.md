# Geographic Boundary Data in C++, Desktop GIS, and Related Tools

**Date checked:** 2026-04-04
**Purpose:** Identify what boundary datasets are used by C++/desktop applications, and how each classifies Crimea.

---

## Summary Table

| Tool/Library | Ships boundary data? | Default data source | Crimea classification | Automatable? |
|---|---|---|---|---|
| **GDAL/OGR** | No (reads any format) | N/A — it's a format library | Depends on input data | N/A |
| **Natural Earth** | Yes (standalone dataset) | Own dataset | **Russia (de facto default)** | Yes — download + parse shapefiles |
| **QGIS** | Yes (bundled `world_map.gpkg`) | Natural Earth (simplified) | **Likely Russia (de facto)** | Yes — load GPKG, query attributes |
| **AutoCAD / Civil 3D** | No built-in boundaries | Uses Bing Maps for basemap tiles | Depends on Bing Maps tile server | No (raster tiles, not queryable) |
| **ArcGIS Pro** | Yes (Living Atlas layers) | Esri + Garmin + HERE + OSM | **Ambiguous** — vendor-dependent, Esri disclaims endorsement | Yes — query ArcGIS REST services |
| **OpenCV** | No | N/A — computer vision library | N/A | N/A |
| **PROJ** | No | N/A — coordinate math only | N/A (no boundaries, only CRS definitions) | N/A |
| **CGAL** | No | N/A — computational geometry primitives | N/A | N/A |
| **VTK** | No | N/A — visualization toolkit | N/A | N/A |
| **GADM** | Yes (standalone dataset) | Own compilation | **Ukraine (de jure)** | Yes — download + parse |
| **geoBoundaries** | Yes (standalone dataset) | Community + official sources | **Ukraine** (uses HDX/COD-AB) | Yes — API available |
| **OpenStreetMap** | Yes (PBF extracts) | Community-edited | **Dual: both Russia and Ukraine** | Yes — parse PBF with osmium/osm4j |
| **Geofabrik extracts** | Yes (regional PBFs) | OpenStreetMap | **Included in BOTH Ukraine and Russia downloads** | Yes — download and diff |
| **Unreal/Unity** | No built-in; plugins use Cesium/ArcGIS/MapTiler | Varies by plugin | Depends on upstream data source | Depends on plugin |

---

## Detailed Findings

### 1. GDAL/OGR

GDAL (Geospatial Data Abstraction Library) is a **format translator**, not a data provider. It reads and writes 200+ raster/vector formats (Shapefile, GeoJSON, GeoPackage, PostGIS, etc.) but **ships no country boundary data**. Whatever sovereignty classification exists comes from the data the user loads.

However, GDAL is the engine underneath nearly every desktop GIS tool, so the question becomes: what data do those tools bundle?

**Crimea relevance:** GDAL itself is neutral. The classification depends entirely on the upstream dataset.

### 2. Natural Earth (the key upstream dataset)

Natural Earth is the most widely used free boundary dataset and the default data source for many tools including QGIS, geopandas, and many web mapping libraries.

**Default Crimea classification: RUSSIA (de facto)**

Natural Earth follows a strict de facto policy — boundaries reflect who controls territory on the ground. Since Russia occupies Crimea, the default `ne_10m_admin_0_countries` shapefile shows Crimea as part of Russia.

**Point-of-view alternatives:** Natural Earth offers POV variants for 31 countries. The US POV shows Crimea as Ukraine. However:
- POV variants **only exist for the 10m (high-resolution) data**
- The commonly used 50m and 110m datasets have **no POV option** — Crimea is always Russia
- The POV mechanism uses attribute columns that are poorly documented

**Automation:** Fully automatable. Download shapefiles, query `SOV_A3` and `ADM0_A3` fields, check which polygon contains Crimea coordinates (e.g., 34.1, 44.95).

**GitHub issues:** Nearly two dozen issues filed about Crimea on `nvkelso/natural-earth-vector` (e.g., #391, #489, #812).

### 3. QGIS

QGIS bundles a simplified Natural Earth layer as `world_map.gpkg`, loadable by typing "world" in the coordinates bar. The only default basemap tile source is OpenStreetMap (XYZ Tiles in the Browser Panel).

**Default Crimea classification: Likely RUSSIA** — because the bundled data derives from Natural Earth's de facto dataset.

QGIS itself is data-agnostic; users can load any dataset. But the out-of-box experience for a new user plotting a world map will show Crimea as Russian.

**Automation:** Load `world_map.gpkg` via GDAL/OGR, query the feature that intersects Crimea's coordinates, check the country name attribute.

### 4. AutoCAD / Civil 3D

AutoCAD and Civil 3D are **CAD tools, not GIS tools**. They do not ship country boundary vector data. Geographic capabilities include:
- Coordinate system assignment (via `MAPCSASSIGN` command, using EPSG/PROJ definitions)
- Live Maps basemap (Bing Maps aerial/road tiles) for georeferenced drawings
- AutoCAD Map 3D can connect to external GIS data sources

**Crimea classification:** Depends entirely on Bing Maps (for basemap tiles) or whatever external GIS data the user connects. Bing Maps' own Crimea policy applies.

**Automation:** Not directly — no queryable boundary dataset. Would need to check Bing Maps tile labeling separately.

### 5. ArcGIS Pro

ArcGIS Pro (C++ based) provides access to Esri's Living Atlas, which includes the **World Countries** and **World Boundaries and Places** layers. Data sources include Esri's own compilation plus Garmin, HERE, and OpenStreetMap.

Esri's disclaimer: "The alignment of boundaries is a presentation of the features as provided by data vendors and does not imply endorsement by Esri or any governing authority."

**Crimea classification: AMBIGUOUS.** Esri does not publicly document a clear de facto vs. de jure policy for Crimea specifically. Their World Countries layer (dated December 2023) uses a blend of vendor data. The practical classification likely varies by which specific layer/service is used and potentially by the user's region.

**Automation:** Yes — query the ArcGIS REST API endpoints for the World Countries feature service, check which polygon contains Crimea coordinates.

### 6. OpenCV

OpenCV is a **computer vision library**. It has **zero geographic or boundary data**. It can read raster images via GDAL (if compiled with GDAL support), but has no concept of countries, borders, or sovereignty.

**Not relevant to this investigation.**

### 7. PROJ

PROJ is a **coordinate transformation library**. It converts between coordinate reference systems (lat/lon to UTM, etc.) using mathematical formulas and datum shift grids. It references the EPSG registry for CRS definitions.

PROJ **does not encode sovereignty or political boundaries**. CRS zones (like UTM zones) are purely geometric and do not imply political control. The EPSG registry does associate CRS codes with "areas of use" described by country names, but this is for technical applicability, not sovereignty claims.

**Not relevant to Crimea classification.**

### 8. CGAL

CGAL (Computational Geometry Algorithms Library) provides geometric primitives: triangulations, Voronoi diagrams, convex hulls, mesh generation, etc. It **ships no geographic data whatsoever**. It can be used to process geographic data (e.g., triangulating terrain), but has no built-in country boundaries.

**Not relevant to this investigation.**

### 9. VTK

VTK (Visualization Toolkit) is a 3D rendering and visualization library. It **ships no geographic boundary data**. Users must provide their own data for geographic visualizations. VTK can render shapefiles and other GIS formats, but the classification depends on the input data.

**Not relevant to this investigation.**

### 10. GADM (Global Administrative Areas Database)

GADM v4.1 is a widely used administrative boundary database. It provides boundaries at multiple administrative levels for every country.

**Crimea classification: UKRAINE (de jure)**

GADM classifies Crimea as "an autonomous republic of Ukraine" under the URL path `gadm.org/maps/UKR/crimea.html`. It is listed as a Level 1 administrative division of Ukraine (UKR), not Russia.

**Automation:** Fully automatable. Download the GADM GeoPackage or Shapefile for Ukraine, verify Crimea is present as a Level 1 unit. Can also download Russia's GADM data and verify Crimea is absent.

**Widely used by:** R (`geodata`, `raster` packages), Python (via download), C++ (via GDAL reading the shapefiles).

### 11. OpenStreetMap PBF Files

OSM uses a **dual-boundary approach** for Crimea, resulting from years of contentious community debate:

- Crimea is mapped as within **both** Ukraine and Russia administrative relations simultaneously
- The boundaries at the Isthmus of Perekop are tagged as disputed
- OSM relation #72639 = "Autonomous Republic of Crimea" (Ukraine admin)
- OSM relation #3795586 = "Republic of Crimea" (Russia admin)

**Geofabrik extracts:**
- **Ukraine download** (`download.geofabrik.de/europe/ukraine.html`): titled "Ukraine (with Crimea)" — explicitly includes Crimea
- **Russia download** (`download.geofabrik.de/russia.html`): includes a "Crimean Federal District" sub-region — also includes Crimea
- Geofabrik states: "the inclusion of Crimea does not constitute a political statement; we have included Crimea in both the Russia and the Ukraine downloads"

**Impact on routing engines:** OSRM and Valhalla (both C++) process whatever PBF extract they're given. If built from the Russia extract, Crimea routes seamlessly within Russia. If built from the Ukraine extract, Crimea routes within Ukraine. The routing engine itself is boundary-agnostic.

**Automation:** Fully automatable. Download both PBFs, use `osmium` to extract admin boundary relations, compare which country-level relation contains Crimea.

### 12. Unreal Engine / Unity

Neither engine ships geographic boundary data natively. Geographic capabilities come from plugins:

- **Cesium for Unreal/Unity** — streams 3D terrain and imagery from Cesium ion (uses Bing Maps, Mapbox, or custom tilesets). Boundary classification depends on the tile provider.
- **ArcGIS Maps SDK for Game Engines** — connects to Esri's services. Classification follows Esri's data (see #5 above).
- **MapTiler plugin** — uses MapTiler/OpenMapTiles data (derived from OpenStreetMap). Classification follows OSM's dual-boundary approach.

**Automation:** Would need to check each tile provider separately.

---

## Key Findings for the Investigation

### The critical chokepoint: Natural Earth

Natural Earth is the single most influential boundary dataset in the open-source ecosystem. Its **de facto default showing Crimea as Russia** propagates to:
- QGIS (bundled world map)
- GeoPandas (`naturalearth_lowres` built-in dataset — bug #2382 filed, being fixed)
- Countless web dashboards (Metabase, Plotly, D3.js, etc.)
- Any tool that grabs "free world boundaries" as a starting point

The POV alternatives exist but are poorly documented and only available at 10m resolution, meaning most automated/quick-start use cases get the Russia classification.

### Bright spots (de jure / pro-Ukraine)
- **GADM** — Crimea is unambiguously Ukraine
- **geoBoundaries** — Uses HDX/COD-AB data, Crimea under Ukraine
- **GeoPandas** — actively fixing their default to show Crimea as Ukraine

### The OSM problem
OpenStreetMap's dual-boundary approach means Crimea appears in **both** countries' data, which is arguably better than Russia-only but still problematic. The Geofabrik "Crimean Federal District" sub-region under Russia normalizes the Russian administrative framing.

### What's NOT a factor
GDAL, PROJ, CGAL, VTK, OpenCV — these are geometry/format/vision libraries with zero boundary data. They are tools, not data sources. The sovereignty question is always upstream in the dataset, not in these libraries.

---

## Automatable Checks

| Check | Method | Difficulty |
|---|---|---|
| Natural Earth default | Download shapefile, spatial query at 44.95N 34.1E | Easy |
| Natural Earth POV variants | Download all 31 POVs, compare Crimea polygon SOV_A3 | Medium |
| GADM | Download UKR + RUS GeoPackages, check for Crimea | Easy |
| QGIS bundled data | Extract `world_map.gpkg` from QGIS install, query | Easy |
| OSM extracts | Download Ukraine + Russia PBFs, parse admin relations | Medium |
| ArcGIS REST services | Query World Countries feature service at Crimea coords | Easy |
| geoBoundaries | Use their API to query Ukraine admin boundaries | Easy |
| GeoPandas built-in | `geopandas.read_file(geopandas.datasets.get_path('naturalearth_lowres'))`, check Ukraine geometry | Easy |
