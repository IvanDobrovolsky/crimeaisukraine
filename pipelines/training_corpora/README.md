# Training Corpora: Where LLMs Learn What to Say About Crimea

**Headline:** C4 Russian has 58.7% conditional Russia framing about Crimea -- the smoking gun for multilingual models. Dolma (OLMo/OLMo-2) has 12.2%. C4 English has 10.0%. Quality-filtered FineWeb-Edu reduces to 5.9% but does not eliminate it. The Russian-language web, harvested by Common Crawl monthly, is majority Russia-framed about Crimea, and every multilingual model inherits this in proportion to its Russian-language training mix.

## Key findings

1. **C4 Russian: 58.7% conditional Russia framing** (61 RU vs 43 UA of 2,000 Crimea-mentioning docs).
2. **Dolma (OLMo-2): 12.2%** (40 RU vs 288 UA) -- first end-to-end causal measurement for a fully transparent model.
3. **C4 English: 10.0%** (27 RU vs 243 UA of 2,436 mentions).
4. **FineWeb-Edu (SmolLM, Llama 3): 5.9%** (13 RU vs 208 UA) -- quality filtering helps but does not eliminate.
5. **C4 Ukrainian: 0.5%** (1 RU vs 194 UA) -- overwhelmingly Ukrainian, as expected.
6. **Russian state media** (RIA, TASS, RT) republished on the open web is the primary upstream source.
7. **Dolma inherits from its academic tier** (peS2o, arXiv) -- linking the academic pipeline's 1,581 Russia-framing papers directly to OLMo-2's training data.
8. **No EU regulation requires sovereignty auditing** of training data; EU AI Act Art. 53 requires only a "sufficiently detailed summary".

## Corpus scan results

| Corpus | Docs scanned | Crimea mentions | UA | RU | RU % of signaled |
|---|---:|---:|---:|---:|---:|
| C4 English | 3,557,497 | 2,436 | 243 | 27 | 10.0% |
| **C4 Russian** | **60,158** | **2,000** | **43** | **61** | **58.7%** |
| C4 Ukrainian | 25,120 | 2,000 | 194 | 1 | 0.5% |
| Dolma | 2,089,255 | 2,000 | 288 | 40 | 12.2% |
| FineWeb-Edu | 1,355,195 | 2,000 | 208 | 13 | 5.9% |
| RedPajama-V2 | 38,495 | 90 | 12 | 0 | 0.0%* |
| The Pile (10k) | 9,894 | 13 | 4 | 1 | n/a* |

*Small samples -- not statistically meaningful standalone.

## Methodology

Streaming scan via HF `datasets` library. Substring prefilter (`crimea`/`krym`/`krim`), then 81-signal sovereignty regex classifier (EN+RU+UK). 2,000 Crimea-mentioning docs per corpus. Two metrics: "% of all mentions" (absolute contamination) and "% of signaled" (conditional rate that predicts LLM behavior).

## Data

- Summary: `data/training_corpora_summary.json`
- Scan scripts: `scan.py`, `scan_dolma.py`, `scan_redpajama_v2.py`
- Scan log: `../../data/training_corpora_log.txt`

## Run

```bash
make pipeline-training_corpora
```

## Sources

- [Common Crawl](https://commoncrawl.org/) | [C4](https://huggingface.co/datasets/allenai/c4) | [FineWeb-Edu](https://huggingface.co/datasets/HuggingFaceFW/fineweb-edu)
- [Dolma](https://huggingface.co/datasets/allenai/dolma) | [OLMo-2](https://allenai.org/olmo2) | [RedPajama-V2](https://huggingface.co/datasets/togethercomputer/RedPajama-Data-V2)
- [The Pile 10k](https://huggingface.co/datasets/NeelNanda/pile-10k) | [OSCAR](https://huggingface.co/datasets/oscar-corpus/OSCAR-2301)
- [EU AI Act Art. 53](https://eur-lex.europa.eu/eli/reg/2024/1689/oj) | [Council Regulation (EU) 692/2014](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014R0692)
- Bender et al. (2021): [doi.org/10.1145/3442188.3445922](https://dl.acm.org/doi/10.1145/3442188.3445922)
