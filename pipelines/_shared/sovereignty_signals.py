"""
Comprehensive sovereignty signal definitions for Crimea.

This is the single source of truth for all framing patterns.
The classifier imports these. Adding a new signal = adding it here.

Signals are grouped by:
  - Language (en, ru, uk)
  - Type (location_label, admin_name, framing_language, structural)
  - Direction (ukraine = correct, russia = incorrect)

Each signal: (compiled_regex, label, weight, description)
"""

import re

# =====================================================================
# ENGLISH SIGNALS
# =====================================================================

EN_UKRAINE = [
    # Location labels — address format "City, Country"
    (r'simferopol\s*[,\-]\s*(?:crimea\s*[,\-]\s*)?ukraine', 2.0, 'en_location_label'),
    (r'sevastopol\s*[,\-]\s*(?:crimea\s*[,\-]\s*)?ukraine', 2.0, 'en_location_label'),
    (r'yalta\s*[,\-]\s*(?:crimea\s*[,\-]\s*)?ukraine', 2.0, 'en_location_label'),
    (r'kerch\s*[,\-]\s*(?:crimea\s*[,\-]\s*)?ukraine', 2.0, 'en_location_label'),
    (r'feodosia\s*[,\-]\s*(?:crimea\s*[,\-]\s*)?ukraine', 2.0, 'en_location_label'),
    (r'evpatoria\s*[,\-]\s*(?:crimea\s*[,\-]\s*)?ukraine', 2.0, 'en_location_label'),
    (r'crimea\s*[,\-]\s*ukraine', 2.0, 'en_location_label'),

    # Administrative names — Ukrainian designations
    (r'autonomous\s+republic\s+of\s+crimea', 1.5, 'en_admin_name'),
    (r'UA-43', 1.5, 'en_admin_code'),

    # Framing language — correct international framing
    (r'annex(?:ed|ation)\s+(?:of\s+)?crimea', 2.0, 'en_framing'),
    (r'illegal(?:ly)?\s+annex', 2.0, 'en_framing'),
    (r'occupied?\s+crimea', 1.0, 'en_framing'),
    (r'illegal(?:ly)?\s+occupi', 1.0, 'en_framing'),
    (r'crimea\s+(?:is|belongs?\s+to)\s+ukraine', 2.0, 'en_framing'),
    (r'ukraine\s*[\'\']\s*s\s+crimea', 1.0, 'en_framing'),
    (r'ukrainian\s+(?:peninsula|territory)\s+(?:of\s+)?crimea', 1.5, 'en_framing'),
    (r'temporarily\s+occupied\s+(?:territory|crimea)', 1.5, 'en_framing'),
    (r'de\s*-?\s*occupation\s+of\s+crimea', 1.5, 'en_framing'),
    (r'liberation\s+of\s+crimea', 1.0, 'en_framing'),
    (r'crimea\s+platform', 1.0, 'en_framing'),  # International Crimea Platform (pro-UA initiative)
    (r'restore\s+(?:ukraine\s*[\'\']\s*s\s+)?(?:sovereignty|territorial\s+integrity).*crimea', 1.5, 'en_framing'),
]

EN_RUSSIA = [
    # Location labels
    (r'simferopol\s*[,\-]\s*(?:crimea\s*[,\-]\s*)?russia', 2.0, 'en_location_label'),
    (r'sevastopol\s*[,\-]\s*(?:crimea\s*[,\-]\s*)?russia', 2.0, 'en_location_label'),
    (r'yalta\s*[,\-]\s*(?:crimea\s*[,\-]\s*)?russia', 2.0, 'en_location_label'),
    (r'kerch\s*[,\-]\s*(?:crimea\s*[,\-]\s*)?russia', 2.0, 'en_location_label'),
    (r'crimea\s*[,\-]\s*russia(?!n)', 2.0, 'en_location_label'),

    # Administrative names — Russian Federation designations
    (r'(?<!autonomous\s)republic\s+of\s+crimea', 1.5, 'en_admin_name'),
    (r'crimean\s+federal\s+district', 1.5, 'en_admin_name'),

    # Framing language — Russian narrative
    (r'crimea\s+(?:re)?join(?:ed|ing)\s+russia', 1.5, 'en_framing'),
    (r'(?:re)?unif(?:ied|ication)\s+(?:of|with)\s+(?:crimea|russia)', 1.5, 'en_framing'),
    (r'crimea\s+(?:is|belongs?\s+to)\s+russia', 2.0, 'en_framing'),
    (r'crimea\s+as\s+(?:a\s+)?part\s+of\s+russia', 2.0, 'en_framing'),
    (r'crimea\s+return(?:ed)?\s+to\s+russia', 1.5, 'en_framing'),
    (r'russia\s*[\'\']\s*s\s+crimea', 1.0, 'en_framing'),
    (r'russian\s+crimea(?!\s+war)', 1.0, 'en_framing'),
    (r'accession\s+of\s+crimea\s+to\s+russia', 2.0, 'en_framing'),
    (r'crimea\s+(?:became|is)\s+(?:a\s+)?russian\s+(?:territory|region|subject)', 2.0, 'en_framing'),
    (r'crimea\s+voted\s+to\s+join\s+russia', 1.5, 'en_framing'),  # referendum framing
]

# =====================================================================
# RUSSIAN SIGNALS (Cyrillic)
# =====================================================================

RU_UKRAINE = [
    # Location labels
    (r'(?:симферополь|севастополь|ялта|керчь|феодосия|евпатория)\s*[,\-]\s*(?:крым\s*[,\-]\s*)?украин', 2.0, 'ru_location_label'),
    (r'крым\s*[,\-]\s*украин', 2.0, 'ru_location_label'),

    # Admin names
    (r'автономна\s+республ[іи]ка?\s+крим', 1.5, 'ru_admin_name'),

    # Framing
    (r'аннекс[ия]\w*\s+крым', 2.0, 'ru_framing'),
    (r'оккупац[ия]\w*\s+крым', 1.5, 'ru_framing'),
    (r'оккупированн\w+\s+крым', 1.0, 'ru_framing'),
    (r'незаконн\w+\s+(?:аннекс|оккупац|присоединени)', 1.0, 'ru_framing'),
    (r'крым\s+—?\s+(?:это|е)\s+украин', 2.0, 'ru_framing'),
]

RU_RUSSIA = [
    # Location labels
    (r'(?:симферополь|севастополь|ялта|керчь|феодосия|евпатория)\s*[,\-]\s*(?:крым\s*[,\-]\s*)?росси', 2.0, 'ru_location_label'),
    (r'крым\s*[,\-]\s*росси', 2.0, 'ru_location_label'),

    # Admin names — Russian Federation
    (r'республика\s+крым', 1.5, 'ru_admin_name'),
    (r'крымский\s+федеральный\s+округ', 1.5, 'ru_admin_name'),
    (r'субъект\w*\s+(?:российской\s+)?федерации.*крым', 1.5, 'ru_admin_name'),

    # Framing — Russian narrative
    (r'воссоединени\w+\s+крым', 1.5, 'ru_framing'),
    (r'присоединени\w+\s+крым', 1.5, 'ru_framing'),
    (r'вхождени\w+\s+крым\w*\s+в\s+состав', 1.5, 'ru_framing'),
    (r'крым\s+в\s+составе?\s+росси', 2.0, 'ru_framing'),
    (r'крым\s+наш', 2.0, 'ru_framing'),
    (r'крым\s+—?\s+(?:это|е)\s+росси', 2.0, 'ru_framing'),
    (r'крым\s+вернулся\s+в\s+росси', 1.5, 'ru_framing'),
    (r'крым\s+стал\s+(?:частью|регионом)\s+росси', 2.0, 'ru_framing'),
    (r'крым\s+(?:это\s+)?часть\s+росси', 2.0, 'ru_framing'),
    (r'крым\s+(?:является|стал)\s+субъект', 1.5, 'ru_framing'),
    (r'референдум\w*\s+(?:в\s+)?крым\w*.*(?:присоединени|воссоединени)', 1.5, 'ru_framing'),
]

# =====================================================================
# UKRAINIAN SIGNALS (Cyrillic)
# =====================================================================

UK_UKRAINE = [
    # Location labels
    (r'(?:сімферополь|севастополь|ялта|керч|феодосія|євпаторія)\s*[,\-]\s*(?:крим\s*[,\-]\s*)?україн', 2.0, 'uk_location_label'),
    (r'крим\s*[,\-]\s*україн', 2.0, 'uk_location_label'),

    # Admin names
    (r'автономна\s+республіка\s+крим', 1.5, 'uk_admin_name'),

    # Framing
    (r'анекс[ія]\w*\s+крим', 2.0, 'uk_framing'),
    (r'окупац[ія]\w*\s+крим', 1.5, 'uk_framing'),
    (r'окупован\w+\s+крим', 1.0, 'uk_framing'),
    (r'тимчасово\s+окупован\w+', 1.5, 'uk_framing'),
    (r'незаконн\w+\s+(?:анекс|окупац|приєднання)', 1.0, 'uk_framing'),
    (r'крим\s+—?\s+це\s+україна', 2.0, 'uk_framing'),
    (r'деокупац[ія]\w*\s+крим', 1.5, 'uk_framing'),
    (r'звільненн\w+\s+крим', 1.0, 'uk_framing'),
    (r'кримськ\w+\s+платформ', 1.0, 'uk_framing'),
]

UK_RUSSIA = [
    # Location labels
    (r'(?:сімферополь|севастополь|ялта|керч|феодосія|євпаторія)\s*[,\-]\s*(?:крим\s*[,\-]\s*)?росі', 2.0, 'uk_location_label'),
    (r'крим\s*[,\-]\s*росі', 2.0, 'uk_location_label'),

    # Admin names — Russian Federation designations in Ukrainian text
    (r'(?<!автономна\s)республіка\s+крим', 1.5, 'uk_admin_name'),
    (r'кримський\s+федеральний\s+округ', 1.5, 'uk_admin_name'),

    # Framing — Russian narrative in Ukrainian text
    (r'возз\'?єднанн\w+\s+крим', 1.5, 'uk_framing'),
    (r'приєднанн\w+\s+крим\w*\s+до\s+росі', 1.5, 'uk_framing'),
    (r'крим\s+у\s+складі\s+росі', 2.0, 'uk_framing'),
    (r'крим\s+став\s+(?:частиною|регіоном)\s+росі', 2.0, 'uk_framing'),
    (r'крим\s+—?\s+це\s+росі', 2.0, 'uk_framing'),
    (r'крим\s+повернувся\s+(?:до|в)\s+росі', 1.5, 'uk_framing'),
    (r'крим\s+наш', 2.0, 'uk_framing'),
]

# =====================================================================
# STRUCTURAL SIGNALS (language-independent)
# =====================================================================

STRUCTURAL_UKRAINE = [
    (r'country_code["\s:=]+ua\b', 1.5, 'structural'),
    (r'country["\s:=]+ukraine', 1.5, 'structural'),
    (r'/ukraine/crimea|/ukraine/simferopol', 1.0, 'structural'),
]

STRUCTURAL_RUSSIA = [
    (r'country_code["\s:=]+ru\b', 1.5, 'structural'),
    (r'country["\s:=]+russia', 1.5, 'structural'),
    (r'/russia/crimea|/russia/simferopol', 1.0, 'structural'),
]

# =====================================================================
# CRIMEA REFERENCE DETECTION (for filtering)
# =====================================================================

CRIMEA_REFERENCE = re.compile(
    r'crimea|крим[уіа]?|крым[ауе]?|krim|kırım|crimée|krimea',
    re.IGNORECASE
)

# =====================================================================
# PROPAGANDA SOURCE DOMAINS
# =====================================================================
# Tiered list of Russian state-controlled/state-adjacent media domains.
# Used to classify the SOURCE of Russia-framing documents.
# Sources: GEC (2020), EU sanctions, EUvsDisinfo, DFRLab/CheckFirst.

# Tier 1: Direct state-owned / state-funded
STATE_MEDIA_T1 = [
    # Rossiya Segodnya group
    "ria.ru", "sputniknews.com", "sputnikglobe.com", "inosmi.ru", "ukraina.ru",
    "baltnews.ee", "baltnews.lt", "baltnews.lv",
    # TASS
    "tass.com", "tass.ru",
    # RT (TV-Novosti)
    "rt.com", "russian.rt.com", "arabic.rt.com", "actualidad.rt.com",
    "rtarabic.com", "ruptly.tv",
    # RT clone/mirror domains (post-EU-sanctions)
    "freedert.online", "dert.online", "rtde.live", "swentr.site", "rurtnews.com",
    # Broadcasters
    "iz.ru", "rg.ru", "tvzvezda.ru", "ntv.ru", "vesti.ru",
    "1tv.ru", "5-tv.ru",
]

# Tier 2: GEC-identified proxy outlets
STATE_MEDIA_T2 = [
    "strategic-culture.org",   # SVR-linked
    "globalresearch.ca",       # Conspiracy, amplifies Russian narratives
    "journal-neo.org",         # New Eastern Outlook, Russian Academy of Sciences
    "news-front.info",         # Based in occupied Crimea
    "southfront.org",          # US-sanctioned, Crimea-based
    "katehon.com",             # Moscow quasi-think-tank
    "geopolitica.ru",          # Dugin-linked
]

# Tier 3: Pravda Network (Portal Kombat) — pravda-branded domains
# Source: American Sunlight Project PK Database, DFRLab/CheckFirst
PRAVDA_NETWORK = [
    "news-pravda.com",         # Main hub (country subdomains) — Portal Kombat / TigerWeb
    "dnr-pravda.ru",           # DNR variant
    # NOTE: pravda.ru = old Soviet newspaper, now in STATE_ADJ_T4 (NOT Portal Kombat)
    # NOTE: pravda.com.ua = Ukrainska Pravda = legitimate Ukrainian outlet, NOT included
]

# Tier 4: Russian domestic state-adjacent / sanctioned
STATE_MEDIA_T4 = [
    "lenta.ru", "aif.ru", "ng.ru", "mk.ru", "kp.ru", "kommersant.ru",
    "gazeta.ru", "tsargrad.tv", "riafan.ru", "anna-news.info",
    "rusvesna.su", "novoeizdanie.com", "sevastopol.su", "e-crimea.info",
    "voiceofeurope.com",       # EU-sanctioned
    "pravda.ru",               # Old Soviet Pravda newspaper (NOT Portal Kombat)
    "pravda-tv.com",
]

# All domains flattened for fast lookup
ALL_PROPAGANDA_DOMAINS = set(
    STATE_MEDIA_T1 + STATE_MEDIA_T2 + PRAVDA_NETWORK + STATE_MEDIA_T4
)

def classify_source(url: str) -> str:
    """Classify a URL's domain against known propaganda tiers.
    Returns: 'state_t1', 'proxy_t2', 'pravda', 'state_adj_t4', or 'independent'.
    """
    if not url:
        return "independent"
    url_lower = url.lower()
    # Extract domain-ish substring (handles full URLs and bare domains)
    for d in STATE_MEDIA_T1:
        if d in url_lower:
            return "state_t1"
    for d in STATE_MEDIA_T2:
        if d in url_lower:
            return "proxy_t2"
    for d in PRAVDA_NETWORK:
        if d in url_lower:
            return "pravda"
    for d in STATE_MEDIA_T4:
        if d in url_lower:
            return "state_adj_t4"
    return "independent"

# =====================================================================
# QUOTATION / ATTRIBUTION MARKERS
# =====================================================================
# These detect when Russia-framing appears as a QUOTATION (attributed to
# a source) rather than as a factual ASSERTION. A BBC article saying
# 'what Russia calls "reunification"' is quoting, not asserting.
# LLMs cannot distinguish these — both produce the same token patterns.

QUOTATION_EN = [
    # ONLY genuine attribution — someone reporting what Russia SAYS
    # NOT skepticism/debunking (that's Ukraine-framing, not quotation)
    r'(?:russia|moscow|kremlin)\s+(?:says?|claims?|calls?\s+it|argues?|insists?|maintains?|considers?)',
    r'(?:putin|lavrov)\s+(?:says?|said|claims?|claimed|declared?|stated?|called)',
    r'according\s+to\s+(?:russia|moscow|the\s+kremlin|putin)',
    r'what\s+(?:russia|moscow|the\s+kremlin)\s+calls?',
    # Quotation marks around SPECIFIC Russian-narrative terms (not general skepticism)
    r'["\u201c\u00ab](?:reunif\w+|accession\s+of\s+crimea|rejoined?\s+russia)["\u201d\u00bb]',
]

QUOTATION_RU = [
    # Genuine attribution in Russian text
    r'(?:россия|кремль|москва|путин)\s+(?:считает|называет|утверждает|заявляет)',
    r'по\s+(?:мнению|версии|заявлению)\s+(?:россии|кремля|москвы|путина)',
    # Quotation marks around Russian-narrative terms
    r'[\u00ab\u201c](?:воссоединени|присоединени)\w*[\u00bb\u201d]',
]

QUOTATION_UK = [
    # Genuine attribution in Ukrainian text
    r'(?:росія|кремль|москва|путін)\s+(?:вважає|називає|стверджує|заявляє)',
    r'за\s+(?:версією|заявою)\s+(?:росії|кремля|москви|путіна)',
    # Quotation marks
    r'[\u00ab\u201c](?:возз\'?єднанн|приєднанн)\w*[\u00bb\u201d]',
]

QUOTATION_MARKERS = [re.compile(p, re.IGNORECASE) for p in
                     QUOTATION_EN + QUOTATION_RU + QUOTATION_UK]

# =====================================================================
# COMPILED SIGNAL GROUPS
# =====================================================================

def compile_all():
    """Compile all signals into a flat list of (regex, direction, weight, signal_type)."""
    signals = []

    for pattern, weight, sig_type in (
        EN_UKRAINE + RU_UKRAINE + UK_UKRAINE + STRUCTURAL_UKRAINE
    ):
        signals.append((re.compile(pattern, re.IGNORECASE), 'ukraine', weight, sig_type))

    for pattern, weight, sig_type in (
        EN_RUSSIA + RU_RUSSIA + UK_RUSSIA + STRUCTURAL_RUSSIA
    ):
        signals.append((re.compile(pattern, re.IGNORECASE), 'russia', weight, sig_type))

    return signals


ALL_SIGNALS = compile_all()

# Stats
_ua = len(EN_UKRAINE) + len(RU_UKRAINE) + len(UK_UKRAINE) + len(STRUCTURAL_UKRAINE)
_ru = len(EN_RUSSIA) + len(RU_RUSSIA) + len(UK_RUSSIA) + len(STRUCTURAL_RUSSIA)

if __name__ == "__main__":
    print(f"Sovereignty signals: {_ua} Ukraine + {_ru} Russia = {_ua + _ru} total")
    print(f"  English:    {len(EN_UKRAINE)} UA + {len(EN_RUSSIA)} RU")
    print(f"  Russian:    {len(RU_UKRAINE)} UA + {len(RU_RUSSIA)} RU")
    print(f"  Ukrainian:  {len(UK_UKRAINE)} UA + {len(UK_RUSSIA)} RU")
    print(f"  Structural: {len(STRUCTURAL_UKRAINE)} UA + {len(STRUCTURAL_RUSSIA)} RU")
