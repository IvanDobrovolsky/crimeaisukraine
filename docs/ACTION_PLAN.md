# Action Plan: Quick Wins & MFA Engagement Targets

## Tier 1: Highest Impact, Easiest to Fix (file a GitHub issue)

These are open source projects where filing a well-documented issue can trigger a change that cascades to millions of downstream users.

| Target | Action | Impact | Effort |
|--------|--------|--------|--------|
| **Natural Earth** | File comprehensive issue citing UNGA 68/262, all 33 existing issues, and this audit | Fixes the root cause for D3, Plotly, Cartopy, etc. | Medium |
| **Plotly** | Reopen #2903 with new evidence from this audit | 965K weekly npm + 55M monthly PyPI | Low |
| **D3 world-atlas** | File issue — no one has yet | 80K weekly npm, every D3 choropleth tutorial | Low |
| **Cartopy** | File issue — no one has yet | 2-3M monthly PyPI, scientific publications | Low |
| **ECharts** | File issue with geometry analysis evidence | 2.3M weekly npm | Low |
| **iso3166-2-db** | Request default changed to UN perspective | 10K weekly npm | Low |
| **Wikidata** | Request removing Russia "preferred" rank for Q7835 | Feeds into many knowledge systems | Low |
| **mledoze/countries** | Send praise — they're correct, cite as example | Positive reinforcement | Low |

## Tier 2: Platform Engagement (email/form, no code needed)

| Target | Action | Who to Contact |
|--------|--------|---------------|
| **Google Maps** | Request "disputed" → "occupied" label change | Google Policy team |
| **Mapbox** | Request Ukraine worldview (UA) — RU exists, UA doesn't | Mapbox support |
| **HERE Maps** | Request Ukraine political view — RU exists, UA doesn't | HERE developer relations |
| **Instagram** | Report dual location tags — request removing "Russia, Crimea" | Meta content policy |
| **TripAdvisor** | Request country label (currently "Europe > Crimea", no country) | TripAdvisor editorial |
| **IANA** | Request removing RU from Europe/Simferopol in zone1970.tab | tz mailing list |

## Tier 3: Praise Correct Platforms (positive pressure)

Public acknowledgment creates social pressure for others to follow.

| Platform | What They Got Right | How to Praise |
|----------|-------------------|---------------|
| **Highcharts** | Deliberately overrides NE to show Ukraine | Blog post, tweet, case study |
| **Cloudflare** | UA-43 classification for Crimea | Cite in paper, mention in media |
| **MaxMind/GeoNames** | Correct IP geolocation | Cite as industry standard |
| **Apple Maps** | Changed post-2022, shows Ukraine outside Russia | Cite as best-in-class map |
| **Weather services** (all 10) | 100% correct classification | "Gold standard" framing |
| **OSM Nominatim** | All Crimean cities resolve to Ukraine | Cite structured data |
| **Encyclopaedia Britannica** | "illegally annexed" — strongest reference source | Cite as authoritative |

## Tier 4: Paper/Media (longer-term)

| Action | Target | Timeline |
|--------|--------|----------|
| Submit paper to Internet Policy Review | Academic legitimacy | 1-2 months |
| Pitch to Kyiv Independent | Ukrainian media coverage | After paper submission |
| Pitch to WIRED / The Verge | International tech media | After paper |
| Brief Atlantic Council / DFRLab | Think tank amplification | After paper |
| Crimea Platform presentation | 60+ countries diplomatic format | Next summit |
| Publish dataset on Kaggle | Open data community | Anytime |

---

## What to Tell the MFA

**The message:** "A single geographic dataset (Natural Earth) encodes Crimea as Russian territory. This cascades to 30 million weekly software downloads. Filing one well-documented GitHub issue could fix the root cause. Here are the 8 issues to file, in order of impact."

**The ask:** Support for filing issues, sending praise letters to correct platforms, and diplomatic engagement with Mapbox/HERE (request Ukraine worldview).

**The metric:** Track how many platforms change after engagement. Re-run the audit quarterly using the published scripts.
