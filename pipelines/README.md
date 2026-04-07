# Pipelines

Each subdirectory is an **independent, self-contained pipeline** for one aspect of the Crimea sovereignty audit. A reviewer can clone just one pipeline, install its `uv` deps, and reproduce its results without touching the rest of the project.

## Pipeline list

| Pipeline | What it audits | Method | Status |
|---|---|---|---|
| [ip](ip/) | IP geolocation databases for Crimean ASNs | API | ✓ stable |
| [telecom](telecom/) | Mobile operators, RIPE NCC | API + WHOIS | ✓ stable |
| [tech_infrastructure](tech_infrastructure/) | IANA tz, libphonenumber, ICAO, postal | Source code | ✓ stable |
| [geodata](geodata/) | Natural Earth, D3, Leaflet, map services | Source + API | ✓ stable |
| [weather](weather/) | Weather APIs (AccuWeather, Yandex, etc.) | API | ✓ stable |
| [media](media/) | GDELT 154K articles + LLM verification | BigQuery + LLM | ✓ stable |
| [academic](academic/) | OpenAlex 91K papers + LLM verification | API + LLM | ✓ stable |
| [wikipedia](wikipedia/) | 17 terms × 30 langs + Wikidata | REST API + SPARQL | ✓ stable |
| [institutions](institutions/) | LoC, ROR, OFAC, EU sanctions, ICAO, ITU, ISO | API + docs | ✓ stable |
| [llm](llm/) | 20+ LLMs × 50 languages × 12 cities × 15 questions | API + Ollama | 🔄 running |
| [training_corpora](training_corpora/) | C4, Dolma, Pile, FineWeb, OSCAR | HF datasets | 🔄 running |

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

The `scripts/build_master_manifest.py` script reads each pipeline's `manifest.json` and aggregates them into `site/src/data/master_manifest.json` — the single source of truth the site reads.

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
