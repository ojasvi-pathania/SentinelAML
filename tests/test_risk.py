import pytest
from src.risk import AMLRiskScorer

def test_risk_scorer_boundaries():
    scorer = AMLRiskScorer(low_threshold=40.0, high_threshold=70.0)
    
    # Mock clear rules
    clear_rules = {
        "structuring": {"triggered": False, "signal_strength": 0.0, "rule_name": "Structuring", "human_readable_reason": ""},
        "high_velocity": {"triggered": False, "signal_strength": 0.0, "rule_name": "High Velocity", "human_readable_reason": ""}
    }
    res_low = scorer.calculate_risk(clear_rules, anomaly_score=0.1)
    assert res_low["risk_level"] == "Low"
    assert res_low["risk_score"] < 40.0
    
    # Mock high triggered rules
    triggered_rules = {
        "structuring": {"triggered": True, "signal_strength": 1.0, "rule_name": "Structuring", "human_readable_reason": "High structuring deposits."},
        "high_velocity": {"triggered": True, "signal_strength": 1.0, "rule_name": "High Velocity", "human_readable_reason": "Burst transactions."}
    }
    res_high = scorer.calculate_risk(triggered_rules, anomaly_score=0.9)
    assert res_high["risk_level"] == "High"
    assert res_high["risk_score"] >= 70.0
