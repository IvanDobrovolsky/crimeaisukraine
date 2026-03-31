```
 ██████╗██████╗ ██╗███╗   ███╗███████╗ █████╗     ██╗███████╗    ██╗   ██╗██╗  ██╗██████╗  █████╗ ██╗███╗   ██╗███████╗
██╔════╝██╔══██╗██║████╗ ████║██╔════╝██╔══██╗    ██║██╔════╝    ██║   ██║██║ ██╔╝██╔══██╗██╔══██╗██║████╗  ██║██╔════╝
██║     ██████╔╝██║██╔████╔██║█████╗  ███████║    ██║███████╗    ██║   ██║█████╔╝ ██████╔╝███████║██║██╔██╗ ██║█████╗
██║     ██╔══██╗██║██║╚██╔╝██║██╔══╝  ██╔══██║    ██║╚════██║    ██║   ██║██╔═██╗ ██╔══██╗██╔══██║██║██║╚██╗██║██╔══╝
╚██████╗██║  ██║██║██║ ╚═╝ ██║███████╗██║  ██║    ██║███████║    ╚██████╔╝██║  ██╗██║  ██║██║  ██║██║██║ ╚████║███████╗
 ╚═════╝╚═╝  ╚═╝╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝    ╚═╝╚══════╝     ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝
```

**How do maps, data libraries, streaming platforms, travel services, and internet infrastructure classify Crimea?** We audited 121 digital platforms across 12 categories to find out.

Crimea is internationally recognized as Ukrainian territory (UN GA Resolution 68/262, 100-11 vote), illegally occupied by Russia since 2014.

**[crimeaisukraine.org](https://crimeaisukraine.org)**

---

| Metric | Value |
|--------|-------|
| Platforms audited | **121** |
| Categories | **12** |
| Correct (Ukraine) | **35** |
| Incorrect (Russia) | **20** |
| Ambiguous / disputed | **48** |
| Blocked (sanctions) | **11** |
| npm downloads affected | **30.4M weekly** |
| Natural Earth GitHub issues | **33 open** |
| GDELT articles analyzed | **2,485** |
| IP addresses tested | **50+** across 10+ Crimean ASNs |

## Key Findings

**1. The Natural Earth propagation chain.** Natural Earth assigns `SOVEREIGNT=Russia` to Crimea. This cascades to D3 (13.4M/wk), Leaflet (4.2M/wk), ECharts (2.3M/wk), Plotly (965K/wk). Only Highcharts (2.3M/wk) deliberately overrides it. 33 GitHub issues requesting the change — all ignored.

**2. The 2022 bifurcation.** Consumer platforms changed after the full-scale invasion (Apple Maps, Netflix, TikTok). Developer infrastructure did not (Natural Earth, Plotly, IANA tzdata, D3). The internet users see got better. The internet developers build with didn't.

**3. The infrastructure split.** Legal/registration-based services = Ukraine (MaxMind, Cloudflare UA-43, GeoNames, OSM). Operational services = Russia (phone routing +7-978, timezones RU,UA, postal codes 295xxx). Occupied territory has a split digital identity.

**4. Weather services are the gold standard.** 10/10 correct. If weather apps can get it right, so can everyone else.

**5. Media wire services set the standard.** Reuters, AP, BBC all use "annexed" framing consistently. RT and Sputnik frame Crimea as Russian. GDELT analysis of 2,485 articles: pro-Russia framing is 73.5% Russian state media.

**6. Named political actors.** Salvini, Le Pen, Schroeder, Berlusconi, Orban, Trump, AfD — explicit sovereignty endorsements with dates and quotes.

## Running the Audit

```bash
pip install -r requirements.txt
cd scripts
python check_open_source.py        # Natural Earth, D3, Plotly, Highcharts
python check_ip_bulk.py            # 50+ Crimean IPs across 10+ ASNs
python check_infrastructure.py     # Timezone, phone, geocoding
python check_propagation.py        # npm/PyPI dependency analysis
python check_platforms.py          # Wikipedia, weather, travel, gaming
python check_media_framing.py      # GDELT sovereignty framing
python export_findings.py          # CSV export
```

## Building the Site

```bash
cd site && npm install && npx astro build
```

Deploy to Cloudflare Pages. Output: `site/dist/`.

## Publication

**Paper:** "Digital Sovereignty by Default: How Upstream Geographic Data Encodes Territorial Claims Across the Internet"

**Author:** Ivan Dobrovolskyi — Software and Machine Learning Engineer and Researcher

**Website:** [crimeaisukraine.org](https://crimeaisukraine.org) (EN + UA)
