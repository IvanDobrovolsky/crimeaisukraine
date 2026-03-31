# Journal Paper Structure

**Working title:** "Digital Sovereignty by Default: How Upstream Geographic Data Encodes Territorial Claims Across the Internet"

**Alternative titles:**
- "One Dataset, Thirty Million Downloads: The Silent Propagation of Crimea's Contested Sovereignty Through Open Source Infrastructure"
- "Crimea Is Ukraine (Except in Your Code): A Cross-Platform Audit of Digital Sovereignty Representation"

**Target journals (in order of fit):**
1. Internet Policy Review (open access, strong on digital governance)
2. Information, Communication & Society (Taylor & Francis, interdisciplinary)
3. Journal of Communication (ICA flagship, high impact)
4. New Media & Society (SAGE, digital media focus)
5. Big Data & Society (SAGE, open access, data infrastructure focus)

---

## Abstract (~250 words)

How do digital platforms, open source libraries, and internet infrastructure represent the sovereignty of occupied territories? We present the first systematic cross-platform audit examining how 97 digital services across 12 categories represent Crimea, internationally recognized as Ukrainian territory but occupied by Russia since 2014. Our analysis reveals a critical propagation mechanism: Natural Earth, the foundational geographic dataset used by the majority of open source mapping libraries, explicitly assigns Crimea's sovereignty to Russia (`SOVEREIGNT=Russia`). This single upstream classification silently cascades to data visualization libraries with over 30 million weekly npm downloads (D3, Plotly, ECharts, Leaflet) and 17 million monthly PyPI downloads (GeoPandas, Cartopy), affecting every choropleth map and geographic visualization built with these tools. We document that only one major library (Highcharts) deliberately overrides this default. Beyond open source, we trace how sovereignty claims propagate through internet infrastructure layers: IP geolocation databases, timezone assignments, phone number routing, postal code systems, and CDN classifications each encode different — and sometimes contradictory — sovereignty determinations. Weather services emerge as the most consistent category (8/8 correct), while social media platforms like Instagram maintain dual location tags that normalize competing sovereignty claims. We complement the technical audit with a multi-language media analysis across 7 language clusters, identifying specific political figures whose explicit sovereignty endorsements correlate with measurable shifts in their national media ecosystems. Our findings demonstrate that digital sovereignty representation is not a neutral technical choice but an editorial decision with geopolitical consequences, made overwhelmingly by default rather than by design.

---

## 1. Introduction (~1,500 words)

### 1.1 The Problem
- Digital platforms make sovereignty determinations constantly — every map, every location tag, every country dropdown
- These decisions are usually invisible, made upstream by data providers and inherited downstream without scrutiny
- Crimea is the paradigmatic test case: UNGA Resolution 68/262 (100-11 vote) affirms Ukrainian sovereignty, yet digital infrastructure routinely contradicts this

### 1.2 Research Questions
- **RQ1:** How do digital platforms across categories (maps, data visualization, travel, social media, reference, infrastructure) represent Crimea's sovereignty?
- **RQ2:** What upstream data sources determine these representations, and how do classification decisions propagate through dependency chains?
- **RQ3:** How do internet infrastructure layers (IP geolocation, timezone, phone routing, DNS) encode sovereignty, and what explains their inconsistencies?
- **RQ4:** To what extent do political actors' explicit sovereignty endorsements correlate with platform behavior in their national contexts?

### 1.3 Why Crimea, Why Now
- 10+ years of occupation provide a stable test case (unlike rapidly changing conflict zones)
- The 2022 full-scale invasion created a natural experiment — which platforms changed their representation?
- Growing scholarly attention to "platform geopolitics" (Bratton 2015, Zook 2017, Boria 2020)
- Practical policy relevance: Ukraine's MFA, Crimea Platform (60+ countries)

### 1.4 Contribution
- First systematic cross-platform digital sovereignty audit (97 platforms, 12 categories)
- Novel identification of the Natural Earth propagation chain as a single point of failure
- Taxonomy: legal-basis services vs. operational-reality services
- Multi-language media analysis connecting political advocacy to digital infrastructure

---

## 2. Literature Review (~2,000 words)

### 2.1 Critical Cartography and Digital Maps
- Harley (1989): Maps as instruments of power
- Crampton (2001): Cartography as social practice
- Zook & Graham (2007): Mapping DigiPlace
- Boria & Rossetto (2017): Digital maps as political artifacts
- Katz (2023): Google Maps' "quasi-sovereign power" (UC Law SF)

### 2.2 Platform Geopolitics
- Bratton (2015): The Stack — on platform sovereignty
- Gillespie (2018): Custodians of the internet
- Van Dijck et al. (2018): Platform society
- Deibert (2015): Authoritarianism and internet control

### 2.3 Crimea in Digital Spaces
- Ermoshina (2023): "Voices from the Island" — informational annexation of Crimea
- Fontugne et al. (2020): Internet routing in Crimea
- Douzet et al. (2020): BGP fragmentation during the Ukrainian crisis
- Golubei/Ukrainer: "Stop Mapaganda" — physical map audit
- CEPA reports on cartographic warfare

### 2.4 Open Source as Infrastructure
- Eghbal (2016, 2020): Roads and Bridges / Working in Public
- Kelty (2008): Two Bits — culture of free software
- Star (1999): The ethnography of infrastructure
- The concept of "defaults" as political choices (Winner 1980)

### 2.5 Gap
No existing study:
1. Audits digital sovereignty representation across platform categories
2. Traces upstream data propagation through open source dependency chains
3. Connects infrastructure defaults to political advocacy

---

## 3. Methodology (~2,000 words)

### 3.1 Platform Selection and Categorization
- 97 platforms across 12 categories (Table 1)
- Selection criteria: reach, category coverage, auditability
- Categories: maps, data visualization, open source datasets, travel, weather, social media, gaming, search engines, reference, IP geolocation, tech infrastructure, sports

### 3.2 Classification Framework
- **Correct:** Shows Crimea as part of Ukraine
- **Ambiguous:** Disputed/no label/configurable/geo-dependent
- **Incorrect:** Shows Crimea as part of Russia
- **Blocked:** Service unavailable in Crimea (sanctions compliance)

### 3.3 Automated Auditing
- Source code inspection: GeoJSON/TopoJSON property analysis, geometry containment testing
- API queries: IP geolocation services, geocoding APIs, Wikipedia API
- Dependency analysis: npm registry, PyPI stats, libraries.io
- GDELT DOC API: sovereignty framing in media articles by language

### 3.4 Manual Verification
- Browser-based platform checks
- VPN-based geo-dependent testing (noted where not completed)
- Screenshot documentation

### 3.5 Media and Political Analysis
- GDELT data from kyivnotkiev project (1.54M articles, 2015-2026)
- GDELT DOC API v2 for explicit sovereignty framing
- Public record research for political figure statements (dated, sourced)
- 7 language clusters: Spanish, French, German, Italian, Chinese, Indian, Turkish

### 3.6 Reproducibility
- All scripts published on GitHub
- JSON database of findings with standardized schema
- CSV exports for statistical analysis
- GDELT queries documented and rerunnable

### 3.7 Limitations
- Rate-limited API access (GDELT, some geocoders)
- VPN-based testing incomplete for some geo-dependent platforms
- GDELT sovereignty framing queries capture articles *about* sovereignty claims, not just endorsements — requires manual classification
- Temporal snapshot (March 2026) — platforms change

---

## 4. Findings (~4,000 words)

### 4.1 The Natural Earth Propagation Chain (RQ2)

**Finding 1: A single upstream dataset determines sovereignty representation for the majority of web mapping.**

- Natural Earth: `SOVEREIGNT=Russia`, `SOV_A3=RUS` for Crimea
- Russia's polygon contains Crimea at all resolutions (50m, 110m); Ukraine's does not
- Downstream impact: 30.4M weekly npm downloads, 17K dependent packages
- D3 world-atlas, Plotly, Cartopy, rnaturalearth all inherit without override
- **Highcharts is the sole major exception** — deliberately assigns Crimea to Ukraine

Table: Propagation chain with download counts and dependency depth

**Finding 2: GitHub issues filed and closed without fix.**

- 6 verified issues across major libraries (Plotly #2903, GeoPandas #2382, rnaturalearth #116, spData #50, moment-timezone #954)
- Common maintainer response: "We don't modify upstream data"
- GeoPandas exception: fixed in v0.12.2, then deprecated entire datasets module

### 4.2 Cross-Platform Audit Results (RQ1)

Table: 97 platforms by category, status, method

**Finding 3: Weather services are the gold standard.**
- 8/8 weather services correctly classify Simferopol as Ukraine
- Consistent reliance on GeoNames (which is correct)

**Finding 4: Map services use geo-fencing to avoid the question.**
- Google Maps: "disputed" default (false equivalence)
- Apple Maps: corrected post-2022 (best major map service)
- HERE Maps and Mapbox: configurable worldview systems — but no Ukraine worldview exists while Russia worldview does

**Finding 5: Social media enables competing claims.**
- Instagram: dual location tags ("Crimea, Ukraine" AND "Russia, Crimea, Yalta") coexist
- TikTok: fixed shared Russia-Ukraine region category in 2022 after Ukrainian government intervention

**Finding 6: Travel platforms defer to sanctions, not sovereignty.**
- Booking.com, Airbnb, Expedia: blocked (sanctions), not labeled
- TripAdvisor: "Europe > Crimea" (avoids country entirely)

### 4.3 The Infrastructure Stack: Legal vs. Operational (RQ3)

**Finding 7: Services based on legal registrations classify Crimea as Ukraine. Services based on operational reality classify it as Russia.**

Table: The infrastructure stack

| Layer | Legal basis → Ukraine | Operational reality → Russia |
|-------|----------------------|------------------------------|
| IP geolocation | MaxMind, GeoNames (UA) | ISP-level: post-2014 RU entities → RU |
| Timezones | zone.tab (UA only) | zone1970.tab (RU,UA); UTC+3 Moscow time |
| Phone numbers | — | libphonenumber: +7-365/978 = RU |
| Postal codes | — | Russian Post: 295000-299xxx = RU |
| Addresses | Google libaddressinput (UA) | — |
| DNS/TLD | .crimea.ua active | .crimea.ru doesn't exist |
| CDN | Cloudflare: country=UA, subdivision=UA-43 | — |
| Geocoding | OSM Nominatim (UA) | — |

**Finding 8: Cloudflare classifies Crimea as UA-43, affecting ~20% of all websites.**

### 4.4 Media and Political Context (RQ4)

**Finding 9: Transliteration (Crimea/Krym) is a linguistic artifact, not a sovereignty signal.**
- Unlike Kyiv/Kiev, the Crimea/Krym ratio does not predict political alignment
- Italian, Vietnamese, Brazilian "Krym" usage reflects transliteration paths, not editorial endorsement

**Finding 10: Explicit sovereignty framing is rare outside Russian state media.**
- GDELT analysis: only 2 of 50+ international outlets used "Russian Crimea" as territorial designation
- Pro-Russia framing dominated by Russian state media (news.mail.ru, ria.ru, vesti.ru, tass.ru)

**Finding 11: Political advocacy is the strongest signal, concentrated in specific individuals.**
- Named politicians with dated, verifiable sovereignty endorsements: Salvini, Berlusconi, Le Pen, Schröder, Orbán, Zemmour, Trump, AfD
- 2022 inflection: rhetorical softening without substantive retraction

**Finding 12: Correct alternatives exist and are in use.**
- mledoze/countries (6.2K GitHub stars) uses thematicmapping.org data, correctly assigns Crimea to Ukraine
- Highcharts, MaxMind, GeoNames, Google libaddressinput, Cloudflare, OurAirports all correct
- Demonstrates that correct classification is an editorial choice, not a technical impossibility

---

## 5. Discussion (~2,000 words)

### 5.1 Defaults as Political Acts
- Natural Earth's "de facto" policy is itself a political choice (echoes Winner 1980, "Do Artifacts Have Politics?")
- The cascading effect of defaults through dependency chains means one organization's editorial decision becomes millions of developers' unwitting political statement
- Comparison to Eghbal's infrastructure metaphor: open source geodata is a "road" that determines where the traffic flows

### 5.2 The Three Tiers of Fixability
- Tier 1 (straightforward): Change NE default, update library data
- Tier 2 (upstream required): Libraries that defer to NE, IANA timezone
- Tier 3 (technical reality): Phone routing, postal codes — reflect physical infrastructure under occupation

### 5.3 Platform Responsibility and the Geo-Fencing Problem
- Google/HERE/Mapbox "worldview" systems: treating sovereignty as a matter of perspective
- The absence of a Ukraine worldview in Mapbox/HERE while Russia's exists
- Weather services prove that a single correct answer is possible and maintainable

### 5.4 Implications for Other Occupied/Disputed Territories
- Western Sahara, Palestine, Kashmir, Taiwan — do the same patterns hold?
- Natural Earth's point-of-view system as a template (and its limitations)
- The generalizability of the "legal vs. operational" infrastructure split

### 5.5 Policy Implications
- For Ukraine's MFA and Crimea Platform: target Natural Earth as the highest-leverage intervention
- For open source governance: the need for sovereignty policy in geographic datasets
- For platform regulation: geo-fencing creates false equivalence; single-answer databases (weather services model) are preferable

---

## 6. Conclusion (~500 words)

- Restate core finding: digital sovereignty is determined by default, not by design
- The Natural Earth propagation chain as the central mechanism
- Correct implementations exist (Highcharts, Cloudflare, MaxMind) — proving this is a choice
- Call for: upstream data correction, open source governance, platform accountability
- Limitation: temporal snapshot; suggest quarterly re-audits using published scripts
- The broader implication: every `pip install plotly` or `npm install d3` quietly encodes a territorial claim

---

## Tables and Figures

1. **Table 1:** 97 platforms by category, status, method (from findings.csv)
2. **Table 2:** Natural Earth propagation chain — packages, weekly downloads, dependency counts
3. **Table 3:** The infrastructure stack — legal vs. operational classification
4. **Table 4:** Weather services (gold standard) — all 8 correct
5. **Table 5:** GitHub issues filed and closed — maintainer responses
6. **Table 6:** Political figures with explicit sovereignty endorsements (dated)
7. **Figure 1:** Propagation diagram — Natural Earth → libraries → downstream applications
8. **Figure 2:** Platform classification distribution (pie/bar chart from 97 findings)
9. **Figure 3:** GDELT sovereignty framing by country of origin
10. **Figure 4:** Timeline — which platforms changed representation after 2022

---

## Supplementary Materials

- GitHub repository with all scripts, data, and documentation
- findings.csv: Full structured dataset (97 findings)
- propagation.csv: Package dependency analysis
- media_framing.json: GDELT article-level data
- Reproducible audit scripts (Python, no cloud dependencies)

---

## Estimated Length

- Main text: ~12,000 words (within most journal limits of 8,000-15,000)
- Tables/figures: 10
- References: ~60-80
- Supplementary: GitHub repo link

---

## Author Contribution Statement

Ivan Dobrovolsky: Conceptualization, methodology design, data collection, analysis, writing. Part of the KyivNotKiev research ecosystem tracking Ukrainian toponym adoption across global media and digital infrastructure.
