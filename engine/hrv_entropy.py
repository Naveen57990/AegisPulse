"""
AegisPulse: Non-linear Heart Rate Variability & Autonomic Dynamics Engine
Computes time-domain, geometric (Poincaré plot), and non-linear entropy metrics from RR intervals.
"""

from typing import List, Dict, Any
import math


def calculate_time_domain_hrv(rr_intervals_ms: List[float]) -> Dict[str, float]:
    """
    Computes standard time-domain HRV indices from RR interval series (in ms).
    - Mean RR, SDNN, RMSSD, pNN50
    """
    if len(rr_intervals_ms) < 3:
        raise ValueError("At least 3 RR intervals are required for time-domain analysis.")

    n = len(rr_intervals_ms)
    mean_rr = sum(rr_intervals_ms) / n
    variance = sum((x - mean_rr) ** 2 for x in rr_intervals_ms) / (n - 1)
    sdnn = math.sqrt(variance)

    # Successive differences
    diffs = [rr_intervals_ms[i + 1] - rr_intervals_ms[i] for i in range(n - 1)]
    rmssd = math.sqrt(sum(d ** 2 for d in diffs) / len(diffs))
    
    # Percentage of successive differences > 50ms
    nn50 = sum(1 for d in diffs if abs(d) > 50.0)
    pnn50 = (nn50 / len(diffs)) * 100.0

    return {
        "mean_rr_ms": round(mean_rr, 2),
        "mean_hr_bpm": round(60000.0 / mean_rr, 1),
        "sdnn_ms": round(sdnn, 2),
        "rmssd_ms": round(rmssd, 2),
        "pnn50_pct": round(pnn50, 2)
    }


def calculate_poincare_geometry(rr_intervals_ms: List[float]) -> Dict[str, float]:
    """
    Calculates Poincaré plot descriptors (SD1, SD2, and SD1/SD2 ratio) using orthogonal projections:
    - SD1^2 = 0.5 * Var(RR_{i+1} - RR_i)
    - SD2^2 = 0.5 * Var(RR_{i+1} + RR_i)
    """
    if len(rr_intervals_ms) < 3:
        raise ValueError("At least 3 RR intervals are required for Poincaré analysis.")

    n = len(rr_intervals_ms) - 1
    # Differences and Sums between consecutive RR intervals
    diffs = [rr_intervals_ms[i + 1] - rr_intervals_ms[i] for i in range(n)]
    sums = [rr_intervals_ms[i + 1] + rr_intervals_ms[i] for i in range(n)]

    mean_diff = sum(diffs) / n
    var_diff = sum((d - mean_diff) ** 2 for d in diffs) / (n - 1 if n > 1 else 1)
    sd1 = math.sqrt(0.5 * var_diff)

    mean_sum = sum(sums) / n
    var_sum = sum((s - mean_sum) ** 2 for s in sums) / (n - 1 if n > 1 else 1)
    sd2 = math.sqrt(0.5 * var_sum)

    ratio = sd1 / sd2 if sd2 > 1e-6 else 0.0
    area_ellipse = math.pi * sd1 * sd2

    return {
        "sd1_ms": round(sd1, 2),
        "sd2_ms": round(sd2, 2),
        "sd1_sd2_ratio": round(ratio, 3),
        "poincare_area": round(area_ellipse, 1)
    }


def calculate_sample_entropy(rr_intervals_ms: List[float], m: int = 2, r_multiplier: float = 0.2) -> float:
    """
    Computes Sample Entropy (SampEn) to assess complexity of cardiac dynamics.
    """
    n = len(rr_intervals_ms)
    if n < 10:
        return 0.0

    mean_rr = sum(rr_intervals_ms) / n
    sdnn = math.sqrt(sum((x - mean_rr) ** 2 for x in rr_intervals_ms) / (n - 1))
    if sdnn < 1e-6:
        return 0.0
    r = max(r_multiplier * sdnn, 15.0)

    def _count_matches(dim: int) -> int:
        count = 0
        vectors = [rr_intervals_ms[i : i + dim] for i in range(n - dim + 1)]
        num_vec = len(vectors)
        for i in range(num_vec):
            for j in range(i + 1, num_vec):
                dist = max(abs(vectors[i][k] - vectors[j][k]) for k in range(dim))
                if dist <= r:
                    count += 1
        return count

    b_matches = _count_matches(m)
    a_matches = _count_matches(m + 1)

    if b_matches == 0:
        return 0.0
    if a_matches == 0:
        return round(-math.log(1.0 / (b_matches + 1)), 4)

    samp_en = -math.log(a_matches / b_matches)
    return round(samp_en, 4)


def analyze_autonomic_profile(rr_intervals_ms: List[float]) -> Dict[str, Any]:
    """
    Integrates time-domain, geometric, and entropy metrics into an actionable autonomic health score.
    """
    time_hrv = calculate_time_domain_hrv(rr_intervals_ms)
    poincare = calculate_poincare_geometry(rr_intervals_ms)
    samp_en = calculate_sample_entropy(rr_intervals_ms)

    if time_hrv["rmssd_ms"] < 15.0 or poincare["sd1_ms"] < 8.0:
        tone_status = "AUTONOMIC_DECOMPENSATION"
        tone_description = "Severe loss of vagal modulation. High vulnerability to septic/arrhythmogenic shock."
        autonomic_score = 22.0
    elif time_hrv["rmssd_ms"] < 25.0 or poincare["sd1_sd2_ratio"] < 0.25:
        tone_status = "SYMPATHETIC_DOMINANCE"
        tone_description = "Acute physiological stress or compensatory tachycardia."
        autonomic_score = 58.0
    else:
        tone_status = "HEALTHY_VARIABILITY"
        tone_description = "Robust vagal buffering and adaptive cardiovascular reserve."
        autonomic_score = 92.5

    return {
        **time_hrv,
        **poincare,
        "sample_entropy": samp_en,
        "autonomic_status": tone_status,
        "autonomic_health_score": autonomic_score,
        "autonomic_description": tone_description
    }
