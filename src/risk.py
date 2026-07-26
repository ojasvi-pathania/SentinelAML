import pandas as pd
import numpy as np

class AMLRiskScorer:
    """
    Transparent composite AML Risk Scoring Engine.
    Combines rule signals and ML anomaly scores into a 0-100 score and risk category.
    """
    def __init__(
        self,
        low_threshold: float = 40.0,
        high_threshold: float = 70.0,
        weights: dict = None
    ):
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold
        
        default_weights = {
            "structuring": 30.0,
            "high_velocity": 20.0,
            "rapid_cash_out": 25.0,
            "unusual_amount": 15.0,
            "near_threshold_deposits": 15.0,
            "cross_border_risk": 15.0,
            "round_amount_pattern": 10.0,
            "ml_anomaly": 15.0
        }
        self.weights = weights if weights else default_weights

    def calculate_risk(
        self,
        rule_results: dict,
        anomaly_score: float = 0.0
    ) -> dict:
        """
        Calculates risk score (0..100) for a customer given rule results and ML anomaly score.
        """
        raw_score = 0.0
        max_possible = sum(self.weights.values())
        
        triggered_patterns = []
        evidence_list = []
        
        for rule_key, res in rule_results.items():
            strg = res.get("signal_strength", 0.0)
            weight = self.weights.get(rule_key, 10.0)
            
            if res.get("triggered", False):
                raw_score += strg * weight
                triggered_patterns.append(res.get("rule_name", rule_key))
                evidence_list.append(res.get("human_readable_reason", ""))
            else:
                # Partial credit for high signal strength even if not fully triggered
                if strg > 0.4:
                    raw_score += strg * weight * 0.4
                    
        # ML Anomaly contribution
        ml_weight = self.weights.get("ml_anomaly", 15.0)
        raw_score += float(anomaly_score) * ml_weight
        if anomaly_score > 0.7:
            triggered_patterns.append("ML Anomaly Detected")
            evidence_list.append(f"Statistical isolation forest anomaly score was high ({anomaly_score:.2f}).")

        # Scale to 0-100 scale with ceiling dampener to avoid score compression
        scaled_score = min(100.0, (raw_score / max_possible) * 180.0)
        risk_score = round(scaled_score, 1)
        
        # Categorize
        if risk_score >= self.high_threshold:
            risk_level = "High"
        elif risk_score >= self.low_threshold:
            risk_level = "Medium"
        else:
            risk_level = "Low"
            
        strongest_evidence = evidence_list[0] if evidence_list else "No significant suspicious indicators detected."
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "triggered_patterns": triggered_patterns,
            "strongest_evidence": strongest_evidence,
            "all_evidence": evidence_list,
            "rule_results": rule_results,
            "anomaly_score": anomaly_score
        }
