"""Statistical analysis and reporting for Empirical Pilot Sessions.

Evaluates:
1. Direct Pre-Aim Mechanism: Delta E^reveal (shrinkage in reveal aim error) vs Delta M_knowledge.
2. Continuous Performance: Delta L_realized (reduction in realized lateness) vs Delta M_knowledge.
3. Feasibility Boundary Crossing: Survival flips on M_reveal < 0 -> M_preaim >= 0 stimuli.
4. Psychometric Ratings: Fairness vs M_reveal and Readability vs M_preaim.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
from scipy import stats
from sklearn.metrics import roc_auc_score


def analyze_pilot_session_file(session_file: str) -> Dict[str, Any]:
    """Load and statistically analyze a pilot session JSON file."""
    with open(session_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Exclude practice trials from experimental analysis
    all_trials = data.get("trials", [])
    exp_trials = [t for t in all_trials if not t.get("is_practice", False)]
    calib = data.get("calibration", {})

    if not exp_trials:
        raise ValueError(f"No experimental trial data found in {session_file}")

    b1_trials = [t for t in exp_trials if t["block_index"] == 1]
    b2_trials = [t for t in exp_trials if t["block_index"] == 2]
    b3_trials = [t for t in exp_trials if t["block_index"] == 3]

    # 1. Survival Rates per Block
    surv_b1 = np.mean([1 if t["player_survived"] else 0 for t in b1_trials]) if b1_trials else 0.0
    surv_b2 = np.mean([1 if t["player_survived"] else 0 for t in b2_trials]) if b2_trials else 0.0
    surv_b3 = np.mean([1 if t["player_survived"] else 0 for t in b3_trials]) if b3_trials else 0.0

    # 2. Predictive Validity of M_reveal vs M_preaim
    def calc_auc(t_list, metric_key):
        y_true = [1 if t["player_survived"] else 0 for t in t_list]
        scores = [t[metric_key] for t in t_list]
        if len(set(y_true)) < 2:
            return float('nan')
        return float(roc_auc_score(y_true, scores))

    auc_m_reveal_b1 = calc_auc(b1_trials, "m_reveal_canonical_tics")
    auc_m_preaim_b1 = calc_auc(b1_trials, "m_preaim_canonical_tics")
    auc_m_reveal_b3 = calc_auc(b3_trials, "m_reveal_canonical_tics")
    auc_m_preaim_b3 = calc_auc(b3_trials, "m_preaim_canonical_tics")

    # 3. Intermediate Pre-Aim & Continuous Learning Telemetry
    arena_ids = sorted(list({t["arena_id"] for t in exp_trials}))
    arena_stats = []
    delta_knowledge_vals = []
    delta_lateness_vals = []
    delta_aim_err_vals = []
    delta_surv_vals = []

    for a_id in arena_ids:
        a_b1 = [t for t in b1_trials if t["arena_id"] == a_id]
        a_b3 = [t for t in b3_trials if t["arena_id"] == a_id]
        if a_b1 and a_b3:
            s_b1 = 1 if a_b1[0]["player_survived"] else 0
            s_b3 = 1 if a_b3[0]["player_survived"] else 0
            lat_b1 = a_b1[0]["realized_lateness_tics"]
            lat_b3 = a_b3[0]["realized_lateness_tics"]
            err_b1 = a_b1[0].get("mean_reveal_aim_error_deg", 0.0)
            err_b3 = a_b3[0].get("mean_reveal_aim_error_deg", 0.0)

            delta_lat = lat_b1 - lat_b3          # Positive = lateness reduced (improvement)
            delta_err = err_b1 - err_b3          # Positive = aim error reduced (pre-aiming occurred)
            delta_s = s_b3 - s_b1
            delta_k = a_b1[0]["delta_m_knowledge_tics"]

            delta_knowledge_vals.append(delta_k)
            delta_lateness_vals.append(delta_lat)
            delta_aim_err_vals.append(delta_err)
            delta_surv_vals.append(delta_s)

            arena_stats.append({
                "arena_id": a_id,
                "category": a_b1[0]["category"],
                "m_reveal": a_b1[0]["m_reveal_canonical_tics"],
                "m_preaim": a_b1[0]["m_preaim_canonical_tics"],
                "delta_m_knowledge": delta_k,
                "survived_b1": bool(s_b1),
                "survived_b3": bool(s_b3),
                "err_b1": err_b1,
                "err_b3": err_b3,
                "delta_aim_err": delta_err,
                "lat_b1": lat_b1,
                "lat_b3": lat_b3,
                "delta_lateness": delta_lat,
                "delta_survival": delta_s,
                "readability_b1": a_b1[0].get("readability_rating"),
                "readability_b3": a_b3[0].get("readability_rating"),
                "fairness_b1": a_b1[0].get("fairness_rating"),
                "fairness_b3": a_b3[0].get("fairness_rating")
            })

    # Direct Pre-Aim Hypothesis: Delta M_knowledge -> Delta Reveal Aim Error Reduction
    spearman_aim = stats.spearmanr(delta_knowledge_vals, delta_aim_err_vals)
    rho_aim_reduction = float(spearman_aim.statistic) if not np.isnan(spearman_aim.statistic) else 0.0

    # Continuous Learning Hypothesis: Delta M_knowledge -> Delta Lateness Reduction
    spearman_lat = stats.spearmanr(delta_knowledge_vals, delta_lateness_vals)
    rho_lateness_reduction = float(spearman_lat.statistic) if not np.isnan(spearman_lat.statistic) else 0.0

    # Secondary Survival Gain Hypothesis
    spearman_surv = stats.spearmanr(delta_knowledge_vals, delta_surv_vals)
    rho_surv = float(spearman_surv.statistic) if not np.isnan(spearman_surv.statistic) else 0.0

    # Psychometric Correlations
    all_fairness = [t["fairness_rating"] for t in exp_trials if t.get("fairness_rating") is not None]
    all_readability = [t["readability_rating"] for t in exp_trials if t.get("readability_rating") is not None]
    all_m_reveal = [t["m_reveal_canonical_tics"] for t in exp_trials if t.get("fairness_rating") is not None]
    all_m_preaim = [t["m_preaim_canonical_tics"] for t in exp_trials if t.get("readability_rating") is not None]

    rho_fairness = float(stats.spearmanr(all_m_reveal, all_fairness).statistic) if all_fairness else 0.0
    rho_readability = float(stats.spearmanr(all_m_preaim, all_readability).statistic) if all_readability else 0.0

    return {
        "session_id": data.get("session_id"),
        "player_id": data.get("player_id"),
        "git_commit_hash": data.get("git_commit_hash"),
        "calibration": calib,
        "total_experimental_trials": len(exp_trials),
        "survival_rate_b1_unfamiliar": surv_b1,
        "survival_rate_b2_learning": surv_b2,
        "survival_rate_b3_familiar": surv_b3,
        "auc_m_reveal_b1_unfamiliar": auc_m_reveal_b1,
        "auc_m_preaim_b1_unfamiliar": auc_m_preaim_b1,
        "auc_m_reveal_b3_familiar": auc_m_reveal_b3,
        "auc_m_preaim_b3_familiar": auc_m_preaim_b3,
        "rho_aim_error_reduction_vs_delta_m": rho_aim_reduction,
        "rho_lateness_reduction_vs_delta_m": rho_lateness_reduction,
        "rho_survival_gain_vs_delta_m": rho_surv,
        "rho_fairness_vs_m_reveal": rho_fairness,
        "rho_readability_vs_m_preaim": rho_readability,
        "arena_breakdown": arena_stats
    }


def print_pilot_analysis_report(summary: Dict[str, Any]):
    """Print comprehensive ASCII table report of empirical pilot findings."""
    calib = summary.get("calibration", {})
    print("\
" + "=" * 96)
    print(f"EMPIRICAL PILOT ANALYSIS REPORT: {summary['session_id']}")
    print(f"Player ID: {summary['player_id']} | Git: {summary.get('git_commit_hash','untracked')} | Experimental Trials: {summary['total_experimental_trials']}")
    if calib:
        print(f"Calibration: Latency A={calib.get('acquisition_latency_s',0)*1000:.1f}ms | Aim omega={calib.get('aim_velocity_deg_s',0):.1f} deg/s")
    print("=" * 96)

    print("\
--- 1. LEARNING TRAJECTORY ACROSS BLOCKS ---")
    print(f"  Phase 1 (UNFAMILIAR / Blind):  {summary['survival_rate_b1_unfamiliar']*100:5.1f}% Survival")
    print(f"  Phase 2 (LEARNING / Repeat):   {summary['survival_rate_b2_learning']*100:5.1f}% Survival")
    print(f"  Phase 3 (FAMILIAR / Pre-Aim):  {summary['survival_rate_b3_familiar']*100:5.1f}% Survival")

    print("\
--- 2. PREDICTIVE VALIDITY (ROC-AUC) ---")
    print(f"  Phase 1 (UNFAMILIAR): AUC(M_reveal) = {summary['auc_m_reveal_b1_unfamiliar']:.3f} | AUC(M_preaim) = {summary['auc_m_preaim_b1_unfamiliar']:.3f}")
    print(f"  Phase 3 (FAMILIAR):   AUC(M_reveal) = {summary['auc_m_reveal_b3_familiar']:.3f} | AUC(M_preaim) = {summary['auc_m_preaim_b3_familiar']:.3f}")

    print("\
--- 3. DIRECT PRE-AIM & CONTINUOUS LEARNING MECHANISMS ---")
    print(f"  Direct Pre-Aim Shift: Spearman rho(Delta M_knowledge, Delta Reveal Aim Error Reduction): {summary['rho_aim_error_reduction_vs_delta_m']:+.3f}")
    print(f"  Lateness Reduction:   Spearman rho(Delta M_knowledge, Delta Lateness Reduction):         {summary['rho_lateness_reduction_vs_delta_m']:+.3f}")
    print(f"  Perceived Fairness:   Spearman rho(M_reveal, Fairness Rating 1-7):                      {summary['rho_fairness_vs_m_reveal']:+.3f}")
    print(f"  Readability:          Spearman rho(M_preaim, Readability Rating 1-7):                   {summary['rho_readability_vs_m_preaim']:+.3f}")

    print("\
--- 4. STIMULUS-BY-STIMULUS EMPIRICAL BREAKDOWN ---")
    print(f"{'Stimulus ID':<32} | {'M_rg':>4} | {'M_pa':>4} | {'dM':>3} | {'B1 Surv':>7} | {'B3 Surv':>7} | {'dErr_deg':>8} | {'dL_lat':>6} | {'B1 Fair':>7} | {'B3 Read':>7}")
    print("-" * 110)
    for a in summary["arena_breakdown"]:
        b1_s = "SURV" if a["survived_b1"] else "DIED"
        b3_s = "SURV" if a["survived_b3"] else "DIED"
        f1_str = f"{a['fairness_b1']}/7" if a['fairness_b1'] is not None else "N/A"
        r3_str = f"{a['readability_b3']}/7" if a['readability_b3'] is not None else "N/A"
        print(f"{a['arena_id']:<32} | {a['m_reveal']:+4d} | {a['m_preaim']:+4d} | {a['delta_m_knowledge']:+3d} | {b1_s:>7} | {b3_s:>7} | {a['delta_aim_err']:+8.1f} | {a['delta_lateness']:+6d} | {f1_str:>7} | {r3_str:>7}")
    print("=" * 110 + "\
")
