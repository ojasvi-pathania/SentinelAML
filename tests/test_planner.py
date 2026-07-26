import pytest
from src.intent_parser import AMLIntentParser
from src.planner import AMLDynamicPlanner

def test_planner_structuring_query():
    parser = AMLIntentParser()
    planner = AMLDynamicPlanner()
    
    intent = parser.parse("Find structuring patterns in the last 30 days.")
    plan = planner.create_plan(intent)
    
    assert "structuring_detector_tool" in plan["selected_tools"]
    assert "anomaly_detection_tool" in plan["skipped_tools"]
    assert "optimization_metrics" in plan
    assert plan["optimization_metrics"]["computation_saved_percent"] > 0

def test_planner_broad_analysis():
    parser = AMLIntentParser()
    planner = AMLDynamicPlanner()
    
    intent = parser.parse("Analyse the complete dataset for suspicious activity.")
    plan = planner.create_plan(intent)
    
    assert "eda_tool" in plan["selected_tools"]
    assert "anomaly_detection_tool" in plan["selected_tools"]
    assert "filtering_tool" in plan["skipped_tools"]

def test_planner_single_customer_eda_skipped():
    parser = AMLIntentParser()
    planner = AMLDynamicPlanner()
    
    intent = parser.parse("Is customer ID C0012 suspicious?")
    plan = planner.create_plan(intent)
    
    assert "customer_lookup_tool" in plan["selected_tools"]
    assert "eda_tool" in plan["skipped_tools"]
    assert "eda_tool" in plan["skipped_tool_reasons"]
    assert "targets a single customer account (C0012)" in plan["skipped_tool_reasons"]["eda_tool"]

def test_planner_optimization_metrics():
    parser = AMLIntentParser()
    planner = AMLDynamicPlanner()
    
    intent = parser.parse("Corporate accounts with rapid cash-out.")
    plan = planner.create_plan(intent)
    
    metrics = plan["optimization_metrics"]
    assert metrics["executed_tools_count"] + metrics["skipped_tools_count"] == metrics["total_available_tools"]
    assert 0 <= metrics["computation_saved_percent"] <= 100
