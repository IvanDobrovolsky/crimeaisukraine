# Pipelines

Each subdirectory is an **independent pipeline** that audits one aspect of how digital systems classify Crimea's sovereignty. Each pipeline is a self-contained briefing: a journalist or researcher can read just one README and understand what was tested, why it matters, how the measurement was done, and what was found — with full citations to standards, regulations, and data sources.

## Pipeline list

| Pipeline | What it audits | Status |
|---|---|---|
| [**ip**](ip/README.md) | IP geolocation databases for Crimean ASNs · BGP, RIPE NCC, MaxMind, Cloudflare | ✓ stable |
| [**telecom**](telecom/README.md) | Mobile operators, RIPE NCC ASN reassignment, ITU E.164 numbering | ✓ stable |
| [**tech_infrastructure**](tech_infrastructure/README.md) | IANA tz, libphonenumber, ISO 3166, CLDR · 189M weekly downloads affected | ✓ stable |
| [**geodata**](geodata/README.md) | Natural Earth + D3 + Leaflet + map services · the 30M downloads/week pipeline | ✓ stable |
| [**weather**](weather/README.md) | 23 weather services · the counterpoint, 70% correct via GeoNames | ✓ stable |
| [**media**](media/README.md) | GDELT 154K articles + LLM verification · 0.5% non-Russian endorsement | ✓ stable |
| [**academic**](academic/README.md) | OpenAlex 91K papers + LLM verification · 1,581 confirmed Russia-framing papers | ✓ stable |
| [**wikipedia**](wikipedia/README.md) | 17 entities × 30 language editions + Wikidata · erasure by omission | ✓ stable |
| [**institutions**](institutions/README.md) | LoC, ROR, OFAC, EUR-Lex, ICAO, ITU, ISO · 6/6 unanimous | ✓ stable |
| [**llm**](llm/README.md) | 20+ LLMs × 50 languages × 12 cities × 15 questions · cognitive dissonance + training cutoff bias | 🔄 running |

## Standard layout per pipeline

```
pipelines/<name>/
├── README.md              # name, why, what, how, run, results, conclusions, findings, limitations
├── pyproject.toml         # uv-managed deps (python>=3.10, dataset-specific libs)
├── scan.py                # main entry point (or run.py for orchestration)
├── data/
│   ├── manifest.json      # standardized output schema
│   ├── raw/               # raw API/file dumps
│   └── findings.csv       # human-readable per-platform findings
└── tests/
    └── test_smoke.py      # at least: imports work, classifier runs
```

## Standardized output schema (manifest.json)

```json
{
  "pipeline": "ip",
  "version": "1.0",
  "generated": "2026-04-07T00:42:00Z",
  "method": "automated_api",
  "summary": {
    "total_items": 5,
    "correct": 4,
    "incorrect": 0,
    "ambiguous": 1
  },
  "findings": [...],
  "key_findings": [
    "..."
  ],
  "limitations": [
    "..."
  ]
}
```

## Master manifest

The `pipelines/_shared/build_master_manifest.py` script reads each pipeline's `manifest.json` and aggregates them into `site/src/data/master_manifest.json` — the single source of truth the site reads.

## Running a single pipeline

```bash
cd pipelines/ip
uv sync
uv run scan.py
```

Each pipeline has its own `pyproject.toml` so you only install what you need. No project-wide requirements.txt.

## Running everything

```bash
make all          # runs all pipelines + builds master manifest + builds site
make pipeline-ip  # runs just one
```
