<p align="center">
  <img src="site/public/logo-org.svg" alt="Crimea Is Ukraine" width="128"/>
</p>

<h1 align="center">Digital Annexation</h1>
<p align="center">A Computational Audit of Crimea's Sovereignty Framing in Large Language Models</p>

<p align="center">
  <a href="https://crimeaisukraine.org"><img src="https://img.shields.io/badge/site-crimeaisukraine.org-0068B7" alt="Site"/></a>
  <a href="https://huggingface.co/CrimeaIsUkraineOrg"><img src="https://img.shields.io/badge/🤗-datasets-0068B7" alt="HuggingFace"/></a>
</p>

[**UN GA Resolution 68/262**](https://digitallibrary.un.org/record/767565) (100–11) places Crimea under Ukrainian sovereignty. The maps, training data, and language models do not.

## Key Numbers

| What | Result |
|------|--------|
| Geodata | Natural Earth `SOVEREIGNT="Russia"` → **65.7M weekly downloads** |
| Training data (C4) | **34.1M** documents scanned, **894,645** Russia-framing |
| Academic metadata | **1,581** papers with Russian designations (98.3% precision) |
| LLM audit | **16 models**, 8 labs, RLHF gap **+0.04 to +0.27** |
| Web search | **5,974** citations, 7.6% Russian-origin, 5/7 GEC proxies accessible |

## Pipelines

| # | Pipeline | Finding |
|--:|----------|---------|
| 1 | [geodata](pipelines/geodata/) | 65.7M weekly downloads inherit `SOVEREIGNT="Russia"` |
| 2 | [c4_sovereignty](c4_sovereignty/) | 894,645 Russia-framing in 34.1M C4 docs |
| 3 | [academic](pipelines/academic/) | 1,581 papers, 161 Western publishers, 59 DOIs in C4 |
| 4 | [llm](pipelines/llm/) | 16 models, declarative-generative gap on all flagships |
| 5 | [media](pipelines/media/) | 154K articles, zero endorsements from top-10 outlets |
| 6 | [grounding](pipelines/grounding/) | 5,974 citations, 5/7 GEC proxy sites accessible |
| 7 | [wikipedia](pipelines/wikipedia/) | 11/14 Crimean cities — country erased |
| 8 | [weather](pipelines/weather/) | 12/25 correct |
| 9 | [telecom](pipelines/telecom/) | 8/9 ASNs reassigned without sovereignty review |
| 10 | [ip](pipelines/ip/) | 53% UA, 16% RU, 31% other |
| 11 | [institutions](pipelines/institutions/) | 9/10 registries correct |
| 12 | [tech_infrastructure](pipelines/tech_infrastructure/) | IANA, libphonenumber split |
| 13 | [religious](pipelines/religious/) | 46 OCU parishes in 2014, zero in 2024 |

## Reproduce

```bash
make pipeline-geodata        # single pipeline
make pipelines-all           # all pipelines
make site                    # build the site
```

## Citation

```bibtex
@article{dobrovolskyi2026digital,
  author = {Dobrovolskyi, Ivan},
  title = {Digital Annexation: A Computational Audit of Crimea's
           Sovereignty Framing in Large Language Models},
  year = {2026},
  journal = {Harvard Kennedy School Misinformation Review},
  url = {https://crimeaisukraine.org}
}
```

## Author

**Ivan Dobrovolskyi**

MIT (code) · CC-BY-4.0 (text)
