import pandas as pd
import numpy as np

class AMLRuleDetector:
    """
    Explainable Rule-Based AML Pattern Detector.
    Evaluates individual customers and transactions against specific compliance rules.
    """
    def __init__(
        self,
        reporting_threshold: float = 10000.0,
        structuring_min: float = 9000.0,
        min_structuring_count: int = 3,
        velocity_24h_threshold: int = 10
    ):
        self.reporting_threshold = reporting_threshold
        self.structuring_min = structuring_min
        self.min_structuring_count = min_structuring_count
        self.velocity_24h_threshold = velocity_24h_threshold

    def detect_customer_rules(self, cust_id: str, tx_df: pd.DataFrame, cust_row: dict) -> dict:
        """
        Runs all rule detectors for a single customer.
        Returns a dict of rule results keyed by rule name.
        """
        c_txs = tx_df[tx_df["customer_id"] == cust_id].copy()
        
        results = {}
        
        # Rule 1: Structuring
        results["structuring"] = self._evaluate_structuring(c_txs, cust_row)
        
        # Rule 2: High Velocity
        results["high_velocity"] = self._evaluate_velocity(c_txs, cust_row)
        
        # Rule 3: Rapid Cash-Out
        results["rapid_cash_out"] = self._evaluate_rapid_cashout(c_txs, cust_row)
        
        # Rule 4: Unusual Amount
        results["unusual_amount"] = self._evaluate_unusual_amount(c_txs, cust_row)
        
        # Rule 5: Repeated Near-Threshold Deposits
        results["near_threshold_deposits"] = self._evaluate_near_threshold(c_txs, cust_row)
        
        # Rule 6: Excessive Cross-Border Activity
        results["cross_border_risk"] = self._evaluate_cross_border(c_txs, cust_row)
        
        # Rule 7: Repeated Round Amounts
        results["round_amount_pattern"] = self._evaluate_round_amounts(c_txs, cust_row)
        
        return results

    def _evaluate_structuring(self, c_txs: pd.DataFrame, cust_row: dict) -> dict:
        if "amount" in c_txs.columns and "transaction_type" in c_txs.columns:
            near_t = c_txs[
                (c_txs["amount"] >= self.structuring_min) &
                (c_txs["amount"] < self.reporting_threshold) &
                (c_txs["transaction_type"].str.lower().str.contains("deposit|cash", regex=True, na=False))
            ]
        elif "is_near_threshold" in c_txs.columns:
            near_t = c_txs[c_txs["is_near_threshold"] == True]
        else:
            near_t = pd.DataFrame()
            
        cnt = len(near_t)
        triggered = cnt >= self.min_structuring_count
        signal_strength = min(1.0, cnt / (self.min_structuring_count * 2)) if cnt > 0 else 0.0
        tx_ids = near_t["transaction_id"].tolist() if "transaction_id" in near_t.columns else []
        
        reason = (
            f"Customer executed {cnt} cash deposits between ${self.structuring_min:,.0f} and "
            f"${self.reporting_threshold:,.0f} (just below reporting threshold of ${self.reporting_threshold:,.0f})."
            if triggered else "No significant structuring pattern detected."
        )
        
        return {
            "rule_name": "Structuring",
            "triggered": triggered,
            "signal_strength": round(signal_strength, 2),
            "supporting_tx_ids": tx_ids,
            "human_readable_reason": reason,
            "evidence": {
                "near_threshold_count": cnt,
                "structuring_min": self.structuring_min,
                "reporting_threshold": self.reporting_threshold,
                "amounts": near_t["amount"].tolist() if not near_t.empty and "amount" in near_t.columns else []
            }
        }

    def _evaluate_velocity(self, c_txs: pd.DataFrame, cust_row: dict) -> dict:
        max_24h = cust_row.get("max_rolling_tx_24h", 0)
        triggered = max_24h >= self.velocity_24h_threshold
        signal_strength = min(1.0, max_24h / (self.velocity_24h_threshold * 1.5)) if max_24h > 0 else 0.0
        
        if "rolling_tx_count_24h" in c_txs.columns and "transaction_id" in c_txs.columns:
            burst_txs = c_txs[c_txs["rolling_tx_count_24h"] >= self.velocity_24h_threshold]
            tx_ids = burst_txs["transaction_id"].tolist()
        else:
            tx_ids = c_txs["transaction_id"].tolist() if "transaction_id" in c_txs.columns else []
            
        reason = (
            f"Customer executed up to {max_24h} transactions within a single 24-hour window "
            f"(threshold: {self.velocity_24h_threshold})."
            if triggered else "Transaction velocity within normal limits."
        )
        
        return {
            "rule_name": "High Velocity",
            "triggered": triggered,
            "signal_strength": round(signal_strength, 2),
            "supporting_tx_ids": tx_ids,
            "human_readable_reason": reason,
            "evidence": {
                "max_24h_transactions": max_24h,
                "velocity_threshold": self.velocity_24h_threshold
            }
        }

    def _evaluate_rapid_cashout(self, c_txs: pd.DataFrame, cust_row: dict) -> dict:
        if "is_rapid_cashout" in c_txs.columns:
            rc_txs = c_txs[c_txs["is_rapid_cashout"] == True]
            cnt = len(rc_txs)
            tx_ids = rc_txs["transaction_id"].tolist() if "transaction_id" in rc_txs.columns else []
        else:
            cnt = cust_row.get("rapid_cashout_count", 0)
            tx_ids = c_txs["transaction_id"].tolist() if "transaction_id" in c_txs.columns else []
            
        triggered = cnt >= 1
        signal_strength = min(1.0, cnt * 0.5) if cnt > 0 else 0.0
        
        reason = (
            f"Detected {cnt} rapid cash-out events where incoming transfers were quickly withdrawn "
            f"or transferred out within 2 hours."
            if triggered else "No rapid incoming-to-outgoing movements detected."
        )
        
        return {
            "rule_name": "Rapid Cash-Out",
            "triggered": triggered,
            "signal_strength": round(signal_strength, 2),
            "supporting_tx_ids": tx_ids,
            "human_readable_reason": reason,
            "evidence": {
                "rapid_cashout_events": cnt
            }
        }

    def _evaluate_unusual_amount(self, c_txs: pd.DataFrame, cust_row: dict) -> dict:
        max_zscore = cust_row.get("max_amount_zscore", 0.0)
        max_amt = cust_row.get("max_amount", 0.0)
        avg_amt = cust_row.get("avg_amount", 1.0)
        
        ratio = max_amt / avg_amt if avg_amt > 0 else 1.0
        triggered = (ratio >= 4.0 and max_amt >= 25000) or max_zscore >= 3.5
        signal_strength = min(1.0, max(ratio / 10.0, max_zscore / 6.0)) if triggered else 0.0
        
        if "amount_zscore" in c_txs.columns and "transaction_id" in c_txs.columns:
            extreme_txs = c_txs[c_txs["amount_zscore"] >= 3.0]
            tx_ids = extreme_txs["transaction_id"].tolist()
        else:
            tx_ids = c_txs["transaction_id"].tolist() if "transaction_id" in c_txs.columns else []
            
        reason = (
            f"Single transaction of ${max_amt:,.2f} significantly exceeds historical average "
            f"of ${avg_amt:,.2f} ({ratio:.1f}x deviation, z-score: {max_zscore:.1f})."
            if triggered else "Transaction amounts conform to customer baseline."
        )
        
        return {
            "rule_name": "Unusual Amount",
            "triggered": triggered,
            "signal_strength": round(signal_strength, 2),
            "supporting_tx_ids": tx_ids,
            "human_readable_reason": reason,
            "evidence": {
                "max_amount": max_amt,
                "avg_amount": avg_amt,
                "deviation_ratio": round(ratio, 2),
                "max_zscore": max_zscore
            }
        }

    def _evaluate_near_threshold(self, c_txs: pd.DataFrame, cust_row: dict) -> dict:
        cnt = cust_row.get("near_threshold_count", 0)
        ratio = cust_row.get("near_threshold_ratio", 0.0)
        triggered = cnt >= 2 and ratio >= 0.15
        signal_strength = min(1.0, ratio * 2.5) if triggered else 0.0
        
        if "is_near_threshold" in c_txs.columns and "transaction_id" in c_txs.columns:
            nt_txs = c_txs[c_txs["is_near_threshold"] == True]
            tx_ids = nt_txs["transaction_id"].tolist()
        else:
            tx_ids = c_txs["transaction_id"].tolist() if "transaction_id" in c_txs.columns else []
            
        reason = (
            f"High proportion ({ratio*100:.1f}%, {cnt} transactions) of deposits near reporting threshold."
            if triggered else "Normal threshold proximity distribution."
        )
        
        return {
            "rule_name": "Near-Threshold Proximity",
            "triggered": triggered,
            "signal_strength": round(signal_strength, 2),
            "supporting_tx_ids": tx_ids,
            "human_readable_reason": reason,
            "evidence": {
                "near_threshold_count": cnt,
                "near_threshold_ratio": ratio
            }
        }

    def _evaluate_cross_border(self, c_txs: pd.DataFrame, cust_row: dict) -> dict:
        n_countries = cust_row.get("countries_count", 1)
        high_risk_jurisdictions = {"CY", "KY", "PA", "AE"}
        cust_countries = set(c_txs["country"].dropna().unique()) if "country" in c_txs.columns else set()
        hr_matches = cust_countries.intersection(high_risk_jurisdictions)
        
        triggered = n_countries >= 4 or len(hr_matches) >= 2
        signal_strength = min(1.0, (n_countries / 6.0) + (len(hr_matches) * 0.3)) if triggered else 0.0
        
        if "country" in c_txs.columns and "transaction_id" in c_txs.columns:
            hr_txs = c_txs[c_txs["country"].isin(high_risk_jurisdictions)]
            tx_ids = hr_txs["transaction_id"].tolist()
        else:
            tx_ids = c_txs["transaction_id"].tolist() if "transaction_id" in c_txs.columns else []
            
        reason = (
            f"Customer transacted across {n_countries} countries, including high-risk jurisdictions: {list(hr_matches)}."
            if triggered else "Cross-border activity within normal profile."
        )
        
        return {
            "rule_name": "Excessive Cross-Border",
            "triggered": triggered,
            "signal_strength": round(signal_strength, 2),
            "supporting_tx_ids": tx_ids,
            "human_readable_reason": reason,
            "evidence": {
                "countries_count": n_countries,
                "high_risk_jurisdictions": list(hr_matches)
            }
        }

    def _evaluate_round_amounts(self, c_txs: pd.DataFrame, cust_row: dict) -> dict:
        n_round = cust_row.get("round_amount_count", 0)
        tot_tx = cust_row.get("tx_count", 1)
        ratio = n_round / tot_tx if tot_tx > 0 else 0.0
        
        triggered = n_round >= 5 and ratio >= 0.4
        signal_strength = min(1.0, ratio) if triggered else 0.0
        
        if "is_round_amount" in c_txs.columns and "transaction_id" in c_txs.columns:
            round_txs = c_txs[c_txs["is_round_amount"] == True]
            tx_ids = round_txs["transaction_id"].tolist()
        else:
            tx_ids = c_txs["transaction_id"].tolist() if "transaction_id" in c_txs.columns else []
            
        reason = (
            f"{n_round} transactions ({ratio*100:.1f}%) were exact round amounts (multiples of $500/$1000)."
            if triggered else "Round amount distribution is normal."
        )
        
        return {
            "rule_name": "Repeated Round Amounts",
            "triggered": triggered,
            "signal_strength": round(signal_strength, 2),
            "supporting_tx_ids": tx_ids,
            "human_readable_reason": reason,
            "evidence": {
                "round_amount_count": n_round,
                "round_amount_ratio": round(ratio, 2)
            }
        }
