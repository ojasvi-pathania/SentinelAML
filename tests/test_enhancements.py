import pytest
import os
import json
import pandas as pd
from src.reports import export_execution_plan_json
from src.evaluation import evaluate_synthetic_performance, OPERATING_MODE_PRESETS
from src.data_generator import generate_synthetic_aml_data

def test_json_execution_plan_structure():
    plan = {
        "detected_intent": "single_customer_investigation",
        "extracted_filters": {"customer_id": "C0012"},
        "reason_for_plan": "Targeted investigation for C0012",
        "selected_tools": ["data_ingestion_tool", "customer_lookup_tool"],
        "selected_tool_reasons": {"data_ingestion_tool": "Ingest dataset"},
        "skipped_tools": ["eda_tool"],
        "skipped_tool_reasons": {"eda_tool": "Skipped for single customer"},
        "optimization_metrics": {
            "executed_tools_count": 2,
            "skipped_tools_count": 1,
            "computation_saved_percent": 33.3,
            "runtime_ms": 12.4
        }
    }
    
    json_str = export_execution_plan_json(plan)
    parsed = json.loads(json_str)
    
    assert "audit_metadata" in parsed
    assert "query_analysis" in parsed
    assert "tool_selection_audit" in parsed
    assert "optimization_metrics" in parsed
    assert parsed["tool_selection_audit"]["selected_tools"] == ["data_ingestion_tool", "customer_lookup_tool"]

def test_operating_mode_presets_and_no_label_leakage():
    raw_df = generate_synthetic_aml_data(num_customers=50, seed=42)
    # Ensure ground truth labels are present in dataset
    assert "is_suspicious_ground_truth" in raw_df.columns
    
    # Model predictions generated independently from rules/score
    cust_df = pd.DataFrame([
        {"customer_id": f"C{i:04d}", "risk_score": 90.0 - i * 1.5, "risk_level": "High" if i < 10 else "Low"}
        for i in range(1, 51)
    ])
    
    res_prec = evaluate_synthetic_performance(raw_df, cust_df, operating_mode="Precision First (Default)")
    res_bal = evaluate_synthetic_performance(raw_df, cust_df, operating_mode="Balanced (F1 Optimal)")
    res_rec = evaluate_synthetic_performance(raw_df, cust_df, operating_mode="Recall First (High Sensitivity)")
    
    assert res_prec["has_ground_truth"] is True
    assert res_prec["cutoff_used"] == 70.0
    assert res_bal["cutoff_used"] == 50.0
    assert res_rec["cutoff_used"] == 40.0
    assert res_rec["recall"] >= res_prec["recall"]
    assert "TP" in res_prec["confusion_matrix"]
    assert "FP" in res_prec["confusion_matrix"]

def test_demo_documentation_and_example_files():
    assert os.path.exists(os.path.join("docs", "demo_scenarios.md"))
    assert os.path.exists(os.path.join("docs", "case_study.md"))
    assert os.path.exists(os.path.join("docs", "system_design.md"))
    assert os.path.exists(os.path.join("docs", "presentation_content.md"))
    assert os.path.exists(".env.example")
    assert os.path.exists(os.path.join(".streamlit", "secrets.toml.example"))
