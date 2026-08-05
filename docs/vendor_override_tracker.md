# Vendor Override Tracker: Who Fixed Their World Map, How, and Who Followed

**Date: 2026-08-05.** Companion to `data/geodata_js_census.json` (empirical Crimea
tests + npm downloads) and `docs/natural_earth_consistency.md`. Scope: JS web
libraries + vendor geodata policies. Everything below is either verified by
point-in-polygon test (marked ✓) or cited to a primary source.

## The four strategies observed in the wild

| Strategy | Who | Crimea result |
|---|---|---|
| 1. Inherit NE default | world-atlas ✓, datahub ✓, d3/react-simple-maps/chartjs-geo/Plot (recipe level) | ❌ Russia |
| 2. Switch data source | **plotly** (UN geodata, 2025) ✓ | ✅ Ukraine (with a catch — see below) |
| 3. Neutral carve-out | **Highcharts** ✓, NE's own ISO-POV file ✓ | ⚠️ Neither |
| 4. Frozen pre-2014 snapshot | echarts@4.9 ✓, datamaps ✓, jsvectormap ✓, vega-datasets ✓, johan ✓ | ✅ Ukraine (by accident) |
| (2/4 hybrid) custom corrected | amCharts ✓, anychart ✓ | ✅ Ukraine |

## Case study 1: plotly — the switch, and the split brain

Timeline (from plotly/plotly.js GitHub, verified 2026-08-05):
- 2019: PR #3874 upgraded to sane-topojson v3 / **Natural Earth v4.1** — the NE era.
- 2019: issue #4345 "Add way to show disputed territories on geo maps" (closed).
- 2025: **v3.1.0-rc.0 introduced maps built from UN geodata** ("UN Geodata
  stylized"). npm-distributed plotly.js now bundles them.
- Issue #7784: an **automated watcher for UN geodata updates** (closed Apr 2026) —
  plotly treats the UN source as living upstream.
- **Issue #7505 (open since 2025-08-01): "Switch CDN topojson maps to UN sourced
  data."** Still open.

Empirical state today (✓ both tested 2026-08-05):
- npm dist `world_110m.json` → Simferopol/Sevastopol in **UKR**.
- `https://cdn.plot.ly/world_110m.json` (the CDN default) → **RUS**.
- `https://cdn.plot.ly/un/world_110m.json` → **UKR**.

**Takeaway: even the vendor that did everything right is half-migrated.** Every
page loading plotly's CDN default still renders the annexation. This is the
strongest evidence that fixes must reach *defaults*, not just options.

## Case study 2: Highcharts — deliberate neutrality by carve-out

- `custom/world.geo.json` ✓: no polygon contains Simferopol or Sevastopol —
  Crimea is blank territory.
- The map collection ships paired variants: `countries/ru/ru-all.geo.json` vs
  `countries/ru/custom/ru-all-disputed.geo.json` — the choice is pushed to the
  developer, while the *default world map* stays neutral.
- Support forum thread "World map with Crimea (Russia)?" confirms this is policy,
  not accident; staff recommend UN maps and neutrality for disputed areas.

**Takeaway: a commercial vendor decided a default that endorses neither claim and
monetized the controversy as a configuration option.** Contrast with NE, which
puts one claim (Russia's) in the default and hides the alternatives in opt-in
files.

## Case study 3: the accidental correctness of frozen data

echarts@4.9 world.json ✓, datamaps ✓, jsvectormap ✓, vega-datasets world-110m ✓,
johan/world.geo.json ✓ — all show Crimea in Ukraine **because their world maps
predate 2014 and were never updated**. Roughly 5.1M weekly npm downloads
(echarts 4.5M + datamaps 262K + jsvectormap 67K + vega ecosystem) ship correct
geometry through inertia, not policy. This cuts both ways: the same inertia that
preserves the pre-annexation truth in these packages preserves the annexation in
NE-derived ones. Nobody in this family made a decision; the decision was made by
whoever they copied from, years ago.

## Case study 4: Anthropic globe (the AI-vendor instance)

Documented on our site (`/anthropic-fix`, July 2026): anthropic.com's 81K
Interviews globe fetches `ne_10m_admin_0_countries_iso` (Natural Earth 10m)
from its CDN and renders it with **D3 `geoNaturalEarth1`** — Crimea inside
Russia's polygon. The same NE row contains `iso_3166_2='UA-43'` and
`woe_label='Crimea, UA, Ukraine'`; the fix is reading a different column of the
data they already ship. This is the concrete proof-of-chain: NE → D3 → a frontier
AI company's public site.

## Vendor-tier context (not JS libraries; for the policy brief)

- **Google Maps**: global "agnostic" view relies on UN/treaty standards for solid
  borders, dashed for disputed; Crimea shown with dashed boundary outside .ru.
- **Bing Maps**: published policy defers to ICJ, then UN/ISO consensus, then
  renders as disputed.
- **Mapbox**: ships an explicit `worldview` style parameter (US/CN/IN/JP…);
  boundary disputes resolved per selected worldview — the US worldview does not
  award Crimea to Russia.
- **OSM ecosystem**: dual-claim tagging; rendering varies by style. (Tile-based —
  out of JS-census scope.)

The pattern policymakers should note: **every major commercial platform has a
worldview mechanism. The open-data root (NE) that feeds the open-source and AI
ecosystems is the only layer whose default awards occupied territory to the
occupier with no mechanism engaged by default.**

## Untested / flagged

- FusionCharts: proprietary webpack bundle; not extracted — untested, not guessed.
- Google GeoChart: renders via Google's border service; not polygon-testable
  client-side in this pass.
