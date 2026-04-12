# Weather Services: Mostly Correct, Not for Free

**Headline:** 12 of 25 weather services classify Simferopol as Ukrainian on both URL and visible UI. All 3 incorrect services are Russian-origin and legally compelled under Federal Law 377-FZ. Weather.com displays Simferopol as `"Simferopol, Simferopol"` -- erasure by omission. Apple WeatherKit and Google Search weather panel are untested (worldview-split hypothesis cannot be verified from a single vantage point).

## Key findings

1. **12 / 25 services** are unambiguously correct on both URL path and `<title>`.
2. **All 3 incorrect services are Russian-origin** (Yandex Weather, rp5.ru, Pogoda.mail.ru) -- legally compelled under [377-FZ](https://www.consultant.ru/document/cons_doc_LAW_170447/). No Western service classifies Crimea as Russian.
3. **Weather.com displays `"Simferopol, Simferopol"`** -- country name replaced by city-name repetition. URL structure routes to UA but the visible label is erased.
4. **AccuWeather's autocomplete** returns both `country=UA` (default) and `country=RU` entries for Simferopol. Default routing is correct, but the RU duplicate exists.
5. **Apple WeatherKit / Google Search weather panel** are `untested` -- conditional rendering keyed to viewer IP/region makes single-vantage-point verification impossible.
6. **Timezone probe**: 3 services reference `Europe/Simferopol` in HTML; 0 reference `Europe/Moscow`.
7. **3 services unreachable** (Weather Atlas, Windfinder, Gismeteo) -- CDN anti-bot blocks automated auditing.

## Status distribution

| Status | Count | Services |
|---|---:|---|
| Correct | 12 | AccuWeather, Weather Underground, TimeAndDate, Weather Spark, Meteoblue, Weather-Forecast.com, yr.no, Foreca, ilMeteo, AEMET, Meteostat, World Weather Online |
| URL-correct, UI-ambiguous | 4 | Weather.com, Ventusky, Windy.com, MSN Weather |
| Incorrect (all Russian) | 3 | Yandex Weather, rp5.ru, Pogoda.mail.ru |
| Unreachable | 3 | Weather Atlas, Windfinder, Gismeteo |
| Untested | 2 | Apple WeatherKit, Google Search weather panel |
| N/A | 1 | tenki.jp |

## Status taxonomy

| Status | Definition |
|---|---|
| Correct | URL path and `<title>` both attribute Simferopol to Ukraine |
| URL-correct, UI-ambiguous | URL routes to UA but visible label strips the country |
| Incorrect | Attributes Simferopol to Russia |
| Untested | Requires signed dev token or Russian IP proxy |
| Unreachable | CDN anti-bot blocked the scanner |
| N/A | Simferopol not in the service |

**Methodology:** 4-signal live scanner (URL path, `<title>` tag, body/breadcrumb, timezone reference). Ground truth: [GeoNames 693805](https://sws.geonames.org/693805/about.rdf) `countryCode: UA`, fetched at scan time.

## Data

- Manifest: `data/manifest.json`
- Scan script: `scan.py`

## Run

```bash
make pipeline-weather
```

Runs `scan.py` against all 25 services, fetches GeoNames ground truth, writes `data/manifest.json`, rebuilds `site/src/data/master_manifest.json`. Set `OWM_API_KEY` for OpenWeatherMap verification.

## Sources

- [GeoNames 693805](https://sws.geonames.org/693805/about.rdf) | [ISO 3166-2:UA](https://www.iso.org/obp/ui/#iso:code:3166:UA)
- [IANA zone1970.tab](https://www.iana.org/time-zones) | [Russian Federal Law 377-FZ](https://www.consultant.ru/document/cons_doc_LAW_170447/)
- [Apple WeatherKit](https://developer.apple.com/weatherkit/) | [yr.no](https://www.yr.no/)
- [Council Regulation (EU) 692/2014](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014R0692)
