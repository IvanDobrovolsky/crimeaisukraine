# Grounding Contamination Audit Pipeline

Tests whether AI chatbot web search surfaces sanctioned or state-documented propaganda sources when answering questions about Crimea.

## Method

4 models × 25 queries × 10 languages = 1,000 API calls with web search enabled.
Each cited URL checked against US OFAC SDN, EU Consolidated Financial Sanctions, UK OFSI, and US State Dept GEC proxy site list.

**Models**: GPT-4o, Claude Sonnet, Gemini 2.5 Flash, Perplexity Sonar
**Languages**: en, uk, ru, de, fr, es, pl, tr, it, nl
**Temperature**: 0 (all models)

## Results

| Source | Citations | % |
|---|---:|---:|
| Sanctioned (OFAC/EU/UK) | 5 | 0.1% |
| Russian government (.gov.ru) | 37 | 0.9% |
| Russian non-gov (.ru/.su) | 259 | 6.6% |
| International | 3,617 | 92.3% |
| **Russian-origin total** | **301** | **7.7%** |

GEC-documented proxy sites: 0 citations in baseline audit, but 74 citations when searched by name (aggressive probes).

## Files

| File | Description |
|---|---|
| `scan.py` | Main pipeline — parallel 8-thread scanner |
| `data/grounding_audit.jsonl` | 1,000 responses with all cited URLs |
| `data/aggressive_proxy_probes.json` | 140 targeted proxy site probes |
| `data/scf_contamination_final.json` | 32 narrative probes (8 queries × 4 models) |
| `data/manifest.json` | Pipeline metadata and verified results |
| `data/LLM_Web_Search_Contamination.docx` | Full briefing document |

## Sanctions Sources

- US OFAC SDN: `treasury.gov/ofac/downloads/sdn.csv`
- EU Consolidated: `webgate.ec.europa.eu/fsd/fsf/public/files/csvFullSanctionsList/content`
- UK OFSI: `ofsistorage.blob.core.windows.net/publishlive/2022format/ConList.csv`
- US State Dept GEC: `2017-2021.state.gov/russias-pillars-of-disinformation-and-propaganda-report/`

## Reproducibility

```bash
export ANTHROPIC_API_KEY=...
export OPENAI_API_KEY=...
export GEMINI_API_KEY=...
export PERPLEXITY_API_KEY=...
python3 pipelines/grounding/scan.py
```

Requires `requests` package. Resume-safe (checkpoints to JSONL). Parallel execution (8 threads).
