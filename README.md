# Crimea Is Ukraine

A computational audit of how digital systems classify Crimea's sovereignty. Built as eleven independent pipelines, each documenting one layer where the world's digital infrastructure encodes a sovereignty position — sometimes consistent with international law, sometimes not.

**[crimeaisukraine.org](https://crimeaisukraine.org)**

## Top-line numbers

| | |
|---|---|
| Platforms audited | **120** across 10 categories |
| Correct (Ukraine) | **41** |
| Incorrect (Russia) | **30** |
| Ambiguous | **35** |
| GDELT articles classified | **154,000** (2015–2026) |
| Academic papers scanned | **91,670** (OpenAlex, 2010–2026) |
| LLM-confirmed Russia-framing papers | **1,581** |
| LLMs audited | **20+** models × 50 languages × 12 cities × 15 questions |
| Combined npm downloads affected | **219M weekly** (geodata + tz + phone libs) |
| Sovereignty signals | **81** in 3 languages |

## Headline findings

1. **One file does most of the damage.** [Natural Earth](https://www.naturalearthdata.com/) assigns `SOVEREIGNT=Russia` to Crimea, propagates to **30.4M weekly npm downloads** via D3, Leaflet, Plotly, ECharts. Crimea is the *only* occupied territory worldwide that Natural Earth merges into the occupier's default polygon — Abkhazia, Donbas, Kherson, Northern Cyprus, Western Sahara, Golan Heights all get separate breakaway treatment. ([geodata pipeline](pipelines/geodata/README.md))

2. **Russian-language web is 58.7% Russia-framed about Crimea.** This is the smoking gun for LLM bias. C4 Russian config: 61 of 104 sovereignty-signaled documents use Russian framing. C4 English: 9.9%. C4 Ukrainian: 0.5%. ([training_corpora pipeline](pipelines/training_corpora/README.md))

3. **LLMs encode contradictory frames simultaneously.** Claude Haiku 4.5 says "Russia illegally annexed Crimea" 98% of the time AND says "Sevastopol is a Russian city" 78% of the time across 50 languages. Gap between Crimean and Donbas city accuracy: **+36 percentage points**. ([llm pipeline](pipelines/llm/README.md))

4. **The indigenous language performs worst.** Crimean Tatar is the worst-performing of all 50 tested languages on the LLM audit (30% accuracy on Q1).

5. **The mundane science vector**: 1,581 LLM-confirmed academic papers use Russian framing. Western Q1 publishers (Wiley h=420, IOP h=92, EDP Sciences h=59, Elsevier SSRN) host them. The papers are about viticulture, ecology, medicine — not political advocacy. DOIs make them permanent. ([academic pipeline](pipelines/academic/README.md))

6. **Major media is largely correct.** Of 154,000 GDELT articles, only 0.5% of non-Russian media endorses Russian framing after LLM verification. Zero major international outlets (BBC, Reuters, CNN, NYT, Guardian) systematically endorse. The 239 non-Russian endorsements are 53 fringe sites + 47 aggregators + 12 non-Western state media + 127 single-incident marginals. **Advocacy works.** ([media pipeline](pipelines/media/README.md))

7. **6/6 institutional and legislative systems unanimous.** OFAC, EUR-Lex, UK legislation, ICAO, ITU, ISO 3166 — every authoritative system classifies Crimea as Ukraine. The regulation gap exists not in law but in the technical infrastructure that bypasses these systems. ([institutions pipeline](pipelines/institutions/README.md))

8. **English Wikipedia uses erasure by omission.** 11 of 14 Crimean cities have Wikipedia descriptions reading "city in Crimea" with no country mentioned — what 1.7 billion English speakers see in Google previews. German Wikipedia says "Ukraine" for all 6 cities tested. Chinese Wikipedia uses "Republic of Crimea" — the only non-Russian edition to do so. ([wikipedia pipeline](pipelines/wikipedia/README.md))

## Pipelines

The audit is organized as 11 independent, self-contained pipelines. Each is a journalist-quality briefing with full methodology, results, and citations.

| Pipeline | Topic | Headline finding |
|---|---|---|
| [ip](pipelines/ip/README.md) | IP geolocation databases (BGP, RIPE NCC, MaxMind) | 16% of Crimean IPs resolve to Russia in commercial databases; Cloudflare follows ISO 3166 and reports UA-43 |
| [telecom](pipelines/telecom/README.md) | Mobile operators, RIPE NCC, ITU numbering | All 3 Ukrainian operators withdrew by Oct 2015; RIPE permitted UA→RU ASN reassignment without sovereignty review |
| [tech_infrastructure](pipelines/tech_infrastructure/README.md) | IANA tz, libphonenumber, ISO 3166, CLDR | IANA tz lists Europe/Simferopol as `RU,UA` dual; libphonenumber maps `+7-365` to RU; combined 189M weekly downloads inherit |
| [geodata](pipelines/geodata/README.md) | Natural Earth + map services + viz libs | Natural Earth uniquely merges Crimea into Russia's polygon; 30.4M npm downloads/week affected |
| [weather](pipelines/weather/README.md) | 23 weather services | 70% correct via GeoNames; the 4 violators are exclusively Russian-origin |
| [media](pipelines/media/README.md) | GDELT 154K articles + LLM verification | 0.5% non-Russian endorsement rate; 0 major outlets; advocacy works (5 documented corrections) |
| [academic](pipelines/academic/README.md) | OpenAlex 91K papers + LLM verification | 1,581 confirmed Russia-framing papers; mundane science via Wiley, IOP, EDP Sciences, Elsevier |
| [wikipedia](pipelines/wikipedia/README.md) | 17 entities × 30 language editions + Wikidata | English Wikipedia uses erasure by omission for 11/14 Crimean cities |
| [institutions](pipelines/institutions/README.md) | LoC, ROR, OFAC, EUR-Lex, ICAO, ITU, ISO | 6/6 systems unanimous: Crimea = Ukraine |
| [llm](pipelines/llm/README.md) | 20+ LLMs × 50 languages × 12 cities × 15 questions | Cognitive dissonance + training cutoff bias; Crimean Tatar performs worst |
| [training_corpora](pipelines/training_corpora/README.md) | C4, Dolma, Pile, FineWeb, OSCAR | C4 Russian web = 58.7% Russia-framed |

## Run

```bash
# Run a single pipeline (each has its own pyproject.toml, isolated deps)
make pipeline-ip
make pipeline-llm
make pipeline-training_corpora

# Run all pipelines sequentially
make pipelines-all

# Build the master manifest from all pipeline outputs
make master-manifest

# Build the static site
make site
```

Each pipeline is independent: a reviewer can clone just one directory and reproduce its results without touching the rest of the project.

## Related work

- [Holubei (2023)](https://www.ukrinform.net/rubric-society/3708065-maps-of-ukraine-without-crimea-origin.html) — prior manual investigation
- [Heiss (2025)](https://doi.org/10.59350/28kp0-nbq92) — R workflow for fixing Natural Earth
- [Lepetiuk et al. (2024)](https://doi.org/10.3138/cart-2024-0023) — "Mapaganda" in Cartographica
- [Li & Haider (2024)](https://aclanthology.org/2024.naacl-long.213/) — BorderLines benchmark for LLM territorial bias
- [Castillo-Eslava et al. (2023)](https://arxiv.org/abs/2304.06030) — Recognition of Territorial Sovereignty by LLMs
- [SovereignMap](https://github.com/IvanDobrovolsky/sovereignmap) — visual map detection tool (C++/OpenCV + CNN)

---

**Author:** [Ivan Dobrovolskyi](mailto:dobrovolsky94@gmail.com) · **License:** MIT
