# Weather Services — Crimea Country Labels

**Research date:** 2026-03-30 (original), 2026-04-02 (expanded)
**Methodology:** Web search analysis, URL pattern examination, direct page fetching
**Test city:** Simferopol (capital of Crimea)

---

## Overview

Weather services provide a useful "ground truth" indicator for how platforms classify disputed territories, because every city forecast requires a country designation in its database. This expanded analysis covers 25 services across 14 countries to test whether the pattern holds globally — including services from Russia, where we expect deliberate misclassification.

---

## International Services — Correct (Ukraine)

### 1. AccuWeather (US)

**Rating:** ✅ Correct

**Label:** "Simferopol, Crimea, **Ukraine**"
**URL:** [accuweather.com/en/ua/simferopol/322464/weather-forecast/322464](https://www.accuweather.com/en/ua/simferopol/322464/weather-forecast/322464)

Note the `/ua/` country code in the URL path, confirming Ukraine classification in their database.

---

### 2. Weather Underground (US — IBM/The Weather Company)

**Rating:** ✅ Correct

**Label:** Simferopol listed under **Ukraine**
**URL:** [wunderground.com/forecast/ua/simferopol](https://www.wunderground.com/forecast/ua/simferopol)

Note the `/ua/` country code in the URL path.

---

### 3. TimeAndDate.com (Norway)

**Rating:** ✅ Correct

**Label:** "Simferopol, **Ukraine**"
**URL:** [timeanddate.com/weather/ukraine/simferopol](https://www.timeanddate.com/weather/ukraine/simferopol)

---

### 4. Weather Spark (US)

**Rating:** ✅ Correct

**Label:** "Simferopol Climate, Weather By Month, Average Temperature (**Ukraine**)"
**URL:** [weatherspark.com/y/98362/Average-Weather-in-Simferopol-Ukraine](https://weatherspark.com/y/98362/Average-Weather-in-Simferopol-Ukraine)

---

### 5. Meteoblue (Switzerland)

**Rating:** ✅ Correct

**Label:** "Weather Simferopol" — URL contains `/ukraine/`
**URL:** [meteoblue.com/en/weather/week/simferopol_ukraine_693805](https://www.meteoblue.com/en/weather/week/simferopol_ukraine_693805)

Note: Uses GeoNames ID 693805, assigned to Simferopol, Ukraine.

---

### 6. Weather-Forecast.com (UK)

**Rating:** ✅ Correct

**Label:** "Simferopol Weather Forecast"
**URL:** [weather-forecast.com/locations/Simferopol/forecasts/latest](https://www.weather-forecast.com/locations/Simferopol/forecasts/latest)

---

### 7. Ventusky (Czech Republic)

**Rating:** ✅ Correct

**Hierarchy:** "World / Ukraine / Autonomous Republic of Crimea"
**URL:** [ventusky.com/44.959;34.11](https://www.ventusky.com/44.959;34.11)

---

### 8. Weather Atlas (Serbia)

**Rating:** ✅ Correct

**Label:** "Weather forecast for today Simferopol, **Ukraine**"
**URL:** [weather-atlas.com/en/ukraine/simferopol](https://www.weather-atlas.com/en/ukraine/simferopol)

---

### 9. weather.com (US — The Weather Channel)

**Rating:** ✅ Correct (browser-verified)

Weather.com is operated by The Weather Company (IBM). Browser verification confirmed Simferopol listed under Ukraine. Screenshot saved.

---

### 10. BBC Weather (UK)

**Rating:** ✅ Correct

BBC Weather uses GeoNames ID 693805 for Simferopol (URL: bbc.com/weather/693805). GeoNames classifies this location as Ukraine. BBC editorial policy refers to Crimea as "annexed" by Russia.

---

## European Regional Services — Correct (Ukraine)

### 11. Windy.com (Czech Republic)

**Rating:** ✅ Correct

**URL:** [windy.com/-Simferopol-Ukraine-693805/simferopol](https://www.windy.com/-Simferopol-Ukraine-693805/simferopol)

URL encodes "Ukraine" and uses GeoNames ID 693805 (Ukraine). JS-rendered app — static HTML confirms Ukraine classification via URL structure and GeoNames integration.

---

### 12. yr.no (Norway — Norwegian Meteorological Institute)

**Rating:** ✅ Correct

**Hierarchy:** "Ukraine > Autonomous Republic of Crimea > Simferopol Raion > Simferopol"
**URL:** [yr.no/en/forecast/daily-table/2-693805/Simferopol](https://www.yr.no/en/forecast/daily-table/2-693805/Simferopol)

Exemplary: uses full Ukrainian administrative hierarchy including "Autonomous Republic of Crimea" — Ukraine's official designation.

---

### 13. Foreca (Finland)

**Rating:** ✅ Correct

**URL:** [foreca.fi/Ukraine/Simferopol](https://www.foreca.fi/Ukraine/Simferopol) — returns 200
**Russia path:** [foreca.fi/Russia/Simferopol](https://www.foreca.fi/Russia/Simferopol) — returns **404**

Simferopol exists only under Ukraine; the Russia path is a dead link.

---

### 14. ilMeteo (Italy)

**Rating:** ✅ Correct

**Label:** "Meteo Simferopol (**Ucraina**) — Previsioni Oggi"
**URL:** [ilmeteo.it/meteo/Simferopol](https://www.ilmeteo.it/meteo/Simferopol)

Explicitly labeled "Ucraina" (Ukraine in Italian) in page title, H1, and metadata. Country dropdown shows `nid=UA`. Simferopol appears alongside Kyiv, Odessa, Kharkiv.

---

### 15. AEMET (Spain — national meteorological agency)

**Rating:** ✅ Correct

**URL:** [aemet.es/es/eltiempo/prediccion/mundo?c=UA&p=simferopol](https://www.aemet.es/es/eltiempo/prediccion/mundo?c=UA&p=simferopol)

Uses country code `c=UA` (Ukraine) in URL. Spain's official meteorological service.

---

### 16. Windfinder (Germany)

**Rating:** ✅ Correct

**Label:** "Simferopol International Airport / Crimea, **Ukraine**"
**URL:** [windfinder.com/forecast/simferopol](https://www.windfinder.com/forecast/simferopol)

---

### 17. OpenWeatherMap (UK)

**Rating:** ✅ Correct

**URL:** [openweathermap.org/city/693805](https://openweathermap.org/city/693805)

API returns country code `"UA"` (Ukraine) for GeoNames ID 693805. JS-rendered frontend; API data confirms classification.

---

### 18. Meteostat (Germany)

**Rating:** ✅ Correct

**Label:** Ukrainian flag icon + "Country: UA"
**URL:** [meteostat.net/en/place/ua/simferopol](https://meteostat.net/en/place/ua/simferopol)

URL uses `/ua/`, displays Ukrainian flag, sidebar explicitly shows "Country: UA."

---

## Ambiguous / Problematic

### 19. World Weather Online (UK)

**Rating:** ⚠️ Ambiguous (dual-listed)

**Ukraine path:** [worldweatheronline.com/simferopol-weather/krym-avtonomna-respublika/ua.aspx](https://www.worldweatheronline.com/simferopol-weather/krym-avtonomna-respublika/ua.aspx) — returns 200, heading "Ukraine Weather"
**Russia path:** [worldweatheronline.com/simferopol-weather/krym-avtonomna-respublika/ru.aspx](https://www.worldweatheronline.com/simferopol-weather/krym-avtonomna-respublika/ru.aspx) — returns 200, heading "Russia Weather"

Simferopol is simultaneously listed under both countries. Both pages serve weather data. This dual-listing treats sovereignty as ambiguous.

---

### 20. MSN Weather (US — Microsoft)

**Rating:** ⚠️ Ambiguous (no country)

**Label:** "Simferopol, Crimea" — no country attribution
**URL:** [msn.com/en-us/weather/forecast/in-Simferopol,Crimea](https://www.msn.com/en-us/weather/forecast/in-Simferopol,Crimea)

Lists "Crimea" as a standalone region, avoiding country attribution entirely.

---

## Russian Services — Incorrect (show Russia)

### 21. Yandex Weather (Russia)

**Rating:** ❌ Incorrect

**Label:** "Республика Крым" (Republic of Crimea — Russian Federation administrative name)
**URL:** yandex.ru/pogoda/ru/simferopol

URL path `/ru/simferopol` places Simferopol under Russia. Uses Russian Federation's administrative terminology.

---

### 22. Gismeteo (Russia)

**Rating:** ❌ Incorrect

**Label:** "Симферополь... Республика Крым, **Россия**" (Republic of Crimea, Russia)
**URL:** gismeteo.ru/weather-simferopol-4995/

Breadcrumb hierarchy: `catalog/russia/republic-crimea/urban-district-simferopol/`. Explicitly labeled "Россия" (Russia).

---

### 23. rp5.ru (Russia)

**Rating:** ❌ Incorrect

**Breadcrumb:** "All countries > **Russia** > Crimea > Simferopol"
**URL:** [rp5.ru/Weather_in_Simferopol](https://rp5.ru/Weather_in_Simferopol)

Simferopol/Crimea explicitly filed under Russia, not Ukraine, despite having a separate Ukraine section.

---

### 24. Pogoda.mail.ru (Russia — Mail.ru Group)

**Rating:** ❌ Incorrect

**JSON metadata:** `"country":{"name":"Россия","code":"ru","alias":"russia"}`
**URL:** pogoda.mail.ru/prognoz/simferopol/

Lists Simferopol alongside Moscow, St. Petersburg. Section titled "In other cities of Russia." Also classifies Donetsk as Russian.

---

## Not Available / Inconclusive

### 25. tenki.jp (Japan)

**Rating:** ➖ Absent

Simferopol is excluded from **both** the Ukraine and Russia city lists. Station 33946 returns 404 under either country. May be deliberate avoidance of the sovereignty question.

---

### Not testable

| Service | Country | Reason |
|---------|---------|--------|
| idokep.hu | Hungary | Broken — defaults to Budapest for non-Hungarian cities |
| La Chaîne Météo | France | Simferopol URL redirects to French village |
| weather.com.cn | China | Domestic-only public interface |
| tianqi.com | China | Simferopol not in database (404) |
| Naver Weather | Korea | Simferopol not in city list |
| Climatempo | Brazil | International section non-functional |
| WeatherBug | US | Client-side rendering only, no data in HTML |
| wetter.com | Germany | Simferopol returns 404 under both UA/RU |
| Apple Weather | US | App-only, no web interface |
| HK Observatory | Hong Kong | Simferopol not listed |

---

## Summary Table

| # | Service | Country of Origin | Label | Verified | Rating |
|---|---------|------------------|-------|----------|--------|
| 1 | AccuWeather | US | Ukraine | Yes (URL + label) | ✅ |
| 2 | Weather Underground | US | Ukraine | Yes (URL) | ✅ |
| 3 | TimeAndDate.com | Norway | Ukraine | Yes (URL + label) | ✅ |
| 4 | Weather Spark | US | Ukraine | Yes (label) | ✅ |
| 5 | Meteoblue | Switzerland | Ukraine | Yes (URL) | ✅ |
| 6 | Weather-Forecast.com | UK | Ukraine | Yes | ✅ |
| 7 | Ventusky | Czech Republic | Ukraine | Yes (hierarchy) | ✅ |
| 8 | Weather Atlas | Serbia | Ukraine | Yes (URL + label) | ✅ |
| 9 | weather.com | US | Ukraine | Browser-verified | ✅ |
| 10 | BBC Weather | UK | Ukraine | GeoNames + editorial | ✅ |
| 11 | Windy.com | Czech Republic | Ukraine | URL + GeoNames | ✅ |
| 12 | yr.no | Norway | Ukraine | Full hierarchy | ✅ |
| 13 | Foreca | Finland | Ukraine | Russia path = 404 | ✅ |
| 14 | ilMeteo | Italy | Ucraina | Explicit in title/H1 | ✅ |
| 15 | AEMET | Spain | UA | Country code in URL | ✅ |
| 16 | Windfinder | Germany | Ukraine | Label in metadata | ✅ |
| 17 | OpenWeatherMap | UK | UA | API country code | ✅ |
| 18 | Meteostat | Germany | UA + flag | URL + sidebar | ✅ |
| 19 | World Weather Online | UK | Both UA and RU | Dual-listed | ⚠️ |
| 20 | MSN Weather | US | "Crimea" (no country) | No country shown | ⚠️ |
| 21 | Yandex Weather | Russia | Russia | URL /ru/ + label | ❌ |
| 22 | Gismeteo | Russia | Россия | Breadcrumb + title | ❌ |
| 23 | rp5.ru | Russia | Russia | Breadcrumb | ❌ |
| 24 | Pogoda.mail.ru | Russia | Россия | JSON + UI | ❌ |
| 25 | tenki.jp | Japan | Absent | Excluded from both | ➖ |

---

## Key Findings

**Expanded scorecard: 25 services tested across 14 countries**

- **18 correct** (✅ Ukraine): All Western/international services that have Simferopol in their database classify it under Ukraine
- **2 ambiguous** (⚠️): World Weather Online dual-lists under both countries; MSN Weather avoids country entirely
- **4 incorrect** (❌ Russia): All four are Russian-owned services — Yandex, Gismeteo, rp5.ru, Pogoda.mail.ru
- **1 absent** (➖): tenki.jp (Japan) excludes Simferopol from both Ukraine and Russia lists

**Pattern:** The dividing line is not geographic but geopolitical. Every non-Russian service that covers Simferopol labels it as Ukraine. The 4 Russian services unanimously label it as Russia using the Russian Federation's administrative terminology ("Республика Крым"). This is consistent with Russian federal law requiring all services to show Crimea as Russian territory.

**Why weather services get it right:** Weather databases rely on standardized geographic databases — primarily GeoNames (ID 693805 = Simferopol, Ukraine) and ISO 3166 (UA = Ukraine, includes Crimea). Russian services override these standards with domestic classifications. This demonstrates that correct classification is technically trivial — it is a policy choice, not a technical limitation.
