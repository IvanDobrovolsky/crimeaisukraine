# Wikipedia & Wikidata: Erasure by Omission

**Headline:** English Wikipedia strips the country from 11 of 14 Crimean city descriptions. Wikidata has no current `P17` (country) for 11 of 17 Crimean entities. 23 Wikipedia editions have a standalone "Republic of Crimea" article without a parallel Ukrainian Autonomous Republic article. Among 244 living Crimean-born people, UA and RU citizenship are at statistical parity (60 vs 58, p = 0.93). Post-2014 passportization is invisible: only 1 of 577 people has a timestamped `P27 = Russia` edge.

## Key findings

1. **English Wikipedia: "city in Crimea" for 11/14 cities** -- erasure by omission. German Wikipedia says "Ukraine" for 6/6, Indonesian for 5/5.
2. **Wikidata P17 missing for 11/17 Crimean entities** -- Google Knowledge Panel, Siri, Alexa, and LLMs all read from this gap.
3. **23 Wikipedia editions** have a standalone Russian federal-subject article with no parallel Ukrainian article -- infrastructural normalization via editorial path dependency.
4. **Living Crimean-born people (n=244)**: UA-only 60, RU-only 58 -- exact binomial p = 0.93, cannot reject parity.
5. **Post-2014 passportization invisible**: only 1 of 577 people has `P27=Russia` with `P580 >= 2014-03-18`. Russia issued ~2 million passports in reality.

## Description field by language

| Language | Says "Ukraine" | Says "Russia" | Says only "Crimea" |
|---|---:|---:|---:|
| German | 6 / 6 | 0 | 0 |
| Indonesian | 5 / 5 | 0 | 0 |
| French | 1 / 1 | 0 | 0 |
| Romanian | 1 / 1 | 0 | 0 |
| **English** | **3 / 14** | **0** | **11 / 14** |
| Italian | 1 / 8 | 0 | 7 / 8 |
| Spanish | 2 / 12 | 0 | 10 / 12 |

## Wikidata P17 (country)

| Result | Count |
|---|---:|
| Missing entirely | 11 / 17 |
| Current = Ukraine (Q212) | 3 / 17 |
| Current = Russia (Q159) | 4 / 17 |

## Entity sitelink asymmetry (143 editions covering either admin entity)

| Pattern | Editions |
|---|---:|
| Both UA + RU articles | 69 |
| UA-only | 31 |
| **RU-only** | **23** |
| Neither (peninsula only) | 51 |

## Methodology

5 live probes: (1) Wikipedia description field across 12 languages x 17 entities, (2) Wikipedia categories, (3) Wikidata P17, (4) sitelink sweep across 156 editions, (5) SPARQL query for 577 Crimean-born people with P19/P27/P570/P580/P582 stratification. All fetched live from `query.wikidata.org` and `{lang}.wikipedia.org`.

## Data

- Manifest: `data/manifest.json`
- Scan script: `scan.py`

## Run

```bash
make pipeline-wikipedia
```

Runs `scan.py` end-to-end against live Wikidata/Wikipedia APIs. Writes `data/manifest.json`, rebuilds `site/src/data/master_manifest.json`.

## Sources

- [Wikipedia REST API](https://en.wikipedia.org/api/rest_v1/page/summary/Simferopol) | [WP:NPOV](https://en.wikipedia.org/wiki/Wikipedia:Neutral_point_of_view)
- [Wikidata SPARQL](https://query.wikidata.org/sparql) | [P17](https://www.wikidata.org/wiki/Property:P17) | [P19](https://www.wikidata.org/wiki/Property:P19) | [P27](https://www.wikidata.org/wiki/Property:P27)
- Crimea entities: [Q7835](https://www.wikidata.org/wiki/Q7835) | [Q15966495](https://www.wikidata.org/wiki/Q15966495) | [Q756294](https://www.wikidata.org/wiki/Q756294)
- [OHCHR Ukraine](https://www.ohchr.org/en/countries/ukraine) | [Council Regulation (EU) 692/2014](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014R0692)
