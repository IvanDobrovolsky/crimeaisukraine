# Pipelines

Each subdirectory audits one aspect of how digital systems classify Crimea's sovereignty. Self-contained: own `scan.py`, `data/manifest.json`, `README.md`.

| Pipeline | What it audits |
|----------|---------------|
| [geodata](geodata/) | Natural Earth, 65.7M weekly downloads |
| [academic](academic/) | 91,670 papers, 1,581 Russia-framing confirmed |
| [llm](llm/) | 16 models, 8 labs, SAS scores |
| [grounding](grounding/) | 4 chatbots, 5,974 citations |
| [media](media/) | 154K GDELT articles |
| [wikipedia](wikipedia/) | 17 entities × 30 editions + Wikidata |
| [weather](weather/) | 25 services, 14 countries |
| [ip](ip/) | 90 IPs, 9 ASNs, 2 geolocation providers |
| [telecom](telecom/) | ASN reassignment, RIPE NCC |
| [institutions](institutions/) | LoC, ROR, OFAC, ISO, ITU |
| [tech_infrastructure](tech_infrastructure/) | IANA, libphonenumber, OSM |
| [religious](religious/) | Moscow Patriarchate, WCC, Vatican |

## Run

```bash
make pipeline-geodata   # single pipeline
make pipelines-all      # all pipelines
```
