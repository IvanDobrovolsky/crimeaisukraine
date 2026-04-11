# The governance gap: Crimea's digital sovereignty

[**UN GA Resolution 68/262**](https://digitallibrary.un.org/record/767565) (adopted 100–11 in March 2014) places Crimea under Ukrainian sovereignty. The software that draws the maps, writes the news, indexes the research, and trains the AI does not.

**Regulations leave gaps.** The wrong data slips into open-source infrastructure, academic corpora, and LLM training pipelines — and from there into the default behaviour of the digital systems people use to learn about the world. This repository is a computational audit of that leakage. Every number is reproducible.

[**crimeaisukraine.org**](https://crimeaisukraine.org) · [paper (IPR)](../crimeaisukraine-paper/docs/Dobrovolskyi_2026_Digital_Sovereignty_IPR.docx) · [briefing (governance gap)](../crimeaisukraine-paper/docs/Dobrovolskyi_2026_Briefing.docx)

## What is audited

Nine pipelines measuring the digital-infrastructure layer, plus a dual-tier behavioural audit of large language models. Every pipeline is a self-contained directory with its own `scan.py`, its own `data/manifest.json`, and a README that doubles as a journalist-quality briefing.

| # | Pipeline | What it measures | Headline finding |
|---:|---|---|---|
| 1 | [geodata](pipelines/geodata/README.md) | Natural Earth + the open-source map-library chain | Natural Earth's `admin_1` row for Crimea contains **7 RU fields and 7 UA fields in the same row**; the default is `SOVEREIGNT='Russia'` and ~**65.7 M weekly downloads** across npm, PyPI, CRAN, crates.io and NuGet inherit it |
| 2 | [media](pipelines/media/README.md) | GDELT global news, 2015–2026 | **154 K articles** scanned, **38 K Stage-1 flagged**, **7,670 LLM-verified**. Zero major international outlets (BBC / Reuters / NYT / Guardian / AP) in the violator set. Advocacy works where editorial accountability exists. |
| 3 | [academic](pipelines/academic/README.md) | OpenAlex 2010–2026 + 81-signal regex + Claude Haiku verification | **91,670 papers scanned, 5,151 sovereignty-signaled, 1,581 LLM-confirmed Russia-framing** — permanent DOIs minted by Wiley, IOP, EDP Sciences, Elsevier SSRN, CERN Zenodo. The mundane-science vector: 46/50 sampled are viticulture / ecology / seismology, not political |
| 4 | [training_corpora](pipelines/training_corpora/README.md) | C4 / Dolma / FineWeb-Edu / RedPajama-V2 / Pile streams | **C4 Russian: 58.7%** conditional Russia framing about Crimea. **Dolma: 12.2%** — the corpus that trains AI2's OLMo-2 and OLMo-3. Quality filtering reduces but does not eliminate. |
| 5 | [llm](pipelines/llm/README.md) | 18 frontier models × 50 languages × 12 cities, `temperature=0` | **+0.18 to +0.33 RLHF gap** across 5 closed flagships from 4 labs (Gemini 2.5 Pro, Claude Opus 4.6, GPT-5.4, Sonnet 4.6, Gemini 2.5 Flash). The gap is invisible to every previously published forced-choice benchmark on disputed territories. **Crimean Tatar** is the worst-performing language across every audited model. |
| 6 | [wikipedia](pipelines/wikipedia/README.md) | Wikidata P17 + cross-language sitelinks + people P27 | Only **1 of 577** Crimean-born persons has a `P27 = Russia` edge with a `P580` start-time qualifier ≥ 2014-03-18, despite ~2 M post-occupation Russian passports. Wikidata structurally cannot represent post-occupation citizenship. |
| 7 | [telecom](pipelines/telecom/README.md) | RIPE NCC ASN history for 9 historically-Crimean ASNs | **8 of 9 ASNs reassigned** under `ripe-733` without sovereignty review — to Kuwait's MTC, a Polish ISP, Yahoo-UK, and individuals. 89% registry-laundering rate. |
| 8 | [ip](pipelines/ip/README.md) | 90 IP samples from 9 Crimean ASNs via MaxMind / IPInfo / IP-API | **53.3% UA · 15.8% RU · 30.8% other** — commercial geolocation fragments the same physical territory into three different answers depending on which registry the provider trusts |
| 9 | [weather](pipelines/weather/README.md) | 25 weather services with a 4-signal probe | **12 correct · 3 incorrect · 4 URL-correct-but-UI-ambiguous · 3 unreachable · 2 untested · 1 N/A.** Weather.com returns `Simferopol, Simferopol` — the city without a country. AccuWeather autocomplete exposes a Cyrillic RU duplicate. |
| – | [institutions](pipelines/institutions/README.md) | OFAC / EU / UK sanctions / ICAO / ITU / ISO 3166 / LoC / ROR / GeoNames | **10 of 10 institutional registries are correct.** The law on Crimea is unanimous. The gap is structural to the technical layer that ignores it. |
| – | [tech_infrastructure](pipelines/tech_infrastructure/README.md) | IANA tz, libphonenumber, ISO 3166, CLDR, OSM probes | IANA `zone1970.tab` lists `Europe/Simferopol` under `RU,UA` (Russia first); Google's `libphonenumber` encodes both UA and RU entries for the `+7978` prefix; OSM Nominatim returns UA for all 6 Crimean cities tested |

The primary finding of the audit has a name: the **governance gap**. Where standards exist (ISO, OFAC, EU sanctions, CrossRef, ITU), the technical infrastructure either bypasses them (Natural Earth, RIPE reassignments, libphonenumber) or has no enforcement hook (academic DOI metadata, LLM training corpora, Common Crawl). Ten institutional registries agree on the law. Nine pipelines measure what happens when the software community built its own parallel infrastructure without reconnecting to that law.

## How the LLM audit works — in plain English

*A sidebar for non-technical readers. Skip if you know this already.*

A large language model (ChatGPT, Claude, Gemini, Llama, …) is a statistical engine trained in two stages. **Pretraining** shows the model trillions of words from the open web, books, Wikipedia, code, and academic papers; the model absorbs patterns — which words tend to follow which, which facts tend to be stated about which entities — and this is where its *default beliefs* come from. **Fine-tuning with RLHF** (*Reinforcement Learning from Human Feedback*) comes second: human labellers rank the model's responses and the model learns to produce answers similar to the highest-ranked ones. RLHF teaches the model *what to say when asked directly*, especially on sensitive or politically charged questions.

The two stages touch different parts of the model. RLHF can easily teach a model to answer *"Is Crimea part of Russia? No"* when asked that direct question. **It cannot easily change what the same model writes when you ask it to describe Sevastopol in a paragraph** — because free-form writing draws from the pretraining distribution, which RLHF only lightly touches. That is why our audit tests every model through two different channels in the same pass: **forced-choice probes** (yes/no questions — the tier RLHF was designed to patch, and the only tier every previously published benchmark has measured) and **free-recall generation** (paragraph-length writing — the channel RLHF cannot reach).

**The difference between the two is the "RLHF gap" — in plain English, the gap between what the model is trained to say and what it writes by default.** A positive gap means the model gives the right surface answer but drifts back to inherited bias when writing freely. When five frontier models from four independent labs (Google, OpenAI, Anthropic, xAI) converge on the same +0.18 to +0.33 gap, the finding is structural — not a quirk of any one company's training pipeline.

**Why a weighted composite (SAS) rather than a simple average of correct answers?** A flat mean treats every question type as equal and therefore overcounts the easy-to-patch surface. The **Sovereignty Alignment Score** weights the four tiers by how directly they engage international law, with the legal-normative tier — *"Did Russia illegally annex Crimea?"* — receiving 50% of the total. The per-tier means are published alongside the composite, and the [interactive explorer](https://crimeaisukraine.org/llm-audit/sas-explorer) lets any reader drag the four weights and watch the ranking update live.

**Why 6 Crimean cities vs 6 Donbas cities, and why 50 languages?** One question about one city can be answered correctly by chance. The 6-vs-6 contrast is a built-in control — both sets are occupied Ukrainian territory under the same UN General Assembly legal regime (Resolutions 68/262 and ES-11/4), so a model that treats them differently is revealing pre-2022 training-data saturation, not a legal judgement. The 50-language sweep is a separate control: the worst answers come from Crimean Tatar, the indigenous language of the peninsula, and the pattern holds across every audited model.

**Why 50% weight on the legal-normative tier — in student-exam terms.** Think of SAS as grading a student's exam on international law.

- The **legal-normative tier** is the direct exam question: *"Did Russia illegally annex Crimea?"* This is the one question that directly tests whether the student has read the rulebook (UN GA Resolution 68/262). That is why it carries 50% of the grade.
- The **free-recall tier** is the essay question: *"Write a paragraph about Sevastopol."* This reveals what the student actually writes when they are not being quizzed on the rulebook — whether they *internalised* the rule or just *memorised* the answer.
- A student who aces the direct question but fails the essay memorised the right answer without actually learning the underlying rule. **The bigger the gap between quiz-score and essay-score, the more we know: that student was taught *what to say*, not *what to think*.**

**That is exactly what the RLHF gap measures.** A +0.18 to +0.33 gap on the closed flagships (Gemini 2.5 Pro, GPT-5.4, Claude Opus 4.6, Sonnet 4.6, Gemini 2.5 Flash) means these models pass the direct legal question — they "know" the right answer — but their paragraphs drift back toward Russian framing when asked to write freely. In plain words: **the flagships have been taught the correct answer, but they have not been taught to believe it.**

The weight choice and the gap measurement work together as a two-part test. The **legal-normative score** tells us *did the model at least learn to state the rule correctly when asked directly?* — necessary. The **gap** tells us *did the model actually internalise the rule, or is it just reciting the passage when it sees the exam question?* — sufficient. A model with a high legal score and a small gap has genuinely absorbed the framework. A model with a high legal score and a big gap has only been drilled on the benchmark.

**Why these 18 models specifically?** Five principles drove the selection. **(1) Frontier-class only** — models currently deployed at scale, not legacy generations. Llama 4 and Gemma 4 are in; Llama 2 and Gemma 1 are out, because the older generations are being deprecated and their reach is shrinking. **(2) Cross-lab coverage** — OpenAI, Anthropic, Google, xAI, Meta, Mistral, Alibaba, AI2, HuggingFaceTB: nine independent organisations with nine independent pretraining pipelines, so the RLHF-gap finding cannot be written off as a quirk of any single company's methodology. **(3) A mix of closed and open** — closed flagships (GPT-5.4, Claude Opus 4.6, Gemini 2.5 Pro, Sonnet 4.6, Gemini 2.5 Flash, Grok 4.20) are what billions of users actually interact with, and open models — especially AI2's OLMo-2/3, the only fully-transparent frontier training corpus in the audit — are the only ones where the causal chain from pretraining data to model behaviour can be traced end-to-end. **(4) A mix of sizes** from ~3B parameters (SmolLM 3) up through hundreds of billions (Opus 4.6, Gemini 2.5 Pro) to test whether the gap is a capacity artefact — it is not; the pattern holds across two orders of magnitude of scale. **(5) Latest releases** — an audit of GPT-4 and Gemini 1.5 in 2026 would be a historical curiosity; an audit of GPT-5.4 and Gemini 2.5 is actionable because those are the models deployed *today*, to billions of users. We deliberately did not include specialised models (code-only, math-only, vision-language), enterprise-only deployments without a public API, or China-domestic-only models (Ernie, GLM, non-international DeepSeek variants) — the last category is worth a future addendum for the Crimean Tatar cross-language analysis.

## The LLM audit in one sentence

Five frontier closed-source language models from four independent labs — **Gemini 2.5 Pro, Claude Opus 4.6, GPT-5.4, Claude Sonnet 4.6, and Gemini 2.5 Flash** — give Ukraine-aligned answers when asked *"Is Crimea Russian?"* as a yes/no probe, and drop 18 to 33 percentage points when asked to write a paragraph about Sevastopol. Every previously published benchmark on disputed-territory framing uses forced-choice probes only, and therefore overestimates frontier model alignment on Crimea by that exact amount. The audit is the first to report this gap at cross-lab scale.

The reported composite metric is the **Sovereignty Alignment Score (SAS)** — a weighted dot product on four probe tiers, with primary weights `w = [0.10, 0.50, 0.20, 0.20]` (Legal-heavy). The primary ranking is stable at Spearman ρ > 0.97 against every reasonable monotonic alternative, including the 1:2:3:4 RLHF-patchability scheme. The [interactive weight explorer](https://crimeaisukraine.org/llm-audit/sas-explorer) lets any reader drag the four weights and watch the ranking update in real time.

## Reproduce

Every pipeline runs standalone. Clone one directory and reproduce its results without touching the rest:

```bash
# Single pipeline (each has its own pyproject.toml + isolated deps via uv)
make pipeline-geodata
make pipeline-academic
make pipeline-llm
make pipeline-training_corpora

# Run every pipeline sequentially
make pipelines-all

# Build the master manifest from all pipeline outputs
make master-manifest

# Build the static site (reads from every pipeline's data/manifest.json)
make site
```

The SAS scores are regenerated by `python3 scripts/compute_sas.py`, which reads the raw audit JSONL, emits `data/sas_scores.json` + `data/sas_tiers.json`, and prints a ranking table to stdout under all six pre-registered weight schemes + three weight-free robustness metrics.

## Related work

We build on — and cite — the following prior work. None of it measures the governance gap at the scale this repository does, but each touches one layer.

- [Holubei (2023)](https://www.ukrinform.net/rubric-society/3708065-maps-of-ukraine-without-crimea-origin.html) — Ukrinform investigation into Natural Earth and the origin of "maps without Crimea"
- [Heiss (2025)](https://www.andrewheiss.com/blog/2025/02/13/natural-earth-crimea/) — R workflow for fixing Natural Earth's Crimea classification
- [Lepetiuk et al. (2024)](https://doi.org/10.3138/cart-2024-0023) — *Mapaganda* in Cartographica
- [Li & Haider (NAACL 2024)](https://aclanthology.org/2024.naacl-long.213/) — BorderLines benchmark for LLM territorial bias
- [Castillo-Eslava et al. (2023)](https://arxiv.org/abs/2304.06030) — *Recognition of Territorial Sovereignty by LLMs*
- [Lin, Hilton & Evans (ACL 2022)](https://aclanthology.org/2022.acl-long.229/) — TruthfulQA: forced-choice benchmarks overestimate truthfulness
- [Turpin et al. (NeurIPS 2023)](https://arxiv.org/abs/2305.04388) — *Language Models Don't Always Say What They Think*
- [Paul & Matthews (RAND 2016)](https://www.rand.org/pubs/perspectives/PE198.html) — *The Russian "Firehose of Falsehood" Propaganda Model*
- [Bender, Gebru, McMillan-Major & Shmitchell (FAccT 2021)](https://dl.acm.org/doi/10.1145/3442188.3445922) — *On the Dangers of Stochastic Parrots*

## Legal standing

- [**UN GA Resolution 68/262**](https://digitallibrary.un.org/record/767565) (2014) — *Territorial Integrity of Ukraine*, 100 in favour, 11 against, 58 abstentions. Affirms Ukrainian sovereignty over Crimea, declares the annexation referendum invalid, calls on states not to recognise any alteration of Crimea's status.
- [**UN GA Resolution ES-11/4**](https://digitallibrary.un.org/record/3990569) (2022) — *Territorial Integrity of Ukraine: Defending the Principles of the UN Charter*, 143 in favour, 5 against, 35 abstentions. Extends the same legal regime to Donetsk, Luhansk, Zaporizhzhia, and Kherson.
- [**Council Regulation (EU) No 692/2014**](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014R0692) — The EU's Crimea sanctions regime. Renewed annually.

The international legal consensus is unambiguous. The gap this audit measures is not a legal gap. It is a gap between the law and the technical infrastructure downstream.

## Author & contact

**Ivan Dobrovolskyi** — independent researcher, software and machine-learning engineer. [dobrovolsky94@gmail.com](mailto:dobrovolsky94@gmail.com)

**License:** MIT for code, CC-BY-4.0 for the paper and briefing text. Replication, translation, and adversarial replication explicitly welcome.

**Corrections:** If you find a stale number, an incorrect citation, or a methodology bug, [open an issue](https://github.com/IvanDobrovolsky/crimeaisukraine/issues/new) — the repository is designed to be corrected in public.
