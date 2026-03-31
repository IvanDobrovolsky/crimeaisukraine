# Crimea Is Ukraine — Digital Sovereignty Audit

Systematic investigation of how digital platforms, open source libraries, and tech infrastructure represent Crimea's sovereignty.

Crimea is internationally recognized as Ukrainian territory (UN GA Resolution 68/262), illegally occupied by Russia since 2014. This project documents which platforms get it right, which don't, and traces the root cause.

## Key Finding

**Natural Earth** — the foundational geographic dataset used by D3.js, Plotly, ECharts, and most mapping libraries — explicitly assigns `SOVEREIGNT=Russia` to Crimea. This single upstream decision propagates to **27+ million weekly npm downloads**, silently encoding an incorrect sovereignty claim into data dashboards, choropleth maps, and geographic visualizations worldwide.

## Audit Coverage

| Category | Platforms | Status |
|----------|-----------|--------|
| Open source geographic data | Natural Earth, GeoJSON repos, npm packages | Automated |
| Data visualization libraries | D3, Plotly, Highcharts, ECharts, Leaflet | Automated |
| IP geolocation | ip-api.com, ipinfo.io, ipapi.co | Automated |
| Wikipedia | EN, DE, FR, IT, ES | Automated |
| Map services | Google, Apple, Bing, OSM, Yandex | In progress |
| Travel platforms | Booking.com, Airbnb, Skyscanner | In progress |
| Gaming | Steam, Epic, EA Sports | In progress |
| Search engines | Google, Bing, DuckDuckGo | In progress |

## Structure

```
docs/           → Findings by category
  REPORT.md     → Summary report
  open_source.md → Data viz & open source findings (core finding)
  tech.md       → IP geolocation & infrastructure
data/           → Structured findings database (JSON)
scripts/        → Reproducible audit scripts
  audit_framework.py      → Classification framework
  check_open_source.py    → Open source & data viz checker
  check_ip_geolocation.py → IP geolocation tester
  check_platforms.py      → Web platform checker
```

## Running the Audit

```bash
pip install -r requirements.txt
cd scripts
python check_open_source.py      # Open source & data viz libraries
python check_ip_geolocation.py   # IP geolocation services
python check_platforms.py        # Web platforms (Wikipedia, travel, etc.)
```

## Related

Part of the [KyivNotKiev](https://github.com/IvanDobrovolsky/kyivnotkiev) research ecosystem.
