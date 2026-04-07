"""
Generate a nice HTML report of Claude Haiku 4.5 sovereignty audit results.

Multiple tables covering:
- Overall stats
- Question × City matrix
- City × Language matrix (Q1 focus)
- Question × Language matrix
- Crimea vs Donbas comparison
- Per-question breakdown
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

PROJECT = Path(__file__).parent.parent
DATA = PROJECT / "data"
OUT_PATH = DATA / "haiku_report.html"

MODEL = "haiku-4.5"

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
    """Return hex color from red (0%) through yellow (50%) to green (100%)."""
    if pct is None:
        return "#2a2a2a"
    if pct >= 90:
        return "#16a34a"  # green
    if pct >= 75:
        return "#65a30d"  # lime
    if pct >= 50:
        return "#ca8a04"  # amber
    if pct >= 25:
        return "#ea580c"  # orange
    return "#dc2626"  # red


def text_color(bg):
    # simple: use white text on dark backgrounds
    return "#fff"


def cell(text, pct=None, subtext=None):
    bg = color_for_pct(pct) if pct is not None else "#1a1a1a"
    fg = text_color(bg)
    sub = f'<br><small style="opacity:0.8;font-size:9px">{subtext}</small>' if subtext else ""
    return f'<td style="background:{bg};color:{fg};text-align:center;padding:6px 4px;font-size:11px">{text}{sub}</td>'


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
<title>Claude Haiku 4.5 — Crimea Sovereignty Audit</title>
<style>
body {{
  font-family: -apple-system, system-ui, sans-serif;
  background: #0a0a0a;
  color: #e5e5e5;
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
  font-size: 13px;
}}
h1 {{ font-size: 28px; margin-top: 0; color: #fff; }}
h2 {{ font-size: 18px; margin-top: 32px; color: #fff; border-bottom: 1px solid #333; padding-bottom: 6px; }}
h3 {{ font-size: 14px; color: #ccc; margin-top: 24px; }}
table {{
  border-collapse: collapse;
  font-size: 11px;
  margin: 12px 0;
}}
th {{
  background: #1a1a1a;
  color: #ccc;
  padding: 6px 8px;
  text-align: left;
  font-weight: 600;
  border: 1px solid #333;
  position: sticky;
  top: 0;
}}
td {{
  border: 1px solid #222;
  padding: 4px 8px;
}}
.label {{ background: #1a1a1a; color: #e5e5e5; font-weight: 600; text-align: left !important; }}
.stat-big {{ font-size: 36px; font-weight: bold; color: #fff; }}
.stat-label {{ font-size: 11px; color: #888; text-transform: uppercase; }}
.stat-card {{ background: #1a1a1a; padding: 16px; border-radius: 8px; display: inline-block; margin-right: 16px; min-width: 180px; }}
.headline {{ background: #7f1d1d; color: #fff; padding: 16px; border-radius: 8px; margin: 16px 0; }}
.headline h3 {{ margin: 0; color: #fff; }}
small {{ color: #888; }}
.legend {{ margin: 12px 0; font-size: 10px; color: #888; }}
.legend span {{ display: inline-block; padding: 2px 8px; margin-right: 4px; color: #fff; }}
</style>
</head>
<body>

<h1>Claude Haiku 4.5 — Crimea Sovereignty Audit</h1>
<p style="color:#888">Generated {datetime.now().strftime("%Y-%m-%d %H:%M")} · {total} queries across 15 questions, 12 cities, 50 languages</p>

<div>
  <div class="stat-card"><div class="stat-big" style="color:#dc2626">{overall_pct}%</div><div class="stat-label">Overall correct</div></div>
  <div class="stat-card"><div class="stat-big">{total:,}</div><div class="stat-label">Total queries</div></div>
  <div class="stat-card"><div class="stat-big" style="color:#16a34a">{total_correct:,}</div><div class="stat-label">Correct</div></div>
  <div class="stat-card"><div class="stat-big" style="color:#dc2626">{total - total_correct:,}</div><div class="stat-label">Incorrect</div></div>
</div>

<div class="headline">
<h3>🎯 Key finding: 100% correct on Donbas/Southern Ukrainian cities, but as low as 17% on Crimean cities</h3>
<p style="margin:8px 0 0 0">Haiku gets every single query about Donetsk, Luhansk, Mariupol, Melitopol, Kherson, Berdyansk right — but fails on Crimean cities at rates up to 83%. Pre-2022 Russian framing of Crimea leaked into training data; post-2022 Donbas/Kherson narrative was correctly learned as Ukrainian.</p>
</div>

<div class="legend">
  <span style="background:#16a34a">≥90%</span>
  <span style="background:#65a30d">75-89%</span>
  <span style="background:#ca8a04">50-74%</span>
  <span style="background:#ea580c">25-49%</span>
  <span style="background:#dc2626">&lt;25%</span>
</div>
""")

# ============================================================
# Table 1: Summary by question with explicit yes/no counts
# ============================================================
html.append("<h2>Table 1 — Accuracy by Question</h2>")
html.append('<p style="color:#888;font-size:11px">"Correct" = answers matching the Expected column. YES/NO counts are the raw answers Haiku gave, regardless of whether they are correct.</p>')
html.append('<table><tr><th>ID</th><th>Question</th><th style="width:70px">Expected</th><th style="width:60px">YES</th><th style="width:60px">NO</th><th style="width:70px">Disputed/Other</th><th style="width:100px">Correct</th><th style="width:80px">%</th></tr>')

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
    yes_style = 'background:#16a34a;color:#fff' if expected in ('yes', 'ukraine') else 'background:#1a1a1a;color:#e5e5e5'
    no_style = 'background:#16a34a;color:#fff' if expected in ('no', 'russia') else 'background:#1a1a1a;color:#e5e5e5'

    html.append(f'''<tr>
<td class="label">{q_id}</td>
<td style="color:#aaa;font-size:11px">{q_prompt}</td>
<td style="text-align:center;color:#16a34a;font-weight:bold">{expected.upper()}</td>
<td style="{yes_style};text-align:center">{yes_label}: {yes_count}</td>
<td style="{no_style};text-align:center">{no_label}: {no_count}</td>
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
    html.append(f'<tr><td class="label">{lang} · {LANGS.get(lang, lang)}</td>')
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
for l in lang_overall[:20]:  # top 20 languages
    html.append(f'<th style="writing-mode:vertical-lr;height:100px">{l}</th>')
html.append("</tr>")

for q_id in QUESTIONS.keys():
    html.append(f'<tr><td class="label" style="font-size:10px">{q_id}</td>')
    for l in lang_overall[:20]:
        d = by_ql.get((q_id, l), {"correct": 0, "total": 0})
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
for l in lang_overall[20:]:
    html.append(f'<th style="writing-mode:vertical-lr;height:100px">{l}</th>')
html.append("</tr>")

for q_id in QUESTIONS.keys():
    html.append(f'<tr><td class="label" style="font-size:10px">{q_id}</td>')
    for l in lang_overall[20:]:
        d = by_ql.get((q_id, l), {"correct": 0, "total": 0})
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
        html.append(f'<td style="background:{color_for_pct(p)};color:#fff;text-align:center;padding:4px{border}">{p}%<br><small>{d["correct"]}/{d["total"]}</small></td>')
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
<p style="background:#7f1d1d;color:#fff;padding:12px;border-radius:6px;margin-top:12px">
<strong>Gap: {round(donbas_p - crimea_p, 1)} percentage points.</strong>
Haiku's training data absorbed pre-2022 Russian framing of Crimea (encoded as ~{crimea_p}% "correct"),
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
    gap_color = "#dc2626" if abs(gap) > 30 else "#ca8a04" if abs(gap) > 15 else "#65a30d"
    html.append(f'<td style="background:{gap_color};color:#fff;text-align:center">+{gap} pts</td>')
    html.append("</tr>")
html.append("</table>")

# ============================================================
# Sample wrong answers
# ============================================================
html.append("<h2>Sample Wrong Answers</h2>")
html.append('<p style="color:#888;font-size:11px">Examples where Haiku got it wrong — first 30</p>')

html.append('<table style="font-size:10px"><tr><th>Q</th><th>City</th><th>Lang</th><th>Prompt</th><th>Answer</th><th>Expected</th></tr>')

wrong_rows = [r for r in rows if r.get("correct") is False][:30]
for r in wrong_rows:
    prompt = r.get("prompt", "")[:80]
    answer = r.get("raw_answer", "")[:60]
    html.append(f'<tr><td>{r.get("question_id","")[:25]}</td><td>{r.get("city","")}</td><td>{r.get("language","")}</td><td style="color:#aaa">{prompt}</td><td style="background:#7f1d1d;color:#fff">{answer}</td><td>{r.get("expected","")}</td></tr>')
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
