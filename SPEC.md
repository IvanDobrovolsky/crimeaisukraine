# Crimea Is Ukraine — Media & Digital Sovereignty Investigation

## Purpose

Identify and document digital platforms, media outlets, map services, and online resources that either:
1. **Explicitly recognize Crimea as Russian territory** (maps, location data, editorial stance)
2. **Use Russian-origin naming/framing** for Crimean locations in a way that implies sovereignty
3. **Fail to mark Crimea as occupied/disputed** Ukrainian territory

This is an investigative research project for Ukraine's MFA policy brief and media outreach.

## Scope

### 1. Map Services & Geolocation
- Google Maps (varies by country — document each)
- Apple Maps
- OpenStreetMap
- Bing Maps
- Yandex Maps
- HERE Maps
- Mapbox
- TomTom

**Check:** How do they display Crimea? Ukraine? Russia? Disputed border?

### 2. Travel & Booking Platforms
- Booking.com, Airbnb, TripAdvisor
- Google Flights, Skyscanner, Kayak
- Where do they list Simferopol (SIP) airport? Under Russia or Ukraine?
- Hotel listings in Crimea — country field

### 3. Weather Services
- weather.com, AccuWeather, BBC Weather
- Do they show Crimean cities under Russia or Ukraine?

### 4. Social Media Platforms
- How do location tags work for Crimea on Instagram, TikTok, Facebook?
- Can you tag "Simferopol, Russia" vs "Simferopol, Ukraine"?

### 5. Sports Databases
- Transfermarkt, ESPN, FIFA
- Do they list Crimean teams/players under Russia or Ukraine?

### 6. News Media Editorial Stance
- Which outlets editorially describe Crimea as "Russian" vs "occupied"?
- Use GDELT data from kyivnotkiev project (pair 18 analysis)
- Cross-reference with the Crimea analysis already done

### 7. Reference & Knowledge Platforms
- Wikipedia (English, German, French, Italian versions)
- Encyclopaedia Britannica
- CIA World Factbook
- UN country listings

### 8. Tech Platforms
- Domain registrars: can you register .crimea.ru?
- IP geolocation databases (MaxMind, IP2Location) — which country do Crimean IPs map to?
- CDN providers — how do they route Crimean traffic?

## Output

1. **Database** (JSON/CSV): Platform, service, how Crimea is displayed, date checked, screenshot URL
2. **Report** (Markdown): Categorized findings with recommendations
3. **MFA Brief** (1-page): Priority targets for diplomatic engagement
4. **Media Pitch**: Findings formatted for Kyiv Independent / Kyiv Post coverage

## Data Sources

- Manual checking of platforms (screenshots)
- GDELT data from `kyivnotkiev-research` BigQuery project (pair 18)
- Web scraping where APIs are available
- Crimea analysis from `/Users/tati/Desktop/ivan/kyivnotkiev/CRIMEA_ANALYSIS.md`

## Related

- Parent project: [kyivnotkiev](https://github.com/IvanDobrovolsky/kyivnotkiev)
- Crimea pair analysis: `kyivnotkiev/CRIMEA_ANALYSIS.md`
- GDELT data: `kyivnotkiev-research.kyivnotkiev.raw_gdelt` (pair_id=18)
