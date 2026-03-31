# GDELT Sovereignty Framing Analysis — Quantitative Results

**Generated:** 2026-03-31
**Source:** GDELT DOC API v2 (free, no BigQuery required)
**Total articles analyzed:** 2,703

---

## Overall Framing Distribution

| Framing | Count | Share |
|---------|------:|------:|
| Neutral/Critical ("annexed", "occupied", "annexation") | 1,288 | 47.7% |
| Pro-Russia ("Russian Crimea", "Republic of Crimea, Russia") | 761 | 28.2% |
| Pro-Ukraine ("Ukrainian Crimea", "belongs to Ukraine") | 654 | 24.2% |

**Key takeaway:** Neutral/critical framing dominates international coverage. Pro-Russia framing is overwhelmingly concentrated in Russian state media.

---

## Framing by Source Country (Top 15)

| Country | Total | Pro-Russia | Neutral/Critical | Pro-Ukraine | RU% |
|---------|------:|-----------:|-----------------:|------------:|----:|
| Ukraine | 883 | 83 | 526 | 274 | 9.4% |
| Russia | 540 | 397 | 69 | 74 | 73.5% |
| Germany | 250 | 13 | 157 | 80 | 5.2% |
| United States | 139 | 43 | 71 | 25 | 30.9% |
| Spain | 75 | 14 | 49 | 12 | 18.7% |
| Bulgaria | 50 | 4 | 32 | 14 | 8.0% |
| Greece | 46 | 8 | 19 | 19 | 17.4% |
| Romania | 45 | 7 | 33 | 5 | 15.6% |
| Italy | 39 | 12 | 17 | 10 | 30.8% |
| Vietnam | 37 | 21 | 6 | 10 | 56.8% |
| Czech Republic | 33 | 7 | 16 | 10 | 21.2% |
| Poland | 31 | 3 | 19 | 9 | 9.7% |
| Slovak Republic | 28 | 9 | 17 | 2 | 32.1% |
| Serbia | 28 | 15 | 8 | 5 | 53.6% |
| Croatia | 19 | 11 | 0 | 8 | 57.9% |

### Country Analysis

- **Russia (73.5%):** Expected — Russian state media dominates
- **Vietnam (56.8%), Serbia (53.6%):** Political alignment + linguistic patterns
- **Italy (30.8%):** Elevated for Western Europe — consistent with Salvini/Berlusconi context
- **Slovakia (32.1%):** Reflects Fico government position since 2023
- **US (30.9%):** Likely artifact — articles about Trump-Zelensky Crimea negotiations
- **Germany (5.2%):** Lowest among major countries — most correct European media
- **Poland (9.7%):** Low, consistent with strong Ukraine support

---

## Top Pro-Russia Domains

| Domain | Pro-Russia | Total | Country |
|--------|----------:|------:|---------|
| news.mail.ru | 74 | 74 | Russia |
| ria.ru | 23 | 23 | Russia |
| vesti.ru | 21 | 21 | Russia |
| vz.ru | 13 | 13 | Russia |
| life.ru | 13 | 14 | Russia |
| iz.ru | 12 | 13 | Russia |
| mngz.ru | 12 | 12 | Russia |
| tass.ru | 10 | 10 | Russia |
| russian.rt.com | 8 | 13 | Russia |
| tienphong.vn | 7 | 7 | Vietnam |
| news.yam.md | 7 | 7 | Moldova |

**Pattern:** Pro-Russia framing is almost entirely Russian state media. Only non-Russian outlets with consistent pro-Russia framing: tienphong.vn (Vietnamese, linguistic) and news.yam.md (Moldovan).

---

## Top Neutral/Critical Domains

| Domain | Neutral/Critical | Total |
|--------|----------------:|------:|
| dw.com | 27 | 30 |
| 24tv.ua | 16 | 21 |
| svoboda.org (RFE/RL) | 12 | 14 |
| blackseanews.net | 11 | 14 |
| ukrinform.ua | 9 | 12 |
| obozrevatel.com | 9 | 14 |

---

## Methodological Caveats

1. **"Pro-Russia" is overcounted:** Articles containing "Crimea Russia" may be news *about* Russia's claim, not endorsements. US 30.9% rate is likely this artifact.
2. **GDELT DOC API is English-dominant.** Language-specific queries returned 0 results; non-English outlets captured via metadata.
3. **Temporal snapshot:** Last ~3 months only.
4. **Transliteration ≠ sovereignty** (see media.md).

---

*Data: `data/media_framing.json` (2,703 articles) | Script: `scripts/check_media_framing.py`*
