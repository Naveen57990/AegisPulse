"""
AegisPulse: Emergency Triage Prioritization & Multi-Patient Queue Balancer
Implements Bayesian clinical risk updating and Emergency Severity Index (ESI) assignment.
"""

from typing import List, Dict, Any
try:
    from .hemodynamic_engine import evaluate_hemodynamic_state
    from .hrv_entropy import analyze_autonomic_profile
except (ImportError, ValueError):
    from hemodynamic_engine import evaluate_hemodynamic_state
    from hrv_entropy import analyze_autonomic_profile


def calculate_bayesian_collapse_probability(
    prior_prob: float,
    hemo_severity: str,
    autonomic_status: str
) -> float:
    """
    Computes posterior probability of imminent hemodynamic collapse using Bayesian evidence integration.
    P(Collapse | Evidence) = P(Evidence | Collapse) * P(Collapse) / P(Evidence)
    """
    # Likelihood ratios
    lr_hemo = {
        "CRITICAL_COLLAPSE": 12.5,
        "IMPENDING_SHOCK": 4.8,
        "ELEVATED_RISK": 1.9,
        "STABLE": 0.2
    }.get(hemo_severity, 1.0)

    lr_hrv = {
        "AUTONOMIC_DECOMPENSATION": 5.2,
        "SYMPATHETIC_DOMINANCE": 2.1,
        "HEALTHY_VARIABILITY": 0.3
    }.get(autonomic_status, 1.0)

    combined_lr = lr_hemo * lr_hrv
    
    # Convert prior probability to odds: Odds = P / (1 - P)
    prior_prob = max(0.01, min(0.99, prior_prob))
    prior_odds = prior_prob / (1.0 - prior_prob)
    
    posterior_odds = prior_odds * combined_lr
    posterior_prob = posterior_odds / (1.0 + posterior_odds)
    
    return round(posterior_prob, 4)


def assign_esi_tier(posterior_prob: float, news_score: int, sbp: float) -> int:
    """
    Assigns Emergency Severity Index (ESI 1 = Resuscitation to ESI 5 = Non-urgent).
    """
    if posterior_prob >= 0.75 or news_score >= 8 or sbp < 75:
        return 1  # Resuscitation (Immediate life threat)
    elif posterior_prob >= 0.40 or news_score >= 5:
        return 2  # Emergent (High risk, confused, severe pain)
    elif posterior_prob >= 0.15 or news_score >= 3:
        return 3  # Urgent (Requires multiple resources, stable vitals)
    elif news_score >= 1:
        return 4  # Less Urgent (Single resource needed)
    else:
        return 5  # Non-urgent (Routine evaluation)


def prioritize_patient_roster(patients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Evaluates, ranks, and prioritizes a roster of ICU / ER patients by acute risk score.
    """
    scored_patients = []
    
    for pt in patients:
        vitals = pt["vitals"]
        rr_series = pt.get("rr_intervals_ms", [800.0, 810.0, 790.0, 805.0, 815.0])
        prior_risk = pt.get("baseline_risk", 0.10)
        
        hemo = evaluate_hemodynamic_state(
            hr=vitals["hr"],
            sbp=vitals["sbp"],
            dbp=vitals["dbp"],
            spo2=vitals["spo2"],
            rr=vitals["rr"],
            temp_c=vitals.get("temp_c", 37.0),
            age=pt.get("age", 50.0)
        )
        
        autonomic = analyze_autonomic_profile(rr_series)
        
        post_prob = calculate_bayesian_collapse_probability(
            prior_prob=prior_risk,
            hemo_severity=hemo["severity"],
            autonomic_status=autonomic["autonomic_status"]
        )
        
        esi = assign_esi_tier(post_prob, hemo["news_score"], vitals["sbp"])
        
        # Composite urgency ranking score (Higher = more urgent)
        urgency_score = (post_prob * 60.0) + (hemo["news_score"] * 4.0) + ((6 - esi) * 5.0)
        
        scored_patients.append({
            "patient_id": pt["patient_id"],
            "name": pt.get("name", "Unknown"),
            "age": pt.get("age", 50),
            "esi_tier": esi,
            "collapse_probability_pct": round(post_prob * 100.0, 1),
            "urgency_score": round(urgency_score, 2),
            "hemodynamics": hemo,
            "autonomic_profile": autonomic
        })
        
    # Sort descending by urgency score (most critical patients first)
    scored_patients.sort(key=lambda x: x["urgency_score"], reverse=True)
    
    # Assign queue ranks
    for rank, p in enumerate(scored_patients, 1):
        p["triage_rank"] = rank
        
    return scored_patients
