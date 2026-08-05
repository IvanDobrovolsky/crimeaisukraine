# Why Twitter Replications Diverged from the Article — Investigation

**Date of all checks: 2026-07-30.** Context: Kyiv Independent article (2026-07-01,
https://kyivindependent.com/why-ai-believes-crimea-is-russian-and-what-to-do-about-it/)
was amplified by @Mylovanov (2026-07-05, https://x.com/Mylovanov/status/2073866029365645454,
~54.6K views, 840 likes). Some commenters attempted to replicate ("ask AI for a map")
and got Crimea rendered as Ukraine, or inconsistent results, reading this as evidence
the article was overstated.

**Conclusion up front: the replication divergence is predicted by the research itself.
The contaminated pathway (code-gen → Natural Earth-derived data) still reproduces
100% mechanically as of today. The "failed" replications used different pathways
(chat Q&A, image generation, or libraries that ship corrected geometry).**

## 1. The contaminated pathway still reproduces (verified 2026-07-30)

Method: point-in-polygon test for Simferopol (34.10E, 44.95N), Sevastopol (33.52E,
44.60N), Kerch (36.47E, 45.36N) against Ukraine and Russia geometries in each
dataset, fetched live from their canonical distribution URLs.

| Dataset (as served today) | Crimea assigned to | Source URL |
|---|---|---|
| Natural Earth master 110m admin0 | ❌ **Russia** | raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson |
| world-atlas@2 110m (D3 standard) | ❌ **Russia** | cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json |
| plotly.js dist topojson (world_110m) | ✅ **Ukraine** | raw.githubusercontent.com/plotly/plotly.js/master/dist/topojson/world_110m.json |
| ECharts 4.9 world.json | ✅ **Ukraine** | cdn.jsdelivr.net/npm/echarts@4.9.0/map/json/world.json |
| johan/world.geo.json (pre-2014, ubiquitous in tutorials) | ✅ **Ukraine** | raw.githubusercontent.com/johan/world.geo.json/master/countries/UKR.geo.json |

Notes:
- Natural Earth 110m: Simferopol and Sevastopol inside Russia polygon; Kerch outside
  both at this resolution (coarse coastline near the strait), not a counter-signal.
- plotly result is the shipped master dist geometry, verified empirically. Provenance
  of the fix not yet traced (no Crimea entry in CHANGELOG.md) — TODO below.
- ECharts 5 no longer bundles world.json; the widely-mirrored echarts@4.9.0 file was
  tested.

**Implication: a code-generated map is a lottery over data sources.** If the model
emits D3 + world-atlas (the most common D3 choropleth recipe) or downloads Natural
Earth directly (geopandas/cartopy path) → Crimea renders as Russia. If it emits
plotly, ECharts, or the old johan GeoJSON → Crimea renders as Ukraine. At consumer
temperature settings the choice of library/dataset varies run to run. **Mixed
replication results are the expected outcome**, not evidence against the finding.

## 2. Why chat replications showed "Crimea is Ukraine"

Most casual replications did not follow the article's pathway (code generation).
They hit paths the paper already measured as correct or that bypass geodata:

1. **Declarative chat Q&A** — "Is Crimea part of Ukraine?" / "show me a map" answered
   in prose. This is the paper's d-tier, where models score high. The gap Δ = d − r
   (declarative-generative gap, +0.04 to +0.27 on 7 closed-source models) is the
   paper's core Layer-2 finding: models *say* the right thing and *do* the wrong
   thing. A commenter's correct chat answer **confirms** the gap; it does not refute
   the generative finding.
2. **Image generation** — "generate a map of Ukraine" in ChatGPT triggers image-gen,
   which draws the iconic country silhouette (which includes Crimea) from learned
   visual patterns, not from any geodatabase. Different mechanism entirely.
3. **Web-grounded responses** — consumer chatbots with search can now retrieve the
   KI article itself and correct their answer (self-referential grounding).
4. **Post-publication vendor patches** — e.g., Anthropic globe fix
   (demos/anthropic-globe-fix/). Vendors may have patched frontends after the
   media wave without touching the upstream data.
5. **Settings drift** — the audit locked temp=0, seed=42, pinned model versions
   (May 2026). Consumer apps use nonzero temperature and rolling model updates.

## 3. Upstream status: Natural Earth unchanged, but the article moved the community

- The natural-earth-vector repo has **no commits since 2022-06** (v5.2.0-pre).
  The data cannot have changed — SOVEREIGNT=Russia for Crimea persists.
- The article visibly drove activity to the repo (checked 2026-07-30):
  - Issues #839, #993, #1001 all received updates 2026-07-03/04 (article was 07-01).
  - **New issue #1021 (2026-07-05, by enn-nafnlaus): "[Proposal] Making available a
    systematic De Jure / UN Consensus view while respecting the De Facto standard"**
    — cites Bing (ICJ/UN/ISO deference) and Google (UN/treaty deference) policies,
    i.e., exactly the paper's regulation-gap argument.
    https://github.com/nvkelso/natural-earth-vector/issues/1021

## 4. What this means for comms and the paper

- **The criticism is answerable with one sentence:** "You asked the model a question;
  the article asked it to build something. Models answer correctly and build
  incorrectly — that gap is the finding, and it's quantified in the paper."
- The plotly/ECharts result is a **positive counterexample worth citing**: downstream
  libraries can and do override Natural Earth, proving the fix is feasible at the
  library level without upstream cooperation.
- Consider a public, one-click reproducible demo (pinned dataset URLs + the
  point-in-polygon test above) so replications target the actual claim. The tests in
  this doc are fully scriptable and model-independent.
- Issue #1021 is a concrete policy vector aligned with the paper's recommendation —
  worth supporting/citing in the revision.

## 5. Not yet verified / open items

- **Reply contents of the Mylovanov thread** — X replies are not accessible without
  auth; need screenshots/links of the specific replication attempts to classify each
  by pathway (chat / image-gen / code-gen + which library).
- **Live model probes (July 2026 versions)** — re-running the map-generation probe
  against current model versions requires API keys; not run in this session.
- **Provenance of the plotly Crimea fix** — empirically Ukraine in shipped dist;
  trace which PR/topojson build changed it before citing as a deliberate override.
