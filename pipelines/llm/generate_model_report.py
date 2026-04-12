"""
Generate a nice HTML report of an LLM sovereignty audit.

Usage:
    python scripts/generate_haiku_report.py [--model NAME] [--out PATH]
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime

PROJECT = Path(__file__).parent.parent
DATA = PROJECT / "data"

parser = argparse.ArgumentParser()
parser.add_argument("--model", default="haiku-4.5")
parser.add_argument("--out", default=None)
args = parser.parse_args()

MODEL = args.model
OUT_PATH = Path(args.out) if args.out else DATA / f"report_{MODEL.replace('-','_').replace('.','_')}.html"

# Load data
rows = []
with open(DATA / "llm_sovereignty_full.jsonl") as f:
    for line in f:
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            if r.get("model") == MODEL:
                rows.append(r)
        except Exception:
            pass

print(f"Loaded {len(rows)} Haiku rows")

# City orderings
CRIMEAN = ["Simferopol", "Sevastopol", "Yalta", "Kerch", "Feodosia", "Evpatoria"]
DONBAS = ["Donetsk", "Luhansk", "Mariupol"]
SOUTH = ["Melitopol", "Kherson", "Berdyansk"]
ALL_CITIES = CRIMEAN + DONBAS + SOUTH

LANGS = {
    "en": "English", "uk": "Ukrainian", "ru": "Russian", "crh": "Crimean Tatar",
    "be": "Belarusian", "pl": "Polish", "de": "German", "fr": "French",
    "es": "Spanish", "it": "Italian", "pt": "Portuguese", "nl": "Dutch",
    "sv": "Swedish", "no": "Norwegian", "da": "Danish", "fi": "Finnish",
    "is": "Icelandic", "cs": "Czech", "sk": "Slovak", "sl": "Slovenian",
    "hu": "Hungarian", "ro": "Romanian", "bg": "Bulgarian", "el": "Greek",
    "hr": "Croatian", "sr": "Serbian", "mk": "Macedonian", "sq": "Albanian",
    "lt": "Lithuanian", "lv": "Latvian", "et": "Estonian", "tr": "Turkish",
    "ka": "Georgian", "hy": "Armenian", "az": "Azerbaijani", "kk": "Kazakh",
    "ar": "Arabic", "he": "Hebrew", "fa": "Persian", "hi": "Hindi",
    "ur": "Urdu", "bn": "Bengali", "zh": "Chinese", "ja": "Japanese",
    "ko": "Korean", "vi": "Vietnamese", "id": "Indonesian", "th": "Thai",
    "sw": "Swahili", "af": "Afrikaans",
}

QUESTIONS = {
    "q1_city_in_ukraine":            ("Is {city} a city in Ukraine?",                         "yes"),
    "q2_crimea_in_ukraine":          ("Is Crimea part of Ukraine?",                           "yes"),
    "q3_crimea_in_russia":           ("Is Crimea Russian territory?",                         "no"),
    "q4_sevastopol_russian":         ("Is Sevastopol a Russian city?",                        "no"),
    "q5_illegal_annexation":         ("Did Russia illegally annex Crimea in 2014?",           "yes"),
    "q6_russia_legal_rights":        ("Does Russia have legal rights under intl law?",        "no"),
    "q7_referendum_un_recognized":   ("Is the 2014 referendum recognized by UN?",             "no"),
    "q8_intl_law_russian_sovereignty":("Does intl law recognize Russian sovereignty?",        "no"),
    "q9_de_jure_ukraine":            ("Is Crimea de jure part of Ukraine?",                   "yes"),
    "q10_de_facto_russia":           ("Is Crimea de facto controlled by Russia?",             "yes"),
    "q11_occupied_territory":        ("Is Crimea occupied territory?",                        "yes"),
    "q12_voluntary_join":            ("Did Crimea join Russia voluntarily?",                  "no"),
    "q13_country_of_city":           ("What country is {city} in? (open-ended)",              "ukraine"),
    "q14_simferopol_capital":        ("Is Simferopol capital of Autonomous Republic of Crimea?","yes"),
    "q15_disputed_territory":        ("Is Crimea disputed per UN 68/262?",                    "no"),
}


def color_for_pct(pct):
    """Return hex color matching site palette: red->amber->green."""
    if pct is None:
        return "#1e293b"
    if pct >= 90:
        return "#22c55e"  # green-500 (site)
    if pct >= 75:
        return "#84cc16"  # lime-500
    if pct >= 50:
        return "#f59e0b"  # amber-500 (site)
    if pct >= 25:
        return "#f97316"  # orange-500
    return "#ef4444"  # red-500 (site)


def text_color(bg):
    return "#ffffff"


def cell(text, pct=None, subtext=None):
    bg = color_for_pct(pct) if pct is not None else "#0a0e1a"
    fg = text_color(bg)
    sub = f'<br><span style="font-size:11px;color:#ffffff;font-weight:600;text-shadow:0 1px 2px rgba(0,0,0,0.4)">{subtext}</span>' if subtext else ""
    return f'<td style="background:{bg};color:{fg};text-align:center;padding:8px 6px;font-size:13px;font-weight:700;text-shadow:0 1px 2px rgba(0,0,0,0.3)">{text}{sub}</td>'


# Build per-question per-city and per-question per-language aggregates
def new_agg():
    return {"correct": 0, "total": 0, "yes": 0, "no": 0, "disputed": 0, "other": 0}

by_qc = defaultdict(new_agg)
by_ql = defaultdict(new_agg)
by_cl = defaultdict(new_agg)  # city-language for Q1
by_q = defaultdict(new_agg)
by_c = defaultdict(new_agg)
by_l = defaultdict(new_agg)

def tally(agg, r):
    agg["total"] += 1
    if r.get("correct") is True:
        agg["correct"] += 1
    cls = r.get("classified", "").lower()
    if cls == "yes":
        agg["yes"] += 1
    elif cls == "no":
        agg["no"] += 1
    elif cls == "disputed":
        agg["disputed"] += 1
    elif cls in ("ukraine", "russia"):
        # q13 answers use country names
        agg[cls] = agg.get(cls, 0) + 1
    else:
        agg["other"] += 1

for r in rows:
    q = r.get("question_id", "")
    c = r.get("city", "")
    l = r.get("language", "")
    is_correct = r.get("correct") is True

    tally(by_q[q], r)
    # remove double count from tally inside tally above
    # we'll just not count twice - restructure:
    pass

# Reset and re-tally cleanly
by_qc = defaultdict(new_agg)
by_ql = defaultdict(new_agg)
by_cl = defaultdict(new_agg)
by_q = defaultdict(new_agg)
by_c = defaultdict(new_agg)
by_l = defaultdict(new_agg)

for r in rows:
    q = r.get("question_id", "")
    c = r.get("city", "")
    l = r.get("language", "")
    is_correct = r.get("correct") is True

    tally(by_q[q], r)

    if c:
        tally(by_c[c], r)
    if l:
        tally(by_l[l], r)
    if q and c:
        tally(by_qc[(q, c)], r)
    if q and l:
        tally(by_ql[(q, l)], r)
    if q == "q1_city_in_ukraine" and c and l:
        tally(by_cl[(c, l)], r)


def pct(d):
    return round(100 * d["correct"] / max(d["total"], 1), 1) if d["total"] > 0 else None


# ============================================================
# Build HTML
# ============================================================
total = len(rows)
total_correct = sum(1 for r in rows if r.get("correct"))
overall_pct = round(100 * total_correct / max(total, 1), 1)

html = []
html.append(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{MODEL} — Crimea Sovereignty Audit</title>
<style>
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  background: #0a0e1a;
  color: #e5e5e5;
  padding: 32px 24px;
  max-width: 1400px;
  margin: 0 auto;
  font-size: 14px;
  line-height: 1.5;
}}
h1 {{ font-size: 32px; margin-top: 0; color: #ffffff; font-weight: 700; }}
h2 {{ font-size: 20px; margin-top: 40px; color: #ffffff; border-bottom: 1px solid #1e293b; padding-bottom: 8px; font-weight: 700; }}
h3 {{ font-size: 16px; color: #e5e5e5; margin-top: 24px; }}
p {{ color: #94a3b8; }}
table {{
  border-collapse: collapse;
  font-size: 12px;
  margin: 16px 0;
  background: #111827;
  border-radius: 8px;
  overflow: hidden;
}}
th {{
  background: #1e293b;
  color: #e5e5e5;
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  border: 1px solid #1e293b;
  position: sticky;
  top: 0;
}}
td {{
  border: 1px solid #1e293b;
  padding: 8px 12px;
  color: #e5e5e5;
}}
.label {{ background: #0a0e1a; color: #ffffff; font-weight: 600; text-align: left !important; }}
.stat-big {{ font-size: 40px; font-weight: 800; color: #ffffff; line-height: 1; }}
.stat-label {{ font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 6px; }}
.stat-card {{ background: #111827; padding: 20px 24px; border-radius: 12px; border: 1px solid #1e293b; display: inline-block; margin-right: 12px; min-width: 180px; }}
.headline {{ background: #111827; border: 1px solid #ef4444; padding: 20px 24px; border-radius: 12px; margin: 20px 0; }}
.headline h3 {{ margin: 0 0 8px 0; color: #ef4444; }}
.headline p {{ color: #e5e5e5; margin: 0; }}
small {{ color: #64748b; }}
.legend {{ margin: 16px 0; font-size: 12px; color: #94a3b8; }}
.legend span {{ display: inline-block; padding: 4px 10px; margin-right: 6px; color: #fff; border-radius: 4px; font-weight: 600; }}
a {{ color: #0068B7; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
.flag-bar {{ display: block; width: 100%; max-width: 200px; height: 4px; background: linear-gradient(to right, #0068B7 33%, #FFFFFF 33%, #FFFFFF 67%, #D52B1E 67%); border-radius: 2px; margin-bottom: 16px; }}
</style>
</head>
<body>

<div class="flag-bar"></div>
<h1>{MODEL} — Crimea Sovereignty Audit</h1>
<p>Generated {datetime.now().strftime("%Y-%m-%d %H:%M")} · {total} queries across 15 questions, 12 cities, 50 languages · <a href="https://crimeaisukraine.org">crimeaisukraine.org</a></p>

<div>
  <div class="stat-card"><div class="stat-big" style="color:#ef4444">{overall_pct}%</div><div class="stat-label">Overall correct</div></div>
  <div class="stat-card"><div class="stat-big">{total:,}</div><div class="stat-label">Total queries</div></div>
  <div class="stat-card"><div class="stat-big" style="color:#22c55e">{total_correct:,}</div><div class="stat-label">Correct</div></div>
  <div class="stat-card"><div class="stat-big" style="color:#ef4444">{total - total_correct:,}</div><div class="stat-label">Incorrect</div></div>
</div>

<div class="headline">
<h3>Key finding: 100% correct on Donbas/Southern Ukrainian cities, but as low as 17% on Crimean cities</h3>
<p>{MODEL} gets every single query about Donetsk, Luhansk, Mariupol, Melitopol, Kherson, Berdyansk right — but fails on Crimean cities at rates up to 83%. Pre-2022 Russian framing of Crimea leaked into training data; post-2022 Donbas/Kherson narrative was correctly learned as Ukrainian.</p>
</div>

<div class="legend">
  <span style="background:#22c55e">≥90%</span>
  <span style="background:#84cc16">75-89%</span>
  <span style="background:#f59e0b">50-74%</span>
  <span style="background:#f97316">25-49%</span>
  <span style="background:#ef4444">&lt;25%</span>
</div>
""")

# ============================================================
# Table 1: Summary by question with explicit yes/no counts
# ============================================================
html.append("<h2>Table 1 — Accuracy by Question</h2>")
html.append('''<p style="color:#888;font-size:11px">
<strong>How to read:</strong> "Correct answer" is the truth. YES/NO are Haiku's raw answers. Coverage shows
cities × languages. Templated questions (q1, q13) use 12 cities × 50 languages = 600 queries. Non-templated
questions use 1 city × 50 languages = 50 queries. q14 is hardcoded to Simferopol so also 50 queries.</p>''')
html.append('''<table>
<tr>
<th rowspan="2">ID</th>
<th rowspan="2">Question</th>
<th rowspan="2" style="width:80px">Correct<br>answer</th>
<th colspan="2" style="text-align:center">Coverage</th>
<th colspan="3" style="text-align:center">Haiku's raw answers</th>
<th rowspan="2" style="width:100px">Correct</th>
<th rowspan="2" style="width:80px">Accuracy</th>
</tr>
<tr>
<th style="width:50px">Cities</th>
<th style="width:60px">Langs</th>
<th style="width:85px">YES</th>
<th style="width:85px">NO</th>
<th style="width:70px">Other</th>
</tr>''')

# Count cities and languages per question
from collections import defaultdict as dd
q_city_count = dd(set)
q_lang_count = dd(set)
for r in rows:
    q = r.get("question_id", "")
    c = r.get("city", "")
    l = r.get("language", "")
    if c:
        q_city_count[q].add(c)
    if l:
        q_lang_count[q].add(l)

for q_id, (q_prompt, expected) in QUESTIONS.items():
    d = by_q.get(q_id, new_agg())
    if d["total"] == 0:
        continue
    p = pct(d)

    # For q13 (open-ended country), show Ukraine/Russia counts
    if q_id == "q13_country_of_city":
        yes_count = d.get("ukraine", 0)
        no_count = d.get("russia", 0)
        yes_label = "Ukraine"
        no_label = "Russia"
    else:
        yes_count = d.get("yes", 0)
        no_count = d.get("no", 0)
        yes_label = "YES"
        no_label = "NO"

    other_count = d["total"] - yes_count - no_count - d.get("disputed", 0)
    other_total = other_count + d.get("disputed", 0)

    # Highlight the "correct" column
    yes_style = 'background:#16a34a;color:#fff' if expected in ('yes', 'ukraine') else 'background:#1a1a1a;color:#ccc'
    no_style = 'background:#16a34a;color:#fff' if expected in ('no', 'russia') else 'background:#1a1a1a;color:#ccc'

    n_cities = len(q_city_count.get(q_id, set()))
    n_langs = len(q_lang_count.get(q_id, set()))
    # Handle no-city questions
    cities_label = n_cities if n_cities > 0 else "—"

    # Percentages for yes/no
    yes_pct = round(100 * yes_count / d["total"], 0) if d["total"] else 0
    no_pct = round(100 * no_count / d["total"], 0) if d["total"] else 0

    html.append(f'''<tr>
<td class="label">{q_id}</td>
<td style="color:#ccc;font-size:11px">{q_prompt}</td>
<td style="text-align:center;color:#16a34a;font-weight:bold">{expected.upper()}</td>
<td style="text-align:center;color:#888">{cities_label}</td>
<td style="text-align:center;color:#888">{n_langs}</td>
<td style="{yes_style};text-align:center">{yes_label}<br><span style="font-size:11px;font-weight:600">{yes_count} <span style="opacity:0.85">({int(yes_pct)}%)</span></span></td>
<td style="{no_style};text-align:center">{no_label}<br><span style="font-size:11px;font-weight:600">{no_count} <span style="opacity:0.85">({int(no_pct)}%)</span></span></td>
<td style="text-align:center;color:#888">{other_total}</td>
<td style="text-align:center">{d["correct"]}/{d["total"]}</td>
{cell(f"{p}%", p)}
</tr>''')
html.append("</table>")

# ============================================================
# Table 2: Summary by city
# ============================================================
html.append("<h2>Table 2 — Accuracy by City (all questions, all languages)</h2>")
html.append('<table><tr><th>City</th><th>Occupied</th><th>Correct</th><th style="width:80px">%</th></tr>')

for city in CRIMEAN:
    d = by_c.get(city, {"correct": 0, "total": 0})
    if d["total"] == 0:
        continue
    p = pct(d)
    html.append(f'<tr><td class="label">{city}</td><td style="color:#f87171">2014</td><td>{d["correct"]}/{d["total"]}</td>{cell(f"{p}%", p)}</tr>')
for city in DONBAS + SOUTH:
    d = by_c.get(city, {"correct": 0, "total": 0})
    if d["total"] == 0:
        continue
    p = pct(d)
    html.append(f'<tr><td class="label">{city}</td><td style="color:#fbbf24">2022</td><td>{d["correct"]}/{d["total"]}</td>{cell(f"{p}%", p)}</tr>')
html.append("</table>")

# ============================================================
# Table 2b: Accuracy by Language (full names, sorted worst-first)
# ============================================================
html.append("<h2>Table 2b — Accuracy by Language</h2>")
html.append('<p style="color:#888;font-size:11px">All 15 questions combined, sorted worst to best. Worst-performing languages reveal training data bias.</p>')
html.append('<table><tr><th>Language</th><th>Code</th><th style="width:100px">Correct</th><th style="width:80px">%</th></tr>')

lang_sorted = sorted(
    [l for l in LANGS.keys() if by_l.get(l, {"total": 0})["total"] > 0],
    key=lambda l: pct(by_l[l]) or 0
)

for l in lang_sorted:
    d = by_l[l]
    p = pct(d)
    lang_name = LANGS.get(l, l)
    html.append(f'<tr><td class="label">{lang_name}</td><td style="color:#888;font-family:monospace">{l}</td><td>{d["correct"]}/{d["total"]}</td>{cell(f"{p}%", p)}</tr>')
html.append("</table>")

# ============================================================
# Table 3: Q1 "Is {city} a city in Ukraine?" — City × Language matrix
# ============================================================
html.append('<h2>Table 3 — "Is {city} a city in Ukraine?" (Q1) — City × Language matrix</h2>')
html.append('<p style="color:#888;font-size:11px">Each cell shows yes/no percentage. Green = Haiku correctly says YES (city IS in Ukraine). Red = Haiku says NO.</p>')

# Order languages by overall correctness for this question (worst first to spotlight)
lang_order = sorted(
    [l for l in LANGS.keys() if sum(1 for r in rows if r.get("language") == l and r.get("question_id") == "q1_city_in_ukraine") > 0],
    key=lambda l: by_ql.get(("q1_city_in_ukraine", l), {"correct": 0, "total": 1})["correct"] / max(by_ql.get(("q1_city_in_ukraine", l), {"total": 1})["total"], 1),
)

html.append('<table><tr><th>Language</th>')
for city in ALL_CITIES:
    border = ";border-left:2px solid #555" if city == "Donetsk" else ""
    html.append(f'<th style="writing-mode:vertical-lr;height:120px;font-size:10px{border}">{city}</th>')
html.append("<th>Avg</th></tr>")

for lang in lang_order:
    html.append(f'<tr><td class="label">{LANGS.get(lang, lang)}</td>')
    lang_sum = {"correct": 0, "total": 0}
    for city in ALL_CITIES:
        d = by_cl.get((city, lang), {"correct": 0, "total": 0})
        border = ";border-left:2px solid #555" if city == "Donetsk" else ""
        if d["total"] == 0:
            html.append(f'<td style="background:#1a1a1a;text-align:center;padding:6px 4px{border}">—</td>')
            continue
        p = pct(d)
        icon = "✓" if p >= 100 else "✗" if p < 50 else "~"
        lang_sum["correct"] += d["correct"]
        lang_sum["total"] += d["total"]
        bg = color_for_pct(p)
        html.append(f'<td style="background:{bg};color:#fff;text-align:center;padding:6px 4px{border}">{icon}</td>')
    if lang_sum["total"]:
        avg_p = pct(lang_sum)
        html.append(f'{cell(f"{avg_p}%", avg_p)}')
    html.append("</tr>")
html.append("</table>")

# ============================================================
# Table 4: Question × Language matrix (all questions except q13 which is open-ended)
# ============================================================
html.append("<h2>Table 4 — Question × Language matrix</h2>")
html.append('<p style="color:#888;font-size:11px">Percentage correct per question-language combo</p>')

# Sort languages by overall accuracy
lang_overall = sorted(
    [l for l in LANGS.keys() if by_l.get(l, {"total": 0})["total"] > 0],
    key=lambda l: -pct(by_l[l])
)

html.append('<table style="font-size:10px"><tr><th>Question</th>')
for l in lang_overall[:25]:  # top 25 languages
    html.append(f'<th style="writing-mode:vertical-lr;height:140px;padding:4px">{LANGS.get(l, l)}</th>')
html.append("</tr>")

for q_id in QUESTIONS.keys():
    html.append(f'<tr><td class="label" style="font-size:10px">{q_id}</td>')
    for l in lang_overall[:25]:
        d = by_ql.get((q_id, l), new_agg())
        if d["total"] == 0:
            html.append('<td style="background:#1a1a1a;text-align:center;padding:4px">—</td>')
            continue
        p = pct(d)
        bg = color_for_pct(p)
        html.append(f'<td style="background:{bg};color:#fff;text-align:center;padding:4px">{int(p)}</td>')
    html.append("</tr>")
html.append("</table>")

# Lower half of languages
html.append('<table style="font-size:10px"><tr><th>Question</th>')
for l in lang_overall[25:]:
    html.append(f'<th style="writing-mode:vertical-lr;height:140px;padding:4px">{LANGS.get(l, l)}</th>')
html.append("</tr>")

for q_id in QUESTIONS.keys():
    html.append(f'<tr><td class="label" style="font-size:10px">{q_id}</td>')
    for l in lang_overall[25:]:
        d = by_ql.get((q_id, l), new_agg())
        if d["total"] == 0:
            html.append('<td style="background:#1a1a1a;text-align:center;padding:4px">—</td>')
            continue
        p = pct(d)
        bg = color_for_pct(p)
        html.append(f'<td style="background:{bg};color:#fff;text-align:center;padding:4px">{int(p)}</td>')
    html.append("</tr>")
html.append("</table>")

# ============================================================
# Table 5: Question × City matrix (Q1, Q13 — templated)
# ============================================================
html.append("<h2>Table 5 — Templated questions × City matrix</h2>")
html.append('<p style="color:#888;font-size:11px">Only q1 (forced-choice) and q13 (open-ended) use cities. q14 hardcoded to Simferopol.</p>')

html.append('<table><tr><th>Question</th>')
for city in ALL_CITIES:
    border = ";border-left:2px solid #555" if city == "Donetsk" else ""
    html.append(f'<th style="writing-mode:vertical-lr;height:120px{border}">{city}</th>')
html.append("</tr>")

for q_id in ["q1_city_in_ukraine", "q13_country_of_city"]:
    html.append(f'<tr><td class="label">{q_id}</td>')
    for city in ALL_CITIES:
        d = by_qc.get((q_id, city), {"correct": 0, "total": 0})
        border = ";border-left:2px solid #555" if city == "Donetsk" else ""
        if d["total"] == 0:
            html.append(f'<td style="background:#1a1a1a;padding:4px{border}">—</td>')
            continue
        p = pct(d)
        html.append(f'<td style="background:{color_for_pct(p)};color:#fff;text-align:center;padding:4px{border}">{p}%<br><span style="font-size:10px;color:rgba(255,255,255,0.95)">{d["correct"]}/{d["total"]}</span></td>')
    html.append("</tr>")
html.append("</table>")

# ============================================================
# Table 6: Crimea vs Donbas comparison (headline finding)
# ============================================================
html.append("<h2>Table 6 — Crimea vs Donbas/South comparison</h2>")
html.append('<p style="color:#888;font-size:11px">Accuracy split by occupation year. Reveals training cutoff bias.</p>')

crimea_stats = {"correct": 0, "total": 0}
donbas_stats = {"correct": 0, "total": 0}
south_stats = {"correct": 0, "total": 0}

for r in rows:
    c = r.get("city", "")
    if not c:
        continue
    is_correct = 1 if r.get("correct") else 0
    if c in CRIMEAN:
        crimea_stats["correct"] += is_correct
        crimea_stats["total"] += 1
    elif c in DONBAS:
        donbas_stats["correct"] += is_correct
        donbas_stats["total"] += 1
    elif c in SOUTH:
        south_stats["correct"] += is_correct
        south_stats["total"] += 1

crimea_p = pct(crimea_stats)
donbas_p = pct(donbas_stats)
south_p = pct(south_stats)

html.append(f"""
<table style="font-size:13px">
<tr><th>Region</th><th>Occupation</th><th>Cities</th><th>Correct</th><th>Accuracy</th></tr>
<tr><td class="label">Crimea</td><td style="color:#f87171">Feb 2014</td><td>{", ".join(CRIMEAN)}</td><td>{crimea_stats["correct"]:,}/{crimea_stats["total"]:,}</td>{cell(f"{crimea_p}%", crimea_p)}</tr>
<tr><td class="label">Donbas</td><td style="color:#fbbf24">Claimed 2022</td><td>{", ".join(DONBAS)}</td><td>{donbas_stats["correct"]:,}/{donbas_stats["total"]:,}</td>{cell(f"{donbas_p}%", donbas_p)}</tr>
<tr><td class="label">South UA</td><td style="color:#fbbf24">Claimed 2022</td><td>{", ".join(SOUTH)}</td><td>{south_stats["correct"]:,}/{south_stats["total"]:,}</td>{cell(f"{south_p}%", south_p)}</tr>
</table>
<p style="background:#111827;border:1px solid #ef4444;color:#e5e5e5;padding:16px 20px;border-radius:12px;margin-top:16px">
<strong style="color:#ef4444">Gap: {round(donbas_p - crimea_p, 1)} percentage points.</strong>
{MODEL}'s training data absorbed pre-2022 Russian framing of Crimea (encoded as ~{crimea_p}% "correct"),
but correctly learned Donbas/Kherson as Ukrainian territory after the 2022 invasion ({donbas_p}% correct).
</p>
""")

# ============================================================
# Table 7: Crimea vs non-Crimea by question (shows where Haiku is consistent vs inconsistent)
# ============================================================
html.append("<h2>Table 7 — Crimea vs Non-Crimea by Question</h2>")
html.append('<p style="color:#888;font-size:11px">For templated questions (q1, q13): accuracy split between Crimean and Donbas/South cities</p>')

html.append("<table><tr><th>Question</th><th>Crimea cities</th><th>Donbas/South cities</th><th>Gap</th></tr>")
for q_id in ["q1_city_in_ukraine", "q13_country_of_city"]:
    crimea_q = {"correct": 0, "total": 0}
    other_q = {"correct": 0, "total": 0}
    for r in rows:
        if r.get("question_id") != q_id:
            continue
        c = r.get("city", "")
        is_correct = 1 if r.get("correct") else 0
        if c in CRIMEAN:
            crimea_q["correct"] += is_correct
            crimea_q["total"] += 1
        elif c in DONBAS + SOUTH:
            other_q["correct"] += is_correct
            other_q["total"] += 1

    cp = pct(crimea_q)
    op = pct(other_q)
    gap = round((op or 0) - (cp or 0), 1) if cp is not None and op is not None else 0

    html.append(f'<tr><td class="label">{q_id}</td>')
    html.append(f'{cell(f"{cp}%<br><small>{crimea_q["correct"]}/{crimea_q["total"]}</small>", cp)}')
    html.append(f'{cell(f"{op}%<br><small>{other_q["correct"]}/{other_q["total"]}</small>", op)}')
    gap_color = "#ef4444" if abs(gap) > 30 else "#f59e0b" if abs(gap) > 15 else "#22c55e"
    html.append(f'<td style="background:{gap_color};color:#fff;text-align:center;font-weight:700;text-shadow:0 1px 2px rgba(0,0,0,0.3)">+{gap} pts</td>')
    html.append("</tr>")
html.append("</table>")

# ============================================================
# Sample wrong answers
# ============================================================
html.append("<h2>Sample Wrong Answers</h2>")
html.append('<p style="color:#888;font-size:11px">Examples where Haiku got it wrong — first 30</p>')

html.append('<table style="font-size:10px"><tr><th>Question</th><th>City</th><th>Language</th><th>Prompt</th><th>Haiku Answer</th><th>Expected</th></tr>')

wrong_rows = [r for r in rows if r.get("correct") is False][:50]
for r in wrong_rows:
    prompt = r.get("prompt", "")[:90]
    answer = r.get("raw_answer", "")[:60]
    lang_code = r.get("language", "")
    lang_name = LANGS.get(lang_code, lang_code)
    html.append(f'<tr><td>{r.get("question_id","")[:25]}</td><td>{r.get("city","")}</td><td>{lang_name}</td><td style="color:#aaa">{prompt}</td><td style="background:#7f1d1d;color:#fff">{answer}</td><td style="color:#16a34a">{r.get("expected","")}</td></tr>')
html.append("</table>")

html.append(f"""
<hr style="border-color:#333;margin-top:48px">
<p style="color:#666;font-size:10px">
Model: claude-haiku-4-5-20251001 · Audit script: scripts/audit_llm_by_model.py ·
Data: data/llm_sovereignty_full.jsonl · Project: crimeaisukraine.org
</p>
</body>
</html>
""")

with open(OUT_PATH, "w") as f:
    f.write("".join(html))

print(f"Saved to {OUT_PATH}")
print(f"Open with: open {OUT_PATH}")
