<p align="center">
  <img src="site/public/logo-org.svg" alt="Crimea Is Ukraine" width="128"/>
</p>

<h1 align="center">Digital Annexation</h1>
<p align="center">A Computational Audit of Crimea's Sovereignty Framing in Large Language Models</p>

<p align="center">
  <a href="https://crimeaisukraine.org"><img src="https://img.shields.io/badge/site-crimeaisukraine.org-CD2E4A" alt="Site"/></a>
  <a href="https://huggingface.co/CrimeaIsUkraineOrg"><img src="https://img.shields.io/badge/🤗-datasets-CD2E4A" alt="HuggingFace"/></a>
</p>

[**UN GA Resolution 68/262**](https://digitallibrary.un.org/record/767565) (100-11) affirms Crimea as Ukrainian territory. The maps, training data, and language models do not.

## Results

| Layer | Finding |
|-------|---------|
| Geodata | Natural Earth `SOVEREIGNT="Russia"` propagates to 65.7M weekly downloads |
| Training data | 891,522 / 34.1M Crimea-mentioning C4 docs contain Russian designations (2.61%). 95.3% from non-sanctioned sources |
| Academic | 1,581 papers with Russian affiliations confirmed (98.5% precision). 161 Western publishers |
| LLM behavior | 16 models, 50 languages. Declarative-generative gap +0.04 to +0.27 on 7 flagships |
| Instruct comparison | Instruction tuning improves forced-choice in 3/4 models, worsens free-recall in all 4 |
| Web search | 5,974 citations, 7.6% Russian-origin. No GEC proxies in baseline; 5/7 accessible via targeted probes |

## Pipelines

| Pipeline | Description |
|----------|-------------|
| [geodata](pipelines/geodata/) | Natural Earth propagation chain |
| [llm](pipelines/llm/) | 16+4 model sovereignty audit (forced-choice + free-recall) |
| [academic](pipelines/academic/) | 91,670 OpenAlex papers, 3-stage classification |
| [grounding](pipelines/grounding/) | Web search citation audit (4 chatbots x 10 languages) |
| [media](pipelines/media/) | GDELT framing analysis (154K articles) |
| [wikipedia](pipelines/wikipedia/) | Crimean city sitelink audit |
| [weather](pipelines/weather/) | Weather platform sovereignty check |
| [telecom](pipelines/telecom/) | ASN reassignment audit |
| [ip](pipelines/ip/) | IP geolocation audit |
| [institutions](pipelines/institutions/) | Domain registry audit |
| [religious](pipelines/religious/) | OCU parish tracking |
| [c4_sovereignty](c4_sovereignty/) | Rust classifier (90 signals, 3 languages) |

## Reproduce

```bash
make help                    # list all targets
make pipeline-llm            # LLM sovereignty audit
make pipeline-academic       # academic framing pipeline
make pipeline-geodata        # Natural Earth propagation
make pipeline-media          # GDELT media framing
make all                     # full run (all pipelines)
make site                    # build site
```

## Data

All datasets on [HuggingFace](https://huggingface.co/CrimeaIsUkraineOrg):

| Dataset | Records | Format |
|---------|---------|--------|
| `crimea-sovereignty-llm` | 43,826 forced-choice + 52,000 free-recall | parquet |
| `crimea-sovereignty-c4-analysis` | 891,522 classified + 90 signals | parquet |
| `crimea-sovereignty-academic` | 91,670 scanned | parquet |
| `crimea-sovereignty-grounding` | 5,974 citations | parquet |
| `crimea-sovereignty-validation` | 300 blind annotations | parquet |

## Citation

```bibtex
@misc{dobrovolskyi2026digital,
  author = {Dobrovolskyi, Ivan},
  title = {Digital Annexation: A Computational Audit of Crimea's
           Sovereignty Framing in Large Language Models},
  year = {2026},
  url = {https://crimeaisukraine.org}
}
```

Ivan Dobrovolskyi — MIT (code) / CC-BY-4.0 (text and data)
