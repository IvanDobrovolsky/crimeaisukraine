# CrimeaIsUkraine — Digital Sovereignty Audit
# Run `make` to see all available targets.
# Run `make all` to execute the full automated pipeline.

PYTHON := python3
SCRIPTS := scripts

# Data outputs
DATA := data
SITE_DATA := site/src/data

.PHONY: help all install audit audit-core audit-extended audit-ip \
        export site clean

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

audit-infrastructure: ## Check tech infrastructure (IANA, libphonenumber, DNS, etc)
	$(PYTHON) $(SCRIPTS)/check_infrastructure.py

audit-propagation: ## Analyze npm/PyPI dependency propagation
	$(PYTHON) $(SCRIPTS)/check_propagation.py

audit-core: audit-open-source audit-infrastructure audit-propagation ## Run core checks (no network APIs)

# ─── API-based audit (needs internet) ──────────────────

audit-platforms: ## Check web platforms (weather, travel, search, reference)
	$(PYTHON) $(SCRIPTS)/check_platforms.py

audit-map-services: ## Check map services and geocoding APIs
	$(PYTHON) $(SCRIPTS)/check_map_services.py

audit-ip: ## Bulk IP geolocation test (90 IPs, 9 ASNs)
	$(PYTHON) $(SCRIPTS)/check_ip_bulk.py

audit-ip-quick: ## Quick IP geolocation test (4 sample IPs)
	$(PYTHON) $(SCRIPTS)/check_ip_geolocation.py

audit-media: ## GDELT media framing analysis
	$(PYTHON) $(SCRIPTS)/check_media_framing.py

audit-trends: ## Google Trends + Ngrams sovereignty framing
	$(PYTHON) $(SCRIPTS)/check_trends.py

audit-api: audit-platforms audit-map-services audit-ip audit-media audit-trends ## Run all API-based checks

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

site: ## Build the static site
	cd site && npm run build

site-dev: ## Start site dev server
	cd site && npx astro dev --port 4321

# ─── Utility ───────────────────────────────────────────

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
