# Institutional Registries: The Law is Unanimous

**Headline:** 9 of 10 authoritative systems classify Crimea unambiguously as Ukrainian territory. The single ambiguous result is a classifier-confidence call on the LoC autocomplete endpoint, not a sovereignty ambiguity. The regulation gap is not upstream in the law; it is downstream in the technical infrastructure that ignores the law.

## Key findings

1. **9 / 10 institutional systems** classify Crimea as Ukrainian across three layers: legislation/sanctions, library catalogs, and research registries.
2. **OFAC SDN list**: 25 Crimean places-of-birth recorded as `Ukraine`, zero as `Simferopol, Russia`. Executive Order 13685 is titled "Crimea Region of Ukraine".
3. **EU Council Regulation 692/2014** prohibits imports originating in Crimea, treating it as illegally annexed Ukrainian territory. Renewed annually since 2014.
4. **ICAO Doc 7910** maintains Ukrainian airport prefixes (UKFF Simferopol, UKFB Sevastopol). Russia's internal codes are not ICAO-recognized.
5. **ITU has not reassigned +380-65x** from Ukraine to Russia. Russia's +7-365x/+7-978 are unilateral domestic assignments never submitted to ITU.
6. **ISO 3166-2 has zero Crimean codes under Russia** (83 federal subdivisions, none include Crimea). In Nov 2014, ISO renamed UA-43 to "Avtonomna Respublika Krym", reinforcing Ukrainian framing.
7. **LoC catalog**: 62 of 100 books classify under Ukraine, 2 under Russia. Canonical subject heading: "Crimea (Ukraine)--History--Russian occupation, 2014-".
8. **ROR + OpenAlex**: 4 of 5 Crimean academic institutions registered as UA. The single RU outlier (Research Institute of Agriculture of Crimea) is the institution whose papers appear most often under "Republic of Crimea, Russian Federation" in OpenAlex.

## Results summary

| Layer | Systems | Result |
|---|---|---|
| Legislation & sanctions | OFAC, EU EUR-Lex, UK legislation, ICAO, ITU, ISO 3166 | 6 / 6 correct |
| Library of Congress | LoC catalog, LCSH suggest API | 1 correct, 1 ambiguous |
| Research registries | ROR v2, OpenAlex | 2 / 2 correct (4/5 institutions UA) |

## Data

- Manifest: `data/manifest.json`
- Scan script: `scan.py`

## Run

```bash
make pipeline-institutions
```

Runs `scan.py` against OFAC, UK legislation, LoC, ROR, and OpenAlex. Writes `data/manifest.json` and rebuilds `site/src/data/master_manifest.json`. ~1 minute.

## Sources

- [OFAC SDN CSV](https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.CSV) | [EO 13685](https://ofac.treasury.gov/sanctions-programs-and-country-information/ukraine-russia-related-sanctions)
- [EUR-Lex Reg 692/2014](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014R0692)
- [UK legislation.gov.uk](https://www.legislation.gov.uk/)
- [ICAO Doc 7910](https://store.icao.int/en/location-indicators-doc-7910) | [ITU E.164](https://www.itu.int/rec/T-REC-E.164)
- [ISO 3166-2:UA](https://www.iso.org/obp/ui/#iso:code:3166:UA) | [CLDR subdivisions.xml](https://github.com/unicode-org/cldr/blob/main/common/supplemental/subdivisions.xml)
- [LoC LCSH](https://id.loc.gov/authorities/subjects.html) | [LoC search](https://www.loc.gov/search/?q=crimea)
- [ROR v2 API](https://api.ror.org/v2/organizations) | [OpenAlex](https://api.openalex.org/institutions)
- [UN GA Resolution 68/262](https://www.un.org/en/ga/68/resolutions.shtml)
