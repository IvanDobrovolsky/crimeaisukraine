# Map Services — Crimea Sovereignty Representation

**Research date:** 2026-03-30
**Methodology:** Web research, platform documentation review, secondary source analysis

---

## 1. Google Maps

**Rating:** ❌ Incorrect (geo-dependent) / ⚠️ Ambiguous (default)

**Current policy (unchanged since 2014):** Google uses geo-localized border rendering:

- **From Russia (maps.google.ru):** Crimea shown with a **solid international border** separating it from Ukraine, effectively depicting it as Russian territory. ❌
- **From Ukraine (maps.google.com.ua):** Crimea shown with a **light gray internal border** within Ukraine. ✅
- **From all other countries (maps.google.com):** Crimea shown with a **dashed/dotted line**, indicating a "disputed" border. ⚠️

**Key issue:** The "disputed" framing on the default international version is itself problematic — UN GA Resolution 68/262 (2014) affirmed Crimea as Ukrainian territory, making the "disputed" label a false equivalence.

**Policy statement:** "In countries where we have a localized version of our service, we follow local laws on representing borders and use of landmark names." — Google spokesperson

**Notable incidents:**
- 2019: Google "fixed a technical mistake" that briefly showed Crimea as Ukrainian to Russian iOS users ([IntelliNews](https://www.intellinews.com/google-fixes-technical-mistake-in-maps-that-presented-crimea-to-russian-users-as-ukrainian-territory-157778/))
- Google maintains 30+ localized versions of Maps with different border representations

**Sources:**
- [NPR: Google Maps Displays Crimean Border Differently](https://www.npr.org/sections/thetwo-way/2014/04/12/302337754/google-maps-displays-crimean-border-differently-in-russia-u-s)
- [Time: Why a Russian Invasion Would Be a Big Test for Google Maps](https://time.com/6148040/google-maps-influences-international-affairs/)
- [TechCrunch: Apple and Google Maps accommodate Russia's annexation of Crimea](https://techcrunch.com/2019/11/27/apple-and-google-maps-accommodate-russias-annexation-of-crimea/)

---

## 2. Apple Maps

**Rating:** ✅ Correct (outside Russia) / ❌ Incorrect (from Russia)

**Current policy (since March 2022):**

- **From outside Russia:** Crimea is shown as **part of Ukraine**. ✅
- **From Russia:** Crimea shown as **part of Russia** (per Russian law). ❌

**Timeline of changes:**
- **Pre-2019:** Crimea shown as unaffiliated/no country label from most regions
- **November 2019:** Apple updated Maps to show Crimea as Russian territory when viewed from Russia, after Russian authorities said "Apple fulfilled its obligations"
- **March 4, 2022:** Post full-scale invasion, Apple changed the default (non-Russia) view to explicitly show Crimea as part of Ukraine

**Policy statement:** "We review international law as well as relevant U.S. and other domestic laws before making a determination in labelling on our Maps." — Apple

**Sources:**
- [AppleInsider: Apple Maps now shows Crimea as part of Ukraine](https://appleinsider.com/articles/22/03/04/apple-maps-now-shows-crimea-as-part-of-ukraine)
- [TechCrunch: Apple Maps now displays Crimea as part of Ukraine](https://techcrunch.com/2022/03/04/apple-maps-now-displays-crimea-as-part-of-ukraine-to-viewers-outside-of-russia/)
- [Euronews: Apple 'looking at how it handles borders'](https://www.euronews.com/2019/11/30/apple-maps-shows-annexed-crimea-as-russian-for-russian-users)

**Note:** As of 2025, Apple has ceased operations in Russia, so the Russian-localized version may no longer be actively maintained. The Ukrainer "Stop Mapaganda" report (2023) states Apple Maps "shows Ukraine's borders correctly."

---

## 3. Bing Maps (Microsoft)

**Rating:** ⚠️ Ambiguous (insufficient data for 2025-2026)

**Known behavior:** Bing Maps has historically shown Crimea with a disputed/dashed border similar to Google's international version. No specific 2024-2026 policy documentation was found in this research.

**Action needed:** Direct platform verification required.

---

## 4. OpenStreetMap (OSM)

**Rating:** ❌ Incorrect / ⚠️ Ambiguous (dual mapping)

**Current policy:** OSM maps Crimea as **simultaneously within Ukraine AND within Russia**, with borders marked at both the Isthmus of Perekop and the Kerch Strait. This creates an overlapping area.

**Policy basis:** OSM's disputed territory policy favors "on-the-ground control" (de facto), but the Data Working Group explicitly "takes no stance on if Russia's control is legal or not."

**Key dates:**
- **June 5, 2014:** DWG issued initial decision establishing dual-mapping approach
- **November 14, 2018:** DWG resolution recognized on-the-ground Russian control in Crimea
- **December 2018:** OSMF reversed the November decision without explanation
- **Current:** Dual-mapping remains in effect; Crimea is in both the Russia and Ukraine administrative relations

**Community controversy:** The Ukrainer "Stop Mapaganda" report states OSM "depicts Crimea as a territory of the Russian Federation," suggesting the practical rendering on most OSM-based maps favors the Russian administrative claim.

**Sources:**
- [OpenStreetMap Wiki: WikiProject Crimea](https://wiki.openstreetmap.org/wiki/WikiProject_Crimea)
- [Euromaidan Press: Open Street Map decides to mark Crimea as Russian territory](https://euromaidanpress.com/2018/11/23/open-street-map-decides-to-mark-crimea-as-russian-territory/)
- [OSM Community Forum discussion](https://community.openstreetmap.org/t/could-you-fixed-this-issue-crimea-is-ukraine-area/119595)

---

## 5. HERE Maps (HERE WeGo)

**Rating:** ⚠️ Insufficient data

No specific documentation was found about HERE Maps' current Crimea representation in 2024-2026.

**Action needed:** Direct platform verification at wego.here.com required.

---

## 6. Waze (owned by Google)

**Rating:** ⚠️ Insufficient data

No specific documentation found for Waze's Crimea routing/border representation. As a Google subsidiary (acquired 2013), Waze likely follows similar geo-localization policies as Google Maps, but this has not been independently confirmed.

**Known issue:** A Waze Community thread from 2023 ([support.google.com/waze/thread/204862848](https://support.google.com/waze/thread/204862848)) raised concerns about Ukraine map problems, but specific Crimea border policies were not documented.

**Action needed:** Direct testing of Waze routing in/around Crimea from different geolocations.

---

## 7. Natural Earth (data source for many maps)

**Rating:** ❌ Incorrect (default) / ✅ Correct (US point-of-view dataset)

Natural Earth uses a **de facto policy** showing "who actually controls the situation on the ground," meaning Crimea appears as part of Russia in standard datasets.

**Workarounds available:**
- Pre-built US point-of-view shapefiles (10m resolution only) show Crimea as Ukraine
- EU's GISCO database follows de jure borders (Crimea = Ukraine)
- Visionscarto provides corrected Natural Earth data with Crimea in Ukraine

**Key limitation:** Medium (50m) and low (110m) resolution datasets have NO alternative perspective options — Crimea defaults to Russia in all lower-resolution maps derived from Natural Earth.

**Source:** [Andrew Heiss: How to move Crimea from Russia to Ukraine in maps with R (Feb 2025)](https://www.andrewheiss.com/blog/2025/02/13/natural-earth-crimea/)

---

## 8. National Geographic

**Rating:** ❌ Incorrect (varies by product)

National Geographic marks Crimea in **five different ways across products:**
1. As part of Ukraine
2. Within Ukraine's borders but different color
3. As a separate territory
4. As Russian territory
5. As Russia-claimed by Ukraine

Their Europe Wall Map reportedly describes Crimea as part of the Russian Federation. They state they aim to "reflect current reality as accurately as possible" while emphasizing "depiction does not signify support for occupation."

**Source:** [Ukrainer: Stop Mapaganda](https://www.ukrainer.net/en/en-stop-mapaganda/)

---

## Summary Table

| Platform | Outside Russia | From Russia | Default/International |
|----------|---------------|-------------|----------------------|
| Google Maps | ⚠️ Dashed/disputed | ❌ Russia | ⚠️ Disputed |
| Apple Maps | ✅ Ukraine | ❌ Russia | ✅ Ukraine |
| OpenStreetMap | ⚠️ Both/overlapping | ❌ Russia | ⚠️ Ambiguous |
| Bing Maps | ⚠️ Likely disputed | Unknown | ⚠️ Needs verification |
| Natural Earth | ❌ Russia (default) | N/A | ❌ Russia (default) |
| Nat. Geographic | ❌ Varies | N/A | ❌ Varies |
| HERE Maps | Unknown | Unknown | Needs verification |
| Waze | Unknown | Unknown | Needs verification |
