#!/usr/bin/env python3
"""
AegisPulse: Tactical Clinical Telemetry & Triage CLI
Edge-native ICU/ER Hemodynamic Shock Forecasting & Non-linear HRV Analytics
"""

import sys
import json
import argparse
from pathlib import Path

# Add parent directory to path for engine imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

try:
    from hemodynamic_engine import evaluate_hemodynamic_state
    from hrv_entropy import analyze_autonomic_profile
    from triage_prioritizer import prioritize_patient_roster
except ImportError as e:
    print(f"Error importing AegisPulse engine: {e}")
    sys.exit(1)


BANNER = r"""
    ___              _       ____        __          
   /   | ___  ____ _(_)____ / __ \__  __/ /___  ___   
  / /| |/ _ \/ __ `/ / ___// /_/ / / / / / __ \/ _ \  
 / ___ /  __/ /_/ / (__  )/ ____/ /_/ / / /_/ /  __/  
/_/  |_\___/\__, /_//____/_/    \__,_/_/ .___/\___/   
           /____/                     /_/             
  >> Clinical Hemodynamic Shock & Autonomic Entropy Suite <<
"""


def cmd_hemodynamics(args):
    print(BANNER)
    print(f"[*] Evaluating Hemodynamics for Patient...")
    result = evaluate_hemodynamic_state(
        hr=args.hr,
        sbp=args.sbp,
        dbp=args.dbp,
        spo2=args.spo2,
        rr=args.rr,
        temp_c=args.temp,
        age=args.age
    )
    
    print("\n" + "="*50)
    print(f" Heart Rate:           {result['heart_rate']} bpm")
    print(f" Blood Pressure:       {result['blood_pressure']} mmHg (MAP: {result['mean_arterial_pressure']} mmHg)")
    print(f" Shock Index (SI):     {result['shock_index']} (Normal < 0.7, Shock >= 0.9)")
    print(f" Modified SI (MSI):    {result['modified_shock_index']}")
    print(f" Age-Adjusted SI:      {result['age_adjusted_si']}")
    print(f" NEWS-2 Score:         {result['news_score']} points")
    print(f" Clinical Severity:    [{result['severity']}]")
    print(f" Mortality Risk:       {result['mortality_risk_pct']}%")
    print(f" Action Protocol:      {result['clinical_action']}")
    print("="*50 + "\n")


def cmd_hrv(args):
    print(BANNER)
    if args.intervals:
        rr_list = [float(x.strip()) for x in args.intervals.split(",")]
    else:
        # Default physiological series
        rr_list = [810.0, 835.0, 790.0, 820.0, 845.0, 800.0, 830.0, 815.0, 840.0, 795.0, 825.0]
        
    print(f"[*] Analyzing RR interval series ({len(rr_list)} beats)...")
    profile = analyze_autonomic_profile(rr_list)
    
    print("\n" + "="*50)
    print(f" Mean RR:              {profile['mean_rr_ms']} ms ({profile['mean_hr_bpm']} bpm)")
    print(f" SDNN:                 {profile['sdnn_ms']} ms")
    print(f" RMSSD:                {profile['rmssd_ms']} ms")
    print(f" pNN50:                {profile['pnn50_pct']}%")
    print(f" Poincaré SD1 (Vagal): {profile['sd1_ms']} ms")
    print(f" Poincaré SD2 (Total): {profile['sd2_ms']} ms")
    print(f" SD1/SD2 Ratio:        {profile['sd1_sd2_ratio']}")
    print(f" Sample Entropy:       {profile['sample_entropy']}")
    print(f" Autonomic Status:     [{profile['autonomic_status']}]")
    print(f" Autonomic Score:      {profile['autonomic_health_score']} / 100")
    print(f" Clinical Description: {profile['autonomic_description']}")
    print("="*50 + "\n")


def cmd_triage(args):
    print(BANNER)
    print(f"[*] Running Bayesian Dynamic Triage Prioritization...\n")
    
    sample_roster = [
        {
            "patient_id": "BED-01",
            "name": "Sarah Jenkins",
            "age": 58,
            "baseline_risk": 0.15,
            "vitals": {"hr": 128, "sbp": 82, "dbp": 48, "spo2": 89, "rr": 26, "temp_c": 39.2},
            "rr_intervals_ms": [468.0, 470.0, 467.0, 469.0, 468.0, 471.0, 469.0, 468.0]
        },
        {
            "patient_id": "BED-02",
            "name": "Robert Miller",
            "age": 64,
            "baseline_risk": 0.08,
            "vitals": {"hr": 76, "sbp": 128, "dbp": 82, "spo2": 97, "rr": 15, "temp_c": 36.9},
            "rr_intervals_ms": [790.0, 810.0, 780.0, 820.0, 805.0, 785.0, 815.0]
        },
        {
            "patient_id": "BED-03",
            "name": "Amira Patel",
            "age": 42,
            "baseline_risk": 0.20,
            "vitals": {"hr": 114, "sbp": 98, "dbp": 62, "spo2": 93, "rr": 22, "temp_c": 38.4},
            "rr_intervals_ms": [525.0, 540.0, 520.0, 535.0, 545.0, 520.0, 530.0]
        },
        {
            "patient_id": "BED-04",
            "name": "Thomas Thorne",
            "age": 79,
            "baseline_risk": 0.30,
            "vitals": {"hr": 142, "sbp": 68, "dbp": 38, "spo2": 84, "rr": 31, "temp_c": 39.8},
            "rr_intervals_ms": [422.0, 424.0, 421.0, 423.0, 422.0, 425.0, 422.0]
        }
    ]
    
    prioritized = prioritize_patient_roster(sample_roster)
    
    print(f"{'RANK':<5} {'BED':<8} {'PATIENT':<16} {'AGE':<5} {'ESI':<5} {'COLLAPSE %':<12} {'SEVERITY':<20} {'URGENCY'}")
    print("-" * 85)
    for p in prioritized:
        print(f"#{p['triage_rank']:<4} {p['patient_id']:<8} {p['name']:<16} {p['age']:<5} ESI-{p['esi_tier']:<2} {p['collapse_probability_pct']:>5.1f}%      {p['hemodynamics']['severity']:<20} {p['urgency_score']:>6.1f}")
    print("-" * 85 + "\n")


def main():
    parser = argparse.ArgumentParser(description="AegisPulse Clinical Telemetry CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Hemodynamics command
    p_hemo = subparsers.add_parser("hemo", help="Evaluate hemodynamic shock state")
    p_hemo.add_argument("--hr", type=float, default=115.0, help="Heart Rate (bpm)")
    p_hemo.add_argument("--sbp", type=float, default=95.0, help="Systolic BP (mmHg)")
    p_hemo.add_argument("--dbp", type=float, default=60.0, help="Diastolic BP (mmHg)")
    p_hemo.add_argument("--spo2", type=float, default=93.0, help="Oxygen Saturation (percent)")
    p_hemo.add_argument("--rr", type=float, default=24.0, help="Respiratory Rate (bpm)")
    p_hemo.add_argument("--temp", type=float, default=38.5, help="Temperature (C)")
    p_hemo.add_argument("--age", type=float, default=55.0, help="Patient Age")
    
    # HRV command
    p_hrv = subparsers.add_parser("hrv", help="Analyze HRV and Poincaré entropy")
    p_hrv.add_argument("--intervals", type=str, default="", help="Comma-separated RR intervals in ms")
    
    # Triage command
    p_triage = subparsers.add_parser("triage", help="Run multi-patient ICU triage optimization")
    
    args = parser.parse_args()
    if args.command == "hemo":
        cmd_hemodynamics(args)
    elif args.command == "hrv":
        cmd_hrv(args)
    elif args.command == "triage":
        cmd_triage(args)
    else:
        # Default to triage demo
        cmd_triage(args)


if __name__ == "__main__":
    main()
