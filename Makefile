# CrimeaIsUkraine — Digital Sovereignty Audit
# Run `make` to see all available targets.
# Run `make all` to execute the full automated pipeline.
# Run `make pipeline-NAME` to execute one pipeline (e.g. `make pipeline-ip`).

PYTHON := python3
SCRIPTS := scripts
PIPELINES := pipelines

# Data outputs
DATA := data
SITE_DATA := site/src/data

PIPELINE_NAMES := ip telecom tech_infrastructure geodata weather media \
                  academic wikipedia institutions llm training_corpora

.PHONY: help all install audit audit-core audit-extended audit-ip \
        export site clean \
        $(addprefix pipeline-,$(PIPELINE_NAMES))

# ─── Per-pipeline targets ───────────────────────────────

pipeline-ip: ## Run IP geolocation pipeline (90 IPs × 9 ASNs, rebuilds master manifest)
	cd $(PIPELINES)/ip && uv sync && uv run scan.py
	$(PYTHON) $(SCRIPTS)/build_master_manifest.py

pipeline-telecom: ## Run telecom operators pipeline (curation, rebuilds master manifest)
	cd $(PIPELINES)/telecom && uv sync && uv run scan.py
	$(PYTHON) $(SCRIPTS)/build_master_manifest.py

pipeline-tech_infrastructure: ## Run tech infrastructure pipeline (IANA tz, libphonenumber, OSM Nominatim; rebuilds master manifest)
	cd $(PIPELINES)/tech_infrastructure && uv sync && uv run scan.py
	$(PYTHON) $(SCRIPTS)/build_master_manifest.py

pipeline-geodata: ## Run geodata pipeline (Natural Earth + maps + viz libs)
	cd $(PIPELINES)/geodata && uv sync && uv run scan.py

pipeline-weather: ## Run weather services pipeline (25 services, 4-signal probe; rebuilds master manifest)
	cd $(PIPELINES)/weather && uv sync && uv run scan.py
	$(PYTHON) $(SCRIPTS)/build_master_manifest.py

pipeline-media: ## Run media framing pipeline aggregator (reads framing.json + media_violators.json; rebuilds master manifest)
	cd $(PIPELINES)/media && uv sync && uv run scan.py
	$(PYTHON) $(SCRIPTS)/build_master_manifest.py

pipeline-academic: ## Run academic framing pipeline (OpenAlex 91K + LLM verification)
	cd $(PIPELINES)/academic && uv sync && uv run scan.py

pipeline-wikipedia: ## Run Wikipedia + Wikidata pipeline (and rebuild master manifest)
	cd $(PIPELINES)/wikipedia && uv sync && uv run scan.py
	$(PYTHON) $(SCRIPTS)/build_master_manifest.py

pipeline-institutions: ## Run institutional registries pipeline (LoC, ROR, OFAC, EU, ICAO, ITU, ISO)
	cd $(PIPELINES)/institutions && uv sync && uv run scan.py

pipeline-llm: ## Run LLM sovereignty audit (20+ models × 50 langs × 12 cities)
	cd $(PIPELINES)/llm && uv sync && uv run scan.py

pipeline-training_corpora: ## Run training corpora scan (C4, Dolma, Pile, FineWeb)
	cd $(PIPELINES)/training_corpora && uv sync && uv run scan.py

pipelines-all: $(addprefix pipeline-,$(PIPELINE_NAMES)) ## Run all pipelines sequentially

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ─── Setup ──────────────────────────────────────────────

install: ## Install Python dependencies
	pip install requests beautifulsoup4 duckdb
	@echo "Optional: pip install playwright && playwright install chromium"

# ─── Core audit (no browser, no API keys needed) ───────

audit-open-source: ## Check open source geographic datasets (Natural Earth, D3, etc)
	$(PYTHON) $(SCRIPTS)/check_open_source.py

audit-infrastructure: pipeline-tech_infrastructure ## Deprecated alias for pipeline-tech_infrastructure

audit-propagation: ## Analyze npm/PyPI dependency propagation
	$(PYTHON) $(SCRIPTS)/check_propagation.py

audit-core: audit-open-source audit-infrastructure audit-propagation ## Run core checks (no network APIs)

# ─── API-based audit (needs internet) ──────────────────

audit-platforms: ## Check web platforms (weather, travel, search, reference)
	$(PYTHON) $(SCRIPTS)/check_platforms.py

audit-map-services: ## Check map services and geocoding APIs
	$(PYTHON) $(SCRIPTS)/check_map_services.py

audit-ip: pipeline-ip ## Deprecated alias for pipeline-ip

audit-ip-quick: ## Quick IP geolocation test (4 sample IPs)
	$(PYTHON) $(SCRIPTS)/check_ip_geolocation.py

audit-media: ## GDELT media framing analysis
	$(PYTHON) $(SCRIPTS)/check_media_framing.py

audit-trends: ## Google Trends + Ngrams sovereignty framing
	$(PYTHON) $(SCRIPTS)/check_trends.py

audit-gdelt-framing: ## Scan GDELT for sovereignty framing (2010-2026)
	$(PYTHON) $(SCRIPTS)/scan_gdelt_framing.py --start 2010

audit-gdelt-quick: ## Quick GDELT framing scan (last 3 months)
	$(PYTHON) $(SCRIPTS)/scan_gdelt_framing.py --quick

audit-academic: ## Scan academic papers via OpenAlex + CrossRef (2010-present)
	$(PYTHON) $(SCRIPTS)/scan_academic.py --start 2010

audit-academic-full: ## Full OpenAlex scan (91K papers, cursor pagination)
	$(PYTHON) $(SCRIPTS)/scan_academic_full.py

audit-wikipedia: pipeline-wikipedia ## Deprecated alias for pipeline-wikipedia

audit-loc: ## Library of Congress subject headings + catalog audit
	$(PYTHON) $(SCRIPTS)/check_loc.py

audit-ror: ## ROR + OpenAlex institutional classification audit
	$(PYTHON) $(SCRIPTS)/check_ror.py

audit-iso-eurlex: ## ISO 3166 + EUR-Lex + OFAC sanctions audit
	$(PYTHON) $(SCRIPTS)/check_iso_eurlex.py

audit-legislation: ## Full legislative audit (OFAC, UK, EU, ICAO, ITU, ISO)
	$(PYTHON) $(SCRIPTS)/check_legislation.py

verify-platforms: ## Re-verify all platform findings and fill evidence fields

verify-llm: ## LLM verification of Russia-labeled articles (requires ANTHROPIC_API_KEY)
	$(PYTHON) $(SCRIPTS)/llm_verify.py --resume
	$(PYTHON) $(SCRIPTS)/verify_all.py

audit-api: audit-platforms audit-map-services audit-ip audit-media audit-trends ## Run all API-based checks

audit-framing: audit-gdelt-framing audit-academic ## Run all sovereignty framing scans

# ─── Browser-based audit (needs Playwright + Chromium) ──

audit-browsers: ## Browser screenshots (needs: playwright install chromium)
	$(PYTHON) $(SCRIPTS)/check_browsers.py

audit-double-game: ## Detect geo-dependent platform behavior
	$(PYTHON) $(SCRIPTS)/check_double_game.py

audit-geo: ## Multi-location browser testing
	$(PYTHON) $(SCRIPTS)/check_geo_dependent.py

audit-browser: audit-browsers audit-double-game audit-geo ## Run all browser-based checks

# ─── Full pipeline ─────────────────────────────────────

all: audit-core audit-api export site ## Run full audit pipeline and build site
	@echo ""
	@echo "✓ Full pipeline complete"
	@echo "  Findings: $$(wc -l < $(DATA)/findings.csv) entries"
	@echo "  Site: site/dist/"

# ─── Export & build ────────────────────────────────────

export: ## Export findings to CSV and sync to site JSON
	$(PYTHON) $(SCRIPTS)/export_findings.py

findings-doc: ## Regenerate docs/FINDINGS.md from platforms.json
	$(PYTHON) $(SCRIPTS)/generate_findings_doc.py

statistics: ## Compute publication statistics (Kappa, CI, regression)
	$(PYTHON) $(SCRIPTS)/compute_statistics.py

manifest: ## Regenerate manifest.json (single source of truth for all site numbers)
	$(PYTHON) $(SCRIPTS)/generate_manifest.py

site: manifest ## Build the static site (regenerates manifest first)
	cd site && npm run build

site-dev: ## Start site dev server
	cd site && npx astro dev --port 4321

# ─── Utility ───────────────────────────────────────────

export-hf: ## Export dataset to Hugging Face Hub (requires: pip install huggingface_hub)
	@echo "Exporting datasets to Hugging Face..."
	$(PYTHON) -c "\
from huggingface_hub import HfApi; \
api = HfApi(); \
repo = 'IvanDobrovolsky/crimeaisukraine'; \
api.create_repo(repo, repo_type='dataset', exist_ok=True); \
api.upload_file(path_or_fileobj='$(DATA)/crimea_full.jsonl', path_in_repo='gdelt/crimea_2015_2026.jsonl', repo_id=repo, repo_type='dataset'); \
api.upload_file(path_or_fileobj='$(DATA)/academic_framing_results.json', path_in_repo='academic/openalex_2010_2026.json', repo_id=repo, repo_type='dataset'); \
api.upload_file(path_or_fileobj='$(SITE_DATA)/platforms.json', path_in_repo='platforms/platforms.json', repo_id=repo, repo_type='dataset'); \
api.upload_file(path_or_fileobj='$(SITE_DATA)/manifest.json', path_in_repo='platforms/manifest.json', repo_id=repo, repo_type='dataset'); \
print('Done: https://huggingface.co/datasets/' + repo)"

clean: ## Remove generated data (keeps raw sources)
	rm -f $(DATA)/map_services_results.json
	rm -f $(DATA)/double_game_results.json
	rm -f $(DATA)/geo_dependent_results.json
	@echo "Cleaned generated outputs"

status: ## Show current findings count by category
	@$(PYTHON) -c "\
import json; \
d=json.load(open('$(SITE_DATA)/platforms.json')); \
f=d['findings']; \
cats={}; \
[cats.__setitem__(x['category'], cats.get(x['category'],0)+1) for x in f]; \
print(f'Total: {len(f)} findings across {len(cats)} categories'); \
[print(f'  {c}: {n}') for c,n in sorted(cats.items())]"

# ─── Master manifest ──────────────────────────────────────

master-manifest: ## Build master manifest aggregating all pipeline outputs
	$(PYTHON) $(SCRIPTS)/build_master_manifest.py

