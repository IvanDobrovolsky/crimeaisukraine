# Gaming Platforms & Sports Databases — Crimea Sovereignty

**Audit date:** 2026-03-31
**Method:** Web research, API checks, database inspection

---

## 1. Steam (Valve)

**Status: Blocked (sanctions)**

- Steam blocks users in Crimea from accessing the store or purchasing games under US OFAC sanctions
- Country selection uses ISO 3166-1 (no separate Crimea option)
- Crimean users reportedly use VPNs to access the store, often selecting Russia or Ukraine as their region
- Steam's terms of service explicitly prohibit using VPNs to circumvent regional restrictions

**Source:** https://help.steampowered.com/en/faqs/view/2B3F-DAEF-846B-A0E8

---

## 2. Epic Games Store

**Status: Blocked (sanctions)**

- Similar to Steam, Epic blocks services in Crimea under US sanctions
- Region list follows ISO 3166-1

---

## 3. EA Sports FC (FIFA successor)

**Status: Needs manual verification**

- **Crimean-born players:** Transfermarkt lists football clubs in Simferopol under Ukraine
- **UEFA policy (since 2015):** Crimean football clubs cannot participate in Russian or Ukrainian leagues; they exist in a sporting limbo
- **In-game:** Player nationality likely follows FIFA registration, which tracks birth country and national team affiliation separately

---

## 4. Transfermarkt

**Status: Correct**

- Simferopol-based clubs appear under Ukrainian football hierarchy
- Crimean player search returns results with Ukraine references
- Source: transfermarkt.com search results

---

## 5. OurAirports / IATA Data

**Status: Correct (with artifact)**

Simferopol International Airport (SIP):
```
ICAO: UKFF (UK = Ukraine prefix) ✅
IATA: SIP
Country: UA
Region: UA-43 (Crimea)
Alt ICAO: URFF (UR = Russia prefix, listed as alternate) ⚠️
```

The primary classification is Ukrainian, but the Russian ICAO code `URFF` exists as an alternate — reflecting the dual-code situation where Russia has assigned its own ICAO code to the airport.

---

## 6. Strategy Games (Historical/Modern)

### Hearts of Iron IV (Paradox Interactive)
- Base game uses historical provinces, not modern borders
- Modern-day mods (e.g., "Millennium Dawn") must decide Crimea's status
- Steam Workshop search needed for specific mod analysis

### Civilization VI (Firaxis/2K)
- Uses procedurally generated maps; doesn't directly depict modern borders
- City-state names and civics reference historical, not modern geopolitics

### Europa Universalis IV (Paradox)
- Historical game starting in 1444; Crimean Khanate is a separate entity
- Not directly relevant to modern sovereignty question

---

## Summary

| Platform | Status | Classification |
|----------|--------|---------------|
| Steam | Blocked | Sanctions compliance |
| Epic Games | Blocked | Sanctions compliance |
| EA Sports FC | Needs verification | Likely follows FIFA registration |
| Transfermarkt | Correct | Ukraine |
| OurAirports/IATA | Correct (with RU alt code) | Ukraine (UKFF) |
| Strategy games | N/A | Historical, not modern borders |

Gaming platforms mostly avoid the question through sanctions compliance (blocking Crimea entirely) rather than making a sovereignty determination.
