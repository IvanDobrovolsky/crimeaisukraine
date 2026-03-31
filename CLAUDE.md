# Claude Instructions

## Project Context

This is an investigative research project documenting how digital platforms represent Crimea's sovereignty. The goal is to produce actionable findings for Ukraine's MFA and media coverage.

**Key principle:** Crimea is internationally recognized as Ukrainian territory, illegally occupied by Russia since 2014. Any platform showing Crimea as part of Russia is factually incorrect under international law.

## Working Style

- Be thorough and systematic — check every platform mentioned in SPEC.md
- Take screenshots (describe what you see if you can't capture)
- Always note the date of each check (platforms change)
- Document the exact URL/path to reproduce findings
- Categorize findings: ✅ Correct (shows Ukraine), ⚠️ Ambiguous (disputed/no label), ❌ Incorrect (shows Russia)

## Data Access

- GDELT data is in BigQuery project `kyivnotkiev-research`, dataset `kyivnotkiev`, pair_id=18
- Existing Crimea analysis at `/Users/tati/Desktop/ivan/kyivnotkiev/CRIMEA_ANALYSIS.md`
- GCP is authenticated — you can run `bq query` commands

## Output Format

- All findings go in `docs/` as markdown files
- Raw data goes in `data/` as JSON/CSV
- One file per category (maps.md, travel.md, media.md, etc.)
- Summary report at `docs/REPORT.md`

## Priority Order

1. Map services (highest visibility, most impactful)
2. Travel platforms (affects real users)
3. News media framing
4. Social media location tags
5. Reference platforms
6. Tech infrastructure
