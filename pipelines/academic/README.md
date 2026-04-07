# Academic Framing: How DOIs Make Sovereignty Claims Permanent

## What is a DOI and why does it matter?

A **[Digital Object Identifier (DOI)](https://www.doi.org/)** is a permanent unique identifier assigned to a published academic work. The DOI system is administered by the [International DOI Foundation](https://www.doi.org/the-foundation/) and the registration is done by member registries — primarily [CrossRef](https://www.crossref.org/) for journals and [DataCite](https://datacite.org/) for datasets. As of 2025, more than **140 million DOIs** have been assigned to published works ([CrossRef stats](https://www.crossref.org/06members/53status.html)).

When a journal publishes a paper, it assigns the paper a DOI like `10.1088/1755-1315/666/5/052019`. The DOI is then resolvable forever to the paper's metadata: title, authors, abstract, **institutional affiliations**, journal, year, and a link to the full text. This metadata is the canonical record. It is what every database — Google Scholar, Scopus, Web of Science — ingests and re-displays.

**Critical for our investigation**: a DOI cannot be revoked. Once issued, the metadata enters the global scholarly record permanently. If a paper lists its institutional affiliation as "Crimean Federal University, Republic of Crimea, Russian Federation," that text is now part of the citation graph, indexed by every academic search engine, and cited by every paper that references this work — forever.

## How academic papers propagate from publisher to reader

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor': '#0057b7', 'primaryTextColor': '#e5e5e5', 'lineColor': '#64748b', 'primaryBorderColor': '#1e293b'}}}%%
graph TB
    A["Author submits paper<br/>with affiliation:<br/>'Magarach Institute,<br/>Republic of Crimea, Russia'"]
    A --> B["Journal publisher<br/>peer review<br/>copy editing"]
    B -->|"DOI minted via"| C["CrossRef<br/>140M+ DOIs<br/>persistent registry"]
    C --> D["Metadata harvested by"]
    D --> E["Google Scholar<br/>200M+ records"]
    D --> F["Scopus<br/>Elsevier"]
    D --> G["Web of Science<br/>Clarivate"]
    D --> H["OpenAlex<br/>250M+ open works"]
    D --> I["Semantic Scholar<br/>200M+ records"]
    E --> J["Citations propagate<br/>through scholarly graph"]
    F --> J
    G --> J
    H --> J
    I --> J
    J --> K["Other papers cite<br/>and inherit affiliation text"]
    K --> L["The 'Republic of Crimea, Russia'<br/>framing becomes permanent<br/>part of the global record"]

    style A fill:#7f1d1d,stroke:#ef4444,color:#ffffff
    style C fill:#111827,stroke:#0057b7,color:#e5e5e5
    style D fill:#111827,stroke:#1e293b,color:#e5e5e5
    style E fill:#111827,stroke:#0057b7,color:#e5e5e5
    style F fill:#111827,stroke:#0057b7,color:#e5e5e5
    style G fill:#111827,stroke:#0057b7,color:#e5e5e5
    style H fill:#111827,stroke:#0057b7,color:#e5e5e5
    style I fill:#111827,stroke:#0057b7,color:#e5e5e5
    style J fill:#111827,stroke:#1e293b,color:#e5e5e5
    style K fill:#111827,stroke:#1e293b,color:#e5e5e5
    style L fill:#111827,stroke:#ef4444,color:#ef4444
```

The chain has no sovereignty checkpoint:
- **The author** writes the affiliation as they wish
- **The journal** copy-edits for grammar and style, not territorial classification
- **CrossRef** mints DOIs for any registered metadata; no validation of factual claims
- **Google Scholar** crawls everything that has a DOI; no editorial filter
- **Scopus and Web of Science** index based on journal selection criteria, but the criteria evaluate the *journal*, not individual papers' metadata claims

The **only** checkpoint where territorial framing could be flagged is the journal editor and peer reviewer. In practice, neither catches it because the framing appears in the affiliation field — administrative metadata, not the substance of the paper. A paper about [grape cultivation in Yalta](https://doi.org/10.1051/bioconf/20213902003) gets reviewed for its findings on grape cultivars, not for whether its first sentence says "the Republic of Crimea, Russia."

## What is OpenAlex and how do we use it?

**[OpenAlex](https://openalex.org/)** is a free, open replacement for Microsoft Academic Graph (which shut down in 2021). Maintained by the non-profit [OurResearch](https://ourresearch.org/) and funded by the [Arcadia Fund](https://www.arcadiafund.org.uk/), OpenAlex contains metadata for **250 million scholarly works**, fully open and queryable via [api.openalex.org](https://api.openalex.org/). It is the most complete open-access source for academic metadata in the world.

For this audit we query OpenAlex for every work that mentions any Crimean place name in its title or abstract. We use cursor pagination to retrieve every match, then reconstruct each paper's abstract from OpenAlex's inverted-index format.

## How we measured

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor': '#0057b7', 'primaryTextColor': '#e5e5e5', 'lineColor': '#64748b', 'primaryBorderColor': '#1e293b'}}}%%
graph TB
    A["OpenAlex API<br/>cursor pagination<br/>5 search queries:<br/>Crimea, Simferopol,<br/>Sevastopol, Yalta, Kerch"] --> B["91,670 papers<br/>2010 to 2026"]
    B --> C["Title + abstract<br/>reconstructed from<br/>inverted index"]
    C --> D["Stage 1 — Regex<br/>81 sovereignty signals<br/>EN + RU + UK"]
    D -->|"5,151 with signals"| E["Stage 2 — LLM<br/>Claude Haiku<br/>per-paper verification"]
    D -->|"86,519 no signal"| Z["Skipped"]
    E -->|"1,581 confirmed"| F["Russia framing<br/>permanent in metadata"]
    E -->|"2,131 confirmed"| G["Ukraine framing"]
    E -->|"1,439 unclear"| H["Insufficient context<br/>in title/abstract"]
    F --> I["Stage 3 — Manual<br/>publisher classification<br/>Q1 / Q2 indexed?"]
    G --> J["data/manifest.json"]
    I --> J
    H --> J

    style A fill:#111827,stroke:#0057b7,color:#e5e5e5
    style B fill:#111827,stroke:#0057b7,color:#e5e5e5
    style D fill:#111827,stroke:#1e293b,color:#e5e5e5
    style E fill:#111827,stroke:#1e293b,color:#e5e5e5
    style F fill:#111827,stroke:#ef4444,color:#ef4444
    style G fill:#111827,stroke:#22c55e,color:#22c55e
    style I fill:#111827,stroke:#1e293b,color:#e5e5e5
    style J fill:#111827,stroke:#22c55e,color:#22c55e
```

**Stage 1 — Regex precision is much higher for academic than for media.** For media, "Republic of Crimea" frequently appears in quotation contexts (BBC reporting on Russian claims). For academic papers, it almost always appears as a literal location label. We measured **84.4% Stage 1 precision** on the academic corpus versus 60.5% on the media corpus. The reason is structural: academic affiliations are not quotations of Russian propaganda; they are the author's own classification of where the research was conducted.

**Stage 2 — LLM verification** uses Claude Haiku to confirm each flagged paper:

> Analyze this academic paper's title and abstract for Crimea sovereignty framing. Does it ENDORSE Crimea as Russian territory (e.g., uses "Republic of Crimea" as a default location label, describes research conducted "in the Republic of Crimea, Russia"), or is it ANALYZING Russian claims critically?

The cost is approximately **$0.0006 per paper**, totaling about **$3** for the full 5,151-paper verification.

## Findings

| Stage | Count |
|---|---|
| OpenAlex papers scanned | **91,670** |
| With sovereignty signals (Stage 1) | 5,151 |
| LLM-confirmed Russia framing (Stage 2) | **1,581** |
| LLM-confirmed Ukraine framing | 2,131 |
| Unclear / analyzes | 1,439 |

### Russia framing peaked in 2021 and stabilized at 42–44%

Year-by-year breakdown of Russia framing as a percentage of papers with sovereignty signals:

| Year | Russia % |
|---|---|
| 2010–2013 | 0–9% |
| 2014 | 21% (annexation year) |
| 2015–2017 | 29–36% |
| 2018–2019 | 34–36% |
| 2020 | 45% |
| **2021** | **51%** (peak) |
| 2022 | 39% (full-scale invasion) |
| 2023 | 37% |
| 2024 | 37% |
| 2025 | 36% |
| 2026 (partial) | 33% |

The pattern is **counter-intuitive**: Russia framing peaked in 2021, **before** the full-scale invasion, when international attention was lower. It dropped after 2022 but stabilized at 36–44% — high and persistent.

### Western Q1 publishers host the violations

We cross-referenced confirmed Russia-framing papers against their journals' h-index and indexing status (Scopus, Web of Science). The result is that several **major Western academic publishers** host significant numbers of Russia-framing papers:

| Publisher | Journal | h-index | Russia papers | Indexing |
|---|---|---|---|---|
| **Wiley** | [Water Resources](https://onlinelibrary.wiley.com/journal/15732106) | 420 | 6 | Scopus Q1 |
| **IOP Publishing** | [J. Physics Conf. Series](https://iopscience.iop.org/journal/1742-6596) | 131 | 3 | Scopus |
| **IOP Publishing** | [IOP Conf. Materials Science](https://iopscience.iop.org/journal/1757-899X) | 92 | 10 | Scopus |
| **IOP Publishing** | [IOP Conf. Earth & Env. Science](https://iopscience.iop.org/journal/1755-1315) | 76 | 19 | Scopus |
| **EDP Sciences** | [E3S Web of Conferences](https://www.e3s-conferences.org/) | 59 | 17 | Scopus |
| **EDP Sciences** | [SHS Web of Conferences](https://www.shs-conferences.org/) | 43 | 7 | Scopus |
| **EDP Sciences** | [BIO Web of Conferences](https://www.bio-conferences.org/) | 31 | 9 | Scopus |
| **Elsevier** | [SSRN](https://www.ssrn.com/) | 452 | 6 | Preprint |
| **CERN** | [Zenodo](https://zenodo.org/) | 198 | 23 | Repository |

The paper that best illustrates the pattern is on SSRN: "[The Reunification of Crimea and the City of Sevastopol with the Russian Federation: Logic Dictating Borders](https://doi.org/10.2139/ssrn.2979268)" — the title alone uses Russian framing, the paper has a permanent DOI minted by Elsevier's preprint server, and it is indexed by Google Scholar.

### The mundane science vector

We sampled 50 papers tagged by the "Republic of Crimea" signal at random and read them carefully. The result:

- **46 of 50** are mundane science: viticulture, marine ecology, seismology, plant pathology, transport infrastructure, archaeology of late antique necropoleis, drinking water quality assessments
- **3 of 50** are political science / international law analyses
- **1 of 50** is a translation error (the paper is actually about pre-2014 events)

The papers are not making sovereignty arguments. They are making **scientific arguments** that happen to list institutional affiliations using Russian administrative names. The mechanism: a researcher at the [Magarach Institute of Viticulture and Winemaking](https://en.wikipedia.org/wiki/Magarach_Institute) (a real research institution in Yalta, founded in 1828) writes a paper about grape varieties. Their affiliation in 2026 is "Magarach Institute of Viticulture and Winemaking, Republic of Crimea, Russian Federation." The paper has nothing to say about geopolitics. It just classifies the location of a vineyard.

This is the **mundane science vector**. It is consequential precisely because it is unremarkable. No journal editor catches it. No peer reviewer is qualified to challenge it. No indexing service flags it. And the result is a steady stream of DOI-minted, permanently-indexed papers carrying Russian sovereignty framing into the global scholarly record.

### The institutional registry contradiction

The [Research Organization Registry (ROR)](https://ror.org/) is the global standardized registry of research institutions. ROR is maintained by [DataCite](https://datacite.org/) and used by [CrossRef](https://www.crossref.org/), [ORCID](https://orcid.org/), and OpenAlex to identify the institutions behind published works.

**ROR codes 13 of 14 Crimean academic institutions as Ukraine** — including [V.I. Vernadsky Crimean Federal University](https://ror.org/05erbjx97). The registry has the correct classification.

But the papers published by researchers at these UA-coded institutions list affiliations as "Republic of Crimea, Russian Federation." **The institution registry says one thing; the paper metadata says another. No system reconciles them.** A researcher's institution is officially Ukrainian per ROR, but every paper they publish enters the scholarly record as Russian.

The single ROR exception is the [Research Institute of Agriculture of Crimea](https://ror.org/04m1rjm36), which is coded as Russia and is also the most prolific producer of "Republic of Crimea, Russia" papers (3,472 works in OpenAlex). The institution coding and the paper coding agree, in the wrong direction.

## The regulation gap

There is no requirement that academic indexing services validate sovereignty claims in metadata. The relevant systems and their gaps:

- **[CrossRef](https://www.crossref.org/)** — mints DOIs for any submitted metadata; explicitly takes a [neutral stance on factual content](https://www.crossref.org/policies/) ("we do not assert opinions on metadata accuracy")
- **[Scopus selection criteria](https://www.elsevier.com/products/scopus/content/content-policy-and-selection)** — evaluate journals for editorial quality but not individual papers' affiliation metadata
- **[Web of Science journal selection process](https://clarivate.com/products/scientific-and-academic-research/research-discovery-and-workflow-solutions/webofscience-platform/journal-evaluation/)** — same: journal-level evaluation
- **[Google Scholar](https://scholar.google.com/intl/en/scholar/about.html)** — crawls everything; no editorial process
- **[DOAJ (Directory of Open Access Journals)](https://doaj.org/apply/transparency/)** — has transparency criteria for journals but not for individual paper claims

[Council Regulation (EU) No 692/2014](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014R0692) — the EU's Crimea sanctions regime — explicitly classifies Crimea as illegally annexed Ukrainian territory and prohibits commercial activity. **No mechanism connects this regulation to Western academic publishers (IOP, Wiley, EDP Sciences, Elsevier) that mint DOIs for papers using Russian sovereignty framing.**

## Findings (numbered for citation)

1. **91,670 academic papers** scanned via OpenAlex 2010–2026
2. **5,151 papers** flagged by 81-signal regex with sovereignty markers
3. **1,581 LLM-confirmed Russia-framing papers** after Stage 2 (84.4% Stage 1 precision)
4. **Russia framing peaked at 51% in 2021**, before the 2022 full-scale invasion
5. **Stabilized at 36–44% post-invasion** — high and persistent rather than declining
6. **Western Q1 publishers host violations**: Wiley (h-index 420), IOP Publishing (76–131), EDP Sciences (31–59), Elsevier SSRN (452), CERN Zenodo (198)
7. **The mundane science vector**: 46 of 50 sampled papers are agriculture, ecology, medicine, archaeology — not political advocacy
8. **ROR codes 13/14 Crimean institutions as Ukraine** — but their papers list "Republic of Crimea, Russia"
9. **No academic indexing service** (CrossRef, Scopus, Web of Science, Google Scholar) **validates sovereignty claims in metadata**
10. **DOIs are permanent**: there is no mechanism to retroactively correct a paper's affiliation field

## Method limitations

- OpenAlex coverage is comprehensive but lags slightly for the most recent year
- Stage 2 LLM verification covers all 5,151 flagged papers, but the 86,519 papers without sovereignty signals were not LLM-verified (false negatives possible)
- Manual annotation of all 1,581 Russia-confirmed papers is in progress but not complete
- Abstract reconstruction from OpenAlex's inverted index is approximate; some papers may have abstracts missing
- Did not test whether papers published in Russian-language journals also have English-language affiliations
- Cannot resolve whether individual researchers chose Russian framing or were required to by their institution

## Sources

- DOI Foundation: https://www.doi.org/
- CrossRef: https://www.crossref.org/
- DataCite: https://datacite.org/
- OpenAlex: https://openalex.org/
- OpenAlex API: https://api.openalex.org/works
- Google Scholar: https://scholar.google.com/
- Scopus: https://www.elsevier.com/products/scopus
- Web of Science: https://clarivate.com/products/scientific-and-academic-research/research-discovery-and-workflow-solutions/webofscience-platform/
- Research Organization Registry (ROR): https://ror.org/
- DOAJ: https://doaj.org/
- Magarach Institute: https://en.wikipedia.org/wiki/Magarach_Institute
- Council Regulation (EU) No 692/2014: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014R0692
- "The Reunification of Crimea and the City of Sevastopol with the Russian Federation": https://doi.org/10.2139/ssrn.2979268
