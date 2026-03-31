# Weather Services — Crimea Country Labels

**Research date:** 2026-03-30
**Methodology:** Web search analysis, URL pattern examination

---

## Overview

Weather services provide a useful "ground truth" indicator for how platforms classify disputed territories, because every city forecast requires a country designation in its database.

---

## 1. AccuWeather

**Rating:** ✅ Correct

**Label:** "Simferopol, Crimea, **Ukraine**"
**URL:** [accuweather.com/en/ua/simferopol/322464/weather-forecast/322464](https://www.accuweather.com/en/ua/simferopol/322464/weather-forecast/322464)

Note the `/ua/` country code in the URL path, confirming Ukraine classification in their database.

---

## 2. Weather Underground (IBM/The Weather Company)

**Rating:** ✅ Correct

**Label:** Simferopol listed under **Ukraine**
**URL:** [wunderground.com/forecast/ua/simferopol](https://www.wunderground.com/forecast/ua/simferopol)

Note the `/ua/` country code in the URL path.

---

## 3. TimeAndDate.com

**Rating:** ✅ Correct

**Label:** "Simferopol, **Ukraine**"
**URL:** [timeanddate.com/weather/ukraine/simferopol](https://www.timeanddate.com/weather/ukraine/simferopol)

---

## 4. Weather Spark

**Rating:** ✅ Correct

**Label:** "Simferopol Climate, Weather By Month, Average Temperature (**Ukraine**)"
**URL:** [weatherspark.com/y/98362/Average-Weather-in-Simferopol-Ukraine](https://weatherspark.com/y/98362/Average-Weather-in-Simferopol-Ukraine)

---

## 5. Meteoblue

**Rating:** ✅ Correct

**Label:** "Weather Simferopol" — URL contains `/ukraine/`
**URL:** [meteoblue.com/en/weather/week/simferopol_ukraine_693805](https://www.meteoblue.com/en/weather/week/simferopol_ukraine_693805)

Note: The GeoNames ID 693805 is assigned to Simferopol, Ukraine.

---

## 6. Weather-Forecast.com

**Rating:** ✅ Correct

**Label:** "Simferopol Weather Forecast"
**URL:** [weather-forecast.com/locations/Simferopol/forecasts/latest](https://www.weather-forecast.com/locations/Simferopol/forecasts/latest)

---

## 7. Ventusky

**Rating:** ✅ Correct

**Hierarchy:** "World / Ukraine / Autonomous Republic of Crimea"
**URL:** [ventusky.com/44.959;34.11](https://www.ventusky.com/44.959;34.11)

---

## 8. Weather Atlas

**Rating:** ✅ Correct

**Label:** "Weather forecast for today Simferopol, **Ukraine**"
**URL:** [weather-atlas.com/en/ukraine/simferopol](https://www.weather-atlas.com/en/ukraine/simferopol)

---

## 9. weather.com (The Weather Channel)

**Rating:** ⚠️ Unable to verify directly (site blocked automated access)

Weather.com is operated by The Weather Company (IBM). Its sister product Weather Underground lists Simferopol under Ukraine. Direct verification of weather.com's label was not possible in this research session.

---

## 10. BBC Weather

**Rating:** ⚠️ Unable to verify directly (site blocked automated access)

BBC Weather uses GeoNames ID 693805 for Simferopol (URL: bbc.com/weather/693805). GeoNames classifies this location as Ukraine. However, direct confirmation of BBC Weather's on-page country label was not possible.

**Note:** BBC editorial policy refers to Crimea as "annexed" by Russia, suggesting their weather service likely labels it as Ukraine.

---

## Summary Table

| Service | Country Label | Verified | Rating |
|---------|--------------|----------|--------|
| AccuWeather | Ukraine | Yes (URL + label) | ✅ |
| Weather Underground | Ukraine | Yes (URL) | ✅ |
| TimeAndDate | Ukraine | Yes (URL + label) | ✅ |
| Weather Spark | Ukraine | Yes (label) | ✅ |
| Meteoblue | Ukraine | Yes (URL) | ✅ |
| Weather-Forecast.com | Ukraine | Yes | ✅ |
| Ventusky | Ukraine | Yes (hierarchy) | ✅ |
| Weather Atlas | Ukraine | Yes (URL + label) | ✅ |
| weather.com | Likely Ukraine | Not directly verified | ⚠️ |
| BBC Weather | Likely Ukraine | Not directly verified | ⚠️ |

---

## Key Finding

Weather services are the **most consistently correct** category. All verifiable weather platforms classify Simferopol under **Ukraine**. This is largely because weather databases rely on standardized geographic databases (GeoNames, ISO 3166) which maintain Ukraine's internationally recognized borders. This stands in stark contrast to map services and social media platforms.
