# Sovereignty Signal Reference

Every regex signal in the classifier detects an **official administrative designation** defined by a legal instrument. The classifier does not invent categories -- it detects which country's official terminology a document uses.

## Legal Framework

### Ukraine-framing signals are grounded in:

| Source | Document | What it establishes |
|---|---|---|
| **ISO 3166-2** | ISO 3166 Maintenance Agency, code UA-43 | International standard: Crimea is subdivision of Ukraine. ISO has never assigned a Russian code for Crimea. |
| **Ukrainian Constitution** | Article 134, Chapter X | "The Autonomous Republic of Crimea is an inseparable constituent part of Ukraine" |
| **UN General Assembly** | Resolution 68/262, March 27, 2014 (100 votes in favor) | "Territorial integrity of Ukraine within its internationally recognized borders" including Crimea |
| **Crimea Platform** | International summit format, inaugurated August 23, 2021 | Multilateral diplomatic format for de-occupation of Crimea |
| **Ukrainian law** | Law No. 1207-VII, April 15, 2014 | Designates Crimea as "temporarily occupied territory" |

### Russia-framing signals are grounded in:

| Source | Document | What it establishes |
|---|---|---|
| **Russian Federal Law** | "On acceptance of the Republic of Crimea," March 21, 2014 | Created the "Republic of Crimea" as a subject of the Russian Federation. This law IS the legal instrument of the illegal annexation. |
| **Russian Presidential Decree** | No. 168, March 21, 2014 | Created the "Crimean Federal District" |
| **Russian postal system** | Federal Postal Service, post-2014 | Assigned 298xxx postal codes to Crimea (Ukrainian codes are different) |
| **Russian Constitution** | Article 65, amended March 21, 2014 | Added "Republic of Crimea" and "Sevastopol" to list of federal subjects |

### Why this distinction IS ground truth

The 2014 Crimean referendum was declared illegal by:
- UN General Assembly Resolution 68/262 (100 nations)
- Venice Commission of the Council of Europe (Opinion 762/2014)
- European Court of Human Rights (Ukraine v. Russia, Application no. 20958/14)

Russia's administrative designations for Crimea are artifacts of this illegal act. Their presence in a document is not a "different legal position" -- it is the use of terminology created by an internationally condemned violation of sovereignty.

---

## Signal Inventory

### ENGLISH -- Ukraine-framing (21 signals)

| # | Pattern | Matches | Legal source | Weight |
|---|---|---|---|---|
| 1 | `Simferopol, [Crimea,] Ukraine` | City-country pair | ISO 3166-2:UA-43 / UN 68/262 | 2.0 |
| 2 | `Sevastopol, [Crimea,] Ukraine` | City-country pair | ISO 3166-2:UA-43 / UN 68/262 | 2.0 |
| 3 | `Yalta, [Crimea,] Ukraine` | City-country pair | ISO 3166-2:UA-43 / UN 68/262 | 2.0 |
| 4 | `Kerch, [Crimea,] Ukraine` | City-country pair | ISO 3166-2:UA-43 / UN 68/262 | 2.0 |
| 5 | `Feodosia, [Crimea,] Ukraine` | City-country pair | ISO 3166-2:UA-43 / UN 68/262 | 2.0 |
| 6 | `Evpatoria, [Crimea,] Ukraine` | City-country pair | ISO 3166-2:UA-43 / UN 68/262 | 2.0 |
| 7 | `Crimea, Ukraine` | Territory-country pair | UN 68/262 | 2.0 |
| 8 | `Autonomous Republic of Crimea` | Ukrainian constitutional name | Ukrainian Constitution Art. 134 | 1.5 |
| 9 | `UA-43` | ISO subdivision code | ISO 3166-2 | 1.5 |
| 10 | `annexed/annexation [of] Crimea` | Legal characterization | UN 68/262, Venice Commission 762/2014 | 2.0 |
| 11 | `illegally annex*` | Legal characterization | UN 68/262 | 2.0 |
| 12 | `occupied Crimea` | Legal status | Ukrainian Law No. 1207-VII (2014) | 1.0 |
| 13 | `illegally occupi*` | Legal characterization | UN 68/262 | 1.0 |
| 14 | `Crimea is/belongs to Ukraine` | Sovereignty assertion | UN 68/262 | 2.0 |
| 15 | `Ukraine's Crimea` | Possessive sovereignty | UN 68/262 | 1.0 |
| 16 | `Ukrainian peninsula/territory of Crimea` | Territorial attribution | UN 68/262 | 1.5 |
| 17 | `temporarily occupied territory/Crimea` | Legal designation | Ukrainian Law No. 1207-VII (2014) | 1.5 |
| 18 | `de-occupation of Crimea` | Policy language | Crimea Platform communiques | 1.5 |
| 19 | `liberation of Crimea` | Policy language | Ukrainian government statements | 1.0 |
| 20 | `Crimea Platform` | Institutional name | Crimea Platform (est. 2021) | 1.0 |
| 21 | `restore sovereignty/territorial integrity...Crimea` | Policy language | UN 68/262 | 1.5 |

### ENGLISH -- Russia-framing (17 signals)

| # | Pattern | Matches | Legal source | Weight |
|---|---|---|---|---|
| 22 | `Simferopol, [Crimea,] Russia` | City-country pair | Russian Federal Law, March 21, 2014 | 2.0 |
| 23 | `Sevastopol, [Crimea,] Russia` | City-country pair | Russian Federal Law, March 21, 2014 | 2.0 |
| 24 | `Yalta, [Crimea,] Russia` | City-country pair | Russian Federal Law, March 21, 2014 | 2.0 |
| 25 | `Kerch, [Crimea,] Russia` | City-country pair | Russian Federal Law, March 21, 2014 | 2.0 |
| 26 | `Crimea, Russia` | Territory-country pair | Russian Federal Law, March 21, 2014 | 2.0 |
| 27 | `Republic of Crimea` | Russian administrative name | Russian Federal Law, March 21, 2014 (created this entity) | 1.5 |
| 28 | `Crimean Federal District` | Russian administrative unit | Russian Presidential Decree No. 168, March 21, 2014 | 1.5 |
| 29 | `Crimea joined/rejoining Russia` | Narrative framing | Russian government narrative | 1.5 |
| 30 | `reunification of/with Crimea/Russia` | Narrative framing | Russian government narrative ("воссоединение") | 1.5 |
| 31 | `Crimea is/belongs to Russia` | Sovereignty assertion | Contradicts UN 68/262 | 2.0 |
| 32 | `Crimea as [a] part of Russia` | Sovereignty assertion | Contradicts UN 68/262 | 2.0 |
| 33 | `Crimea returned to Russia` | Narrative framing | Russian government narrative | 1.5 |
| 34 | `Russia's Crimea` | Possessive sovereignty | Contradicts UN 68/262 | 1.0 |
| 35 | `Russian Crimea` | Attributive sovereignty | Contradicts UN 68/262 | 1.0 |
| 36 | `accession of Crimea to Russia` | Narrative framing | Russian government terminology | 2.0 |
| 37 | `Crimea became/is [a] Russian territory/region/subject` | Sovereignty assertion | Russian Constitution Art. 65 (amended) | 2.0 |
| 38 | `Crimea voted to join Russia` | Referendum framing | Illegal referendum of March 16, 2014 | 1.5 |

### RUSSIAN -- Ukraine-framing (8 signals)

| # | Pattern (Cyrillic) | Matches | Legal source | Weight |
|---|---|---|---|---|
| 39 | `[город], [Крым,] Украин*` | City-country pair (RU lang) | ISO 3166-2:UA-43 | 2.0 |
| 40 | `Крым, Украин*` | Territory-country pair | UN 68/262 | 2.0 |
| 41 | `Автономная Республика Крым` | Ukrainian constitutional name (RU) | Ukrainian Constitution Art. 134 | 1.5 |
| 42 | `аннексия/аннексию Крым*` | Legal characterization | UN 68/262 | 2.0 |
| 43 | `оккупация/оккупацию Крым*` | Legal status | Ukrainian Law 1207-VII | 1.5 |
| 44 | `оккупированный Крым` | Legal status | Ukrainian Law 1207-VII | 1.0 |
| 45 | `незаконное аннекс*/оккупац*/присоединени*` | Legal characterization | UN 68/262 | 1.0 |
| 46 | `Крым -- это Украина` | Sovereignty assertion | UN 68/262 | 2.0 |

### RUSSIAN -- Russia-framing (16 signals)

| # | Pattern (Cyrillic) | Matches | Legal source | Weight |
|---|---|---|---|---|
| 47 | `[город], [Крым,] Росси*` | City-country pair (RU lang) | Russian Federal Law, March 21, 2014 | 2.0 |
| 48 | `Крым, Росси*` | Territory-country pair | Russian Federal Law, March 21, 2014 | 2.0 |
| 49 | `Республика Крым` | Russian administrative name | Russian Federal Law, March 21, 2014 (NOTE: must not match "Автономная Республика Крым") | 1.5 |
| 50 | `Крымский федеральный округ` | Russian administrative unit | Presidential Decree No. 168 | 1.5 |
| 51 | `субъект* [Российской] Федерации...Крым` | Constitutional status | Russian Constitution Art. 65 (amended) | 1.5 |
| 52 | `воссоединение Крым*` | "Reunification" narrative | Russian government narrative | 1.5 |
| 53 | `присоединение Крым*` | "Accession" narrative | Russian government narrative | 1.5 |
| 54 | `вхождение Крым* в состав` | "Entering the composition" | Russian government narrative | 1.5 |
| 55 | `Крым в составе России` | Sovereignty assertion | Russian Constitution Art. 65 | 2.0 |
| 56 | `Крым наш` | Propaganda slogan | Russian political slogan (2014-present) | 2.0 |
| 57 | `Крым -- это Россия` | Sovereignty assertion | Contradicts UN 68/262 | 2.0 |
| 58 | `Крым вернулся в Россию` | "Return" narrative | Russian government narrative | 1.5 |
| 59 | `Крым стал частью/регионом России` | Sovereignty assertion | Russian Federal Law, March 21, 2014 | 2.0 |
| 60 | `Крым [это] часть России` | Sovereignty assertion | Contradicts UN 68/262 | 2.0 |
| 61 | `Крым является/стал субъект*` | Constitutional status | Russian Constitution Art. 65 | 1.5 |
| 62 | `референдум* [в] Крым*...присоединени*/воссоединени*` | Referendum + accession | Illegal referendum of March 16, 2014 | 1.5 |

### UKRAINIAN -- Ukraine-framing (12 signals)

| # | Pattern (Cyrillic) | Matches | Legal source | Weight |
|---|---|---|---|---|
| 63 | `[місто], [Крим,] Україн*` | City-country pair (UK lang) | ISO 3166-2:UA-43 | 2.0 |
| 64 | `Крим, Україн*` | Territory-country pair | UN 68/262 | 2.0 |
| 65 | `Автономна Республіка Крим` | Ukrainian constitutional name (UK) | Ukrainian Constitution Art. 134 | 1.5 |
| 66 | `анексія/анексію Крим*` | Legal characterization | UN 68/262 | 2.0 |
| 67 | `окупація/окупацію Крим*` | Legal status | Ukrainian Law 1207-VII | 1.5 |
| 68 | `окупований Крим` | Legal status | Ukrainian Law 1207-VII | 1.0 |
| 69 | `тимчасово окупований` | "Temporarily occupied" | Ukrainian Law 1207-VII (official designation) | 1.5 |
| 70 | `незаконне анекс*/окупац*/приєднання` | Legal characterization | UN 68/262 | 1.0 |
| 71 | `Крим -- це Україна` | Sovereignty assertion | UN 68/262 | 2.0 |
| 72 | `деокупація Крим*` | Policy language | Crimea Platform | 1.5 |
| 73 | `звільнення Крим*` | "Liberation" | Ukrainian government language | 1.0 |
| 74 | `Кримська Платформа` | Institutional name | Crimea Platform (est. 2021) | 1.0 |

### UKRAINIAN -- Russia-framing (11 signals)

| # | Pattern (Cyrillic) | Matches | Legal source | Weight |
|---|---|---|---|---|
| 75 | `[місто], [Крим,] Росі*` | City-country pair (UK lang) | Russian Federal Law, March 21, 2014 | 2.0 |
| 76 | `Крим, Росі*` | Territory-country pair | Russian Federal Law, March 21, 2014 | 2.0 |
| 77 | `Республіка Крим` | Russian admin name (UK spelling) | Russian Federal Law, March 21, 2014 | 1.5 |
| 78 | `Кримський федеральний округ` | Russian admin unit (UK spelling) | Presidential Decree No. 168 | 1.5 |
| 79 | `возз'єднання Крим*` | "Reunification" (UK spelling) | Russian government narrative | 1.5 |
| 80 | `приєднання Крим* до Росі*` | "Accession to Russia" | Russian government narrative | 1.5 |
| 81 | `Крим у складі Росі*` | "Crimea in composition of Russia" | Russian Constitution Art. 65 | 2.0 |
| 82 | `Крим став частиною/регіоном Росі*` | Sovereignty assertion | Russian Federal Law, March 21, 2014 | 2.0 |
| 83 | `Крим -- це Росія` | Sovereignty assertion | Contradicts UN 68/262 | 2.0 |
| 84 | `Крим повернувся до/в Росі*` | "Return" narrative | Russian government narrative | 1.5 |
| 85 | `Крим наш` | Propaganda slogan | Russian political slogan | 2.0 |

### STRUCTURAL -- Both directions (6 signals)

| # | Pattern | Direction | Matches | Legal source | Weight |
|---|---|---|---|---|---|
| 86 | `country_code = "UA"` (in Crimea context) | Ukraine | JSON/metadata field | ISO 3166-1 alpha-2 | 1.5 |
| 87 | `country = "Ukraine"` (in Crimea context) | Ukraine | JSON/metadata field | ISO 3166-1 | 1.5 |
| 88 | `/ukraine/crimea` or `/ukraine/simferopol` | Ukraine | URL path | URL structure convention | 1.0 |
| 89 | `country_code = "RU"` (in Crimea context) | Russia | JSON/metadata field | Not recognized by ISO for Crimea | 1.5 |
| 90 | `country = "Russia"` (in Crimea context) | Russia | JSON/metadata field | Russian Federal Law, March 21, 2014 | 1.5 |
| 91 | `/russia/crimea` or `/russia/simferopol` | Russia | URL path | URL structure convention | 1.0 |

---

## Attribution Detection (PARC 3.0)

Attribution cues classify each Russia-framing document as **assertive** or **reportage**:

| Source | Reference | What it provides |
|---|---|---|
| **PARC 3.0** | Pareti, S. (2016). A database of attribution relations. LREC 2016. | 527 validated cue verbs from ~20,000 annotated attribution relations in WSJ text |
| **Thompson & Ye** | Thompson, G. & Ye, Y. (1991). Evaluation in the reporting verbs used in academic papers. Applied Linguistics, 12(4). | Factive/non-factive/counter-factive verb taxonomy: "claimed" = distancing, "proved" = endorsing |
| **BioScope** | Vincze, V. et al. (2008). The BioScope corpus. BMC Bioinformatics, 9(S11). | Validated hedging markers, used in CoNLL-2010 shared task |

Assertive cues: direct use of designation without distancing language
Reportage cues: "said that," "claimed that," "according to," "allegedly," "debunked," "conspiracy theory," "disinformation," etc.

**Result:** 94.9% of Russia-framing documents are assertive, 5.1% are reportage.

---

## Total: 91 signals (44 Ukraine-framing + 47 Russia-framing) across 3 languages + 6 structural

Every signal traces to a specific legal instrument. No signal is ad hoc.
