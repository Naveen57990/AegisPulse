"""
AegisPulse Comprehensive Test Suite
Pure deterministic verification of hemodynamic kinetics, Poincaré geometry, entropy, and Bayesian triage.
"""

import unittest
import time
from hemodynamic_engine import (
    calculate_map,
    calculate_shock_index,
    calculate_modified_shock_index,
    calculate_age_adjusted_si,
    evaluate_hemodynamic_state
)
from hrv_entropy import (
    calculate_time_domain_hrv,
    calculate_poincare_geometry,
    calculate_sample_entropy,
    analyze_autonomic_profile
)
from triage_prioritizer import (
    calculate_bayesian_collapse_probability,
    assign_esi_tier,
    prioritize_patient_roster
)


class TestAegisPulseEngine(unittest.TestCase):

    def test_01_map_and_shock_indices(self):
        # SBP=120, DBP=80 -> MAP = 80 + 40/3 = 93.33
        map_val = calculate_map(120, 80)
        self.assertAlmostEqual(map_val, 93.333, places=2)
        
        # HR=110, SBP=100 -> SI = 1.10
        si = calculate_shock_index(110, 100)
        self.assertEqual(si, 1.1)

        # MSI = 110 / 93.333 = 1.178
        msi = calculate_modified_shock_index(110, 120, 80)
        self.assertAlmostEqual(msi, 1.178, places=2)

    def test_02_hemodynamic_state_classification(self):
        # Severe shock scenario: HR=135, SBP=75, DBP=45, SpO2=88, RR=28
        state_critical = evaluate_hemodynamic_state(
            hr=135, sbp=75, dbp=45, spo2=88, rr=28, temp_c=39.5, age=65
        )
        self.assertEqual(state_critical["severity"], "CRITICAL_COLLAPSE")
        self.assertGreaterEqual(state_critical["news_score"], 7)
        self.assertGreater(state_critical["mortality_risk_pct"], 40.0)

        # Healthy baseline: HR=72, SBP=120, DBP=80, SpO2=99, RR=14
        state_stable = evaluate_hemodynamic_state(
            hr=72, sbp=120, dbp=80, spo2=99, rr=14, temp_c=37.0, age=30
        )
        self.assertEqual(state_stable["severity"], "STABLE")
        self.assertEqual(state_stable["news_score"], 0)

    def test_03_time_domain_hrv(self):
        rr_series = [800.0, 820.0, 780.0, 810.0, 850.0, 790.0, 830.0]
        hrv = calculate_time_domain_hrv(rr_series)
        self.assertAlmostEqual(hrv["mean_rr_ms"], 811.43, places=2)
        self.assertAlmostEqual(hrv["mean_hr_bpm"], 73.9, places=1)
        self.assertGreater(hrv["rmssd_ms"], 0.0)
        self.assertGreater(hrv["sdnn_ms"], 0.0)

    def test_04_poincare_geometry(self):
        rr_series = [800.0, 820.0, 780.0, 810.0, 850.0, 790.0, 830.0]
        poincare = calculate_poincare_geometry(rr_series)
        self.assertGreater(poincare["sd1_ms"], 0.0)
        self.assertGreater(poincare["sd2_ms"], 0.0)
        self.assertGreater(poincare["poincare_area"], 0.0)
        self.assertTrue(0.0 <= poincare["sd1_sd2_ratio"] <= 2.0)

    def test_05_sample_entropy(self):
        # Deterministic periodic vs stochastic
        periodic_rr = [800.0] * 10
        samp_en_periodic = calculate_sample_entropy(periodic_rr)
        self.assertEqual(samp_en_periodic, 0.0)

        varying_rr = [800.0, 810.0, 795.0, 805.0, 815.0, 800.0, 810.0, 795.0, 805.0, 820.0, 800.0, 812.0]
        samp_en_var = calculate_sample_entropy(varying_rr)
        self.assertGreater(samp_en_var, 0.0)

    def test_06_autonomic_profile_integration(self):
        # Severely depressed HRV (rigid septic shock profile)
        rigid_rr = [600.0, 602.0, 601.0, 603.0, 600.0, 602.0, 601.0, 602.0, 601.0, 603.0]
        profile = analyze_autonomic_profile(rigid_rr)
        self.assertEqual(profile["autonomic_status"], "AUTONOMIC_DECOMPENSATION")
        self.assertLess(profile["autonomic_health_score"], 50.0)

    def test_07_bayesian_probability_and_esi(self):
        # High-risk evidence
        post_prob = calculate_bayesian_collapse_probability(
            prior_prob=0.15,
            hemo_severity="CRITICAL_COLLAPSE",
            autonomic_status="AUTONOMIC_DECOMPENSATION"
        )
        self.assertGreater(post_prob, 0.85)
        esi = assign_esi_tier(post_prob, news_score=9, sbp=70)
        self.assertEqual(esi, 1)

        # Low-risk evidence
        post_prob_low = calculate_bayesian_collapse_probability(
            prior_prob=0.05,
            hemo_severity="STABLE",
            autonomic_status="HEALTHY_VARIABILITY"
        )
        self.assertLess(post_prob_low, 0.05)
        esi_low = assign_esi_tier(post_prob_low, news_score=0, sbp=120)
        self.assertEqual(esi_low, 5)

    def test_08_multi_patient_roster_prioritization(self):
        roster = [
            {
                "patient_id": "PT-101",
                "name": "Marcus Vance",
                "age": 62,
                "baseline_risk": 0.10,
                "vitals": {"hr": 74, "sbp": 122, "dbp": 78, "spo2": 98, "rr": 14, "temp_c": 36.8},
                "rr_intervals_ms": [810.0, 830.0, 790.0, 820.0, 840.0, 800.0, 825.0]
            },
            {
                "patient_id": "PT-102",
                "name": "Elena Rostova",
                "age": 71,
                "baseline_risk": 0.25,
                "vitals": {"hr": 138, "sbp": 72, "dbp": 42, "spo2": 87, "rr": 29, "temp_c": 39.4},
                "rr_intervals_ms": [435.0, 437.0, 434.0, 436.0, 435.0, 438.0, 436.0, 435.0]
            },
            {
                "patient_id": "PT-103",
                "name": "David Chen",
                "age": 48,
                "baseline_risk": 0.12,
                "vitals": {"hr": 108, "sbp": 102, "dbp": 68, "spo2": 94, "rr": 22, "temp_c": 38.2},
                "rr_intervals_ms": [550.0, 570.0, 540.0, 560.0, 575.0, 545.0, 560.0]
            }
        ]
        
        prioritized = prioritize_patient_roster(roster)
        self.assertEqual(len(prioritized), 3)
        # Elena Rostova (septic collapse) must be Rank 1 (ESI 1)
        self.assertEqual(prioritized[0]["patient_id"], "PT-102")
        self.assertEqual(prioritized[0]["esi_tier"], 1)
        self.assertEqual(prioritized[0]["triage_rank"], 1)
        # Marcus Vance (stable) must be Rank 3
        self.assertEqual(prioritized[-1]["patient_id"], "PT-101")


if __name__ == "__main__":
    t0 = time.perf_counter()
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAegisPulseEngine)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    elapsed = time.perf_counter() - t0
    print(f"\nExecution Time: {elapsed:.6f}s")
    if not result.wasSuccessful():
        exit(1)
