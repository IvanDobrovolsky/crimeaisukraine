# Telecom Operators: Infrastructure-Level Sovereignty Change

**Headline:** Of 11 telecom entities: 4 operate under Russian regulation, 3 Ukrainian operators withdrew, 3 services are blocked by sanctions/state action, 1 remains on Ukrainian infrastructure. Live RIPE NCC probe: 8 of 9 historical Crimean ASNs have been reassigned under `ripe-733` without sovereignty review -- an 89% registry-laundering rate. Reassignments land at Kuwait's MTC, a Polish ISP, and Yahoo-UK.

## Key findings

1. **Registry laundering: 89% reassignment.** Of 9 historical Crimean ASNs, only Miranda-Media (AS201776) retains its original holder. The rest were reassigned under [`ripe-733`](https://www.ripe.net/publications/docs/ripe-733) to entities with no Crimean connection.
2. **All 3 Ukrainian MNOs withdrew by Oct 2015** (Kyivstar, Vodafone UA, lifecell). Classified `n/a`, not `blocked` -- this is erosion of sovereign infrastructure, not sanctions.
3. **4 Russian-regulated entities replaced them**: K-Telecom/Win Mobile, Miranda-Media (Rostelecom), Kerch Strait cable (Rostelecom), RIPE NCC ASN re-registrations.
4. **`ripe-733` has no sovereignty review.** Policy prioritizes routing-table stability over international law.
5. **Kerch Strait submarine cable** reversed Crimea's topology: primary fiber now points east to Krasnodar, not west to Kyiv.
6. **Standards Silencing at ITU.** `+380-65x` remains in force at ITU, but libphonenumber has switched to the unilateral Russian `+7-365x`. The UN system has no mechanism to notice.
7. **`.crimea.ua` subdomain** is the sole `correct` finding -- Ukrainian infrastructure that has persisted through the occupation.

## Live RIPE NCC registry probe

| ASN | Historical operator | Current holder | Country | Match? |
|---|---|---|---:|:---:|
| **AS201776** | Miranda-Media | Miranda-Media Ltd | RU | original |
| AS28761 | KNET | CrimeaCom South LLC | RU | reassigned |
| AS48031 | CrimeaCom | Ivanov Vitaliy Sergeevich | UA | reassigned |
| AS56485 | SevStar | TheHost LLC | UA | reassigned |
| AS198948 | Sim-Telecom | UNINET Sp. z o.o. | PL | reassigned |
| AS42961 | CrimeaTelecom | MTC K.S.C.P. | KW | reassigned |
| AS47598 | Sevastopolnet | PE Khersontelecom | UA | reassigned |
| AS44629 | CrimeaLink | PE Sinenko V.M. | UA | reassigned |
| AS203070 | Crimean Telecom Co | Yahoo-UK Limited | GB | reassigned |

## Status taxonomy

| Status | Count | Entities |
|---|---:|---|
| Incorrect (Russian regulation) | 4 | K-Telecom, Miranda-Media, Kerch cable, RIPE re-registrations |
| N/A (Ukrainian operators withdrew) | 3 | Kyivstar, Vodafone UA, lifecell |
| Blocked (sanctions/state action) | 3 | Starlink, Netflix, Speedtest.net |
| Correct (Ukrainian infrastructure) | 1 | `.crimea.ua` subdomain |

## Data

- Manifest: `data/manifest.json`
- Scan script: `scan.py`

## Run

```bash
make pipeline-telecom
```

Reads curated telecom findings from `site/src/data/platforms.json`, writes `data/manifest.json`, rebuilds `site/src/data/master_manifest.json`.

## Sources

- [RIPE NCC](https://www.ripe.net/) | [RIPE STAT](https://stat.ripe.net/) | [`ripe-733`](https://www.ripe.net/publications/docs/ripe-733)
- [ITU E.164](https://www.itu.int/rec/T-REC-E.164) | [TeleGeography submarine cable map](https://www.submarinecablemap.com/)
- [Reuters (2015)](https://www.reuters.com/article/us-ukraine-crisis-crimea-mobile-idUSKCN0Q428H20150730) | [Kyiv Post](https://www.kyivpost.com/article/content/ukraine-politics/ukraines-mobile-operators-pull-out-of-crimea-389614.html)
- [Hostmaster.ua](https://hostmaster.ua/) | [Council Regulation (EU) 692/2014](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014R0692)
