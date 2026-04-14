#!/usr/bin/env python3
"""
Categorize remaining 'uncategorized' documents in categorized_russia_framing.jsonl.

Reads the original file, applies domain-based heuristics to uncategorized docs,
writes categorized_russia_framing_v2.jsonl with updated site_type fields.

Never overwrites the original file.
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent / "data"
INPUT = BASE / "categorized_russia_framing.jsonl"
OUTPUT = BASE / "categorized_russia_framing_v2.jsonl"

if OUTPUT.exists():
    print(f"WARNING: {OUTPUT} already exists, will be overwritten.", file=sys.stderr)

# ---------------------------------------------------------------------------
# Domain -> category mapping (exact match)
# ---------------------------------------------------------------------------
EXACT_DOMAIN = {
    # --- Russian state / pro-Kremlin news ---
    "life.ru": "news_ru_other",
    "tvc.ru": "news_ru_other",
    "vesti-k.ru": "news_ru_other",
    "otr-online.ru": "news_ru_other",
    "360tv.ru": "news_ru_other",
    "rusplt.ru": "news_ru_other",
    "nation-news.ru": "news_ru_other",
    "rusdialog.ru": "news_ru_other",
    "vladtime.ru": "news_ru_other",
    "kremlinrus.ru": "news_ru_other",
    "gosnovosti.com": "news_ru_other",
    "fn-volga.ru": "news_ru_other",
    "ruspekh.ru": "news_ru_other",
    "nahnews.org": "news_ru_other",
    "rusnext.ru": "news_ru_other",
    "pravda-tv.ru": "news_ru_other",
    "news-rbk.ru": "news_ru_other",
    "crimea-24.com": "news_ru_other",
    "intavrida.ru": "news_ru_other",
    "crimea-news.com": "news_ru_other",
    "newc.info": "news_ru_other",
    "1sn.ru": "news_ru_other",
    "news.ru": "news_ru_other",
    "1crimea.com": "news_ru_other",
    "vesti-sudak.ru": "news_ru_other",
    "crimeapress.info": "news_ru_other",
    "primechaniya.ru": "news_ru_other",
    "rustelegraph.ru": "news_ru_other",
    "interfax-russia.ru": "news_ru_other",
    "trn-news.ru": "news_ru_other",
    "inforeactor.ru": "news_ru_other",
    "nversia.ru": "news_ru_other",
    "nevnov.ru": "news_ru_other",
    "newsoftheday.ru": "news_ru_other",
    "krasvremya.ru": "news_ru_other",
    "newkaliningrad.ru": "news_ru_other",
    "iarex.ru": "news_ru_other",
    "dailystorm.ru": "news_ru_other",
    "jcnews.ru": "news_ru_other",
    "novostimira.net": "news_ru_other",
    "novostimira.com": "news_ru_other",
    "newsexpress.ru": "news_ru_other",
    "eg.ru": "news_ru_other",
    "city-n.ru": "news_ru_other",
    "bk55.ru": "news_ru_other",
    "teleport2001.ru": "news_ru_other",
    "24smi.org": "news_ru_other",
    "nvdaily.ru": "news_ru_other",
    "kvedomosti.com": "news_ru_other",
    "allpravda.info": "news_ru_other",
    "stockinfocus.ru": "news_ru_other",
    "medialeaks.ru": "news_ru_other",
    "svopi.ru": "news_ru_other",
    "snob.ru": "news_ru_other",
    "tjournal.ru": "news_ru_other",
    "ruposters.ru": "news_ru_other",
    "anna-news.info": "news_ru_other",
    "newinform.com": "news_ru_other",
    "rossaprimavera.ru": "news_ru_other",
    "amur.net": "news_ru_other",
    "newsmir.info": "news_ru_other",
    "sevastopolnews.info": "news_ru_other",
    "feo.today": "news_ru_other",
    "gorod24.online": "news_ru_other",
    "4vsar.ru": "news_ru_other",
    "omsk.com": "news_ru_other",
    "ekburg.tv": "news_ru_other",

    # --- Sanctioned / pro-Kremlin propaganda ---
    "novoross.info": "sanctioned_media",
    "antifashist.com": "sanctioned_media",
    "anti-maidan.com": "sanctioned_media",
    "novorosinform.org": "sanctioned_media",
    "novorossiia.ru": "sanctioned_media",
    "novorus.info": "sanctioned_media",
    "rusnod.ru": "sanctioned_media",
    "rusila.su": "sanctioned_media",
    "voicesevas.ru": "sanctioned_media",

    # --- Russian independent / opposition ---
    "echo.msk.ru": "news_ru_independent",
    "sova-center.ru": "news_ru_independent",
    "kavkaz-uzel.eu": "news_ru_independent",
    "mediarepost.ru": "news_ru_independent",

    # --- Ukrainian news ---
    "apostrophe.ua": "news_ua",
    "dialog.ua": "news_ua",
    "rbc.ua": "news_ua",
    "nv.ua": "news_ua",
    "rian.com.ua": "news_ua",
    "antikor.com.ua": "news_ua",
    "for-ua.com": "news_ua",
    "thekievtimes.ua": "news_ua",
    "vesti-ukr.com": "news_ua",
    "jankoy.org.ua": "news_ua",

    # --- International / other news ---
    "politeka.net": "news_aggregator",
    "pikabu.ru": "news_aggregator",
    "m.pikabu.ru": "news_aggregator",
    "fishki.net": "news_aggregator",
    "m.fishki.net": "news_aggregator",
    "surfingbird.ru": "news_aggregator",
    "yablor.ru": "news_aggregator",

    # --- Kyrgyz / Kazakh news ---
    "gazeta.kg": "news_aggregator",
    "time.kg": "news_aggregator",
    "jashtar.kg": "news_aggregator",
    "chalkan.kg": "news_aggregator",
    "crimea.kz": "news_aggregator",

    # --- News portals / aggregators ---
    "politros.com": "news_aggregator",
    "ruspravda.info": "news_aggregator",
    "politobzor.net": "news_aggregator",
    "politpuzzle.ru": "news_aggregator",
    "politcentr.ru": "news_aggregator",
    "politrussia.com": "news_aggregator",
    "politikus.ru": "news_aggregator",
    "russiagoodnews.ru": "news_aggregator",
    "gogetnews.info": "news_aggregator",
    "pravdanews.info": "news_aggregator",
    "hronika.info": "news_aggregator",
    "trueinform.ru": "news_aggregator",
    "x-true.info": "news_aggregator",
    "geo-politica.info": "news_aggregator",
    "tehnowar.ru": "news_aggregator",
    "7days.us": "news_aggregator",
    "nr2.lt": "news_aggregator",
    "udf.by": "news_aggregator",

    # --- Bezformata (regional news aggregator) ---
    # Handled by pattern below

    # --- Maps / geo ---
    "map-russ.ru": "maps",
    "r-nav.ru": "maps",
    "intmaps.ru": "maps",
    "geophoto.ru": "maps",

    # --- Real estate ---
    "tavridadom.ru": "real_estate",
    "docrimea.ru": "real_estate",
    "invest-in-crimea.ru": "real_estate",
    "lookuprealty.ru": "real_estate",
    "rosreestr.net": "real_estate",
    "crimeanhome.com.ua": "real_estate",
    "vashdomkrym.ru": "real_estate",
    "krim-nash-russia.ru": "real_estate",
    "perspectiva-sochi.ru": "real_estate",

    # --- Travel / tourism ---
    "rutraveller.ru": "travel",
    "aroundtravels.com": "travel",
    "visitcrimea.guide": "travel",
    "crimea-hotels.ru": "travel",
    "alean.ru": "travel",
    "tixrussia.ru": "travel",
    "incamp.ru": "travel",
    "hotelsbroker.com": "travel",
    "hotels24.ua": "travel",
    "gotonature.ru": "travel",
    "domotdiha.ru": "travel",
    "solvex.ru.postman.ru": "travel",
    "kudanayuga.ru": "travel",
    "morekrim.ru": "travel",
    "lodkavmore.life": "travel",
    "pick-route.ru": "travel",
    "aviales.ru": "travel",
    "axis.travel": "travel",
    "strekoza.travel": "travel",
    "smorodina.com": "travel",
    "privetyug.com": "travel",

    # --- Sanatorium / health-travel ---
    "sanatoriy.net": "travel",
    "naftusia.ru": "travel",

    # --- Dating ---
    "love.ru": "dating",
    "mamba.ru": "dating",
    "simpotka.ru": "dating",
    "znakomilki.ru": "dating",
    "davajpozhenimsya.com": "dating",
    "urbanlove.ru": "dating",
    "mymobimeet.com": "dating",
    "tvbgirls.com": "dating",
    "sxnarod.com": "dating",

    # --- Business directories / registers ---
    "rusprofile.ru": "classifieds",
    "bicotender.ru": "classifieds",
    "zachestnyibiznes.ru": "classifieds",
    "casebook.ru": "classifieds",
    "contragents.ru": "classifieds",
    "egrinf.com": "classifieds",

    # --- Classifieds ---
    "1001ads.ru": "classifieds",
    "sidex.ru": "classifieds",
    "metaprom.ru": "classifieds",

    # --- Jobs ---
    "trudvsem.ru": "jobs",

    # --- Blog platforms ---
    "proza.ru": "blog",
    "ridero.ru": "blog",

    # --- Forums ---
    "kharkovforums.com": "forum",
    "history-forum.ru": "forum",

    # --- Government ---
    "adm-saki.ru": "government_crimea",

    # --- Education ---
    "pochemu4ka.ru": "education",
    "uchportfolio.ru": "education",
    "myshared.ru": "education",
    "docplayer.ru": "education",

    # --- Encyclopedic / reference ---
    "slovodel.com": "encyclopedia",
    "metateka.com": "encyclopedia",
    "spravochnik.org": "encyclopedia",

    # --- Culture ---
    "tavrida-museum.ru": "culture",
    "portal-kultura.ru": "culture",

    # --- Military ---
    "blackseafleet-21.com": "military",
    "warfiles.ru": "military",

    # --- Sports ---
    "water-games.ru": "sports",

    # --- Society / NGO ---
    "milli-firka.org": "society_org",
    "myrotvorets.center": "society_org",
    "yeghiazaryan.org": "society_org",
    "so-edinenie.org": "society_org",
    "lyudi.org": "society_org",

    # --- Finance ---
    "bankgorodov.ru": "finance",

    # --- Monitoring / analytics ---
    "z-monitor.ru": "other_categorized",

    # --- Portals ---
    "3652.ru": "portal",
    "3654.ru": "portal",
    "chernomorskoe-rk.ru": "portal",
    "simblago.com": "portal",
    "club-rf.ru": "portal",

    # --- Legal ---
    "moneylaw.ru": "legal",

    # --- Commerce ---
    "puteukazatel.com": "commerce",
    "1cont.ru": "commerce",
    "bonzon.ru": "commerce",
    "goods-club.ru": "commerce",
    "prodbox.ru": "commerce",
    "shebni.ru": "commerce",
    "planetaizmerenij.ru": "commerce",
    "webmineral.ru": "commerce",

    # --- Agriculture ---
    "rynok-apk.ru": "commerce",

    # --- Minecraft / gaming ---
    "old-minecraft.ru": "entertainment",

    # --- Auto ---
    "auto-club.biz": "auto",

    # --- Health ---
    "ukrmed.ru": "health",
    "medicina99.ru": "health",

    # --- IT / tech ---
    "cherlock.ru": "tech",

    # --- Flowers / delivery ---
    "bflorist.ru": "commerce",

    # --- Distance / geography reference ---
    "gorod-rastoynie.ru": "maps",

    # --- Crimea-specific portals ---
    "qrim.ru": "portal",
    "qrim.org": "portal",
    "crymnash.ru": "portal",
    "c-in.ru": "portal",

    # --- Second pass: top remaining uncategorized domains ---
    # Portals / directories
    "gorodnet.com": "portal",
    "krikyn.ru": "classifieds",
    "zinki.ru": "classifieds",
    "ru.esosedi.org": "maps",
    "images.esosedi.org": "maps",
    "imag.one": "other_categorized",
    "kapital-rus.ru": "finance",
    "krim.ros-spravka.ru": "classifieds",
    "bee-ru.com": "classifieds",
    "komu.info": "classifieds",
    "gdz-reshim.ru": "education",
    "fek.ru": "legal",
    "u-f.ru": "news_ru_other",
    "dom.vidido.ua": "real_estate",
    "vidido.ua": "classifieds",
    "rusevik.ru": "news_ru_other",
    "pravdoryb.info": "news_ru_other",
    "termloan.ru": "finance",
    "hdbk24.ru": "classifieds",
    "vip-spravka.com": "classifieds",
    "1areal.ru": "news_ru_other",
    "raui.ru": "classifieds",
    "ves-rf.ru": "portal",
    "trasto.ru": "commerce",
    "mrk24rf.ru": "portal",
    "thehole.ru": "entertainment",
    "proone.ru": "commerce",
    "55rur.ru": "classifieds",
    "art-center.ru": "culture",
    "evp-integral.ru": "commerce",
    "chernomorsk.info": "portal",
    "anapa-pro.com": "travel",
    "agentika.com": "travel",
    "newsonline24.com.ua": "news_ua",
    "cmyki.ru": "commerce",
    "glavportal.com": "portal",
    "profi-forex.org": "finance",
    "turum.net": "travel",
    "arsenal-info.ru": "news_ru_other",
    "propfr.ru": "commerce",
    "polit.info": "news_aggregator",
    "rating.gd.ru": "classifieds",
    "konkurs.sertification.org": "education",
    "s-s.su": "commerce",
    "ua.krymr.com": "news_ua",
    "discred.ru": "finance",
    "energovestnik.ru": "news_ru_other",
    "e-news.su": "news_aggregator",
    "rosinform.ru": "news_ru_other",
    "mir-politika.ru": "news_aggregator",
    "yavix.ru": "classifieds",
    "topic.lt": "news_aggregator",
    "allforsmart.ru": "commerce",
    "vsemayki.ru": "commerce",
    "evening-crimea.com": "news_ru_other",
    "uslando.ru": "classifieds",
    "rusfact.ru": "news_ru_other",
    "vmeste-rf.tv": "news_ru_other",
    "ambaro.ru": "commerce",
    "ya2017.com": "other_categorized",
    "lratvakan.com": "news_aggregator",
    "ua-ru.info": "news_aggregator",
    "lechenieboli.ru": "health",
    "rfgf.ru": "government",
    "old.rfgf.ru": "government",
    "kamael.com.ua": "news_ua",
    "pandero.ru": "commerce",
    "hvylya.net": "news_ua",
    "articlet.com": "blog",
    "prolit-septo.ru": "commerce",
    "tanzpol.org": "entertainment",
    "interaffairs.ru": "news_ru_other",
    "saitevpatorii.com": "portal",
    "disclosure.skrin.ru": "finance",
    "opoccuu.com": "news_aggregator",
    "proza.ru": "blog",
    "via-midgard.com": "sanctioned_media",

    # --- More news ---
    "vashgorodnews.ru": "news_ru_other",
    "artv-news.ru": "news_ru_other",
    "naonews.ru": "news_ru_other",
    "newlow.ru": "news_ru_other",
    "permnew.ru": "news_ru_other",
    "rrnews.ru": "news_ru_other",
    "ejnew.org": "news_aggregator",
    "liganews.net": "news_ua",
    "onsmi.ru": "news_aggregator",
    "vladivostoktimes.ru": "news_ru_other",
    "uefima.ru": "news_ru_other",
    "focusgoroda.ru": "news_ru_other",
    "mediasar.ru": "news_ru_other",
    "info-suhinichi.ru": "news_ru_other",
    "naupri.ru": "news_ru_other",
    "russmir.info": "news_ru_other",
    "ironpost.ru": "news_ru_other",
    "politinformer.ru": "news_aggregator",
    "roskraeved.ru": "culture",
    "sakha.ru": "portal",
    "evromaidan2014.com": "news_aggregator",
    "rusorel.info": "news_ru_other",
    "dosie.su": "classifieds",
    "souzpisatel.ru": "culture",
    "yunarmy.ru": "military",
    "penzacitylib.ru": "culture",
    "newtribuna.ru": "news_ru_other",

    # --- Third pass: punycode domains ---
    "xn--80apbncz.xn--p1ai": "portal",           # миамир.рф
    "xn--24-1lchu.xn--p1ai": "portal",            # мрк24.рф
    "xn----8sbnojigiuni.xn--p1ai": "auto",         # номер-такси.рф
    "xn--80ad5aze.xn--p1ai": "classifieds",       # явам.рф
    "xn--80aapudk6ad.xn--p1ai": "commerce",       # анталекс.рф
    "xn-----6kcbechue4acjte0afmn6afrh4evgua3i.xn--p1ai": "classifieds",  # сайт-бесплатных-объявлений.рф
    "xn----ptbeiljj3c5a.xn--p1ai": "travel",      # крым-сочи.рф
    "xn----7sbbagdq9bj2abdo7azg0e.xn--p1ai": "auto",  # первая-автошкола.рф
    "xn--j1aidcn.org": "news_ua",                  # укроп.org
    "xn--80ahcclckrige5az7c.xn--p1ai": "entertainment",  # киномедиацентр.рф
    "xn--80ahtnegiq.xn--p1ai": "portal",          # просудак.рф
    "xn--b1aghc8bceu.xn--p1ai": "news_ru_other",  # тихвести.рф

    # --- Third pass: more remaining top domains ---
    "joojee.ru": "classifieds",
    "profas.expert": "commerce",
    "molod-sov.ru": "society_org",
    "rus-novosti.net": "news_ru_other",
    "eventsinrussia.com": "entertainment",
    "limpa.ru": "commerce",
    "germes-gp.ru": "commerce",
    "krasnoperekopsk.net": "portal",
    "zagolovki.ru": "news_aggregator",
    "myslo.ru": "news_ru_other",
    "sakirs.ru": "classifieds",
    "brunelcr.ru": "commerce",
    "rusotdih.ru": "travel",
    "riamo.ru": "news_ru_other",
    "simgov.ru": "government_crimea",
    "mc.dp.ua": "portal",
    "megasmi.net": "news_aggregator",
    "ya-russ.ru": "news_ru_other",
    "tvil.ru": "travel",
    "oane.ws": "news_aggregator",
    "openrussia.org": "society_org",
    "gakada.ru": "classifieds",
    "promoz.ru": "commerce",
    "ktelegraf.com.ru": "news_ru_other",
    "2000.ua": "news_ua",
    "theins.ru": "news_ru_independent",
    "samarameet.ru": "dating",
    "perevozka24.ru": "commerce",
    "vestikavkaza.ru": "news_ru_other",
    "narzur.ru": "commerce",
    "kievsmi.net": "news_ua",
    "imfast.com": "tech",
    "krasnodar.metalloobrabotchiki.ru": "commerce",
    "is-zakupki.ru": "commerce",
    "liport.ru": "classifieds",
    "teleguide.ru": "entertainment",
    "voenpro.ru": "military",
    "strana.ua": "news_ua",
    "doskaros.ru": "classifieds",
    "misare.ru": "commerce",
    "pro.myseldon.com": "news_aggregator",
}


# ---------------------------------------------------------------------------
# Subdomain / platform patterns  (checked as substring or via regex)
# ---------------------------------------------------------------------------
# These are platforms where subdomains represent cities/regions.
SUBDOMAIN_PLATFORMS = {
    ".bezformata.": "news_aggregator",
    ".allbusiness.": "classifieds",
    ".mnekvartiru.": "real_estate",
    ".biznesarenda.": "real_estate",
    ".bestru.": "classifieds",
    ".moneylaw.": "legal",
    ".doski.": "classifieds",
    ".novosel.": "real_estate",
    ".tiu.": "commerce",
    ".stavtrack.": "classifieds",
    ".vezetvsem.": "classifieds",
    ".pulset.": "classifieds",
    ".gorodrabot.": "jobs",
    ".people-city.": "portal",
    ".arendator.": "real_estate",
    ".nashaspravka.": "classifieds",
    ".nedvrf.": "real_estate",
    ".migts.": "real_estate",
    ".domoscope.": "real_estate",
    ".spcteh.": "commerce",
    ".imls.": "real_estate",
    ".glavny.tv": "news_ru_other",
    ".izbirkom.": "government",
    ".trud.com": "jobs",
    ".rambler.ru": "portal",
    ".rtrs.ru": "tech",
    ".olimpiada.ru": "education",
    ".regionshop.": "commerce",
    ".mirtesen.ru": "blog",
    ".my1.ru": "blog",
    "elections.": "government",
    ".ucoz.": "blog",
    ".narod.ru": "blog",
    ".jimdo.": "blog",
    ".wix.": "blog",
    ".2br.ru": "classifieds",
    ".chelobkom.": "classifieds",
    ".ros-spravka.": "classifieds",
    ".amarket.": "commerce",
    ".incrimea.": "portal",
    ".uo-simf.": "education",
    ".vidido.ua": "classifieds",
    ".esosedi.": "maps",
    ".skrin.ru": "finance",
    ".directrix.ru": "classifieds",
    ".metalloobrabotchiki.": "commerce",
    ".myseldon.": "news_aggregator",
    ".chelindustry.": "commerce",
    ".monocore.": "tech",
    ".spb.ru": "portal",
}


# ---------------------------------------------------------------------------
# Keyword / TLD patterns (applied in order, first match wins)
# ---------------------------------------------------------------------------
def classify_by_patterns(host: str, path: str) -> str | None:
    """Return a site_type or None based on domain heuristics."""

    # Government by TLD
    if ".gov.ru" in host or ".gov.ua" in host or ".gov." in host:
        return "government"
    if host.endswith(".mil.ru"):
        return "military"

    # Education by TLD / keywords
    if ".edu." in host or ".edu" == host[-4:]:
        return "education"
    if any(kw in host for kw in ("universit", "academ", "school", "lyceum",
                                  "gimnazi", "college", "uchitel", "pedagog",
                                  "uchportfolio", "1sept.")):
        return "education"

    # Wiki / encyclopedic
    if "wikipedia.org" in host or "wikimedia.org" in host:
        return "encyclopedia"

    # Social media
    if host in ("vk.com", "ok.ru", "facebook.com", "m.facebook.com",
                "twitter.com", "instagram.com", "t.me", "telegram.me",
                "youtube.com", "m.youtube.com", "odnoklassniki.ru"):
        return "social_media"

    # Blog platforms
    if any(kw in host for kw in (".livejournal.com", ".blogspot.", "wordpress.com",
                                  ".tumblr.com", ".blogger.com", "medium.com",
                                  ".liveinternet.ru", ".diary.ru", "zen.yandex.")):
        return "blog"

    # Forums
    if host.startswith("forum.") or host.startswith("forums.") or "forum" in host.split(".")[0]:
        return "forum"

    # Dating keywords
    if any(kw in host for kw in ("dating", "znakom", "love", "flirt", "mamba",
                                  "bride", "kisses", "devushk")):
        return "dating"

    # Real estate keywords
    if any(kw in host for kw in ("realt", "kvartir", "nedvizh", "zhilye", "zhitlo",
                                  "arend", "ipoteka", "domofond", "cian.",
                                  "avito.", "irn.", "etag.", "m2bomber")):
        return "real_estate"

    # Travel / tourism / hotels
    if any(kw in host for kw in ("travel", "turiz", "hotel", "hostel", "sanator",
                                  "kuror", "tur.", "otdyh", "otpusk", "excurs",
                                  "booking", "trivago")):
        return "travel"
    if host.endswith(".travel"):
        return "travel"

    # Health / medical
    if any(kw in host for kw in ("medic", "zdorov", "doctor", "clinic", "hospital",
                                  "apteka", "vrach", "bolnic", "pharma", "health",
                                  "poliklini")):
        return "health"

    # Legal
    if any(kw in host for kw in ("law", "zakon", "pravo", "jurist", "advokat",
                                  "sud.", "arbitr", "legal")):
        return "legal"

    # Finance / banking
    if any(kw in host for kw in ("bank", "financ", "kredit", "ipoteka", "invest",
                                  "buhgalt", "nalog")):
        return "finance"

    # Auto
    if any(kw in host for kw in ("auto", "avto", "car.", "mashina", "drom.",
                                  "drive2.")):
        return "auto"

    # Jobs
    if any(kw in host for kw in ("rabota", "job", "trud", "vakansi", "hh.",
                                  "karier")):
        return "jobs"

    # Tech / IT
    if any(kw in host for kw in ("habr.", "geektimes", "opennet", "ixbt.",
                                  "overclock", "4pda.", "w3c.")):
        return "tech"

    # Commerce (broad)
    if any(kw in host for kw in ("shop", "store", "market", "magazin", "tovar",
                                  "opt.", "sale", "kupit", "price", "catalog",
                                  "torg.", "tender")):
        return "commerce"

    # Weather
    if any(kw in host for kw in ("weather", "pogoda", "meteo")):
        return "weather"

    # Maps / geo
    if any(kw in host for kw in ("map", "karta", "geo.", "coord", "navi")):
        return "maps"

    # Sports
    if any(kw in host for kw in ("sport", "futbol", "football", "hockey",
                                  "olimp")):
        return "sports"

    # Entertainment / gaming
    if any(kw in host for kw in ("game", "igra", "kino", "film", "movie",
                                  "music", "muzik", "minecraft", "steam")):
        return "entertainment"

    # Culture / museums
    if any(kw in host for kw in ("museum", "muzey", "culture", "kultura",
                                  "librar", "bibliotek", "gallery", "galere")):
        return "culture"

    # Military / defense
    if any(kw in host for kw in ("militar", "army", "armiy", "war.", "flot.",
                                  "fleet", "yunarmy", "oboron")):
        return "military"

    # Pro-Kremlin / propaganda keywords
    if any(kw in host for kw in ("novoross", "antimaid", "antifash",
                                  "russpring", "rusvesna")):
        return "sanctioned_media"

    # Russian news (broad catch — domains with 'news' in them ending in .ru/.info/.net)
    if "news" in host and any(host.endswith(t) for t in (".ru", ".info", ".net", ".com")):
        return "news_ru_other"

    # Broader news patterns (vesti, gazeta, inform, obzor, etc.)
    if any(kw in host for kw in ("vesti.", "gazet", "inform.", "obzor",
                                  "herald", "times.", "daily", "press.",
                                  "chronicle", "reporter", "zhurnal")):
        return "news_ru_other"

    # Construction / repair
    if any(kw in host for kw in ("stroy", "remont", "plitk", "okna.",
                                  "potolok", "krovl", "fasad", "dver",
                                  "santehni", "otoplen", "elektri")):
        return "commerce"

    # Food / restaurants
    if any(kw in host for kw in ("restoran", "kafe.", "eda.", "food",
                                  "cook", "recept", "kulinar")):
        return "commerce"

    # Children / parenting
    if any(kw in host for kw in ("deti.", "child", "rebenk", "roditeli",
                                  "mama.", "baby")):
        return "other_categorized"

    # Religion
    if any(kw in host for kw in ("church", "cerkov", "pravoslav", "hram.",
                                  "monast", "eparch")):
        return "culture"

    # Agriculture
    if any(kw in host for kw in ("agro", "ferma", "selhoz", "sadov",
                                  "ogorod", "dacha")):
        return "commerce"

    # Pets / animals
    if any(kw in host for kw in ("animal", "zoolog", "pitom", "kosha",
                                  "sobak", "veteri")):
        return "other_categorized"

    # Education broader
    if any(kw in host for kw in ("obrazovan", "obucheni", "kurs.",
                                  "repetitor", "uroki.", "detskijsad")):
        return "education"

    # Reference / directories (spravka, spravochnik, katalog)
    if any(kw in host for kw in ("spravk", "katalog", "spravochn",
                                  "dosie.", "baza-firm", "organy-vlasti")):
        return "classifieds"

    # Crimea portals (krym, krim, sevastopol in the domain)
    if any(kw in host for kw in ("crimea", "krym", "krim.", "sevastopol",
                                  "simferopol", "yalta", "evpatori",
                                  "sudak", "kerch", "feodos")):
        # check if news-like
        if any(nw in host for nw in ("news", "press", "inform", "vesti")):
            return "news_ru_other"
        return "portal"

    # SMI (media) keyword
    if "smi" in host.split(".")[0] or host.startswith("smi."):
        return "news_aggregator"

    # Doska (bulletin board) keywords
    if any(kw in host for kw in ("doska", "dosk.", "objav", "obyav")):
        return "classifieds"

    # Free hosting TLDs (.tk/.ga/.gq/.cf) -- mostly spam/misc
    if any(host.endswith(t) for t in (".tk", ".ga", ".gq", ".cf")):
        return "other_categorized"

    # .su (Soviet TLD) with political / news keywords
    if host.endswith(".su"):
        if any(kw in host for kw in ("news", "polit", "inform", "press")):
            return "news_ru_other"

    # Government: admin, administr, mun, city official
    if any(kw in host for kw in ("admin.", "administr", "municipalit",
                                  "adm-", "gorsovet", "gorodskaya-duma",
                                  "region.", "oblast.", "krasnod.krai")):
        return "government"

    # Broader classifieds patterns
    if any(kw in host for kw in ("doska", "objav", "obyav", "bazar",
                                  "barahl", "kupiprodai")):
        return "classifieds"

    return None


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------
def main():
    stats = Counter()
    recategorized = 0
    still_uncategorized = 0
    total = 0

    with open(INPUT) as fin, open(OUTPUT, "w") as fout:
        for line in fin:
            total += 1
            doc = json.loads(line)

            if doc.get("site_type") != "uncategorized":
                stats[doc["site_type"]] += 1
                fout.write(line)
                continue

            # --- Try to categorize ---
            url = doc.get("url", "")
            try:
                parsed = urlparse(url)
                host = parsed.netloc.lower()
                path = parsed.path.lower()
                if host.startswith("www."):
                    host = host[4:]
            except Exception:
                still_uncategorized += 1
                stats["uncategorized"] += 1
                fout.write(line)
                continue

            new_type = None

            # 1. Exact domain lookup
            new_type = EXACT_DOMAIN.get(host)

            # 2. Subdomain platform lookup
            if new_type is None:
                for pattern, cat in SUBDOMAIN_PLATFORMS.items():
                    if pattern in host or host.startswith(pattern.lstrip(".")):
                        new_type = cat
                        break

            # 3. Keyword / TLD heuristics
            if new_type is None:
                new_type = classify_by_patterns(host, path)

            if new_type is not None:
                doc["site_type"] = new_type
                recategorized += 1
                stats[new_type] += 1
                fout.write(json.dumps(doc, ensure_ascii=False) + "\n")
            else:
                still_uncategorized += 1
                stats["uncategorized"] += 1
                fout.write(line)

    # --- Report ---
    print(f"\n{'='*60}")
    print(f"  Categorization complete")
    print(f"{'='*60}")
    print(f"  Total documents:         {total:>10,}")
    print(f"  Recategorized:           {recategorized:>10,}")
    print(f"  Still uncategorized:     {still_uncategorized:>10,}")
    print(f"{'='*60}")
    print(f"\n  Category distribution (all docs):\n")
    for cat, count in stats.most_common():
        pct = 100.0 * count / total
        print(f"    {count:>8,}  ({pct:5.1f}%)  {cat}")
    print()


if __name__ == "__main__":
    main()
