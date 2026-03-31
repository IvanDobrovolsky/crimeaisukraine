# Timeline: Platform Changes After 2022 Full-Scale Invasion

**Context:** Russia's full-scale invasion of Ukraine on February 24, 2022 triggered a wave of platform changes. This timeline documents which services changed their Crimea representation — and which did not.

---

## Changed After 2022

| Date | Platform | Change | Trigger |
|------|----------|--------|---------|
| 2022-03-04 | **Apple Maps** | Shows Crimea as Ukraine (outside Russia) | Full-scale invasion |
| 2022-03 | **Booking.com** | Suspended all Russia/Crimea operations | EU/US sanctions |
| 2022-03 | **Airbnb** | Blocked all Crimea listings | Sanctions compliance |
| 2022-03 | **Netflix** | Exited Russia (Crimea included) | Sanctions |
| 2022-03 | **EU media regulators** | Banned RT and Sputnik across EU | EU Council Decision |
| 2022-03 | **Expedia/Hotels.com** | Ceased Russia travel sales | Sanctions |
| 2022-04 | **Spotify** | Exited Russia (Crimea included) | Sanctions |
| 2022-H2 | **TikTok** | Moved Ukraine from shared Russia+Ukraine region | Ukrainian MoD intervention |
| 2022-12-10 | **GeoPandas** | PR #2670 merged: Crimea assigned to Ukraine in naturalearth_lowres | GitHub issue #2382 |
| 2024 | **GeoPandas** | Deprecated entire `datasets` module in v1.0 | Upstream data quality concerns |

---

## NOT Changed (Still Unchanged as of 2026)

| Platform | Current State | Why Unchanged |
|----------|--------------|---------------|
| **Google Maps** | "Disputed" dashed border internationally | Policy: "follow local laws" in localized versions |
| **Natural Earth** | `SOVEREIGNT=Russia` | Policy: "de facto" boundaries. **33 open GitHub issues** requesting change (as of March 2026) |
| **IANA tzdata** | `RU,UA` in zone1970.tab | Policy: "not intended to take or endorse any position" |
| **Plotly** | Issue #2903 closed day after filing (2020-11-16) | Maintainer pointed to plotly.js #4345, which was also closed |
| **rnaturalearth (R)** | Issue #116 closed without fix (2025-02-03) | Maintainer: "We do not modify the underlying data" |
| **spData (R)** | Issue #50 closed without fix (2020-08-21) | "Requires upstream fix" |
| **moment-timezone** | Issue #954 closed without fix (2022-08-25) | "We directly consume IANA data" |
| **D3 world-atlas** | Inherits Natural Earth | No known issue filed |
| **Cartopy** | Downloads NE at runtime | No issue filed; no POV option |
| **Instagram** | Dual location tags coexist | No known policy change |

---

## GitHub Issue Activity on Natural Earth (33 issues)

The most recent issues show increasing frustration with Natural Earth's policy:

| Issue # | Date | Title |
|---------|------|-------|
| #1001 | 2026-02-21 | "Issue with the representation of Crimea on the maps" |
| #987 | 2025-10-09 | "Correct Crimea's administrative regions" |
| #986 | 2025-10-09 | "Correct Crimea's sovereignty to Ukraine in admin_0 shapefile" |
| #968 | 2025-06-25 | "Why the hell is Crimea russian?" |
| #967 | 2025-06-19 | "CRIMEA shouldnt be part of Russia - please change it" |
| #949 | 2025-04-02 | "The Crimea should be a part of Ukraine." |
| #844 | 2023-03-12 | "Crimea is part of Ukraine, not Russia!" |
| #839 | 2023-02-28 | "Crimea" |
| #838 | 2023-02-27 | "Crimea is reported as the Russian territory" |
| #791 | 2022-07-25 | "Consistency of ISO worldview (e.g. Crimea)" |

**Pattern:** Issue filing accelerated post-2022 but Natural Earth has not changed its policy. All issues remain open.

---

## Key Observation

The 2022 invasion created a **bifurcation**:
- **Consumer-facing platforms** (Apple, Booking, Netflix, Spotify, TikTok) changed rapidly — driven by sanctions compliance and public pressure
- **Developer-facing infrastructure** (Natural Earth, IANA, Plotly, D3, rnaturalearth) did NOT change — maintainers defer to "upstream data" or "de facto" policies

This means the user-visible internet shifted toward correct representation, but the **underlying infrastructure** that developers use to build new applications still encodes Crimea as Russian. Every new project built with Natural Earth data perpetuates the incorrect classification.
