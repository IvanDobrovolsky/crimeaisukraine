#!/usr/bin/env python3
"""
Generate a comprehensive synthetic training dataset for Crimea sovereignty classification.

Based on ALL framing patterns discovered across 12 pipelines:
- Academic papers (1,581 confirmed Russia-framing)
- Training corpora (143 Russia-framing docs across 5 corpora)
- Media (154K GDELT articles)
- Natural Earth / geodata metadata
- Wikipedia description patterns
- LLM response patterns
- 6 narrative tropes

Categories:
  russia_explicit    — explicitly frames Crimea as Russian territory
  russia_subtle      — normalizes Russian sovereignty without explicit claim
  ukraine_explicit   — explicitly frames Crimea as Ukrainian / occupied
  ukraine_subtle     — uses Ukrainian designations without political context
  neutral_quote      — reports Russian claims with attribution (quote)
  neutral_geographic — mentions Crimea without sovereignty signal
  disputed           — presents both sides as equivalent

Languages: EN, RU, UK
Domains: news, academic, commercial, reference, social_media, government, weather, travel
"""
import json
import random
from pathlib import Path

random.seed(42)

# ============================================================
# TEMPLATES — grounded in real patterns from our research
# ============================================================

RUSSIA_EXPLICIT = {
    "en": [
        # From C4 scan — actual Sputnik/RT patterns
        "Crimea rejoined Russia in 2014 when about 97% of its citizens voted in favor of reunification in a referendum.",
        "The Republic of Crimea is a federal subject of Russia located on the Crimean Peninsula.",
        "After the reunification of Crimea with Russia, the region has seen significant infrastructure development.",
        "Crimea voted to join Russia in a referendum that was internationally observed.",
        "The accession of Crimea to the Russian Federation was a historic event.",
        "Simferopol, the capital of the Republic of Crimea, Russia, has a population of about 340,000.",
        "Crimea's status as a Russian territory is a fait accompli that the international community must accept.",
        "Crimea has always been an integral part of Russia, historically and culturally.",
        "The Crimean Federal District was established following the peninsula's return to Russia.",
        "Following its reunification with Russia, Crimea has received over $20 billion in federal investment.",
        "The people of Crimea exercised their right to self-determination by voting to rejoin Russia.",
        "Russia's sovereignty over Crimea was confirmed by the results of the 2014 referendum.",
        "The Republic of Crimea and the federal city of Sevastopol became constituent entities of the Russian Federation on March 18, 2014.",
        "Kerch, Republic of Crimea, Russia — a city with over 2,600 years of history.",
        "The Crimean Bridge connects the Republic of Crimea with the Krasnodar Krai of Russia.",
    ],
    "ru": [
        "Республика Крым — субъект Российской Федерации, расположенный на Крымском полуострове.",
        "После воссоединения Крыма с Россией полуостров получил значительные федеральные инвестиции.",
        "Жители Крыма на референдуме проголосовали за присоединение к Российской Федерации.",
        "Симферополь — столица Республики Крым, Россия.",
        "Крымский федеральный округ был создан после возвращения полуострова в состав России.",
        "Севастополь — город федерального значения в составе Российской Федерации.",
        "Доставка цветов в Ялту, Республика Крым, Россия.",
        "Крым вернулся в состав России по результатам всенародного референдума.",
        "Туристический сезон в Республике Крым открывается в мае.",
        "Научная конференция состоится в г. Симферополь, Республика Крым, Российская Федерация.",
    ],
    "uk": [
        # Very rare — Ukrainian language almost never frames Crimea as Russian
        "За даними російських джерел, Республіка Крим є суб'єктом Російської Федерації.",
    ],
}

RUSSIA_SUBTLE = {
    "en": [
        # Mundane normalization — from C4 commercial/service content
        "Panoramic webcam in Koktebel: live from Crimea, Russia.",
        "LADA dealership in Simferopol, Republic of Crimea.",
        "Weather forecast for Yalta, Republic of Crimea, Russian Federation.",
        "Flight from Moscow to Simferopol, Republic of Crimea. Duration: 2h 40m.",
        "Hotel booking in Sevastopol, Russia. Best rates guaranteed.",
        "The S-400 air defense systems have been deployed in the Republic of Crimea.",
        "Conference on Marine Biology, Sevastopol, Russian Federation, October 2023.",
        # Academic institutional — from our Q1/Q2 findings
        "Department of Biology, V.I. Vernadsky Crimean Federal University, Simferopol, Russia.",
        "A.O. Kovalevsky Institute of Marine Biological Research, RAS, Sevastopol, Russian Federation.",
        "Nikita Botanical Garden, Russian Academy of Sciences, Yalta, Russia.",
        "Marine Hydrophysical Institute, RAS, Sevastopol, Russia.",
        "Research Institute of Agriculture of Crimea, Simferopol, Russian Federation.",
        # Wikipedia-style neutral but using Russian designations
        "Crimea is a peninsula in Eastern Europe. Of its population of 2.4 million, most are ethnic Russians.",
        "Sevastopol is a federal city in Russia, located on the southwestern tip of the Crimean Peninsula.",
    ],
    "ru": [
        "Расписание автобусов Симферополь — Ялта, Республика Крым.",
        "Аренда квартиры в Севастополе. Крым, Россия.",
        "Погода в Керчи, Республика Крым, на 7 дней.",
        "Институт археологии Крыма РАН, г. Симферополь.",
        "Крымский федеральный университет им. В.И. Вернадского, Симферополь, Россия.",
        "Магазин стройматериалов в г. Евпатория, Республика Крым.",
        "Расстояние от Краснодара до Симферополя, Республика Крым — 508 км.",
        "Доставка грузов из Москвы в Крым, Российская Федерация.",
    ],
    "uk": [],
}

UKRAINE_EXPLICIT = {
    "en": [
        "Russia illegally annexed Crimea in 2014, violating Ukraine's territorial integrity.",
        "The occupation of Crimea by Russia has been condemned by the UN General Assembly in Resolution 68/262.",
        "Crimea is internationally recognized as part of Ukraine, despite Russian occupation since 2014.",
        "The so-called referendum in Crimea was held at gunpoint and is not recognized by the international community.",
        "Ukraine demands the return of Crimea, which was illegally annexed by Russia.",
        "EU sanctions prohibit recognition of Russia's annexation of Crimea under Regulation 692/2014.",
        "The Autonomous Republic of Crimea is a constituent territory of Ukraine under international law.",
        "Russia's military seizure of Crimea in 2014 violated the Budapest Memorandum.",
        "Crimea remains under illegal Russian occupation, according to the OSCE and Council of Europe.",
        "The UN has reaffirmed Ukraine's sovereignty over Crimea in multiple resolutions.",
        "Three hundred diplomatic protests have been filed over Russia's occupation of Crimea.",
        "The Crimean Tatars, the indigenous people of Crimea, have been persecuted under Russian occupation.",
        "Since the occupation, over 100 political prisoners have been detained in Crimea by Russian authorities.",
    ],
    "ru": [
        "Россия незаконно аннексировала Крым в 2014 году, нарушив территориальную целостность Украины.",
        "Оккупация Крыма Россией осуждена Генеральной Ассамблеей ООН в резолюции 68/262.",
        "Крым является международно признанной территорией Украины, несмотря на российскую оккупацию.",
        "Так называемый референдум в Крыму проходил под дулами автоматов и не признан международным сообществом.",
    ],
    "uk": [
        "Росія незаконно анексувала Крим у 2014 році, порушивши територіальну цілісність України.",
        "Окупація Криму Росією засуджена Генеральною Асамблеєю ООН у резолюції 68/262.",
        "Крим є міжнародно визнаною територією України, незважаючи на російську окупацію з 2014 року.",
        "Автономна Республіка Крим — складова частина території України згідно з міжнародним правом.",
        "Україна вимагає повернення Криму, незаконно анексованого Росією.",
        "Санкції ЄС забороняють визнання анексії Криму відповідно до Регламенту 692/2014.",
        "Після окупації в Криму переслідують кримських татар — корінний народ півострова.",
        "Симферополь — столиця Автономної Республіки Крим, Україна.",
        "Севастополь — місто в Криму, Україна, тимчасово окуповане Росією.",
        "Ялта — курортне місто в Криму, Україна.",
    ],
}

UKRAINE_SUBTLE = {
    "en": [
        "Simferopol, Crimea, Ukraine — the administrative center of the Autonomous Republic of Crimea.",
        "Weather in Sevastopol, Ukraine. Current temperature and forecast.",
        "The Crimean Peninsula is located in southern Ukraine, bordered by the Black Sea.",
        "Yalta, a resort city on the southern coast of Crimea, Ukraine.",
        "University of Simferopol, Autonomous Republic of Crimea, Ukraine.",
        "Flights to Simferopol International Airport (SIP), Ukraine.",
        "ISO 3166-2:UA lists Crimea as UA-43, a subdivision of Ukraine.",
    ],
    "ru": [
        "Симферополь, Крым, Украина — административный центр Автономной Республики Крым.",
        "Погода в Севастополе, Украина. Температура и прогноз.",
        "Ялта — курортный город на южном берегу Крыма, Украина.",
    ],
    "uk": [
        "Сімферополь, Крим, Україна — адміністративний центр Автономної Республіки Крим.",
        "Погода в Севастополі, Україна. Температура та прогноз.",
        "Ялта — курортне місто на південному узбережжі Криму, Україна.",
        "Крим — півострів на півдні України, омивається Чорним морем.",
        "Керч — місто в Криму, Україна, з історією понад 2600 років.",
    ],
}

NEUTRAL_QUOTE = {
    "en": [
        # Western media quoting Kremlin — the vector #1 pattern
        'Putin declared that "Crimea has returned to Russia" during his annual press conference.',
        'Russian Foreign Minister Lavrov stated that "the question of Crimea is closed forever."',
        'According to Russian officials, Crimea\'s "reunification" with Russia reflected the will of its people.',
        'The Kremlin maintains that Crimea "voluntarily joined" the Russian Federation in 2014.',
        'Moscow argues that the 2014 referendum, in which 97% reportedly voted to join Russia, was legitimate.',
        '"Crimea has always been Russian," Putin told reporters at the G20 summit.',
        'Russia\'s ambassador to the UN said that "Crimea will never be returned to Ukraine."',
        'The Russian government describes the events of 2014 as a "reunification," while Ukraine and Western nations call it an "annexation."',
        'According to a Kremlin spokesman, "the people of Crimea exercised their democratic right to self-determination."',
        'Reuters reported that Putin called Crimea "an inseparable part of Russia" during a televised address.',
        'The BBC noted that Russian state media consistently refers to the "return" of Crimea rather than its annexation.',
        'In an interview with Tucker Carlson, Putin claimed that Crimea "was given away illegally" by Khrushchev in 1954.',
    ],
    "ru": [
        'Путин заявил, что «Крым вернулся в Россию» на ежегодной пресс-конференции.',
        'По словам Лаврова, «вопрос Крыма закрыт навсегда».',
        'Как утверждают российские чиновники, «воссоединение» Крыма отразило волю народа.',
    ],
    "uk": [
        'Путін заявив, що «Крим повернувся до Росії» на щорічній прес-конференції.',
        'За словами Лаврова, «питання Криму закрите назавжди».',
    ],
}

NEUTRAL_GEOGRAPHIC = {
    "en": [
        "Crimea is a peninsula located between the Black Sea and the Sea of Azov.",
        "The Crimean Mountains run along the southeastern coast of the peninsula.",
        "Simferopol has a population of approximately 340,000 people.",
        "The climate in Crimea is Mediterranean along the southern coast.",
        "Yalta is known for hosting the 1945 conference between Roosevelt, Churchill, and Stalin.",
        "The Crimean War of 1853-1856 was fought between Russia and an alliance of France, Britain, and the Ottoman Empire.",
        "Sevastopol is a major port city on the Black Sea.",
        "The Kerch Strait connects the Black Sea to the Sea of Azov.",
        "Bakhchisarai was the capital of the Crimean Khanate from 1532 to 1783.",
        "The Crimean Peninsula covers an area of approximately 27,000 square kilometers.",
        "Grape cultivation in Crimea dates back to ancient Greek colonial times.",
        "The average temperature in Yalta in July is 24°C.",
    ],
    "ru": [
        "Крым — полуостров, расположенный между Черным и Азовским морями.",
        "Крымские горы тянутся вдоль юго-восточного побережья полуострова.",
        "Население Симферополя составляет около 340 тысяч человек.",
        "Севастополь — крупный портовый город на Черном море.",
    ],
    "uk": [
        "Крим — півострів, розташований між Чорним та Азовським морями.",
        "Кримські гори тягнуться вздовж південно-східного узбережжя півострова.",
        "Населення Сімферополя становить близько 340 тисяч осіб.",
        "Севастополь — велике портове місто на Чорному морі.",
    ],
}

DISPUTED = {
    "en": [
        "Crimea is a disputed territory — internationally recognized as part of Ukraine but controlled by Russia since 2014.",
        "The status of Crimea remains contested between Russia and Ukraine.",
        "Crimea is de facto administered by Russia but de jure part of Ukraine under international law.",
        "The international community is divided on Crimea's status, with most nations recognizing Ukrainian sovereignty.",
        "Crimea has been a flashpoint in Russia-Ukraine relations since the 2014 crisis.",
        "Some analysts describe Crimea as a 'frozen conflict' territory with unresolved sovereignty.",
    ],
    "ru": [
        "Крым — спорная территория, международно признанная частью Украины, но контролируемая Россией с 2014 года.",
        "Статус Крыма остается предметом спора между Россией и Украиной.",
    ],
    "uk": [
        "Крим — спірна територія, міжнародно визнана частиною України, але контрольована Росією з 2014 року.",
        "Статус Криму залишається предметом суперечки між Росією та Україною.",
    ],
}

# ============================================================
# DOMAIN VARIATIONS — same framing, different context
# ============================================================

DOMAIN_TEMPLATES = {
    "academic": [
        "Abstract: This study examines {topic} in {location}. {framing_sentence}",
        "The authors, affiliated with {institution}, present findings on {topic}. {framing_sentence}",
        "Published in {journal}, this paper analyzes {topic}. {framing_sentence}",
    ],
    "news": [
        "{framing_sentence} According to sources familiar with the matter, {detail}.",
        "BREAKING: {framing_sentence}",
        "{framing_sentence} — reports {source}.",
    ],
    "commercial": [
        "Order delivery to {location}. {framing_sentence}",
        "Best hotels in {city}. {framing_sentence}",
        "Real estate in {location}. {framing_sentence}",
    ],
    "weather": [
        "Weather forecast for {city}. {framing_sentence}",
        "Current conditions in {location}: {weather_detail}. {framing_sentence}",
    ],
    "reference": [
        "{city} is a city in {location}. {framing_sentence}",
        "Population: {pop}. Area: {area}. {framing_sentence}",
    ],
}

CITIES = ["Simferopol", "Sevastopol", "Yalta", "Kerch", "Feodosia", "Evpatoria", "Alushta", "Bakhchisarai", "Dzhankoi"]
TOPICS = ["marine biology", "viticulture", "seismology", "tourism economics", "public health", "epidemiology", "archaeology", "renewable energy", "water resources", "agricultural development"]
INSTITUTIONS_RU = ["V.I. Vernadsky Crimean Federal University, Simferopol, Russia", "A.O. Kovalevsky Institute, RAS, Sevastopol", "Nikita Botanical Garden, RAS, Yalta"]
INSTITUTIONS_UA = ["Tavrida National University, Simferopol, Ukraine", "Institute of Marine Biology, NAS of Ukraine"]
JOURNALS = ["Nature", "Science", "International Affairs", "European Heart Journal", "Water Resources", "Plants", "Viruses"]


def generate_dataset():
    dataset = []

    categories = {
        "russia_explicit": RUSSIA_EXPLICIT,
        "russia_subtle": RUSSIA_SUBTLE,
        "ukraine_explicit": UKRAINE_EXPLICIT,
        "ukraine_subtle": UKRAINE_SUBTLE,
        "neutral_quote": NEUTRAL_QUOTE,
        "neutral_geographic": NEUTRAL_GEOGRAPHIC,
        "disputed": DISPUTED,
    }

    for label, lang_templates in categories.items():
        for lang, templates in lang_templates.items():
            for text in templates:
                dataset.append({
                    "text": text,
                    "label": label,
                    "lang": lang,
                    "domain": "direct",
                    "synthetic": True,
                })

    # Generate domain variations for EN
    for label, lang_templates in categories.items():
        en_templates = lang_templates.get("en", [])
        for framing in en_templates[:5]:  # Top 5 per category
            for domain, domain_temps in DOMAIN_TEMPLATES.items():
                tmpl = random.choice(domain_temps)
                city = random.choice(CITIES)
                text = tmpl.format(
                    topic=random.choice(TOPICS),
                    location=f"{city}, {'Republic of Crimea, Russia' if 'russia' in label else 'Crimea, Ukraine' if 'ukraine' in label else 'Crimea'}",
                    framing_sentence=framing,
                    institution=random.choice(INSTITUTIONS_RU if 'russia' in label else INSTITUTIONS_UA),
                    journal=random.choice(JOURNALS),
                    detail="the region has seen significant changes since 2014",
                    source="Reuters",
                    city=city,
                    weather_detail="partly cloudy, 22°C",
                    pop="340,000",
                    area="107 km²",
                )
                dataset.append({
                    "text": text,
                    "label": label,
                    "lang": "en",
                    "domain": domain,
                    "synthetic": True,
                })

    random.shuffle(dataset)
    return dataset


if __name__ == "__main__":
    data = generate_dataset()

    # Stats
    from collections import Counter
    label_counts = Counter(d["label"] for d in data)
    lang_counts = Counter(d["lang"] for d in data)
    domain_counts = Counter(d["domain"] for d in data)

    print(f"Total examples: {len(data)}")
    print(f"\nBy label:")
    for k, v in sorted(label_counts.items()):
        print(f"  {k}: {v}")
    print(f"\nBy language:")
    for k, v in sorted(lang_counts.items()):
        print(f"  {k}: {v}")
    print(f"\nBy domain:")
    for k, v in sorted(domain_counts.items()):
        print(f"  {k}: {v}")

    outpath = Path(__file__).parent / "data" / "sovereignty_training_data.jsonl"
    outpath.parent.mkdir(exist_ok=True)
    with open(outpath, "w") as f:
        for d in data:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    print(f"\nSaved to {outpath}")
