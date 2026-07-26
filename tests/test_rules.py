import pytest
import pandas as pd
from src.rules import AMLRuleDetector

def test_structuring_detector_trigger():
    detector = AMLRuleDetector(reporting_threshold=10000.0, structuring_min=9000.0, min_structuring_count=3)
    
    # Synthetic transactions for 1 customer
    tx_df = pd.DataFrame([
        {"transaction_id": "TX1", "customer_id": "C0001", "amount": 9500.0, "transaction_type": "cash_deposit", "is_near_threshold": True},
        {"transaction_id": "TX2", "customer_id": "C0001", "amount": 9600.0, "transaction_type": "cash_deposit", "is_near_threshold": True},
        {"transaction_id": "TX3", "customer_id": "C0001", "amount": 9700.0, "transaction_type": "cash_deposit", "is_near_threshold": True},
    ])
    
    cust_row = {"near_threshold_count": 3, "near_threshold_ratio": 1.0, "tx_count": 3}
    
    res = detector.detect_customer_rules("C0001", tx_df, cust_row)
    assert res["structuring"]["triggered"] is True
    assert len(res["structuring"]["supporting_tx_ids"]) == 3
    assert res["structuring"]["signal_strength"] > 0.0

def test_velocity_detector_trigger():
    detector = AMLRuleDetector(velocity_24h_threshold=10)
    tx_df = pd.DataFrame([
        {"transaction_id": f"TX{i}", "customer_id": "C0002", "rolling_tx_count_24h": 12, "amount": 500.0, "transaction_type": "transfer", "is_near_threshold": False}
        for i in range(12)
    ])
    cust_row = {"max_rolling_tx_24h": 12, "tx_count": 12}
    
    res = detector.detect_customer_rules("C0002", tx_df, cust_row)
    assert res["high_velocity"]["triggered"] is True
