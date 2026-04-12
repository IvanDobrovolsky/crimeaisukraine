# Tech Infrastructure: Standards, Libraries, and Protocols

**Headline:** IANA `zone1970.tab` lists `Europe/Simferopol` as `RU,UA` (Russia first). Google libphonenumber lists 4 Russian mobile operators under `+7-978` -- a prefix Russia assigned unilaterally and never submitted to ITU. OSM Nominatim resolves all 6 tested Crimean cities to `country_code=UA`. Combined downstream impact: ~205 million weekly library downloads inherit these sovereignty decisions with no regulatory oversight.

## Key findings

1. **IANA `zone1970.tab`**: `Europe/Simferopol` listed as `RU,UA` (dual, Russia first). Legacy `zone.tab` still says `UA` only -- proving the dual listing is a 2014 editorial decision, not a data-model requirement.
2. **libphonenumber `+7-978` carrier file**: 4 active Russian operators (Elemte-Invest, K-Telecom Ltd, MTS, Sevastopol TELECOM). Russia's `+7-978` was never submitted to ITU; this is **Standards Silencing**.
3. **libphonenumber dual-encodes Crimean numbers**: 3 entries under `+380` (Ukraine, ITU-valid) and 2 under `+7` (Russia, unilateral).
4. **OSM Nominatim**: 6/6 Crimean cities return `country_code=UA`.
5. **Timezone library impact: ~189M weekly downloads** (pytz 105.5M, dayjs 39.6M, luxon 23.2M, moment-timezone 14.2M, date-fns-tz 7.1M) all inherit the IANA dual listing.
6. **Phone library impact: ~15.6M weekly npm downloads** (libphonenumber-js + google-libphonenumber) inherit the `+7-978` Russian carrier assignment.

## Live probe results

| Probe | Result | Status |
|---|---|:---:|
| IANA `zone1970.tab` | `RU,UA` dual listing, Russia first | ambiguous |
| IANA legacy `zone.tab` | `UA` only | correct |
| libphonenumber `+7-978` carrier | 4 Russian mobile carriers | incorrect |
| libphonenumber `+7` geocoding | 2 Crimean-city entries | incorrect |
| libphonenumber `+380` geocoding | 3 Crimean-city entries (dual) | -- |
| OSM Nominatim | 6/6 cities = UA | correct |

## Downstream library propagation

| Library | Registry | Weekly downloads |
|---|---|---:|
| pytz | PyPI | 105.5M |
| dayjs | npm | 39.6M |
| luxon | npm | 23.2M |
| moment-timezone | npm | 14.2M |
| date-fns-tz | npm | 7.1M |
| libphonenumber-js | npm | 14.1M |
| google-libphonenumber | npm | 1.5M |

## Data

- Manifest: `data/manifest.json`
- Scan script: `scan.py`

## Run

```bash
make pipeline-tech_infrastructure
```

Runs `scan.py` (IANA tzdata + libphonenumber + OSM Nominatim). Writes `data/manifest.json`, rebuilds `site/src/data/master_manifest.json`. ~20 seconds.

## Sources

- [IANA tzdata](https://www.iana.org/time-zones) | [zone1970.tab](https://github.com/eggert/tz/blob/main/zone1970.tab)
- [Google libphonenumber](https://github.com/google/libphonenumber) | [carrier/en/7.txt](https://raw.githubusercontent.com/google/libphonenumber/master/resources/carrier/en/7.txt)
- [OSM Nominatim](https://nominatim.openstreetmap.org/) | [On the Ground rule](https://wiki.openstreetmap.org/wiki/On_the_ground_rule)
- [ITU E.164](https://www.itu.int/rec/T-REC-E.164) | [ISO 3166-2:UA](https://www.iso.org/obp/ui/#iso:code:3166:UA)
- Download counts: [npmjs.org API](https://api.npmjs.org/downloads/point/last-week/) | [pypistats.org](https://pypistats.org/) (verified 2026-04-07)
