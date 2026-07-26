import time
import pandas as pd
import numpy as np

from src.intent_parser import AMLIntentParser
from src.planner import AMLDynamicPlanner
from src.features import engineer_aml_features
from src.rules import AMLRuleDetector
from src.anomaly import AMLAnomalyDetector
from src.risk import AMLRiskScorer
from src.explanations import generate_aml_explanation
from src.recommendations import get_escalation_recommendation

class SentinelAMLAgent:
    """
    SentinelAML Orchestrator Agent.
    Accepts natural language query, parses intent, builds dynamic plan, executes
    selected tools, computes risk scores, explanations, and escalation recommendations.
    """
    def __init__(
        self,
        reporting_threshold: float = 10000.0,
        structuring_min: float = 9000.0,
        velocity_threshold: int = 10,
        low_risk_threshold: float = 40.0,
        high_risk_threshold: float = 70.0,
        contamination: float = 0.08
    ):
        self.parser = AMLIntentParser()
        self.planner = AMLDynamicPlanner()
        self.reporting_threshold = reporting_threshold
        self.structuring_min = structuring_min
        self.velocity_threshold = velocity_threshold
        self.low_risk_threshold = low_risk_threshold
        self.high_risk_threshold = high_risk_threshold
        self.contamination = contamination

    def process_query(self, query: str, raw_df: pd.DataFrame) -> dict:
        """
        Processes analyst query end-to-end according to dynamic plan.
        """
        t_start = time.time()
        
        # Step 1: Parse Intent
        parsed_intent = self.parser.parse(query)
        
        # Step 2: Create Dynamic Execution Plan
        plan = self.planner.create_plan(parsed_intent)
        selected_tools = set(plan["selected_tools"])
        
        # Filter raw data if needed before feature engineering
        df_filtered = raw_df.copy()
        df_filtered["dt"] = pd.to_datetime(df_filtered["timestamp"], errors="coerce")
        
        last_n_days = parsed_intent.get("last_n_days")
        if last_n_days and "dt" in df_filtered.columns:
            max_dt = df_filtered["dt"].max()
            if pd.notna(max_dt):
                cutoff_dt = max_dt - pd.Timedelta(days=last_n_days)
                df_filtered = df_filtered[df_filtered["dt"] >= cutoff_dt]
                
        country_filter = parsed_intent.get("country")
        if country_filter and "country" in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["country"] == country_filter]

        segment_filter = parsed_intent.get("segment")
        if segment_filter and "segment" in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["segment"] == segment_filter]

        # Step 3: Feature Engineering
        tx_features_df, cust_features_df = engineer_aml_features(
            df_filtered,
            reporting_threshold=self.reporting_threshold,
            structuring_min=self.structuring_min
        )
        
        if cust_features_df.empty:
            runtime_ms = round((time.time() - t_start) * 1000, 1)
            plan["optimization_metrics"]["runtime_ms"] = runtime_ms
            return {
                "query": query,
                "parsed_intent": parsed_intent,
                "execution_plan": plan,
                "summary": "No transactions matched the specified query filters.",
                "customer_results": pd.DataFrame(),
                "flagged_transactions": pd.DataFrame(),
                "tx_features_df": tx_features_df
            }

        # Step 4: ML Anomaly Detection (only if selected in plan)
        if "anomaly_detection_tool" in selected_tools:
            anomaly_model = AMLAnomalyDetector(contamination=self.contamination)
            cust_features_df = anomaly_model.fit_predict(cust_features_df)
        else:
            cust_features_df["anomaly_score"] = 0.0
            cust_features_df["is_anomaly"] = False

        # Step 5: Rule Detectors & Risk Scorer
        rule_detector = AMLRuleDetector(
            reporting_threshold=self.reporting_threshold,
            structuring_min=self.structuring_min,
            min_structuring_count=3,
            velocity_24h_threshold=self.velocity_threshold
        )
        
        risk_scorer = AMLRiskScorer(
            low_threshold=self.low_risk_threshold,
            high_threshold=self.high_risk_threshold
        )
        
        results_list = []
        for idx, row in cust_features_df.iterrows():
            cust_id = row["customer_id"]
            cust_dict = row.to_dict()
            
            rule_res = rule_detector.detect_customer_rules(cust_id, tx_features_df, cust_dict)
            risk_res = risk_scorer.calculate_risk(rule_res, anomaly_score=row.get("anomaly_score", 0.0))
            
            explanation = generate_aml_explanation(cust_id, risk_res, cust_dict)
            recommendation = get_escalation_recommendation(
                cust_id,
                risk_res["risk_score"],
                risk_res["risk_level"],
                risk_res["triggered_patterns"]
            )
            
            # Lookup segment
            cust_txs = raw_df[raw_df["customer_id"] == cust_id]
            cust_seg = cust_txs["segment"].iloc[0] if ("segment" in cust_txs.columns and not cust_txs.empty) else "Retail"

            results_list.append({
                "customer_id": cust_id,
                "segment": cust_seg,
                "risk_score": risk_res["risk_score"],
                "risk_level": risk_res["risk_level"],
                "triggered_patterns": ", ".join(risk_res["triggered_patterns"]) if risk_res["triggered_patterns"] else "None",
                "triggered_patterns_list": risk_res["triggered_patterns"],
                "strongest_evidence": risk_res["strongest_evidence"],
                "short_explanation": explanation["short_explanation"],
                "detailed_explanation": explanation["detailed_explanation"],
                "evidence_table": explanation["evidence_table"],
                "recommended_action": recommendation["recommended_action"],
                "urgency_level": recommendation["urgency_level"],
                "action_rationale": recommendation["action_rationale"],
                "next_steps": recommendation["next_steps"],
                "tx_count": row.get("tx_count", 0),
                "total_amount": row.get("total_amount", 0.0),
                "max_amount": row.get("max_amount", 0.0),
                "anomaly_score": row.get("anomaly_score", 0.0),
                "related_tx_ids": explanation["related_tx_ids"]
            })
            
        cust_results_df = pd.DataFrame(results_list)
        
        # Handle specific query filters
        cust_id_target = parsed_intent.get("customer_id")
        if cust_id_target and not cust_results_df.empty:
            cust_results_df = cust_results_df[cust_results_df["customer_id"] == cust_id_target]
            
        risk_cat_target = parsed_intent.get("risk_category")
        if risk_cat_target and not cust_results_df.empty:
            cust_results_df = cust_results_df[cust_results_df["risk_level"] == risk_cat_target]
            
        amt_thresh = parsed_intent.get("amount_threshold")
        amt_cond = parsed_intent.get("amount_condition")
        min_cnt = parsed_intent.get("min_tx_count")
        
        if (amt_thresh is not None or min_cnt is not None) and not cust_results_df.empty:
            if amt_thresh is not None:
                if amt_cond == "below":
                    cust_results_df = cust_results_df[cust_results_df["max_amount"] < amt_thresh]
                else:
                    cust_results_df = cust_results_df[cust_results_df["total_amount"] > amt_thresh]
            if min_cnt is not None:
                cust_results_df = cust_results_df[cust_results_df["tx_count"] >= min_cnt]
                
        target_pattern = parsed_intent.get("target_pattern")
        if target_pattern and not cust_results_df.empty:
            pattern_kw = target_pattern.replace("_", " ")
            cust_results_df = cust_results_df[
                cust_results_df["triggered_patterns"].str.lower().str.contains(pattern_kw, na=False) |
                (cust_results_df["risk_level"] == "High")
            ]

        # Sort results by risk score descending
        if not cust_results_df.empty:
            cust_results_df = cust_results_df.sort_values("risk_score", ascending=False).reset_index(drop=True)
            
        # Collect flagged transactions
        flagged_tx_ids = []
        if not cust_results_df.empty:
            for r_ids in cust_results_df["related_tx_ids"]:
                flagged_tx_ids.extend(r_ids)
        flagged_tx_ids = set(flagged_tx_ids)
        
        flagged_tx_df = tx_features_df[tx_features_df["transaction_id"].isin(flagged_tx_ids)].copy() if flagged_tx_ids else pd.DataFrame()

        runtime_ms = round((time.time() - t_start) * 1000, 1)
        plan["optimization_metrics"]["runtime_ms"] = runtime_ms

        n_results = len(cust_results_df)
        n_high = (cust_results_df["risk_level"] == "High").sum() if n_results > 0 else 0
        summary_str = f"Found {n_results} matching accounts ({n_high} high risk) in {runtime_ms}ms with {plan['optimization_metrics']['computation_saved_percent']}% computation saved."

        return {
            "query": query,
            "parsed_intent": parsed_intent,
            "execution_plan": plan,
            "summary": summary_str,
            "customer_results": cust_results_df,
            "flagged_transactions": flagged_tx_df,
            "tx_features_df": tx_features_df
        }
