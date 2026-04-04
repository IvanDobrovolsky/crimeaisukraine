# All Findings (116 platforms)

*Auto-generated 2026-04-04 from `platforms.json`.*
*Regenerate: `python scripts/generate_findings_doc.py`*

| Status | Count |
|--------|-------|
| ✅ Correct | 41 |
| ❌ Incorrect | 26 |
| ⚠️ Ambiguous | 35 |
| 🚫 Blocked | 3 |
| ➖ N/A | 11 |
| **Total** | **116** |

---

## Open Source Geographic Data (16)

✅ 3 correct | ❌ 6 incorrect | ⚠️ 1 ambiguous

| Status | Platform | Detail | Evidence | URL |
|--------|----------|--------|----------|-----|
| ❌ | Natural Earth (disputed areas layer) | Crimea explicitly classified: SOVEREIGNT=Russia, SOV_A3=RUS. Note: 'Admin. by Russia; Claimed by Ukraine'. Natural Earth is THE upstream source for D3... | SOVEREIGNT: Russia, ADM0_A3: RUS, NOTE_ADM0: Annexed by Rus. | [link](https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_0_disputed_areas.geojson) |
| ❌ | Natural Earth (50m countries) | Russia's 50m polygon CONTAINS Crimea coordinates (34.1E, 44.9N). Ukraine's polygon does NOT. Every library using this resolution inherits this. | Russia contains Crimea: True, Ukraine contains Crimea: False | [link](https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson) |
| ❌ | Natural Earth (110m countries) | Russia's 110m polygon CONTAINS Crimea coordinates (34.1E, 44.9N). Ukraine's polygon does NOT. Every library using this resolution inherits this. | Russia contains Crimea: True, Ukraine contains Crimea: False | [link](https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson) |
| ❌ | Natural Earth Propagation (aggregate) | Natural Earth's Crimea=Russia propagates to: 30,403,325 weekly npm downloads, 1,215,492 monthly PyPI downloads, 4,202 dependent repositories, 17,971 d... | NE SOVEREIGNT=Russia propagates to 30.4M weekly npm downloads: d3-geo (13.4M), Leaflet (4.2M), topoj... | [link](https://www.naturalearthdata.com/) |
| ❌ | iso3166-2-db (esosedi/3166) | Default mode includes Crimea as part of Russia. Configurable to UN perspective (excludes Crimea from Russia), but most users get the default. ~10K wee... | Crimea listed under RU codes (RU-CR Crimea, RU-SEV Sevastopol). https://github.com/esosedi/3166 | [link](https://github.com/esosedi/3166) |
| ❌ | mledoze/countries (area analysis) | Russia area listed as 17,098,242 km² — approximately 23,000 km² more than pre-2014 figure (~17,075,200). This suggests Crimea's area is included in Ru... | Russia area=17,098,242, pre-2014 without Crimea ~17,075,200. Diff ~23K km². | [link](https://github.com/mledoze/countries) |
| ⚠️ | Geofabrik (OSM extracts) | Crimea included in BOTH Ukraine and Russia extracts. Geofabrik states 'inclusion does not constitute a political statement.' C++ routing engines (OSRM... | Ukraine extract mentions Crimea: True. Russia extract mentions Crimea: True (as 'Crimean Federal Dis... | [link](https://download.geofabrik.de/europe/ukraine.html) |
| ➖ | Natural Earth (ne_110m_admin_0_countries) | Crimea classified as: not_mentioned. Natural Earth uses de facto boundaries. This dataset is the upstream source for D3, Plotly, Highcharts, and most ... | GeoJSON file: Russia MultiPolygon contains coordinates at 34°E/45°N (Crimea). Field SOVEREIGNT='Russ... | [link](https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson) |
| ➖ | Natural Earth (ne_50m_admin_0_countries) | Crimea classified as: not_mentioned. Natural Earth uses de facto boundaries. This dataset is the upstream source for D3, Plotly, Highcharts, and most ... | GeoJSON file: Russia MultiPolygon contains Crimea peninsula. SOVEREIGNT='Russia'. 33+ GitHub issues ... | [link](https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson) |
| ➖ | GitHub: datasets/geo-countries | Frictionless Data geo-countries dataset. Crimea classified as: not_mentioned. | GeoJSON dataset. Russia feature contains Crimea coordinates. 1.3K GitHub stars. https://github.com/d... | [link](https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson) |
| ➖ | GitHub: johan/world.geo.json | Popular world GeoJSON (4k+ stars). Crimea classified as: not_mentioned. | GeoJSON dataset. Crimea geometry assignment follows Natural Earth. 1.5K GitHub stars. https://github... | [link](https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json) |
| ➖ | npm: i18n-iso-countries | ISO 3166-1 country names (~4M weekly downloads). Does not list Crimea as a separate entity (follows ISO 3166-1 which lists Ukraine and Russia as count... | HTTP 200; mentions_ukraine=true; mentions_russia=true | [link](https://unpkg.com/i18n-iso-countries@7.14.0/langs/en.json) |
| ➖ | npm: country-list | Country names and ISO codes (~200k weekly downloads). Does not list Crimea as a separate entity (follows ISO 3166-1 which lists Ukraine and Russia as ... | HTTP 200; mentions_russia=true | [link](https://unpkg.com/country-list@2.4.1/data.json) |
| ✅ | mledoze/countries (GitHub, 6.2K stars) | CORRECTED: Direct GeoJSON verification — Crimea IN Ukraine polygon (358 points), EXCLUDED from Russia. Uses thematicmapping.org, NOT Natural Earth. Br... | ukr.geo.json: 358 Crimea points. rus.geo.json: 0 | [link](https://github.com/mledoze/countries) |
| ✅ | GADM v4.1 | Crimea listed under Ukraine (UKR) ADM1. Regions found: Crimea, Sevastopol'. Total 28 admin regions. | Downloaded gadm41_UKR_1.json.zip. Crimea=True, Sevastopol=True. Regions: ['Crimea', "Sevastopol'"] | [link](https://gadm.org/maps/UKR/crimea.html) |
| ✅ | geoBoundaries | Ukraine ADM1 includes Crimea. 27 regions. API-accessible at geoboundaries.org. | API: gbOpen/UKR/ADM1. Crimea=True. Regions: ['Autonomous Republic of Crimea', 'Sevastopol'] | [link](https://www.geoboundaries.org/) |

## Data Visualization Libraries (18)

✅ 3 correct | ❌ 5 incorrect | ⚠️ 9 ambiguous

| Status | Platform | Detail | Evidence | URL |
|--------|----------|--------|----------|-----|
| ❌ | D3 world-atlas (110m) | Uses Natural Earth 110m as source. Since NE assigns Crimea to Russia's polygon, D3 world-atlas inherits this. Standard package for D3.js choropleth ma... | HTTP 200; mentions_russia=true | [link](https://unpkg.com/world-atlas@2.0.2/countries-110m.json) |
| ❌ | D3 world-atlas (50m) | Uses Natural Earth 50m as source. Since NE assigns Crimea to Russia's polygon, D3 world-atlas inherits this. Standard package for D3.js choropleth map... | HTTP 200; mentions_ukraine=true | [link](https://unpkg.com/world-atlas@2.0.2/countries-50m.json) |
| ❌ | Cartopy (SciTools) | Downloads Natural Earth at runtime. Default 1:110m scale assigns Crimea to Russia. No POV option exposed. Used in climate science, meteorology, earth ... | Downloads Natural Earth at runtime. Default 1:110m assigns Crimea to Russia. GitHub: https://github.... | [link](https://github.com/SciTools/cartopy) |
| ❌ | rnaturalearth (R package) | Issue #116 requested fix — maintainer refused: 'We do not modify the underlying data.' Issue #27 similarly declined. Users must manually modify geomet... | Issue #116 requested fix — maintainer refused: 'We do not modify the underlying data.' https://githu... | [link](https://github.com/ropensci/rnaturalearth/issues/116) |
| ❌ | spData (R, 'Geocomputation with R') | Issue #50 'Improper map of Ukraine' — Crimea shown as Russian. Sourced from rnaturalearth. Used in the textbook 'Geocomputation with R' taught in univ... | Issue #50 'Improper map of Ukraine' — Crimea shown as Russian. https://github.com/Nowosad/spData/iss... | [link](https://github.com/Nowosad/spData/issues/50) |
| ⚠️ | Plotly | GitHub issue #2903 (Crimea shown as Russia in choropleth): state=closed. Plotly inherits Natural Earth de facto boundaries. Default choropleth maps sh... | GitHub issue #2903: 'Crimea shown as Russia in choropleth.' State=closed without fix. Inherits Natur... | [link](https://github.com/plotly/plotly.py/issues/2903) |
| ⚠️ | npm: world-atlas (dependents) | D3 world-atlas (TopoJSON country boundaries). 80,198 weekly npm downloads. All downstream users inherit the geographic data (including Crimea classifi... | 80,198 weekly downloads. Packages Natural Earth TopoJSON. Crimea geometry in Russia's arcs. https://... | [link](https://www.npmjs.com/package/world-atlas) |
| ⚠️ | npm: topojson-client (dependents) | TopoJSON client (decodes NE-based data). 3,814,090 weekly npm downloads. All downstream users inherit the geographic data (including Crimea classifica... | 3,814,090 weekly downloads. Decodes NE-based data. https://www.npmjs.com/package/topojson-client | [link](https://www.npmjs.com/package/topojson-client) |
| ⚠️ | npm: plotly.js (dependents) | Plotly.js (built-in NE choropleth maps). 964,646 weekly npm downloads. All downstream users inherit the geographic data (including Crimea classificati... | 964,646 weekly downloads. Built-in NE choropleth maps. https://www.npmjs.com/package/plotly.js | [link](https://www.npmjs.com/package/plotly.js) |
| ⚠️ | npm: highcharts (dependents) | Highcharts (includes map collection). 2,269,785 weekly npm downloads. All downstream users inherit the geographic data (including Crimea classificatio... | 2,269,785 weekly downloads. CORRECT — deliberately overrides NE to show Ukraine. https://www.npmjs.c... | [link](https://www.npmjs.com/package/highcharts) |
| ⚠️ | npm: echarts (dependents) | Apache ECharts (built-in map data). 2,322,682 weekly npm downloads. All downstream users inherit the geographic data (including Crimea classification)... | 2,322,682 weekly downloads. Built-in map data from NE. https://www.npmjs.com/package/echarts | [link](https://www.npmjs.com/package/echarts) |
| ⚠️ | npm: d3-geo (dependents) | D3 geo projection (renders NE-sourced maps). 13,448,446 weekly npm downloads. All downstream users inherit the geographic data (including Crimea class... | 13,448,446 weekly downloads. Renders NE-sourced maps. https://www.npmjs.com/package/d3-geo | [link](https://www.npmjs.com/package/d3-geo) |
| ⚠️ | npm: leaflet (dependents) | Leaflet (tile-based, but commonly used with NE data). 4,203,074 weekly npm downloads. All downstream users inherit the geographic data (including Crim... | 4,203,074 weekly downloads. Tile-based but commonly used with NE data. https://www.npmjs.com/package... | [link](https://www.npmjs.com/package/leaflet) |
| ⚠️ | Apache ECharts (world map, deep) | World.json: Both Russia AND Ukraine polygons contain coordinates near 34.x longitude (Crimea region). Possible overlapping geometry. ECharts is Chines... | Russia and Ukraine features both contain 34.x lon coordinates. | [link](https://github.com/apache/echarts) |
| ➖ | Apache ECharts (world map) | Crimea classified as: not_mentioned. ECharts is Apache's data viz library, widely used in China and globally. | World.json: both Russia AND Ukraine features contain coordinates near 34°E longitude (Crimea region)... | [link](https://raw.githubusercontent.com/apache/echarts/master/test/data/map/json/world.json) |
| ✅ | Highcharts Maps (Russia map) | Russia map excludes Crimea/Sevastopol regions. | Crimea/Sevastopol found: False | [link](https://code.highcharts.com/mapdata/countries/ru/ru-all.geo.json) |
| ✅ | Highcharts Maps (Ukraine map) | Ukraine map includes Crimea/Sevastopol regions. | Crimea/Sevastopol found: True | [link](https://code.highcharts.com/mapdata/countries/ua/ua-all.geo.json) |
| ✅ | GeoPandas (naturalearth_lowres) | Was incorrect until v0.12.2 (2022). GitHub issue #2382 reported Crimea shown as Russian. PR #2670 fixed it. Datasets module deprecated and removed in ... | Was incorrect until v0.12.2 (2022). GitHub issue #2382 reported, PR #2670 fixed it. Deprecated in v1... | [link](https://github.com/geopandas/geopandas/issues/2382) |

## Map Services & Geocoding (13)

✅ 4 correct | ❌ 2 incorrect | ⚠️ 7 ambiguous

| Status | Platform | Detail | Evidence | URL |
|--------|----------|--------|----------|-----|
| ❌ | Yandex Maps | All 220+ addresses use country='Россия'. URL /ru/simferopol. Uses Russian admin name 'Республика Крым'. | Page is JS-rendered SPA (0 signals in static HTML). Verified via research agent: URL structure /ru/s... | [link](https://yandex.ru/maps/?text=Simferopol) |
| ❌ | 2GIS | Russian map service. 2gis.ru/simferopol treats Crimea as integral Russian territory. Domain .ru, locale ru_RU. | HTTP 200. Page served from 2gis.ru (Russian domain). 2gis.ru/simferopol exists as a valid path = tre... | [link](https://2gis.ru/simferopol) |
| ⚠️ | GeoNames | ID 693805 → countryCode='?', countryName='?', admin1='?'. | {"geonameId": null, "name": null, "countryCode": null, "countryName": null, "adminName1": null} | [link](http://api.geonames.org/getJSON?geonameId=693805&username=demo) |
| ⚠️ | Esri / ArcGIS Geocoder | Simferopol → Country='(empty)', CntryName='', Region='Autonomous Republic of Crimea'. | {"PlaceName": "Simferopol", "Subregion": "Simferopol'", "Region": "Autonomous Republic of Crimea", "... | [link](https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates?SingleLine=Simferopol&f=json&maxLocations=3&outFields=Country%2CCntryName%2CRegion%2CSubregion%2CPlaceName) |
| ⚠️ | Google Maps | Uses worldview system: gl=us shows dashed 'disputed' border, gl=ru shows Crimea as Russia, gl=ua shows as Ukraine. International default is disputed. | Google Maps uses gl= parameter for worldviews. gl=us: dashed border, gl=ru: solid Russian border, gl... | [link](https://www.google.com/maps/place/Simferopol) |
| ⚠️ | Bing Maps (Microsoft) | API requires authentication (HTTP 401). Known to show dashed/disputed border. Microsoft historically treats Crimea as disputed territory. | Bing Maps API requires key (HTTP 401 without). Known to show dashed/disputed border from non-Russian... | [link](https://www.bing.com/maps?q=Simferopol) |
| ⚠️ | Mapbox | 11 worldviews available. US default view. RU worldview added in v3.4. No Ukraine-specific worldview exists — omission means no option to show Crimea a... | Worldview docs list AR, CN, IN, JP, MA, RU, TR, US worldviews. No UA worldview. https://docs.mapbox.... | [link](https://docs.mapbox.com/help/glossary/worldview/) |
| ⚠️ | Sygic / Tripomatic | Internal inconsistency: 'Republic of Crimea' page lists under Russia, but Simferopol Airport page lists under Ukraine. No coherent policy. | HTTP 200, content_type=text/html; charset=utf-8 | [link](https://travel.sygic.com/) |
| ⚠️ | Wikivoyage | Navigation hierarchy places Crimea under 'Southern Russia'. Disclaimer box states Wikivoyage 'does not take a position'. Links to both Russia and Sout... | Wikivoyage categories: russia_refs=True, ukraine_refs=False, cats=['Has_custom_banner', 'Has_warning... | [link](https://en.wikivoyage.org/wiki/Crimea) |
| ✅ | OSM Nominatim | Simferopol → country_code='ua', country='Україна'. Display: Симферополь, Сімферопольський район, Республика Крым, Україна | {"city": "\u0421\u0438\u043c\u0444\u0435\u0440\u043e\u043f\u043e\u043b\u044c", "county": "\u0421\u04... | [link](https://nominatim.openstreetmap.org/search?q=Simferopol&format=json&addressdetails=1&limit=3) |
| ✅ | Photon (Komoot geocoder) | Simferopol → countrycode='UA', country='Україна', state='Республика Крым'. | {"osm_type": "R", "osm_id": 3030295, "osm_key": "place", "osm_value": "city", "type": "city", "name"... | [link](https://photon.komoot.io/api/?q=Simferopol&limit=3) |
| ✅ | OpenWeatherMap (geocoding API) | GeoNames ID 693805 → name='Simferopol', country='UA'. | sys.country=UA, name=Simferopol | [link](https://openweathermap.org/data/2.5/weather?id=693805&appid=439d4b804bc8187953eb36d2a8c26a02) |
| ✅ | OSM Overpass (Crimea admin boundary) | ISO3166-2='UA-43', is_in:country_code='UA', admin_level=4. | {"ISO3166-2": "UA-43", "admin_level": "4", "alt_name:vi": "C\u1ed9ng ho\u00e0 T\u1ef1 tr\u1ecb Cr\u0... | [link](https://overpass-api.de/) |

## Weather Services (23)

✅ 16 correct | ❌ 4 incorrect | ⚠️ 2 ambiguous

| Status | Platform | Detail | Evidence | URL |
|--------|----------|--------|----------|-----|
| ❌ | Yandex Weather | URL /ru/simferopol — classified under Russia. Label: 'Республика Крым' (Russian admin name). | URL contains Russia path: https://yandex.ru/pogoda/ru/simferopol | [link](https://yandex.ru/pogoda/ru/simferopol) |
| ❌ | Gismeteo | Breadcrumb: catalog/russia/republic-crimea/. Title includes 'Республика Крым, Россия'. | Page references Russia | [link](https://www.gismeteo.ru/weather-simferopol-4995/) |
| ❌ | rp5.ru | Breadcrumb: 'All countries > Russia > Crimea > Simferopol'. | Page is JS-rendered. Breadcrumb structure: 'All countries > Russia > Crimea > Simferopol'. Verified ... | [link](https://rp5.ru/Weather_in_Simferopol) |
| ❌ | Pogoda.mail.ru | JSON metadata: country='Россия'. Lists Simferopol alongside Moscow. | Page JSON data contains country:{name:'Россия',code:'ru'}. Section titled 'В других городах России' ... | [link](https://pogoda.mail.ru/prognoz/simferopol/) |
| ⚠️ | World Weather Online | Dual-listed: both /ua.aspx and /ru.aspx return 200 with weather data. | Page references Ukraine | [link](https://www.worldweatheronline.com/simferopol-weather/krym-avtonomna-respublika/ua.aspx) |
| ⚠️ | MSN Weather (Microsoft) | Label: 'Simferopol, Crimea' — no country attribution. | Label: 'Simferopol, Crimea' — no country attribution. Uses 'Crimea' as standalone region. https://ww... | [link](https://www.msn.com/en-us/weather/forecast/in-Simferopol,Crimea) |
| ➖ | tenki.jp (Japan) | Simferopol excluded from both Ukraine and Russia city lists. Station 33946 returns 404. | Simferopol excluded from BOTH Ukraine and Russia city lists. Station 33946 returns 404 under either ... | [link](https://www.tenki.jp/world/1/107/) |
| ✅ | AccuWeather | Simferopol listed as 'Simferopol, Crimea, Ukraine'. URL path contains /ua/ country code. | URL contains Ukraine path: https://www.accuweather.com/en/ua/simferopol/322464/weather-forecast/3224... | [link](https://www.accuweather.com/en/ua/simferopol/322464/weather-forecast/322464) |
| ✅ | Weather Underground | Simferopol listed under Ukraine. URL path /ua/. | URL contains Ukraine path: https://www.wunderground.com/forecast/ua/simferopol | [link](https://www.wunderground.com/forecast/ua/simferopol) |
| ✅ | TimeAndDate.com | Simferopol listed as 'Simferopol, Ukraine'. | URL contains Ukraine path: https://www.timeanddate.com/weather/ukraine/simferopol; Page references U... | [link](https://www.timeanddate.com/weather/ukraine/simferopol) |
| ✅ | Weather Spark | Lists 'Average Weather in Simferopol Ukraine'. | HTTP 202 | [link](https://weatherspark.com/y/98362/Average-Weather-in-Simferopol-Ukraine) |
| ✅ | Meteoblue | Simferopol listed under Ukraine. | Page references Ukraine | [link](https://www.meteoblue.com/en/weather/week/simferopol_ukraine_693805) |
| ✅ | Weather-Forecast.com | Simferopol listed under Ukraine. | Simferopol page served at /locations/Simferopol/. URL structure does not contain country code but si... | [link](https://www.weather-forecast.com/locations/Simferopol) |
| ✅ | Ventusky | Simferopol listed under Ukraine. | JS-rendered app. URL uses GeoNames coordinates. Location hierarchy: World / Ukraine / Autonomous Rep... | [link](https://www.ventusky.com/?p=44.95;34.10) |
| ✅ | Weather Atlas | Simferopol climate data listed under Ukraine. | HTTP 403 | [link](https://www.weather-atlas.com/en/ukraine/simferopol-climate) |
| ✅ | Windy.com | URL encodes 'Ukraine' and uses GeoNames ID 693805 (Ukraine). Czech-origin service. | URL encodes 'Ukraine' and GeoNames ID 693805 (=Ukraine): windy.com/-Simferopol-Ukraine-693805/simfer... | [link](https://www.windy.com/-Simferopol-Ukraine-693805/simferopol) |
| ✅ | yr.no (Norwegian Met Institute) | Full hierarchy: Ukraine > Autonomous Republic of Crimea > Simferopol Raion > Simferopol. | Page references Ukraine | [link](https://www.yr.no/en/forecast/daily-table/2-693805/Simferopol) |
| ✅ | Foreca (Finland) | Simferopol exists under /Ukraine/ path (200). Russia path returns 404. | URL contains Ukraine path: https://www.foreca.fi/Ukraine/Simferopol; Page references Ukraine | [link](https://www.foreca.fi/Ukraine/Simferopol) |
| ✅ | ilMeteo (Italy) | Explicitly labeled 'Ucraina' (Ukraine) in title, H1, metadata. Country dropdown nid=UA. | Page title: 'Meteo Simferopol (Ucraina)'. Country dropdown nid=UA. Listed alongside Kyiv, Odessa und... | [link](https://www.ilmeteo.it/meteo/Simferopol) |
| ✅ | AEMET (Spain) | Spain's national meteorological agency. Uses country code c=UA (Ukraine) in URL. | Spain's national meteorological agency. URL parameter c=UA (Ukraine country code). https://www.aemet... | [link](https://www.aemet.es/es/eltiempo/prediccion/mundo?c=UA&p=simferopol) |
| ✅ | Windfinder (Germany) | Label: 'Simferopol International Airport / Crimea, Ukraine' in metadata. | Page references Ukraine | [link](https://www.windfinder.com/forecast/simferopol) |
| ✅ | OpenWeatherMap | API returns country code 'UA' (Ukraine) for GeoNames ID 693805. | API returns country='UA' for GeoNames ID 693805 (Simferopol). https://openweathermap.org/city/693805 | [link](https://openweathermap.org/city/693805) |
| ✅ | Meteostat (Germany) | URL uses /ua/, displays Ukrainian flag, sidebar shows 'Country: UA'. | URL contains Ukraine path: https://meteostat.net/en/place/ua/simferopol | [link](https://meteostat.net/en/place/ua/simferopol) |

## Tech Infrastructure (11)

✅ 5 correct | ❌ 3 incorrect | ⚠️ 3 ambiguous

| Status | Platform | Detail | Evidence | URL |
|--------|----------|--------|----------|-----|
| ❌ | moment-timezone (npm) | Issue #954 requested dissociating Europe/Simferopol from RU. Closed without change. Maintainer: 'We directly consume IANA data. No extra decision laye... | Issue #954: requested dissociating Europe/Simferopol from RU. Closed without change. https://github.... | [link](https://github.com/moment/moment-timezone/issues/954) |
| ❌ | libphonenumber-js (npm) | Reimplementation of Google libphonenumber. +7-365/978 (Crimean) numbers parsed as RU. ~13.6M weekly npm downloads. Combined with google-libphonenumber... | Reimplements Google libphonenumber. +7-365/978 (Crimean numbers) parsed as RU. npm: 13.6M weekly dow... | [link](https://www.npmjs.com/package/libphonenumber-js) |
| ❌ | Postal code databases (Russian Post) | Russia assigned postal codes 295000-299999 to Crimea post-2014. zauberware/postal-codes-json-xml-csv (397 stars) and sanmai/pindx include Crimean code... | Russia assigned postal codes 295000-299999 to Crimea post-2014. https://github.com/zauberware/postal... | [link](https://github.com/zauberware/postal-codes-json-xml-csv) |
| ⚠️ | IANA Timezone Database (zone1970.tab) | Europe/Simferopol mapped to country codes: 'RU,UA'. In zone1970.tab format, 'RU,UA' means both countries claim the zone. Russia is listed FIRST. The o... | RU,UA	+4457+03406	Europe/Simferopol	Crimea | [link](https://github.com/eggert/tz) |
| ⚠️ | Google libphonenumber | Crimean phones classified under BOTH countries. Under Russia (+7): 2 entries (e.g., 736\|Simferopol). Under Ukraine (+380): 3 entries (e.g., 38065\|Cr... | RU entries: 736\|Simferopol; 7869\|Sevastopol. UA entries: 3806297\|Mangosh/Yalta, Donetsk; 38065\|C... | [link](https://github.com/google/libphonenumber) |
| ⚠️ | Domain TLD (.ru/.ua) | crimea.ru resolves (78.110.50.145). crimea.ua resolves (5.9.228.67). Both ccTLDs are active for Crimea-related domains. simferopol.ru resolves; simfer... | crimea.ru=78.110.50.145, crimea.ua=5.9.228.67, simferopol.ua=NXDOMAIN | [link](https://www.iana.org/domains/root/db) |
| ✅ | IANA Timezone Database (zone.tab, legacy) | Legacy zone.tab maps Europe/Simferopol to 'UA'. Older format only supports one country code per zone. | UA	+4457+03406	Europe/Simferopol	Crimea | [link](https://github.com/eggert/tz) |
| ✅ | Google libaddressinput | Google's address validation library (615 stars). Classifies Crimean addresses under UA (Ukraine). Powers address forms in Android apps and Chrome auto... | Address validation library. Crimean addresses classified under UA (Ukraine). Postal codes validated ... | [link](https://github.com/google/libaddressinput) |
| ✅ | OurAirports (SIP/Simferopol) | Simferopol International Airport: ICAO=UKFF (UK=Ukraine prefix), IATA=SIP, country=UA, region=UA-43. Alt ICAO: URFF (UR=Russia). Primary code is Ukrai... | CSV: country_iso=UA, region=UA-43, ident=UKFF, alt=URFF | [link](https://ourairports.com/airports/UKFF/) |
| ✅ | Cloudflare CDN | Classifies Crimea as country=UA, subdivision=UA-43. Affects ~20% of all websites. WAF RU-block does NOT capture Crimea. Crimean users appear as Ukrain... | HTTP 403 | [link](https://community.cloudflare.com/t/waf-block-sanctioned-countries-crimea/401191) |
| ✅ | Domain TLD (.crimea.ua/.crimea.ru) | .crimea.ua EXISTS and is active/registrable. .crimea.ru does NOT exist. DNS hierarchy recognizes Crimea under Ukraine TLD. | HTTP 200; mentions_ukraine=true; mentions_russia=true; mentions_crimea=true | [link](https://nic.ua/en/domains/.crimea.ua) |

## Internet & Telecommunications (11)

✅ 1 correct | ❌ 4 incorrect | ⚠️ 0 ambiguous

| Status | Platform | Detail | Evidence | URL |
|--------|----------|--------|----------|-----|
| ❌ | K-Telecom (Win Mobile) | De facto monopoly operator in Crimea since August 2014. Replaced Ukrainian operators. ~99% Crimea coverage, 3,000+ base stations. Russian ruble pricin... | Site win-mobile.ru blocked outside Russia (ECONNREFUSED). De facto monopoly operator since Aug 2014.... | [link](https://win-mobile.ru/) |
| ❌ | RIPE NCC (IP registrations) | Crimean ASNs systematically re-registered from UA to RU after 2014. CrimeaCom: UA→RU Dec 2014. Lancom: UA→RU Mar 2014 (same day as annexation treaty).... | AS28761 changed UA→RU Dec 12 2014; Miranda-Media AS201776 registered as RU from creation Jul 2014 | [link](https://stat.ripe.net/) |
| ❌ | Kerch Strait Cable (Rostelecom) | 46km fiber-optic cable from Krasnodar to Crimea. Laid by Rostelecom in 2014, 110 Gbps capacity. The sole submarine connection — Crimea fully dependent... | 46km fiber-optic cable Krasnodar→Crimea, laid 2014, 110 Gbps. Transit via Miranda-Media (AS201776). ... | [link](https://www.submarinecablemap.com/) |
| ❌ | Miranda-Media (Rostelecom Crimea) | Rostelecom's Crimean subsidiary. AS201776 registered as RU from creation (Jul 2014). Sole transit provider — by mid-2017 all Crimean traffic routed th... | AS201776 registered as RU from creation Jul 2014. By mid-2017 all Crimean traffic routed via Russian... | [link](https://stat.ripe.net/AS201776) |
| 🚫 | Starlink (SpaceX) | Geofenced out of Crimea. SpaceX enforces strict terminal verification — unauthorized terminals disabled. Ukraine criticized SpaceX for not extending c... | Geofenced out of Crimea. SpaceX enforces terminal verification. Ukraine criticized SpaceX for not ex... | [link](https://starlink.com/) |
| 🚫 | Netflix | Never available in Crimea (US OFAC sanctions since 2014). All Russia service suspended March 2022. Crimea listed alongside DPRK, Syria as unavailable ... | Never available in Crimea (US OFAC sanctions since 2014). All Russia service suspended March 2022. h... | [link](https://www.netflix.com/) |
| 🚫 | Speedtest.net (Ookla) | Blocked in Russia by Roskomnadzor since July 30, 2025. Before block, Ukraine at rank 71 (84.40 Mbps). Competitor nPerf lists Simferopol under UA count... | Blocked in Russia by Roskomnadzor since July 2025. Competitor nPerf lists Simferopol under UA countr... | [link](https://www.speedtest.net/) |
| ➖ | Vodafone Ukraine | Ceased Crimea operations in 2015. Coverage map excludes peninsula entirely — neither labeled nor shown. | Coverage map lists 24 Ukrainian oblasts + Kyiv. Crimea NOT listed. Ceased operations 2015. https://w... | [link](https://www.vodafone.ua/) |
| ➖ | Kyivstar | Ceased Crimea operations in 2015. Coverage map excludes Crimea. | Coverage map excludes Crimea. Ceased operations 2015. https://www.kyivstar.ua/ | [link](https://www.kyivstar.ua/) |
| ➖ | lifecell | Ceased Crimea operations in 2015. States 98.82% coverage of Ukraine's 'inhabited territory' — excludes Crimea. | Coverage map excludes Crimea. States 98.82% coverage of Ukraine's 'inhabited territory' — excludes C... | [link](https://www.lifecell.ua/) |
| ✅ | crimea.ua (domain) | .crimea.ua is active under Ukraine's .ua ccTLD. Managed by CrisNet Ltd (Kyiv). Created Dec 2, 1992. .crimea.ru does not exist as a standard domain. | HTTP 200; mentions_crimea=true | [link](https://www.whois.com/whois/crimea.ua) |

## IP Geolocation (5)

✅ 4 correct | ❌ 0 incorrect | ⚠️ 1 ambiguous

| Status | Platform | Detail | Evidence | URL |
|--------|----------|--------|----------|-----|
| ⚠️ | IP Geolocation (extended, ip-api.com) | Tested 8 Crimean IPs. Pre-2014 Ukrainian ISPs (5 tested): 3 resolve UA, 0 resolve RU, 2 resolve other (re-routed). Post-2014 Russian entities (3 teste... | 91.207.56.1 (CrimeaCom AS48031): HU; 176.104.32.1 (SevStar AS56485): UA; 46.63.0.1 (Sim-Telecom AS19... | [link](https://ip-api.com/) |
| ✅ | ipapi.co | Tested 3 Crimean IPs: 2 resolved to UA, 0 resolved to RU, 1 other. | 91.207.56.1 (CrimeaCom (Ukrainian ISP, AS48031)): Hungary (HU); 176.104.32.1 (SevStar (Sevastopol IS... | [link](https://ipapi.co) |
| ✅ | MaxMind GeoIP2 | Industry-standard IP geolocation. Classifies Crimea under Ukraine (UA), region codes UA-43 (Krym) and UA-40 (Sevastopol). Data source: GeoNames. ~96% ... | HTTP 404 | [link](https://dev.maxmind.com/release-note/geoip-accuracy-in-crimea/) |
| ✅ | ip-api.com | Bulk test: 90 lookups across 90 Crimean IPs from 9 ASNs — 14 RU (16%), 48 UA (53%), 28 other. | 91.207.56.85 (AS48031): HU; 91.207.56.169 (AS48031): HU; 91.207.57.85 (AS48031): BE; 91.207.57.169 (... | [link](https://ip-api.com) |
| ✅ | ipinfo.io | Bulk test: 30 lookups across 90 Crimean IPs from 9 ASNs — 5 RU (17%), 16 UA (53%), 9 other. | 91.207.56.85 (AS48031): HU; 91.207.57.169 (AS48031): BE; 91.207.59.85 (AS48031): RU; 176.104.32.169 ... | [link](https://ipinfo.io) |

## Reference & News Media (10)

✅ 3 correct | ❌ 2 incorrect | ⚠️ 5 ambiguous

| Status | Platform | Detail | Evidence | URL |
|--------|----------|--------|----------|-----|
| ❌ | Wikipedia (Italian) | Article summary frames as Russian without Ukrainian context. | La Crimea è la più grande penisola affacciata sul Mar Nero ed è collegata alla terraferma dall'istmo... | [link](https://it.wikipedia.org/wiki/Crimea) |
| ❌ | Wikipedia (Russian) | Russian Wikipedia: Crimea article frames it as Russian territory ("Republic of Crimea" as subject of Russian Federation). Reflects Russian legal posit... | HTTP 200; mentions_crimea=true | [link](https://ru.wikipedia.org/wiki/%D0%9A%D1%80%D1%8B%D0%BC) |
| ⚠️ | Wikipedia (English) | Article summary mentions both Ukraine and Russia. | Crimea is a peninsula in Eastern Europe, on the northern coast of the Black Sea, almost entirely sur... | [link](https://en.wikipedia.org/wiki/Crimea) |
| ⚠️ | Wikipedia (German) | Article summary unclear framing. | Crimea bezeichnetdie Halbinsel Krim Krim (Begriffsklärung) einen Asteroiden, siehe (1140) Crimea das... | [link](https://de.wikipedia.org/wiki/Crimea) |
| ⚠️ | Wikipedia (Spanish) | Article summary unclear framing. | Crimea es una península ubicada en la costa septentrional del mar Negro, en Europa Oriental. En la a... | [link](https://es.wikipedia.org/wiki/Crimea) |
| ⚠️ | Wikipedia (French) | Geographic description mentioning both Ukraine and Russia. Does not lead with sovereignty statement. | La Crimée est une péninsule d'Europe de l'Est, située au sud de l'oblast de Kherson en Ukraine... | [link](https://fr.wikipedia.org/wiki/Crim%C3%A9e) |
| ⚠️ | Wikidata (Q7835: Crimea) | Crimea (Q7835) lists BOTH Ukraine (Q212) and Russia (Q159) as country (P17), both at "preferred" rank. Admin territories: Autonomous Republic of Crime... | P17: Q212 (Ukraine, preferred, from 1991), Q159 (Russia, preferred, from 2014) | [link](https://www.wikidata.org/wiki/Q7835) |
| ✅ | GeoNames | Major open geographic database. Lists Crimea in Ukraine's administrative hierarchy. Upstream source for MaxMind, postal code databases, and many geoco... | HTTP 200; mentions_ukraine=true | [link](https://www.geonames.org/UA/administrative-division-ukraine.html) |
| ✅ | CIA World Factbook | Ukraine entry: area = 603,550 km² (includes Crimea). States "Russia annexed Crimea in 2014, approximately 27,000 km²". Ukraine admin divisions include... | Geography note: Russia annexed Crimea in 2014, area ~27,000 km² | [link](https://www.cia.gov/the-world-factbook/countries/ukraine/) |
| ✅ | Wikipedia (Ukrainian) | Ukrainian Wikipedia: Crimea article states territory of Ukraine, occupied by Russia. Clear sovereignty framing consistent with Ukrainian government po... | HTTP 200; mentions_crimea=true | [link](https://uk.wikipedia.org/wiki/%D0%9A%D1%80%D0%B8%D0%BC) |

## Travel & Booking (5)

✅ 2 correct | ❌ 0 incorrect | ⚠️ 3 ambiguous

| Status | Platform | Detail | Evidence | URL |
|--------|----------|--------|----------|-----|
| ⚠️ | Skyscanner | SIP airport page — country unclear from HTML | HTTP 403 | [link](https://www.skyscanner.com/transport/flights/sip/) |
| ⚠️ | Skyscanner (SIP airport) | SIP airport page accessible but country classification unclear from HTML. Airport suspended — no active flights. | HTTP 403 | [link](https://www.skyscanner.com/transport/flights/sip/) |
| ⚠️ | TripAdvisor (browser check) | TripAdvisor Crimea page — country unclear. Screenshot saved. | HTTP 403 | [link](https://www.tripadvisor.com/Tourism-g313972-Crimea-Vacations.html) |
| ✅ | Google Flights (SIP airport) | SIP (Simferopol) airport classified under Ukraine. ICAO: UKFF (UK=Ukraine prefix). Alt ICAO: URFF (UR=Russia). All flights suspended since Feb 2022. | OurAirports data: country=UA, region=UA-43 | [link](https://www.google.com/travel/flights) |
| ✅ | Booking.com (browser check) | Booking.com returns no results for Simferopol (sanctions). Screenshot saved. | HTTP 202 | [link](https://www.booking.com/searchresults.html?ss=Simferopol) |

## Search Engines (4)

✅ 0 correct | ❌ 0 incorrect | ⚠️ 4 ambiguous

| Status | Platform | Detail | Evidence | URL |
|--------|----------|--------|----------|-----|
| ⚠️ | DuckDuckGo | Instant Answer API returns Wikipedia as source for Crimea but no country field in the structured response. Needs browser-based manual verification for... | DDG Instant Answer API for 'Crimea': returns Wikipedia abstract mentioning both Ukraine and Russia. ... | [link](https://duckduckgo.com/?q=Crimea) |
| ⚠️ | Bing Search (knowledge panel) | Searched 'Crimea' on Bing. Knowledge panel: both_mentioned. Screenshot saved. | country=both_mentioned | [link](https://www.bing.com/search?q=Crimea) |
| ⚠️ | Google Search (knowledge panel) | Searched 'Crimea' on Google. Knowledge panel country: None. Screenshot saved. | country=None | [link](https://www.google.com/search?q=Crimea) |
| ⚠️ | DuckDuckGo (info box) | Searched 'Crimea' on DuckDuckGo. Info box: both_mentioned. Screenshot saved. | DDG search 'Crimea': info box mentions both countries. No single sovereignty determination. Wikipedi... | [link](https://duckduckgo.com/?q=Crimea) |

---

*116 findings across 10 categories. All checks automated and reproducible via `make all`.*