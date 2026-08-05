# Digital Non-Recognition: Why US Policy on Crimea Stops Where the Data Begins

**Policy brief prepared for CEPA presentation — draft 2026-08-05.**
Author: Ivan Dobrovolskyi (crimeaisukraine.org). All technical claims verified
2026-07-30 – 2026-08-05; methods and raw data in the linked artifacts.

## The one-paragraph version

The United States does not recognize Russia's annexation of Crimea (Crimea
Declaration, 2018 — the direct heir of the 1940 Welles Declaration). Every
relevant US standard encodes that position: FIPS 10-4 codes Crimea `UP11`
(UP = Ukraine), the NGA GEOnet Names Server places Crimean cities in Ukraine,
the Library of Congress classifies "Crimea (Ukraine)--History--Russian
occupation, 2014-". Yet the default world map of the open-source web — Natural
Earth, feeding the D3/world-atlas ecosystem with ~25 million weekly npm
downloads and the training corpora of every major AI model — assigns Crimea's
sovereignty to Russia. US policy exists on paper and in standards; the data
infrastructure that actually draws the world's maps defaults against it. This is
a non-recognition compliance gap that costs nothing geopolitically to close and
is currently being closed by no one.

## Five findings policymakers should know

### 1. Natural Earth's default contradicts Natural Earth's own encoding of the US worldview
Natural Earth ships per-country "point of view" files. Its **USA-POV file places
Crimea in Ukraine**. Its ISO-POV file assigns Crimea to neither state. Only the
*default* file — the one every downstream library packages — awards Crimea to
Russia (verified by point-in-polygon test, 2026-08-05). American products
consuming the default are therefore displaying a worldview that the dataset
itself identifies as *not the US worldview*.
→ Artifact: crimeaisukraine.org/natural-earth-audit (interactive; POV toggle)

### 2. The "de facto policy" defense does not survive an audit
Among eight Russia-linked occupied territories in Natural Earth's data (Crimea,
Donetsk, Luhansk, 2022-occupied south Ukraine, Abkhazia, South Ossetia,
Transnistria — plus Armenian-held Karabakh at the data freeze), the de facto rule
is applied **exactly once: Crimea**, the only case that benefits Russia's
sovereignty claim. Donetsk and Luhansk were seized the same year and remain
Ukrainian in the data. Northern Cyprus — the exact precedent (invasion →
self-declared entity) — got its own unit rather than absorption into Turkey.
The closest parallel (Golan) at least carries a country-level "Disputed" marker;
Russia's polygon is a clean "Sovereign country."
→ Artifact: docs/natural_earth_consistency.md + data/ne_consistency_matrix.json

### 3. The loaded gun: the next update flips four more oblasts
The pattern that fits Natural Earth's data is "sovereignty flips upon formal
annexation declaration" (Crimea 2014, Golan 1981). The repo froze in June 2022.
Russia declared annexation of Donetsk, Luhansk, Kherson, and Zaporizhzhia on
30 September 2022. If maintenance resumes under the revealed rule, four more
Ukrainian oblasts flip to `SOVEREIGNT="Russia"` and propagate to every library
and every AI training corpus. Preventing this is cheaper than reversing it.

### 4. The industry has already demonstrated three viable fixes — at every layer except the root
Empirical census of every JS web mapping library (npm weekly downloads,
2026-08-05): **plotly** switched its bundled maps to **UN geodata** (2025);
**Highcharts** ships a neutral carve-out (Crimea assigned to no one);
**amCharts/anychart** maintain corrected custom data; Google, Bing, and Mapbox
all operate worldview mechanisms. The open-data root refuses all of these
strategies. Critically, plotly's fix illustrates the default problem: its npm
package is corrected, but `cdn.plot.ly`'s default file *still serves the
pro-Russia map* (verified 2026-08-05; migration issue open since Aug 2025).
**Fixes that do not reach defaults do not fix anything.**
→ Artifact: crimeaisukraine.org/geodata-propagation (live census chart)

### 5. This is an AI-supply-chain issue, demonstrated on a US AI company
Anthropic's public website globe renders Natural Earth data via D3 — Crimea
inside Russia (documented with reverse-engineered data source and a drop-in fix
at crimeaisukraine.org/anthropic-fix). The same chain contaminates model
training: 891,522 Russia-framing documents in Google's C4 corpus; 16 frontier
LLMs audited show a declarative-generative gap — models *say* Crimea is Ukraine
but *build* maps and datasets that say otherwise (Kyiv Independent, 2026-07-01).
Ask a US model to "make a dashboard" and the code it writes pulls the
contaminated default.

## Recommendations

1. **OMB/GSA digital-services guidance**: federal websites and dashboards must
   use geodata consistent with US recognition policy (i.e., consistent with
   FIPS/GNS). A one-line procurement requirement; an audit of existing federal
   dashboards using D3/world-atlas defaults would likely find violations today.
2. **Fund the de jure worldview at the root**: the Natural Earth community has an
   open proposal for a systematic De Jure/UN-consensus worldview
   (natural-earth-vector issue #1021, opened 4 days after the Kyiv Independent
   piece). A modest grant — or an NGA/USGS-published open admin-0 layer aligned
   with the US worldview — solves the upstream problem for the entire ecosystem.
3. **AI training-data provenance**: NIST AI RMF and procurement language should
   require disclosure of geographic data sources in AI systems and flag
   sovereignty-sensitive defaults, exactly as done for security provenance
   (SBOM → "GBOM" for geodata).
4. **Engage vendors on defaults, not options**: the plotly CDN case shows the
   gap between shipping a fix and deploying it. Public praise for completed
   default-level migrations is cheap and effective diplomacy.
5. **Message discipline for public diplomacy**: the accurate claim is not "the
   internet's maps are Russian propaganda" but "the default file contradicts the
   US worldview encoded in the same dataset, and is applied inconsistently in
   Russia's favor." The precision is what makes it actionable.

## Presentation artifacts (all live)

| Artifact | What it shows |
|---|---|
| crimeaisukraine.org/natural-earth-audit | Interactive map + table: the de facto rule applied once, POV toggle showing NE contradicting itself, "Russia test" inset |
| crimeaisukraine.org/geodata-propagation | Live census: every JS map library, npm reach, who fixed what and how |
| crimeaisukraine.org/anthropic-fix | Case study: NE→D3 chain on a frontier AI company's site, with the fix |
| docs/vendor_override_tracker.md | plotly/Highcharts/amCharts provenance archaeology, primary sources |
| data/ne_consistency_matrix.json, data/geodata_js_census.json | Raw verifiable results |
| Kyiv Independent (2026-07-01) | Media narrative + LLM audit numbers |
