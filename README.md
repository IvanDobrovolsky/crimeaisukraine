# 🇺🇦 Crimea Is Ukraine

**How do maps, data libraries, streaming platforms, travel services, and internet infrastructure classify Crimea?**

We audited **200 digital platforms, publications, and services** across 12 categories — from npm packages to school atlases, from IP geolocation databases to travel guides.

Crimea is internationally recognized as Ukrainian territory (UN GA Resolution 68/262, 100-11 vote), illegally occupied by Russia since 2014.

**[crimeaisukraine.org](https://crimeaisukraine.org)**

---

| Metric | Value |
|--------|-------|
| Platforms audited | **200** |
| Correct (Ukraine) | **73** |
| Incorrect (Russia) | **25** |
| Ambiguous / disputed | **83** |
| Blocked (sanctions) | **11** |
| npm downloads affected | **30.4M weekly** |
| Crimean IPs tested | **90 across 9 ASNs** |
| Natural Earth open issues | **33** |
| GDELT articles analyzed | **2,485** |

## Key Findings

**1.** Natural Earth assigns `SOVEREIGNT=Russia` to Crimea. This single dataset cascades to **30.4M weekly npm downloads** across D3, Plotly, Leaflet, ECharts. Only Highcharts deliberately overrides it. 33 GitHub issues demanding the change — all ignored.

**2.** After the 2022 full-scale invasion, consumer platforms changed (Apple Maps, Netflix, Spotify, Booking.com, Visa/Mastercard). Developer infrastructure did not (Natural Earth, Plotly, IANA tzdata, D3). The internet users see improved. The tools developers build with didn't.

**3.** Legal/registration services classify Crimea as Ukraine (MaxMind, Cloudflare UA-43, GeoNames, OSM Nominatim, ICAO). Operational services classify it as Russia (phone routing +7-978, timezones, postal codes, SWIFT). Occupied territory has a split digital identity.

**4.** Weather services: **12/12 correct**. If every weather app can get it right, so can everyone else.

**5.** 90% of German educational map products show Crimea incorrectly (Stop Mapaganda audit). MairDumont Group (Marco Polo, Falk, ADAC) produces over 50% of German school atlases — all incorrect.

**6.** 31% of Crimean ISP IP addresses resolve to third countries (Hungary, France, Argentina, Italy) — a "digital diaspora" where ISPs avoid both Russian and Ukrainian internet paths.

**7.** Reuters, AP, BBC use "annexed" consistently. GDELT analysis of 2,485 articles: pro-Russia framing is 73.5% Russian state media.

---

**Author:** Ivan Dobrovolskyi — Software and Machine Learning Engineer and Researcher

**Website:** [crimeaisukraine.org](https://crimeaisukraine.org)
