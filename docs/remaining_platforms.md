# Remaining Platform Audit: Crimea Sovereignty Representation

**Research date:** 2026-03-30
**Methodology:** Web research, API documentation review, source code inspection, direct data verification

---

## 1. HERE Maps (here.com)

**Status:** Ambiguous (geo-dependent, configurable)

**How it works:** HERE Maps implements a "political view" system through its Raster Tile API, Map Image API, and Geocoding & Search API. Customers set a `politicalView` parameter using ISO 3166-1 alpha-3 country codes (e.g., `politicalView=RUS` or `politicalView=ARG`).

**Default behavior:** The default view is defined by the "HERE Geopolitical Board" and is described as a neutral international view. For disputed territories, the default shows dashed/disputed borders. If a country code is provided for which HERE has no dedicated political view, it falls back to this default.

**Crimea handling:** HERE's documentation does not explicitly list which political views are available or how Crimea is rendered in each. Based on the system's design (analogous to Google Maps' geo-localization), the Russian political view (`RUS`) likely shows Crimea as Russia, while the default international view likely shows a disputed border.

**Key limitation:** No Ukraine-specific political view was documented -- the system appears to lack a `UKR` view that would show Crimea as unambiguously Ukrainian.

**Evidence URL:** https://developer.here.com/documentation/geocoding-search-api/dev_guide/topics/political-views.html (redirects to https://www.here.com/docs)
**Alt URL:** https://www.here.com/docs/bundle/raster-tile-api-developer-guide/page/topics/geopolitical-views.html

**Notes:** HERE was acquired by a consortium of Audi, BMW, and Daimler in 2015. Their political view system mirrors Google's approach -- they accommodate multiple perspectives rather than asserting one correct view.

---

## 2. Yandex Maps (yandex.ru/maps)

**Status:** Incorrect (shows Crimea as Russia)

**Behavior:** Yandex Maps shows Crimea as an integral part of Russia with a solid international border at the Isthmus of Perekop, separating it from Ukraine. Simferopol is listed under "Republic of Crimea, Russia." This has been the case since 2014 and is consistent across all Yandex products.

**Rationale:** Yandex is a Russian company subject to Russian law. Russian law requires all maps distributed in Russia to show Crimea as Russian territory (Federal Law No. 209-FZ). Yandex does not offer alternative views for non-Russian audiences.

**Evidence URL:** https://yandex.ru/maps/?ll=34.10,44.95&z=8
**Source:** Direct observation; confirmed by multiple secondary sources including the Ukrainer "Stop Mapaganda" report.

---

## 3. Mapbox

**Status:** Ambiguous (configurable worldview system; default shows US perspective)

**Worldview system:** Mapbox supports 11 worldviews: `all`, `AR` (Argentina), `CL` (Chile), `CN` (China), `IN` (India), `JP` (Japan), `MA` (Morocco), `RS` (Serbia), `RU` (Russia), `TR` (Turkey), and `US` (United States).

**Default behavior:** Mapbox-designed styles (Mapbox Light, Mapbox Outdoors, etc.) use the **US worldview** by default. The Geocoding API also defaults to the US worldview.

**Russia worldview:** Added in Boundaries v3.4. When the `RU` worldview is selected, maps are intended "for a Russian audience" -- this likely shows Crimea as Russian territory.

**US/default worldview:** The documentation does not explicitly state how the US worldview renders Crimea. Given that the US government does not recognize Russia's annexation, the US worldview likely shows a disputed border or Crimea within Ukraine.

**Key issue:** There is **no Ukraine worldview** (`UA`). Developers building for Ukrainian audiences cannot select a view that explicitly shows Crimea as Ukrainian -- they must rely on the US default or `all` worldview.

**Disputed border styling:** Mapbox provides `disputed_` class prefixes in relevant layers that must be selected in conjunction with the worldview filter for proper rendering.

**Evidence URL:** https://docs.mapbox.com/help/glossary/worldview/
**Changelog:** https://docs.mapbox.com/data/boundaries/changelog/

**Notes:** The absence of a Ukrainian worldview while having a Russian one is a significant asymmetry. Mapbox added the Russia worldview before adding several others (Argentina, Morocco, Serbia, Turkey followed later).

---

## 4. TomTom

**Status:** Ambiguous (insufficient public documentation)

**What is known:**
- TomTom lists Ukraine as having complete coverage in its European map zone for the TomTom GO Expert app
- Russia is divided into 5 regional map zones (Central, Northwest, Siberia, Southeast, Southwest)
- **Crimea is not mentioned separately** in any map zone documentation
- TomTom's coverage documentation does not address disputed territories or geopolitical views
- TomTom's Supplier Code of Conduct requires sanctions compliance, but no public-facing border/territory policy was found

**Map zone ambiguity:** Since Ukraine has "complete coverage" and Crimea is not listed under any Russia zone, it is plausible that TomTom includes Crimea within Ukraine's coverage area, but this cannot be confirmed without direct testing.

**Evidence URL:** https://help.tomtom.com/hc/en-gb/articles/360013959319-European-map-coverage-in-the-TomTom-GO-Expert-app

**Notes:** TomTom is a Dutch company, subject to EU sanctions on Crimea. EU Council Regulation 692/2014 restricts EU entities from providing certain services related to Crimea. This may influence how TomTom treats the territory.

---

## 5. Encyclopaedia Britannica

**Status:** Correct (Ukraine)

**Classification:** Britannica describes Crimea as an **"autonomous republic, southern Ukraine"** in its article header. The article explicitly states: "In 2014 Russia covertly invaded and illegally annexed Crimea, a move that was denounced by the international community."

**Key framing:**
- Header identifies Crimea as part of Ukraine
- Uses the word "illegally" to describe the annexation
- Notes the international community's denunciation
- Article last updated March 26, 2026

**Evidence URL:** https://www.britannica.com/place/Crimea

**Notes:** Britannica is one of the clearest major reference sources. It unambiguously identifies Crimea as Ukrainian territory and characterizes Russia's actions as illegal.

---

## 6. CIA World Factbook

**Status:** Correct (Ukraine)

**Classification:** The CIA World Factbook lists Crimea under **Ukraine's administrative divisions** as: "1 autonomous republic (avtonomna respublika)" with capital at Simferopol. The entry explicitly states: "The US Government does not recognize Russia's illegal annexation of Ukraine's Autonomous Republic of Crimea."

**Key details:**
- Ukraine's entry lists "24 provinces (oblasti, singular - oblast), 1 autonomous republic*, and 2 municipalities (mista, singular - misto) with oblast status"
- The autonomous republic is Crimea (Avtonomna Respublika Krym [Simferopol])
- Economic data notes exclude "temporarily occupied territories of the Autonomous Republic of Crimea"
- Russia's entry mentions "annexed Crimea in 2014" but does not list Crimea in Russia's administrative divisions
- Russia's entry notes that the annexation is "not recognized by the international community"

**Evidence URL:** https://www.cia.gov/the-world-factbook/countries/ukraine/

**Notes:** The Factbook is unambiguous: Crimea is an administrative division of Ukraine, and Russia's annexation is illegal and unrecognized. The "temporarily occupied territories" framing is also used by the Ukrainian government.

---

## 7. UN Country Listings

**Status:** Correct (Ukraine)

**Classification:** The United Nations explicitly lists Crimea as Ukrainian territory across multiple instruments:

1. **UNGA Resolution 68/262 (March 27, 2014):** "Territorial integrity of Ukraine" -- adopted 100-11-58, affirming Crimea's status as Ukrainian territory, declaring the 2014 referendum invalid, and calling on states not to recognize any altered status.

2. **ISO 3166-2:UA:** Crimea is listed as UA-43 (Avtonomna Respublika Krym) under Ukraine's subdivisions. On 2014-11-03, ISO updated the name from "Respublika Krym" to "Avtonomna Respublika Krym." Sevastopol is UA-40.

3. **UN M49 Statistical Standard:** Ukraine (code 804) includes all internationally recognized territories. No separate code exists for Crimea.

4. **Subsequent resolutions:** UNGA has adopted additional resolutions on Crimea (2018 on militarization, 2020 on human rights), all reaffirming Ukraine's territorial integrity.

5. **Crimea Platform:** Established 2021, an international coordination mechanism supporting Crimea's de-occupation, endorsed by 60+ countries.

**Evidence URLs:**
- https://press.un.org/en/2014/ga11493.doc.htm
- https://digitallibrary.un.org/record/767565
- https://unstats.un.org/unsd/methodology/m49/
- https://crimea-platform.org/en/news/united-nations/

**Notes:** The UN position is unequivocal. Only 11 countries voted against Resolution 68/262 (Armenia, Belarus, Bolivia, Cuba, DPRK, Nicaragua, Russia, Sudan, Syria, Venezuela, Zimbabwe).

---

## 8. ESPN

**Status:** Ambiguous (editorial balance; structural classification leans Russia for sports)

**Editorial framing:** ESPN describes Crimea as "the Crimea region annexed by Russia" and notes "Ukraine considers its territory." This is balanced but uses "annexed" -- an accurate descriptor that avoids the euphemism "reunified" used by Russian sources.

**Sports classification:**
- Crimean football clubs: After 2014, Russia registered new clubs (SKChF Sevastopol, Zhemchuzhina Yalta, Tavria Simferopol) to play in Russian leagues. ESPN covered this under the Russian Premier League section (league code `rus.1`)
- UEFA response: Banned Crimean clubs from Russian league, created a "special zone" administered directly by UEFA
- Athlete nationality: ESPN reports some Crimean athletes compete for Russia, others for Ukraine. No uniform policy.

**Key issue:** ESPN's sports database classifies Crimean clubs structurally under Russia (since they play in Russian-administered leagues), even while editorial coverage acknowledges the territory as annexed Ukrainian land.

**Evidence URLs:**
- https://www.espn.com/soccer/story/_/id/37374107/crimea-clubs-set-play-russian-league
- https://www.espn.com/soccer/story/_/id/37430503/uefa-backed-league-begins-crimea-russia-annexation

---

## 9. weather.com (The Weather Channel)

**Status:** Likely correct (Ukraine) -- not directly verified

**Assessment:** weather.com is operated by The Weather Company (IBM). Its sister product Weather Underground (also IBM/TWC) definitively lists Simferopol under Ukraine with `/ua/` in the URL path. Weather.com blocked automated access during this research, preventing direct verification.

**Indirect evidence:**
- Weather Underground: `wunderground.com/forecast/ua/simferopol` -- Ukraine
- Both products share the same parent company and underlying geographic database
- All other weather services tested (AccuWeather, TimeAndDate, WeatherSpark, Meteoblue, etc.) classify Simferopol as Ukraine

**Evidence URL:** https://www.wunderground.com/forecast/ua/simferopol (sister product, same company)

**Notes:** Direct verification of weather.com needed. Given the Weather Company's database consistency, it is highly likely Simferopol appears under Ukraine.

---

## 10. BBC Weather

**Status:** Likely correct (Ukraine) -- not directly verified

**Assessment:** BBC Weather uses GeoNames ID 693805 for Simferopol. The URL pattern is `bbc.com/weather/693805`. GeoNames classifies Simferopol as Ukraine (country code UA), and BBC Weather typically inherits the GeoNames country classification.

**Indirect evidence:**
- GeoNames ID 693805 = Simferopol, Ukraine
- BBC editorial policy refers to Crimea as "annexed" by Russia, indicating recognition of Ukraine's sovereignty
- BBC Weather's URL does not contain a country path segment, relying instead on the GeoNames ID

**Evidence URL:** https://www.bbc.com/weather/693805

**Notes:** Direct verification was blocked by BBC's access controls. However, given GeoNames sourcing and BBC editorial policy, classification as Ukraine is highly probable.

---

## 11. Domain Registrars / TLDs

**Status:** Correct (Ukrainian TLD infrastructure maintained)

**Key findings:**

**.crimea.ua exists and is active:**
- Managed by Hostmaster Ltd (administrator of the .UA ccTLD)
- Created in 2015 as a geographic second-level domain under .UA
- Registration open to any individual or legal entity
- Multiple registrars offer .crimea.ua domains (NIC.UA, Regery, BB-Online, etc.)
- Prices range from ~$3.79 to ~$29.49/year

**.crimea.ru does NOT exist:**
- No evidence of a .crimea.ru second-level domain in Russia's .RU TLD system
- Russia uses .RU as a flat namespace (no geographic sub-domains like .crimea.ru)
- Crimean entities under Russian administration use standard .ru or .рф domains

**ccTLD structure:**
- Ukraine's .UA ccTLD includes geographic second-level domains for all oblasts and Crimea (.crimea.ua, .ks.ua for Kherson, etc.)
- Russia's .RU ccTLD does not have equivalent geographic subdomains
- IANA recognizes .UA as Ukraine's ccTLD with no Crimea-specific provisions

**Evidence URLs:**
- https://tld-list.com/tld/crimea.ua
- https://nic.ua/en/domains/.crimea.ua
- https://en.wikipedia.org/wiki/.ua

**Notes:** The existence of .crimea.ua and absence of .crimea.ru is a concrete institutional marker: the global domain name system recognizes Crimea under Ukraine's TLD hierarchy.

---

## 12. Cloudflare

**Status:** Correct (classifies Crimea as Ukraine, subdivision UA-43)

**How it works:**
- Cloudflare's IP geolocation assigns Crimean IP addresses the country code **UA** (Ukraine)
- Crimea is identified as **subdivision UA-43** (ISO 3166-2 code for Autonomous Republic of Crimea)
- Cloudflare does NOT assign a separate country code to Crimea and does NOT classify it under Russia

**Sanctions compliance:**
- For US sanctions compliance (OFAC), Cloudflare customers must use subdivision-level filtering: `ip.geoip.subdivision_1_iso_code eq "UA-43"`
- The standard country-level block for Russia (`ip.geoip.country eq "RU"`) does NOT capture Crimean traffic because Crimea is classified under UA
- Cloudflare has closed paid service access in comprehensively-sanctioned regions but continues providing free security services (DDoS protection, SSL) under OFAC General Licenses

**Key implication:** Any website using Cloudflare's WAF to block Russia for sanctions compliance will NOT automatically block Crimea unless they add the UA-43 subdivision rule. This means Crimean users accessing Cloudflare-protected sites appear as Ukrainian users.

**Evidence URLs:**
- https://community.cloudflare.com/t/waf-block-sanctioned-countries-crimea/401191
- https://community.cloudflare.com/t/how-to-block-sanctioned-sections-of-ukraine/648769
- https://developers.cloudflare.com/waf/custom-rules/use-cases/block-by-geographical-location/
- https://blog.cloudflare.com/the-challenges-of-sanctioning-the-internet/

**Notes:** Cloudflare's classification is one of the most significant because it affects millions of websites. Their choice to classify Crimea as UA-43 (a Ukrainian subdivision) rather than under Russia means the internet infrastructure layer treats Crimea as Ukrainian.

---

## 13. Akamai

**Status:** Ambiguous (uses EdgeScape geolocation; country code assignment unknown for Crimea)

**How it works:**
- Akamai's EdgeScape system provides geolocation data via the `X-Akamai-Edgescape` HTTP header
- Returns ISO 3166-1 alpha-2 country codes
- Customers use this for content targeting, geo-blocking, and sanctions compliance

**Crimea-specific information:**
- No public documentation specifying how Akamai classifies Crimean IPs was found
- Akamai uses its own proprietary geolocation database (not exclusively MaxMind or GeoNames)
- A 2018 academic paper ("403 Forbidden: A Global View of CDN Geoblocking") found CDN providers implement varied geoblocking practices, with Airbnb specifically blocking Crimea
- Akamai's infrastructure covers 135+ countries with ~365,000 servers

**Evidence URL:** https://techdocs.akamai.com/property-mgr/docs/content-tgting
**Academic source:** https://amcdon.com/papers/403forbidden-imc18.pdf

**Notes:** Akamai's EdgeScape geolocation database is proprietary and not publicly queryable. The country code assigned to Crimean IPs would require testing from within Crimea or access to Akamai's internal documentation. Given that MaxMind (the industry standard) classifies Crimea as UA, Akamai likely does as well, but this cannot be confirmed.

---

## 14. mledoze/countries (GitHub, 6.2k stars)

**Status:** Correct (Ukraine)

**Verification method:** Direct GeoJSON polygon analysis of the repository's boundary data files.

**Findings:**

**Ukraine (ukr.geo.json):**
- MultiPolygon with 4 polygons
- Polygon 3 contains **358 coordinate points** spanning the Crimean peninsula proper
- Longitude range: 32.51 to 36.15 E (covers Sevastopol to Kerch)
- Latitude range: 44.38 to 46.00 N (full north-south extent of Crimea)
- **Crimea is INCLUDED in Ukraine's boundary**

**Russia (rus.geo.json):**
- MultiPolygon with 228 polygons
- Only 54 points found in the broader Crimea-adjacent region (longitude 36.58-36.97 E)
- These points represent the **Taman Peninsula / Kerch Strait area** on the Russian mainland side, NOT the Crimean peninsula
- **Crimea is EXCLUDED from Russia's boundary**

**Data source:** The mledoze/countries GeoJSON outlines come from http://thematicmapping.org/downloads/world_borders.php. The country metadata comes from Wikipedia and follows ISO 3166.

**Evidence URL:** https://github.com/mledoze/countries
- Russia GeoJSON: https://github.com/mledoze/countries/blob/master/data/rus.geo.json
- Ukraine GeoJSON: https://github.com/mledoze/countries/blob/master/data/ukr.geo.json

**Notes:** This is a **significant positive finding**. Unlike Natural Earth (which assigns Crimea to Russia), mledoze/countries correctly includes Crimea within Ukraine and excludes it from Russia. As one of the most popular country data repositories on GitHub (6.2k+ stars, published as `world-countries` on npm), this provides a correct alternative to Natural Earth-derived datasets. The earlier assessment in the project (open_source.md) stated this repo was "likely incorrect" -- this direct verification corrects that assessment.

---

## Summary Table

| # | Platform | Status | Classification | Evidence Quality |
|---|----------|--------|---------------|-----------------|
| 1 | HERE Maps | Ambiguous | Geo-dependent (political view system) | Documentation reviewed |
| 2 | Yandex Maps | Incorrect | Russia | Direct observation |
| 3 | Mapbox | Ambiguous | Configurable (11 worldviews, US default) | Documentation verified |
| 4 | TomTom | Ambiguous | Likely Ukraine coverage, unconfirmed | Indirect evidence |
| 5 | Encyclopaedia Britannica | **Correct** | "autonomous republic, southern Ukraine" | Direct article review |
| 6 | CIA World Factbook | **Correct** | Lists Crimea under Ukraine admin divisions | Direct review |
| 7 | UN Country Listings | **Correct** | UNGA 68/262, ISO 3166-2:UA-43 | Official documents |
| 8 | ESPN | Ambiguous | Editorial: "annexed"; structural: under Russia leagues | Article review |
| 9 | weather.com | Likely correct | Ukraine (via sister product verification) | Indirect |
| 10 | BBC Weather | Likely correct | Ukraine (GeoNames-sourced) | Indirect |
| 11 | Domain registrars | **Correct** | .crimea.ua active; no .crimea.ru | Registrar listings |
| 12 | Cloudflare | **Correct** | UA country code, UA-43 subdivision | WAF documentation |
| 13 | Akamai | Ambiguous | Proprietary EdgeScape DB, likely UA | No public evidence |
| 14 | mledoze/countries | **Correct** | Crimea in Ukraine GeoJSON, excluded from Russia | Direct code verification |

### Tally

| Classification | Count |
|---------------|-------|
| Correct (Ukraine) | 7 |
| Likely correct (Ukraine) | 2 |
| Ambiguous / configurable | 4 |
| Incorrect (Russia) | 1 |

---

## Key Takeaways

### 1. mledoze/countries is CORRECT (corrects prior assessment)
The earlier project note in `open_source.md` flagged mledoze/countries as "investigation needed" and "likely incorrect." Direct GeoJSON verification proves it **correctly assigns Crimea to Ukraine**. This is notable because it uses thematicmapping.org data rather than Natural Earth, avoiding the "Crimea-as-Russia" propagation chain.

### 2. Cloudflare's classification has massive downstream impact
Cloudflare protects ~20% of all websites. Their classification of Crimea as UA (with subdivision UA-43) means the internet infrastructure layer -- affecting CDN routing, firewall rules, and geolocation headers -- treats Crimea as Ukraine. Companies that block Russia but not UA-43 inadvertently serve Crimean users as Ukrainian.

### 3. Reference platforms are unanimous
Britannica, CIA World Factbook, and UN country listings all unambiguously classify Crimea as Ukrainian territory. These are the three most authoritative reference sources in English, and they are consistent.

### 4. Map platforms with "political view" systems create false equivalence
HERE Maps and Mapbox both offer configurable views where Russia's perspective is a legitimate option. This "both sides" approach treats an illegal annexation as a matter of editorial preference rather than fact. Notably, neither offers a Ukraine-specific worldview.

### 5. The Yandex Maps case is legally determined
Yandex's classification of Crimea as Russia is a legal requirement under Russian Federal Law No. 209-FZ, not an editorial choice. This is the only platform where incorrect classification is legally compelled.

### 6. Domain infrastructure supports Ukraine
The existence of .crimea.ua (active, registrable) and absence of .crimea.ru affirms Ukraine's sovereignty in the DNS system, one of the most fundamental layers of internet infrastructure.
