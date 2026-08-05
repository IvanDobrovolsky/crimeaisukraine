# Natural Earth's "De Facto" Policy: A Consistency Audit

**Date of all checks: 2026-08-05.** Source: NE master branch (data frozen since
June 2022, v5.2.0-pre), 10m `admin_0_countries`, `admin_0_disputed_areas`, and POV
variant files, fetched live from GitHub. Method: point-in-polygon of representative
cities. Raw results: `data/ne_consistency_matrix.json`.

## Claim under test

NE defends Crimea→Russia as neutral application of a "de facto control" policy.
If that were a rule, it would apply uniformly. It does not.

## Finding 1: Among Russia-linked occupied territories, only Crimea is reassigned

All of these were under de facto Russian or Russian-proxy control at NE's data
freeze (June 2022):

| Territory | De facto since | NE SOVEREIGNT | Separate unit? |
|---|---|---|---|
| **Crimea** | 2014 | ❌ **Russia** | No — absorbed |
| Donetsk (DNR) | **2014 (same year)** | Ukraine | No |
| Luhansk (LNR) | **2014 (same year)** | Ukraine | No |
| Mariupol, Melitopol, Kherson, N. Kakhovka | Feb–May 2022 (before freeze) | Ukraine | No |
| Abkhazia | 1993/2008 (Russian garrison) | Georgia | No |
| South Ossetia | 2008 (Russian garrison) | Georgia | No |
| Transnistria | 1992 (Russian troops) | Moldova | No |

Same war, same aggressor, same year (DNR/LNR vs Crimea) — opposite treatment.
The `disputed_areas` layer makes it explicit: DNR/LNR entries read
"Self admin.; Claimed by Ukraine" with SOVEREIGNT=Ukraine; the Crimea entry reads
"Admin. by Russia; Claimed by Ukraine" with SOVEREIGNT=**Russia**. **Crimea is the
only Russia-linked entry in the entire disputed layer whose sovereignty column is
awarded to Russia.**

## Finding 2: The de facto rule is violated in both directions

- Nagorno-Karabakh: Armenian-controlled at NE's June 2022 data freeze → NE assigns
  **Azerbaijan** (de jure preferred over de facto). *Status note: since the Sept
  2023 offensive and Artsakh's dissolution (1 Jan 2024), the territory is fully
  Azerbaijani — NE's assignment now matches reality, but it predates those events;
  at the time the data was authored it contradicted the stated de facto rule.*
- Kherson/Mariupol/Melitopol: Russian-controlled at the freeze → NE assigns
  **Ukraine** (de jure preferred over de facto).
- Crimea: Russian-controlled → NE assigns **Russia** (de facto preferred).

A policy applied in whichever direction — except it always lands on Ukraine losing
Crimea — is not a policy; it is an editorial choice per territory.

## Finding 3: NE has a template for de facto control that does not reward the occupier — and did not use it for Crimea

- **Northern Cyprus** (Turkish invasion 1974): own unit, SOVEREIGNT=Northern
  Cyprus — **not** absorbed into Turkey.
- **Somaliland** (1991): own unit. **Taiwan** (1949): own unit. **Kosovo**: own
  unit, TYPE=Disputed. **Western Sahara** (SADR zone): own unit, Indeterminate.

The N. Cyprus precedent is exact: armed invasion → self-declared entity → NE gives
it a separate unit while the occupying power's polygon stays unchanged. For Crimea,
NE instead merged the territory into the invader's polygon.

## Finding 4: Even the closest parallels carry dispute markers Russia does not

Golan Heights and East Jerusalem (annexed 1981/1980, unrecognized) are assigned to
Israel — but **Israel's entire admin-0 feature is TYPE="Disputed"** (verified: Tel
Aviv point returns TYPE=Disputed), and Palestine exists as separate ADMIN units.
Russia's feature, with Crimea inside, is TYPE="Sovereign country" — no feature-level
dispute marker at all. The Kuril Islands (1945, Japanese claim) are also inside
Russia's clean polygon.

**Honest-framing caveat for media use:** it is *not* accurate to say the occupier
assignment "happens only for Crimea" globally — Golan, E. Jerusalem, Kurils, and
Moroccan W. Sahara are also assigned to their occupiers. The accurate claims are:
(a) among Russia's own occupied territories, only Crimea; (b) Crimea is the only
21st-century annexation of a UN member's territory absorbed into the annexing
state's polygon; (c) unlike the Israel cases, the absorbing polygon carries no
dispute type; (d) see Finding 5 — NE's own alternative views contradict the default.

## Finding 5: NE's own POV variants refute the default (strongest new evidence)

NE ships per-worldview country files. Checked for Simferopol:

| File | Crimea assigned to |
|---|---|
| `admin_0_countries` (**default — what every library ships**) | ❌ Russia, "Sovereign country" |
| `admin_0_countries_usa` (US worldview) | ✅ **Ukraine** |
| `admin_0_countries_ukr` (Ukraine worldview) | ✅ Ukraine |
| `admin_0_countries_iso` (ISO worldview) | ⚠️ Unassigned hole — in **neither** polygon |

NE's own encoding of the US government worldview and the ISO worldview does **not**
give Crimea to Russia. The pro-Russia assignment is exclusively the default file's
choice — and downstream distributions (world-atlas → D3, geopandas, cartopy)
package only the default. The corrective variants and the `disputed_areas` overlay
are opt-in files that effectively never propagate (see
`docs/replication_divergence_2026-07.md` §1 for the downstream verification).

## Finding 6: The revealed rule, and its chilling implication

The pattern that actually fits the data: **sovereignty flips when the occupier
formally declares annexation** (Crimea 2014, Golan 1981, E. Jerusalem 1980;
non-annexed occupations stay de jure). NE froze its data in June 2022. Russia
declared annexation of Donetsk, Luhansk, Kherson, and Zaporizhzhia oblasts on
30 Sept 2022. If NE resumes updates under its revealed rule, those four oblasts
flip to SOVEREIGNT=Russia — and propagate to every dependent library and every
AI training corpus. This is worth stating in any follow-up article: the dataset's
next update is a loaded gun.

## Context

- NE repo dormant: no commits since June 2022; policy page last touched
  27 Feb 2022 (3 days after the full-scale invasion) without reclassifying Crimea.
- Community pressure post-KI-article: issues #839/#993/#1001 active July 2026;
  issue #1021 (5 Jul 2026) proposes a systematic De Jure/UN Consensus worldview.
