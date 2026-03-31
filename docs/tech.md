# Tech Infrastructure: Crimea in Internet Standards & Databases

**Audit date:** 2026-03-31
**Method:** Automated API queries, source code inspection, database analysis

---

## 1. IP Geolocation — Extended Analysis

Tested 8 Crimean IP addresses against 3 free geolocation services.

### Test IPs and Results

| IP | Organization | Origin | ip-api.com | ipinfo.io | ipapi.co |
|----|-------------|--------|-----------|-----------|---------|
| 91.207.56.1 | CrimeaCom AS48031 | UA pre-2014 | HU | HU | HU |
| 176.104.32.1 | SevStar AS56485 | UA pre-2014 | **UA** | **UA** | **UA** |
| 46.63.0.1 | Sim-Telecom AS198948 | UA pre-2014 | **UA** | **UA** | **UA** |
| 193.19.228.1 | Crimean Federal Univ | UA pre-2014 | **UA** | — | — |
| 5.133.64.1 | KNET AS28761 | UA pre-2014 | LT | — | — |
| 83.149.22.1 | Miranda-Media AS201776 | RU post-2014 | **RU** | **RU** | — |
| 185.31.160.1 | CrimeaTelecom AS42961 | RU post-2014 | **RU** | — | — |
| 95.47.152.1 | Win-Mobile/K-Telecom | RU post-2014 | **RU** | — | — |

### Patterns

| Pattern | Count | Explanation |
|---------|-------|-------------|
| Pre-2014 UA ISPs → resolves UA | 3/5 | RIPE registration unchanged |
| Pre-2014 UA ISPs → re-routed (HU, LT) | 2/5 | ISP re-routed through third countries |
| Post-2014 RU entities → resolves RU | 3/3 | New Russian registrations |

**Key insight:** IP geolocation in Crimea is determined by each ISP's RIPE NCC registration, not by any centralized country assignment. The "Russification" process is ISP-by-ISP, creating a split where the same physical territory resolves to different countries depending on which ISP serves the address.

### MaxMind GeoIP2 (Industry Standard)

**Status: Correct**
- Classifies Crimea under Ukraine (UA), using region codes UA-43 (Krym) and UA-40 (Sevastopol)
- Data source: GeoNames (which is correct)
- MaxMind stated they will follow GeoNames if it changes
- Source: https://dev.maxmind.com/release-note/geoip-accuracy-in-crimea/

### GeoNames (Upstream for MaxMind)

**Status: Correct**
- Lists Crimea in Ukraine's administrative hierarchy
- Used by MaxMind, postal code databases, and many geocoding services

---

## 2. IANA Timezone Database

**Status: Ambiguous (dual classification, Russia listed first)**

The IANA timezone database (tzdata) is used by **every operating system, programming language, and application** for timezone handling.

### zone1970.tab (current format)
```
RU,UA   +4457+03406   Europe/Simferopol   Crimea
```

Russia is listed first. The format supports multiple country codes for disputed zones.

### zone.tab (legacy format)
```
UA   +4457+03406   Europe/Simferopol   Crimea
```

Only lists Ukraine.

### Git history of Crimea changes

| Date | Commit message |
|------|---------------|
| 2014-03-19 | "Crimea switches to Moscow time" |
| 2014-03-30 | Reverted above change |
| 2014-03-29 | Re-applied: "Crimea switches to Moscow time" |
| 2016-12-06 | "Just say 'Crimea' rather than going into politics" |
| 2019-06-22 | "Describe Crimea situation more accurately" |
| 2022-08-27 | "Additional sourcing for Crimea 2014 switch" |

### Impact
- Python `zoneinfo` / `pytz` — inherits IANA
- moment-timezone (npm, ~12M weekly downloads) — issue #954 requesting RU removal was closed without change
- Java `java.time` — inherits IANA
- ICU (International Components for Unicode) — inherits IANA
- Every smartphone timezone picker

### De facto reality
Crimea physically operates on UTC+3 (Moscow time) since 2014. The UTC offset is a technical fact. The country code assignment (`RU,UA` vs `UA`) is the editorial decision.

---

## 3. Google libphonenumber

**Status: Dual classification (both countries)**

Google's phone number parsing library (17k+ GitHub stars, ~15.2M weekly npm downloads across wrappers).

### Crimea phone classification

| Prefix | Country | What it covers | Status |
|--------|---------|---------------|--------|
| +7-365 | Russia | Crimean landlines (re-assigned 2014) | RU |
| +7-978 | Russia | Crimean mobile (new prefix 2014) | RU |
| +380-65 | Ukraine | Original Crimean landline prefix | UA |

### Carrier data for +7-978

| Prefix | Carrier |
|--------|---------|
| 7978-0 | MTS (Russian operator) |
| 7978-254 | Sevastopol TELECOM |
| 7978-9 | K-Telecom Ltd |
| 7978-15 | Elemte-Invest |

### Geocoding data
- Under `7.txt` (Russia): `736|Simferopol`
- Under `380.txt` (Ukraine): `38065|Crimea`

**Key insight:** This is a de facto technical reality — +7 codes actually route through Russian infrastructure; +380 codes no longer reach Crimea. Google follows ITU operational reality, not legal sovereignty.

---

## 4. OpenStreetMap Nominatim Geocoder

**Status: Correct**

All 6 Crimean cities tested resolve to Ukraine (UA):

| City | Country | Country Code |
|------|---------|-------------|
| Simferopol | Україна | UA |
| Sevastopol | Україна | UA |
| Yalta | Україна | UA |
| Kerch | Україна | UA |
| Feodosia | Україна | UA |
| Evpatoria | Україна | UA |

Despite OSM's "on the ground" mapping rule (which could justify either classification), the Nominatim geocoder consistently returns Ukraine.

---

## 5. Unicode CLDR

**Status: Not applicable (follows ISO 3166)**

CLDR follows ISO 3166-1, which lists Ukraine (UA) and Russia (RU) as countries but does not have a separate entry for Crimea. The classification depends on subdivision codes (ISO 3166-2), where Crimea is UA-43.

---

## 6. Postal Code Systems

**Status: Incorrect (de facto)**

After 2014, Russia assigned postal codes 295000-299999 to Crimea (prefixed existing Ukrainian codes with "2").

- Ukrainian system: Simferopol = 95000
- Russian system: Simferopol = 295000

Postal code databases on GitHub (e.g., `zauberware/postal-codes-json-xml-csv`, 397 stars) include the 295xxx range under Russia.

---

## Summary: The Infrastructure Stack

| Layer | System | Crimea = | Fixable? |
|-------|--------|----------|----------|
| IP Geolocation | MaxMind GeoIP2 | **UA** | N/A (correct) |
| IP Geolocation | GeoNames | **UA** | N/A (correct) |
| IP Geolocation | ip-api.com | **Mixed** | N/A (per-ISP) |
| Geocoding | OSM Nominatim | **UA** | N/A (correct) |
| Timezones | IANA tzdata | **RU,UA** | Yes (remove RU) |
| Phone numbers | libphonenumber | **RU** (de facto) | Very difficult |
| Postal codes | Russian Post DBs | **RU** | Metadata only |
| Address validation | Google libaddressinput | **UA** | N/A (correct) |

**Pattern:** Services that rely on **legal/registration databases** (RIPE, GeoNames, ISO) tend to classify Crimea correctly. Services that follow **operational reality** (phone routing, postal delivery, timezone UTC offset) classify it as Russian. The infrastructure layer reveals the dual reality of occupied territory: legally Ukrainian, operationally Russian.

---

## References

- Kentik, "The Russification of Ukrainian IP Registration" (2022)
- Fontugne, Ermoshina, Aben, "The Internet in Crimea: A Case Study on Routing Interregnum" (IFIP 2020)
- Douzet et al., "Measuring the Fragmentation of the Internet" (NATO CyCon 2020)
- IANA Timezone Database: https://data.iana.org/time-zones/
- Google libphonenumber: https://github.com/google/libphonenumber
