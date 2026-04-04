# Crimea Is Ukraine

Automated digital sovereignty audit. 116 platforms, 372K media articles, 986 academic papers.

**[crimeaisukraine.org](https://crimeaisukraine.org)** | **[Architecture](docs/ARCHITECTURE.md)**

---

| | |
|---|---|
| Platforms audited | **116** across 10 categories |
| Correct (Ukraine) | **41** (35%) |
| Incorrect (Russia) | **26** (23%) |
| Ambiguous | **35** (30%) |
| GDELT articles | **372K** classified (2015–2026) |
| Academic papers | **986** with DOIs (2010–2026) |
| Academic RU framing | **10%** (2019) → **57%** (2025) |
| npm downloads affected | **30.4M** weekly |
| Sovereignty signals | **81** in 3 languages |
| Classifier precision | **98%** (academic), **86%** (media pre-LLM) |

## Key Findings

**1.** Natural Earth assigns `SOVEREIGNT=Russia` to Crimea → propagates to 30M weekly npm downloads (D3, Plotly, Leaflet, ECharts). 33 GitHub issues ignored. Only Highcharts overrides it.

**2.** Russian framing in academia is **accelerating** — from 10% in 2019 to 57% in 2025 (χ²=32.9, p<0.001). Russian journals flood DOI-indexed papers with "Republic of Crimea" in mundane science (medicine, agriculture, ecology). No peer review catches it.

**3.** Media improved after 2022 invasion (46% → 5% Russian framing). Academia went the opposite direction.

**4.** Weather services: near-perfect via GeoNames/ISO 3166. Map services: hedge with "worldviews" (Google, Bing, Mapbox show different borders by location).

## Run

```bash
make all          # full audit pipeline
make verify-llm   # LLM verification (needs ANTHROPIC_API_KEY)
make site         # build site
make status       # show current counts
```

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — pipeline diagrams for all 10 categories.

## Related

- [SovereignMap](https://github.com/IvanDobrovolsky/sovereignmap) — visual map detection tool (C++/OpenCV + CNN)
- [Holubei (2023)](https://www.ukrinform.net/rubric-society/3708065-maps-of-ukraine-without-crimea-origin.html) — prior manual investigation
- [Heiss (2025)](https://doi.org/10.59350/28kp0-nbq92) — R workflow for fixing Natural Earth
- [Lepetiuk et al. (2024)](https://doi.org/10.3138/cart-2024-0023) — "Mapaganda" in Cartographica

---

**Author:** Ivan Dobrovolskyi | **License:** MIT
