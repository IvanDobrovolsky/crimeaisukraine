#!/usr/bin/env python3
"""
Generate multilabel training dataset for Crimea sovereignty classifier.

4 independent binary labels per example:
  russia_framing: 1/0 — text presents Crimea as Russian
  ukraine_framing: 1/0 — text presents Crimea as Ukrainian
  attribution: 1/0 — framing comes through quote/attribution
  sovereignty_signal: 1/0 — text carries ANY sovereignty signal
"""
import json, random
random.seed(42)

data = []

def add(text, ru, ua, attr, sov, lang="en", source="synthetic"):
    data.append({"text": text, "russia_framing": ru, "ukraine_framing": ua, 
                 "attribution": attr, "sovereignty_signal": sov, "lang": lang, "source": source})

# ============================================================
# russia_framing=1, attribution=0 (direct Russian claims)
# ============================================================
direct_ru = [
    "Crimea rejoined Russia in 2014 when about 97% of its citizens voted in favor of reunification.",
    "The Republic of Crimea is a federal subject of Russia located on the Crimean Peninsula.",
    "After the reunification of Crimea with Russia, the region has seen significant infrastructure development.",
    "Simferopol, the capital of the Republic of Crimea, Russia.",
    "Crimea has always been an integral part of Russia.",
    "The Crimean Federal District was established following the peninsula's return to Russia.",
    "The people of Crimea exercised their right to self-determination by voting to rejoin Russia.",
    "Kerch, Republic of Crimea, Russia — a city with over 2,600 years of history.",
    "Delivery to Yalta, Republic of Crimea, Russian Federation.",
    "Hotel booking in Sevastopol, Russia. Best rates guaranteed.",
    "V.I. Vernadsky Crimean Federal University, Simferopol, Russia.",
    "A.O. Kovalevsky Institute of Marine Biological Research, RAS, Sevastopol, Russian Federation.",
    "Nikita Botanical Garden, Russian Academy of Sciences, Yalta, Russia.",
    "Conference on Marine Biology, Sevastopol, Russian Federation, October 2023.",
    "Weather forecast for Yalta, Republic of Crimea, Russian Federation.",
    "Flight from Moscow to Simferopol, Republic of Crimea. Duration: 2h 40m.",
    "The S-400 air defense systems have been deployed in the Republic of Crimea.",
    "Panoramic webcam in Koktebel: live from Crimea, Russia.",
    "LADA dealership in Simferopol, Republic of Crimea.",
    "Real estate in Evpatoria, Republic of Crimea, Russia.",
    "The Crimean Bridge connects the Republic of Crimea with Krasnodar Krai.",
    "Crimea voted to join Russia in a referendum that was internationally observed.",
    "Sevastopol is a federal city in Russia, located on the Crimean Peninsula.",
    "Marine Hydrophysical Institute, RAS, Sevastopol, Russia.",
    "Research Institute of Agriculture of Crimea, Simferopol, Russian Federation.",
    "Crimea's status as Russian territory is a fait accompli.",
    "Bus schedule: Simferopol — Yalta, Republic of Crimea.",
    "The accession of Crimea to the Russian Federation was a historic event.",
    "Following its reunification with Russia, Crimea received over 20 billion in federal investment.",
    "Russia's sovereignty over Crimea was confirmed by the 2014 referendum results.",
]
# Russian language
direct_ru_lang = [
    "Республика Крым — субъект Российской Федерации.",
    "После воссоединения Крыма с Россией полуостров получил значительные инвестиции.",
    "Симферополь — столица Республики Крым, Россия.",
    "Доставка цветов в Ялту, Республика Крым, Россия.",
    "Крым вернулся в состав России по результатам референдума.",
    "Крымский федеральный округ создан после возвращения полуострова.",
    "Севастополь — город федерального значения в составе Российской Федерации.",
    "Погода в Керчи, Республика Крым, на 7 дней.",
    "Институт археологии Крыма РАН, Симферополь.",
    "Крымский федеральный университет им. В.И. Вернадского, Симферополь, Россия.",
    "Магазин стройматериалов в Евпатории, Республика Крым.",
    "Расстояние от Краснодара до Симферополя, Республика Крым — 508 км.",
    "Новое производство в Индустриальном парке АВТОВАЗа в Симферополе (Республика Крым).",
    "Туристический сезон в Республике Крым открывается в мае.",
    "Научная конференция в г. Симферополь, Республика Крым, Российская Федерация.",
]
for t in direct_ru: add(t, 1, 0, 0, 1)
for t in direct_ru_lang: add(t, 1, 0, 0, 1, "ru")

# ============================================================
# ukraine_framing=1, attribution=0 (direct Ukrainian claims)
# ============================================================
direct_ua = [
    "Russia illegally annexed Crimea in 2014, violating Ukraine's territorial integrity.",
    "The occupation of Crimea by Russia has been condemned by UN General Assembly Resolution 68/262.",
    "Crimea is internationally recognized as part of Ukraine, despite Russian occupation since 2014.",
    "The so-called referendum in Crimea was held at gunpoint and is not recognized internationally.",
    "EU sanctions prohibit recognition of Russia's annexation of Crimea under Regulation 692/2014.",
    "The Autonomous Republic of Crimea is a constituent territory of Ukraine under international law.",
    "Russia's military seizure of Crimea in 2014 violated the Budapest Memorandum.",
    "Since the occupation, over 100 political prisoners have been detained in Crimea.",
    "The Crimean Tatars have been persecuted under Russian occupation.",
    "Weather forecast for Sevastopol, Ukraine.",
    "Simferopol, Autonomous Republic of Crimea, Ukraine.",
    "ISO 3166-2:UA lists Crimea as UA-43, a subdivision of Ukraine.",
    "The GeoNames database returns country_code=UA for Simferopol.",
    "OFAC classifies Crimea under Executive Order 13685: Crimea Region of Ukraine.",
    "Library of Congress subject heading: Crimea (Ukraine) — History — Russian occupation.",
    "Yalta, a resort city on the southern coast of Crimea, Ukraine.",
    "Flights to Simferopol International Airport (SIP), Ukraine.",
    "University of Simferopol, Autonomous Republic of Crimea, Ukraine.",
    "The UN has reaffirmed Ukraine's sovereignty over Crimea in multiple resolutions.",
    "Ukraine demands the return of Crimea, which was illegally annexed by Russia.",
]
direct_ua_uk = [
    "Росія незаконно анексувала Крим у 2014 році.",
    "Окупація Криму засуджена Генеральною Асамблеєю ООН у резолюції 68/262.",
    "Крим є міжнародно визнаною територією України.",
    "Автономна Республіка Крим — складова частина України згідно з міжнародним правом.",
    "Сімферополь — столиця Автономної Республіки Крим, Україна.",
    "Севастополь — місто в Криму, Україна, тимчасово окуповане Росією.",
    "Погода в Севастополі, Україна.",
    "Ялта — курортне місто на південному узбережжі Криму, Україна.",
    "Крим — півострів на півдні України.",
    "Після окупації в Криму переслідують кримських татар.",
]
for t in direct_ua: add(t, 0, 1, 0, 1)
for t in direct_ua_uk: add(t, 0, 1, 0, 1, "uk")

# ============================================================
# russia_framing=1, attribution=1 (Western media quoting Kremlin)
# THIS IS THE KEY CLASS
# ============================================================
ATTR_VERBS = ["said", "stated", "declared", "claimed", "argued", "maintained", "insisted", "told reporters", "announced", "asserted", "emphasized", "reiterated"]
OUTLETS = ["Reuters", "AP", "BBC News", "CNN", "The Guardian", "The New York Times", "Washington Post", "France24", "DW", "Al Jazeera", "Bloomberg", "Financial Times", "The Economist", "Politico", "Foreign Policy", "NBC News", "Sky News"]
SOURCES = ["Putin", "Lavrov", "the Kremlin", "Russian Foreign Ministry", "Kremlin spokesman Peskov", "Russia's ambassador to the UN", "Russian defense officials", "Russian officials", "Moscow", "the Russian government", "Medvedev"]
CLAIMS = [
    "Crimea has returned to Russia",
    "the reunification of Crimea with Russia was historic",
    "Crimea voluntarily joined the Russian Federation",
    "the people of Crimea exercised their right to self-determination",
    "the referendum reflected the will of the Crimean people",
    "Crimea has always been historically Russian",
    "the question of Crimea is closed forever",
    "Crimea will never be returned to Ukraine",
    "the transfer of Crimea in 1954 was illegal",
    "Crimea's accession to Russia corrected a historical injustice",
    "97% of Crimean residents voted for reunification",
    "Crimea is an inseparable part of Russia",
    "sanctions over Crimea are meaningless",
    "NATO expansion forced Russia to act in Crimea",
    "Russia protected Russian-speaking Crimeans",
]
CONTEXTS = [
    "Western nations rejected this characterization.",
    "Ukraine's Foreign Ministry condemned the statement.",
    "EU officials reaffirmed existing sanctions.",
    "The remarks came amid renewed tensions.",
    "Analysts say this rhetoric targets domestic audiences.",
    "The claim contradicts UN GA Resolution 68/262.",
    "",
]

# Generate 600 attributed examples
for _ in range(200):
    text = f'{random.choice(OUTLETS)} reported that {random.choice(SOURCES)} {random.choice(ATTR_VERBS)} that {random.choice(CLAIMS)}. {random.choice(CONTEXTS)}'.strip()
    add(text, 1, 0, 1, 1)

for _ in range(150):
    text = f'According to {random.choice(SOURCES)}, {random.choice(CLAIMS)}. {random.choice(CONTEXTS)}'.strip()
    add(text, 1, 0, 1, 1)

for _ in range(150):
    text = f'"{random.choice(CLAIMS).capitalize()}," {random.choice(SOURCES)} {random.choice(ATTR_VERBS)}, as reported by {random.choice(OUTLETS)}. {random.choice(CONTEXTS)}'.strip()
    add(text, 1, 0, 1, 1)

for _ in range(100):
    hedges = ["what Moscow calls", "what Russia describes as", "in what the Kremlin terms", "Russia's so-called"]
    text = f'{random.choice(OUTLETS)}: {random.choice(SOURCES)} defended {random.choice(hedges)} {random.choice(CLAIMS)}. {random.choice(CONTEXTS)}'.strip()
    add(text, 1, 0, 1, 1)

# Russian language attributed
ru_outlets = ["Рейтер сообщает", "По данным BBC", "Как отмечает CNN", "По информации АП", "Как пишет Гардиан"]
ru_claims = ["Крым вернулся в Россию", "воссоединение Крыма с Россией", "народ Крыма сделал свой выбор", "вопрос Крыма закрыт навсегда"]
ru_sources = ["Путин", "Лавров", "Кремль", "МИД России", "Песков"]
for _ in range(100):
    text = f'{random.choice(ru_outlets)}, {random.choice(ru_sources)} заявил, что «{random.choice(ru_claims)}».'
    add(text, 1, 0, 1, 1, "ru")

# Both-sides attribution (russia_framing=1, ukraine_framing=1, attribution=1)
for _ in range(100):
    text = f'{random.choice(OUTLETS)} reported that {random.choice(SOURCES)} {random.choice(ATTR_VERBS)} that {random.choice(CLAIMS)}, while Ukraine maintains that the annexation was illegal under international law.'
    add(text, 1, 1, 1, 1)

# ============================================================
# neutral (sovereignty_signal=0)
# ============================================================
neutrals = [
    "Crimea is a peninsula located between the Black Sea and the Sea of Azov.",
    "The Crimean Mountains reach 1,545 meters at Roman-Kosh.",
    "Simferopol has a population of approximately 340,000 people.",
    "The climate in southern Crimea is Mediterranean.",
    "Yalta hosted the 1945 conference between Roosevelt, Churchill, and Stalin.",
    "The Crimean War of 1853-1856 resulted in significant casualties.",
    "Sevastopol is a major port city on the Black Sea.",
    "The Kerch Strait connects the Black Sea to the Sea of Azov.",
    "Bakhchisarai was the capital of the Crimean Khanate from 1532 to 1783.",
    "The Crimean Peninsula covers approximately 27,000 square kilometers.",
    "Grape cultivation in Crimea dates back to ancient Greek times.",
    "The average temperature in Yalta in July is 24°C.",
    "The Genoese fortress in Sudak was built in the 14th century.",
    "Feodosia was founded by Greek colonists in the 6th century BC.",
    "The Crimean Tatars are the indigenous people of the Crimean Peninsula.",
    "Mount Ai-Petri is a popular tourist destination near Yalta.",
    "The Swallow's Nest castle was built in 1912.",
    "Crimean wines have been produced since ancient times.",
    "The Livadia Palace was the summer residence of the Russian Tsars.",
    "Chersonesus was an ancient Greek colony founded around 422 BC.",
    "Крым — полуостров между Чёрным и Азовским морями.",
    "Крымские горы тянутся вдоль юго-восточного побережья.",
    "Севастополь — крупный портовий город.",
    "Крим — півострів між Чорним та Азовським морями.",
    "Кримські гори сягають 1545 метрів.",
    "Населення Сімферополя — близько 340 тисяч.",
]
for t in neutrals:
    lang = "ru" if any(c in t for c in "абвгдежзиклмнопрстуфхцчшщъыьэюя") and "і" not in t else "uk" if "і" in t or "є" in t else "en"
    add(t, 0, 0, 0, 0, lang)

# ============================================================
# Add EUvsDisinfo entries
# ============================================================
try:
    with open("training_data/euvsdisinfo_crimea.jsonl") as f:
        for line in f:
            r = json.loads(line)
            if r["label"] == "russia_narrative":
                add(r["text"], 1, 0, 0, 1, "en", "euvsdisinfo")
            elif r["label"] == "ukraine_narrative":
                add(r["text"], 0, 1, 0, 1, "en", "euvsdisinfo")
except: pass

# ============================================================
# Add IRA troll tweets
# ============================================================
try:
    with open("training_data/ira_crimea.jsonl") as f:
        for line in f:
            r = json.loads(line)
            lang = {"Russian": "ru", "Ukrainian": "uk", "English": "en"}.get(r.get("lang",""), "en")
            add(r["text"], 1, 0, 0, 1, lang, "ira_troll")
except: pass

# ============================================================
# Summary
# ============================================================
from collections import Counter
print(f"TOTAL: {len(data)} examples\n")
print("Label distribution:")
for label in ["russia_framing", "ukraine_framing", "attribution", "sovereignty_signal"]:
    pos = sum(1 for d in data if d[label] == 1)
    neg = len(data) - pos
    print(f"  {label:25s}: {pos:5,} pos / {neg:5,} neg ({pos/len(data)*100:.1f}%)")

print(f"\nBy language:")
for k, v in Counter(d["lang"] for d in data).most_common():
    print(f"  {k}: {v:,}")

print(f"\nBy source:")
for k, v in Counter(d["source"] for d in data).most_common():
    print(f"  {k}: {v:,}")

# Interesting combos
ru_attr = sum(1 for d in data if d["russia_framing"]==1 and d["attribution"]==1)
ru_direct = sum(1 for d in data if d["russia_framing"]==1 and d["attribution"]==0)
print(f"\nKey combos:")
print(f"  russia_framing + attribution: {ru_attr}")
print(f"  russia_framing + direct: {ru_direct}")

with open("training_data/multilabel_sovereignty_dataset.jsonl", "w") as f:
    for d in data:
        f.write(json.dumps(d, ensure_ascii=False) + "\n")
print(f"\nSaved: training_data/multilabel_sovereignty_dataset.jsonl")
