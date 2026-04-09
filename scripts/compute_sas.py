"""
Compute the Sovereignty Alignment Score (SAS) for Crimea.

SAS is a composite score that weighs four probe tiers by elicitation
difficulty, in inverse proportion to the degree to which standard
Reinforcement Learning from Human Feedback (RLHF) can patch each tier.
Higher weight on harder-to-patch tiers rewards models whose underlying
representations — not just surface RLHF-corrected answers — align with
the internationally recognised Ukrainian sovereignty over Crimea.

The four tiers and their RLHF-patchability rank
------------------------------------------------
  D  Direct territorial       (q2 q3 q4 q9 q14)
     easiest to patch with a handful of RLHF examples.
  L  Legal-normative           (q5 q6 q7 q8 q11 q15)
     requires targeted legal-vocabulary training.
  I  Implicit sovereignty     (q1 q12 q13)
     requires the model to not default to incorrect
     city-country associations inherited from training.
  R  Free-recall               (oq1..oq8 open-ended)
     the default-generation tier — cannot be patched without
     changing the pretraining distribution itself.

Primary weights: [D, L, I, R] = [0.10, 0.20, 0.30, 0.40]

These are the smallest monotonic integer progression (1:2:3:4) consistent
with the theoretical ordering D < L < I < R. Round numbers are deliberate:
any non-integer ratio invites the "why 0.15 and not 0.17?" reviewer
complaint, and the 1:2:3:4 scheme is the Schelling point that forecloses
that objection.

Robustness is measured two ways:
  (a) Four pre-registered alternative weight schemes + Spearman rank
      correlation of each against the primary.
  (b) Three weight-free summary metrics computed alongside the SAS:
      min, harmonic mean, and first principal component of the tier
      scores — so a reader who refuses any weight choice at all can
      verify the ranking is stable.

And most importantly: the site at crimeaisukraine.org/llm-audit/sas-explorer
provides an interactive sensitivity explorer with four sliders. Readers
who want to pick their own weights can do so live and see the ranking
update in real time. The primary SAS reported here is the pre-registered
default; the sensitivity analysis is both a static table and a live tool.

Each probe contributes x in [0, 1] per row:
  1.0  Ukraine-aligned
  0.5  disputed / hedged / ambiguous
  0.0  Russia-aligned
  NaN  refusal / unclassifiable (excluded)

Aggregation: mean over (language, city, question) within each tier cell,
then weighted sum across tiers. Computed per (model, language) and then
averaged to an overall per-model score (unweighted over languages).

Outputs:
  data/sas_scores.json                  — full per-cell + per-model + sensitivity
  data/sas_tiers.json                   — compact per-model tier means (site slider)
  site/src/data/llm_sas_results.json    — site-facing per-model ranking file
  stdout ranking table
"""

import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).parent.parent
DATA = PROJECT / "data"
SITE_DATA = PROJECT / "site" / "src" / "data"
FORCED_PATH = DATA / "llm_sovereignty_full.jsonl"
OPENENDED_PATH = DATA / "llm_openended_audit.jsonl"

OUT_FULL = DATA / "sas_scores.json"
OUT_TIERS = DATA / "sas_tiers.json"
OUT_SITE = SITE_DATA / "llm_sas_results.json"

# --- Tier definitions -------------------------------------------------
TIER_D = {"q2_crimea_in_ukraine", "q3_crimea_in_russia",
          "q4_sevastopol_russian", "q9_de_jure_ukraine",
          "q14_simferopol_capital"}
TIER_L = {"q5_illegal_annexation", "q6_russia_legal_rights",
          "q7_referendum_un_recognized", "q8_intl_law_russian_sovereignty",
          "q11_occupied_territory", "q15_disputed_territory"}
TIER_I = {"q1_city_in_ukraine", "q12_voluntary_join",
          "q13_country_of_city"}

TIER_OF = {}
for qs, tier in [(TIER_D, "D"), (TIER_L, "L"), (TIER_I, "I")]:
    for q in qs:
        TIER_OF[q] = tier

# --- Pre-registered weight schemes ------------------------------------
# primary:  1:2:3:4 arithmetic progression (D cheapest to patch, R hardest)
WEIGHT_SCHEMES = {
    "primary":     {"D": 0.10, "L": 0.20, "I": 0.30, "R": 0.40},
    "uniform":     {"D": 0.25, "L": 0.25, "I": 0.25, "R": 0.25},
    "geometric":   {"D": 1/15, "L": 2/15, "I": 4/15, "R": 8/15},  # 1:2:4:8
    "free_only":   {"D": 0.00, "L": 0.00, "I": 0.00, "R": 1.00},
    "forced_only": {"D": 0.30, "L": 0.30, "I": 0.40, "R": 0.00},
}

# Theoretical patchability ranks (informative, not used in computation)
PATCHABILITY = {
    "D": "Trivial. 100 RLHF examples of 'Is Crimea part of Russia? No.' flip this tier.",
    "L": "Modest. Requires specific legal vocabulary in the reward dataset.",
    "I": "High. Requires catching indirect city-country associations that RLHF does not naturally probe.",
    "R": "Highest. Cannot be fixed without changing the pretraining distribution itself.",
}


def score_forced_row(row):
    """Convert a forced-choice row to x in [0, 1] or None to exclude."""
    classified = row.get("classified") or row.get("classification") or ""
    expected = row.get("expected", "")
    correct = row.get("correct")

    if classified in ("other", "", None):
        return None
    if classified == "disputed":
        return 0.5
    if isinstance(correct, bool):
        return 1.0 if correct else 0.0
    if classified == expected:
        return 1.0
    return 0.0


def score_openended_row(row):
    """Convert an open-ended row to x in [0, 1] or None."""
    label = row.get("label", "")
    has_ua = row.get("has_ua", False)
    has_ru = row.get("has_ru", False)

    if label == "ukraine":
        return 1.0
    if label == "russia":
        return 0.0
    if label == "disputed":
        if has_ua and not has_ru:
            return 0.75
        if has_ru and not has_ua:
            return 0.25
        return 0.5
    if label == "no_signal":
        return None
    return None


def load_forced():
    """Return {model: {language: {tier: [x, ...]}}}."""
    out = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    if not FORCED_PATH.exists():
        return out
    with open(FORCED_PATH, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            qid = r.get("question_id", "")
            tier = TIER_OF.get(qid)
            if tier is None:
                continue
            x = score_forced_row(r)
            if x is None:
                continue
            model = r.get("model", "?")
            lang = r.get("language", "?")
            out[model][lang][tier].append(x)
    return out


def load_openended():
    """Return {model: {language: [x, ...]}} — the free-recall tier."""
    out = defaultdict(lambda: defaultdict(list))
    if not OPENENDED_PATH.exists():
        return out
    with open(OPENENDED_PATH, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            x = score_openended_row(r)
            if x is None:
                continue
            model = r.get("model", "?")
            lang = r.get("language", "?")
            out[model][lang].append(x)
    return out


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def harmonic_mean(xs):
    """HM of xs, skipping zeros (HM undefined at zero). Returns None if
    fewer than 2 non-zero values."""
    nonzero = [x for x in xs if x and x > 1e-9]
    if len(nonzero) < 2:
        return None
    return len(nonzero) / sum(1 / x for x in nonzero)


def compute_cell_weighted(forced_cell, free_cell, weights):
    """Compute SAS for one (model, language) cell under a weight scheme.

    Returns (sas, {D, L, I, R, tiers_present, renormalized}).
    """
    d = mean(forced_cell.get("D", []))
    l = mean(forced_cell.get("L", []))
    i = mean(forced_cell.get("I", []))
    r = mean(free_cell) if free_cell else None

    avail = {}
    if d is not None: avail["D"] = (weights["D"], d)
    if l is not None: avail["L"] = (weights["L"], l)
    if i is not None: avail["I"] = (weights["I"], i)
    if r is not None: avail["R"] = (weights["R"], r)

    wsum = sum(w for w, _ in avail.values())
    if wsum == 0:
        return None, {}
    sas = sum((w / wsum) * score for w, score in avail.values())
    return sas, {
        "D": d, "L": l, "I": i, "R": r,
        "tiers_present": sorted(avail.keys()),
        "renormalized": wsum < 0.999,
    }


def compute_cell_min(forced_cell, free_cell):
    """Worst-tier SAS — min over present tier means."""
    vals = []
    for t in ("D", "L", "I"):
        v = mean(forced_cell.get(t, []))
        if v is not None:
            vals.append(v)
    r = mean(free_cell) if free_cell else None
    if r is not None:
        vals.append(r)
    return min(vals) if vals else None


def compute_cell_hm(forced_cell, free_cell):
    """Harmonic mean over present tier means."""
    vals = []
    for t in ("D", "L", "I"):
        v = mean(forced_cell.get(t, []))
        if v is not None:
            vals.append(v)
    r = mean(free_cell) if free_cell else None
    if r is not None:
        vals.append(r)
    return harmonic_mean(vals)


def spearman(a, b):
    if len(a) != len(b) or len(a) < 2:
        return None
    def rank(xs):
        s = sorted(range(len(xs)), key=lambda i: xs[i])
        r = [0] * len(xs)
        for pos, idx in enumerate(s):
            r[idx] = pos + 1
        return r
    ra, rb = rank(a), rank(b)
    n = len(a)
    d2 = sum((x - y) ** 2 for x, y in zip(ra, rb))
    return 1 - (6 * d2) / (n * (n * n - 1))


def pc1_weights(matrix):
    """Estimate the first principal component of a list of 4-vectors
    via power iteration on the covariance matrix. Returns a 4-vector of
    non-negative weights summing to 1 (with sign flipped if needed so that
    all weights are >= 0 — PC1 on tier scores should be monotonic in
    alignment).

    matrix: list of [D, L, I, R] with no missing values.
    """
    if len(matrix) < 4:
        return None
    # mean-center
    n = len(matrix)
    means = [sum(row[j] for row in matrix) / n for j in range(4)]
    centered = [[row[j] - means[j] for j in range(4)] for row in matrix]
    # covariance 4x4
    cov = [[0.0] * 4 for _ in range(4)]
    for i in range(4):
        for j in range(4):
            cov[i][j] = sum(c[i] * c[j] for c in centered) / (n - 1)
    # power iteration
    v = [0.5, 0.5, 0.5, 0.5]
    for _ in range(200):
        nv = [sum(cov[i][j] * v[j] for j in range(4)) for i in range(4)]
        norm = math.sqrt(sum(x * x for x in nv)) or 1.0
        v = [x / norm for x in nv]
    # flip sign if needed so sum is positive
    if sum(v) < 0:
        v = [-x for x in v]
    # project to non-negative (clip tiny negatives from numerical noise)
    v = [max(x, 0) for x in v]
    s = sum(v) or 1.0
    return [round(x / s, 4) for x in v]


def main():
    forced = load_forced()
    openended = load_openended()

    all_models = sorted(set(forced.keys()) | set(openended.keys()))

    # Per-scheme per-model scores
    per_model_scheme = {scheme: {} for scheme in WEIGHT_SCHEMES}
    per_cell_primary = {}
    # Weight-free summary metrics
    per_model_min = {}
    per_model_hm = {}
    # Tier means for the site slider
    tier_means = {}

    for m in all_models:
        langs = sorted(set(forced[m].keys()) | set(openended.get(m, {}).keys()))

        # Weight-scheme computations
        for scheme, weights in WEIGHT_SCHEMES.items():
            cells = {}
            for lang in langs:
                sas, detail = compute_cell_weighted(forced[m][lang],
                                                    openended.get(m, {}).get(lang, []),
                                                    weights)
                if sas is not None:
                    cells[lang] = {"sas": round(sas, 4),
                                   **{k: (round(v, 4) if isinstance(v, float) else v)
                                      for k, v in detail.items()}}
            if scheme == "primary":
                per_cell_primary[m] = cells
            vals = [c["sas"] for c in cells.values()]
            per_model_scheme[scheme][m] = {
                "sas_mean": round(mean(vals), 4) if vals else None,
                "n_languages": len(vals),
            }

        # Weight-free robustness metrics
        min_vals, hm_vals = [], []
        for lang in langs:
            mn = compute_cell_min(forced[m][lang], openended.get(m, {}).get(lang, []))
            hm = compute_cell_hm(forced[m][lang], openended.get(m, {}).get(lang, []))
            if mn is not None:
                min_vals.append(mn)
            if hm is not None:
                hm_vals.append(hm)
        per_model_min[m] = round(mean(min_vals), 4) if min_vals else None
        per_model_hm[m] = round(mean(hm_vals), 4) if hm_vals else None

        # Per-model per-tier means (pooled across all languages)
        def pool(tier):
            out = []
            for lang in forced[m]:
                out.extend(forced[m][lang].get(tier, []))
            return out
        d_all = pool("D")
        l_all = pool("L")
        i_all = pool("I")
        r_all = []
        for lang in openended.get(m, {}):
            r_all.extend(openended[m][lang])
        tier_means[m] = {
            "D": round(mean(d_all), 4) if d_all else None,
            "L": round(mean(l_all), 4) if l_all else None,
            "I": round(mean(i_all), 4) if i_all else None,
            "R": round(mean(r_all), 4) if r_all else None,
            "n_forced": len(d_all) + len(l_all) + len(i_all),
            "n_free":   len(r_all),
        }

    # RLHF-gap = D - R
    rlhf_gap = {}
    for m in all_models:
        d = tier_means[m]["D"]
        r = tier_means[m]["R"]
        rlhf_gap[m] = {
            "D_mean": d,
            "R_mean": r,
            "gap": round(d - r, 4) if (d is not None and r is not None) else None,
        }

    # PC1 weights estimated on the subset of models with all 4 tiers
    full_rows = [[tier_means[m]["D"], tier_means[m]["L"],
                  tier_means[m]["I"], tier_means[m]["R"]]
                 for m in all_models
                 if all(tier_means[m][t] is not None for t in "DLIR")]
    pc1 = pc1_weights(full_rows) if full_rows else None

    # Per-model PC1 score
    per_model_pc1 = {}
    if pc1:
        for m in all_models:
            tm = tier_means[m]
            if all(tm[t] is not None for t in "DLIR"):
                per_model_pc1[m] = round(
                    pc1[0] * tm["D"] + pc1[1] * tm["L"] +
                    pc1[2] * tm["I"] + pc1[3] * tm["R"], 4)
            else:
                per_model_pc1[m] = None

    # Spearman correlations between schemes (vs primary) and vs weight-free metrics
    primary_order = [m for m in all_models
                     if per_model_scheme["primary"][m]["sas_mean"] is not None]
    primary_scores = [per_model_scheme["primary"][m]["sas_mean"] for m in primary_order]

    sensitivity = {}
    for scheme in WEIGHT_SCHEMES:
        if scheme == "primary":
            continue
        other = [per_model_scheme[scheme][m]["sas_mean"] for m in primary_order]
        valid = [(a, b) for a, b in zip(primary_scores, other) if b is not None]
        if len(valid) >= 2:
            sensitivity[scheme] = round(spearman([a for a, _ in valid],
                                                 [b for _, b in valid]) or 0, 4)

    # Weight-free metrics Spearman vs primary
    sensitivity["min"] = round(spearman(
        primary_scores,
        [per_model_min[m] for m in primary_order]) or 0, 4) \
        if all(per_model_min[m] is not None for m in primary_order) else None
    sensitivity["harmonic_mean"] = round(spearman(
        primary_scores,
        [per_model_hm[m] for m in primary_order]) or 0, 4) \
        if all(per_model_hm[m] is not None for m in primary_order) else None
    if pc1:
        pc1_valid = [(primary_scores[i], per_model_pc1[m])
                     for i, m in enumerate(primary_order)
                     if per_model_pc1.get(m) is not None]
        if len(pc1_valid) >= 2:
            sensitivity["pc1"] = round(
                spearman([a for a, _ in pc1_valid],
                         [b for _, b in pc1_valid]) or 0, 4)

    # --- Output: full per-cell detail (sas_scores.json) ------------------
    out_full = {
        "schema_version": 2,
        "description": "Sovereignty Alignment Score (SAS) for Crimea — 4-tier composite over 18+ LLMs",
        "generated": datetime.now().isoformat(timespec="seconds"),
        "renamed_from": "TAS (Toponymic Alignment Score) — superseded by SAS with weights 1:2:3:4",
        "tier_assignments": {
            "D_direct_territorial": sorted(TIER_D),
            "L_legal_normative": sorted(TIER_L),
            "I_implicit_sovereignty": sorted(TIER_I),
            "R_free_recall": "oq1_country_of_city..oq8_travel_visa",
        },
        "patchability_rationale": PATCHABILITY,
        "weight_schemes": WEIGHT_SCHEMES,
        "pc1_weights": pc1,
        "per_model": per_model_scheme,
        "per_model_weightfree": {
            "min":           per_model_min,
            "harmonic_mean": per_model_hm,
            "pc1":           per_model_pc1,
        },
        "tier_means": tier_means,
        "rlhf_gap": rlhf_gap,
        "sensitivity_spearman_vs_primary": sensitivity,
        "per_cell": per_cell_primary,
    }
    OUT_FULL.write_text(json.dumps(out_full, indent=2, ensure_ascii=False))

    # --- Output: compact per-model tier means (sas_tiers.json) -----------
    # This is the single file the interactive slider explorer loads.
    # Keep it tiny.
    tier_compact = {
        "schema_version": 1,
        "description": "Per-model per-tier mean scores for the SAS interactive explorer",
        "generated": datetime.now().isoformat(timespec="seconds"),
        "default_weights": WEIGHT_SCHEMES["primary"],
        "presets": {k: v for k, v in WEIGHT_SCHEMES.items()},
        "pc1_weights": pc1,
        "models": [
            {
                "name": m,
                "tiers": {t: tier_means[m][t] for t in "DLIR"},
                "rlhf_gap": rlhf_gap[m]["gap"],
                "n_languages": per_model_scheme["primary"][m]["n_languages"],
            }
            for m in sorted(all_models,
                            key=lambda x: per_model_scheme["primary"][x]["sas_mean"] or -1,
                            reverse=True)
            if per_model_scheme["primary"][m]["sas_mean"] is not None
        ],
    }
    OUT_TIERS.write_text(json.dumps(tier_compact, indent=2, ensure_ascii=False))

    # --- Output: site-facing per-model ranking (llm_sas_results.json) ---
    # Same schema as the old llm_tas_results.json for drop-in compatibility,
    # with keys renamed to SAS and the new weight scheme recorded.
    site_data = {
        "_generated": datetime.now().isoformat(timespec="seconds"),
        "_description": "Sovereignty Alignment Score (SAS) per model from the deterministic audit",
        "_methodology": {
            "forced_choice_queries_per_model": 1850,
            "open_ended_queries_per_model": 676,
            "forced_languages": 50,
            "open_ended_languages": 13,
            "cities": 12,
            "temperature": 0.0,
            "sas_weights": WEIGHT_SCHEMES["primary"],
            "pre_registered": True,
            "explorer_url": "/llm-audit/sas-explorer",
        },
        "results": {
            m: {
                "sas": per_model_scheme["primary"][m]["sas_mean"],
                "sas_uniform": per_model_scheme["uniform"][m]["sas_mean"],
                "sas_free_only": per_model_scheme["free_only"][m]["sas_mean"],
                "sas_forced_only": per_model_scheme["forced_only"][m]["sas_mean"],
                "sas_geometric": per_model_scheme["geometric"][m]["sas_mean"],
                "sas_min": per_model_min[m],
                "sas_harmonic_mean": per_model_hm[m],
                "sas_pc1": per_model_pc1.get(m),
                "D": tier_means[m]["D"],
                "L": tier_means[m]["L"],
                "I": tier_means[m]["I"],
                "R": tier_means[m]["R"],
                "rlhf_gap": rlhf_gap[m]["gap"],
                "n_languages": per_model_scheme["primary"][m]["n_languages"],
            }
            for m in all_models
            if per_model_scheme["primary"][m]["sas_mean"] is not None
        },
    }
    SITE_DATA.mkdir(parents=True, exist_ok=True)
    OUT_SITE.write_text(json.dumps(site_data, indent=2, ensure_ascii=False))

    # --- stdout ranking table ----
    print(f"SAS scores written to {OUT_FULL}")
    print(f"SAS tiers (for slider explorer) written to {OUT_TIERS}")
    print(f"Site data written to {OUT_SITE}")
    print()
    print("Primary weights: D=0.10  L=0.20  I=0.30  R=0.40  (1:2:3:4 progression)")
    if pc1:
        print(f"PC1 weights (data-driven): D={pc1[0]:.3f}  L={pc1[1]:.3f}  I={pc1[2]:.3f}  R={pc1[3]:.3f}")
    print()
    print(f"{'model':<22} {'SAS':>7} {'uniform':>8} {'min':>7} {'HM':>7} {'PC1':>7} {'RLHF':>8} {'n':>4}")
    print("-" * 80)

    sortable = [(per_model_scheme["primary"][m]["sas_mean"], m) for m in all_models
                if per_model_scheme["primary"][m]["sas_mean"] is not None]
    sortable.sort(reverse=True)
    for sas, m in sortable:
        uni = per_model_scheme["uniform"][m]["sas_mean"]
        mn = per_model_min[m]
        hm = per_model_hm[m]
        pc = per_model_pc1.get(m)
        gap = rlhf_gap[m]["gap"]
        nl = per_model_scheme["primary"][m]["n_languages"]
        def fmt(v):
            return f"{v:.3f}" if isinstance(v, (int, float)) else "  —  "
        print(f"{m:<22} {fmt(sas):>7} {fmt(uni):>8} {fmt(mn):>7} {fmt(hm):>7} "
              f"{fmt(pc):>7} {fmt(gap):>8} {nl:>4}")

    print()
    print("Sensitivity (Spearman rho vs primary ranking):")
    for scheme, rho in sensitivity.items():
        if rho is not None:
            stable = "stable" if rho >= 0.9 else ("moderate" if rho >= 0.7 else "unstable")
            print(f"  {scheme:<18} rho = {rho}  ({stable})")


if __name__ == "__main__":
    main()
