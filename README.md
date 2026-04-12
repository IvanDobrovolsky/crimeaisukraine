<p align="center">
  <img src="site/public/logo-org.svg" alt="Crimea Is Ukraine" width="128"/>
</p>

<h1 align="center">Crimea Is Ukraine — Digital Sovereignty Audit</h1>

<p align="center">
  <img src="https://img.shields.io/badge/-Crimean%20flag-0068B7?style=flat&labelColor=0068B7&color=D52B1E" alt="Crimean flag"/>
  <a href="https://crimeaisukraine.org"><img src="https://img.shields.io/badge/site-crimeaisukraine.org-0068B7" alt="Site"/></a>
  <a href="https://huggingface.co/CrimeaIsUkraineOrg"><img src="https://img.shields.io/badge/🤗-HuggingFace-0068B7" alt="HuggingFace"/></a>
</p>

[**UN GA Resolution 68/262**](https://digitallibrary.un.org/record/767565) (adopted 100–11) places Crimea under Ukrainian sovereignty. The software that draws the maps, writes the news, indexes the research, and trains the AI does not.

**[crimeaisukraine.org](https://crimeaisukraine.org)** · [briefing](../crimeaisukraine-paper/docs/Dobrovolskyi_2026_Briefing.docx) · [paper draft](../crimeaisukraine-paper/docs/Dobrovolskyi_2026_Crimea_Digital_Sovereignty_MC_v2.docx) · [datasets](https://huggingface.co/CrimeaIsUkraineOrg)

## Pipelines

| # | Pipeline | Headline finding |
|--:|----------|-----------------|
| 1 | [geodata](pipelines/geodata/) | Natural Earth assigns `SOVEREIGNT='Russia'` to Crimea — **65.7M weekly downloads** inherit it. 30/31 worldviews in its own data say Ukraine; only Russia's says Russia. |
| 2 | [academic](pipelines/academic/) | **91,670 papers** scanned, **1,581 Russia-framing** confirmed (98.3% precision). 12 Q1 journals including Oxford, Max Planck, IEEE. |
| 3 | [training_corpora](pipelines/training_corpora/) | C4 Russian: **58.7%** Russia-framing. Dolma: **12.2%** (web) / **18.5%** (academic tier). DOI-level trace confirmed into Dolma. |
| 4 | [llm](pipelines/llm/) | **18 models, 9 labs.** RLHF gap **+0.18 to +0.33** on 5 flagships. GPT-5.4 says "yes" to "Is Sevastopol in Ukraine?" but writes "Kerch, Republic of Crimea, Russia" in free recall. |
| 5 | [media](pipelines/media/) | **154K articles** scanned. Zero endorsements from top-10 international outlets. Advocacy works where editorial accountability exists. |
| 6 | [wikipedia](pipelines/wikipedia/) | English Wikipedia erases the country for **11/14** Crimean cities. Only **1 of 577** Crimean-born people has a recorded post-2014 citizenship transition. |
| 7 | [weather](pipelines/weather/) | **12/25** services correct. Weather.com displays "Simferopol, Simferopol" — the city without a country. |
| 8 | [telecom](pipelines/telecom/) | **8/9 ASNs** reassigned without sovereignty review under RIPE `ripe-733`. |
| 9 | [ip](pipelines/ip/) | **53% UA, 16% RU, 31% other** — geolocation fragments the same territory into three answers. |
| 10 | [institutions](pipelines/institutions/) | **10/10** institutional registries correct. The law is unanimous; the gap is in the technical layer. |
| 11 | [tech_infrastructure](pipelines/tech_infrastructure/) | IANA tzdata lists `RU,UA` (Russia first). Google's libphonenumber encodes both UA and RU for `+7978`. |
| 12 | [religious](pipelines/religious/) | Moscow Patriarchate annexed 3 Crimean dioceses (2022). WCC defeated ROC expulsion; Vatican omitted Crimea. **46 OCU parishes in 2014, zero in 2024.** |

## Reproduce

```bash
make pipeline-geodata        # any single pipeline
make pipelines-all           # all pipelines
make site                    # build the site
```

Each pipeline has its own `scan.py`, `data/manifest.json`, and `README.md`.

## Related work

- [Holubei / Stop Mapaganda (2023)](https://www.ukrainer.net/en/en-stop-mapaganda/) — 90% of educational products in German bookstores misrepresent Crimea
- [Beketova / CEPA (2024)](https://cepa.org/article/behind-the-lines-mapaganda-and-the-cartographic-war-on-ukraine/) — "mapaganda" and the cartographic war on Ukraine
- [Plotly.js (2025)](https://plotly.com/blog/improved-map-accuracy-plotlyjs-un-geodata/) — switched from Natural Earth to UN geodata
- [Heiss (2025)](https://www.andrewheiss.com/blog/2025/02/13/natural-earth-crimea/) — R workaround for Natural Earth's Crimea classification
- [Katz (2023)](https://repository.uclawsf.edu/hastings_science_technology_law_journal/vol14/iss1/4/) — Google Maps and quasi-sovereign power

## Author

**Ivan Dobrovolskyi** · [dobrovolsky94@gmail.com](mailto:dobrovolsky94@gmail.com)

MIT (code) · CC-BY-4.0 (text). [Open an issue](https://github.com/IvanDobrovolsky/crimeaisukraine/issues/new) for corrections.
