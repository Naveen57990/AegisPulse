"""
AegisPulse: Hemodynamic Shock & Cardiovascular Decompensation Engine
Pure Python deterministic clinical kinetics modeling for rapid triage and early warning.
"""

from typing import Dict, Any, List
import math


def calculate_map(sbp: float, dbp: float) -> float:
    """Calculates Mean Arterial Pressure (MAP) in mmHg."""
    if sbp < dbp:
        raise ValueError("Systolic blood pressure cannot be lower than diastolic blood pressure.")
    return dbp + (sbp - dbp) / 3.0


def calculate_shock_index(hr: float, sbp: float) -> float:
    """Calculates standard Shock Index (SI = HR / SBP)."""
    if sbp <= 0:
        raise ValueError("Systolic BP must be greater than zero.")
    return hr / sbp


def calculate_modified_shock_index(hr: float, sbp: float, dbp: float) -> float:
    """Calculates Modified Shock Index (MSI = HR / MAP)."""
    mean_ap = calculate_map(sbp, dbp)
    if mean_ap <= 0:
        raise ValueError("Mean Arterial Pressure must be greater than zero.")
    return hr / mean_ap


def calculate_age_adjusted_si(hr: float, sbp: float, age: float) -> float:
    """Calculates Age-multiplied Shock Index (Age * SI)."""
    si = calculate_shock_index(hr, sbp)
    return si * age


def evaluate_hemodynamic_state(
    hr: float,
    sbp: float,
    dbp: float,
    spo2: float,
    rr: float,
    temp_c: float = 37.0,
    age: float = 45.0
) -> Dict[str, Any]:
    """
    Evaluates comprehensive cardiovascular stability and decompensation risk.
    Returns computed indices, risk tier, and clinical action protocols.
    """
    map_val = calculate_map(sbp, dbp)
    si = calculate_shock_index(hr, sbp)
    msi = calculate_modified_shock_index(hr, sbp, dbp)
    age_si = calculate_age_adjusted_si(hr, sbp, age)
    pulse_pressure = sbp - dbp
    rate_pressure_product = hr * sbp

    # Early Warning Composite Score (NEWS2 approximation)
    news_points = 0
    
    # Respiration Rate
    if rr <= 8 or rr >= 25:
        news_points += 3
    elif 21 <= rr <= 24:
        news_points += 2
    elif 9 <= rr <= 11:
        news_points += 1
        
    # SpO2
    if spo2 <= 91:
        news_points += 3
    elif 92 <= spo2 <= 93:
        news_points += 2
    elif 94 <= spo2 <= 95:
        news_points += 1
        
    # Systolic BP
    if sbp <= 90:
        news_points += 3
    elif 91 <= sbp <= 100:
        news_points += 2
    elif 101 <= sbp <= 110:
        news_points += 1
    elif sbp >= 220:
        news_points += 3
        
    # Heart Rate
    if hr <= 40 or hr >= 131:
        news_points += 3
    elif 111 <= hr <= 130:
        news_points += 2
    elif 41 <= hr <= 50 or 91 <= hr <= 110:
        news_points += 1
        
    # Temperature
    if temp_c <= 35.0:
        news_points += 3
    elif temp_c >= 39.1:
        news_points += 2
    elif (35.1 <= temp_c <= 36.0) or (38.1 <= temp_c <= 39.0):
        news_points += 1

    # Shock Severity Classification
    if si >= 1.3 or msi >= 1.7 or sbp < 80 or news_points >= 7:
        severity = "CRITICAL_COLLAPSE"
        action = "Immediate resuscitation, emergent vasopressor/fluid protocol, bedside ultrasound."
        mortality_risk_pct = 48.5
    elif si >= 0.9 or msi >= 1.3 or pulse_pressure < 30 or news_points >= 5:
        severity = "IMPENDING_SHOCK"
        action = "Urgent clinical escalation, continuous arterial monitoring, IV access, lactate check."
        mortality_risk_pct = 19.2
    elif si >= 0.7 or msi >= 0.9 or news_points >= 3:
        severity = "ELEVATED_RISK"
        action = "Increased vital surveillance every 15 min, re-evaluate underlying infection/blood loss."
        mortality_risk_pct = 5.4
    else:
        severity = "STABLE"
        action = "Routine surveillance according to baseline telemetry protocol."
        mortality_risk_pct = 0.8

    return {
        "heart_rate": hr,
        "blood_pressure": f"{int(sbp)}/{int(dbp)}",
        "mean_arterial_pressure": round(map_val, 1),
        "pulse_pressure": round(pulse_pressure, 1),
        "rate_pressure_product": round(rate_pressure_product, 0),
        "shock_index": round(si, 3),
        "modified_shock_index": round(msi, 3),
        "age_adjusted_si": round(age_si, 1),
        "news_score": news_points,
        "severity": severity,
        "mortality_risk_pct": mortality_risk_pct,
        "clinical_action": action
    }
