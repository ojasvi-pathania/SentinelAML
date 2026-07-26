import pandas as pd
import numpy as np

def validate_aml_dataset(df: pd.DataFrame) -> dict:
    """
    Validates AML transaction dataset for quality issues without throwing exceptions.
    Returns detailed quality report dictionary.
    """
    report = {
        "total_rows": len(df),
        "total_customers": 0,
        "missing_values": {},
        "duplicate_tx_ids": 0,
        "invalid_timestamps": 0,
        "invalid_amounts": 0,
        "missing_customer_ids": 0,
        "unsupported_types": 0,
        "warnings": [],
        "is_valid": True
    }
    
    if df is None or df.empty:
        report["warnings"].append("Dataset is empty.")
        report["is_valid"] = False
        return report
        
    # Check missing values per column
    for col in df.columns:
        n_miss = int(df[col].isna().sum())
        if n_miss > 0:
            report["missing_values"][col] = n_miss
            report["warnings"].append(f"Column '{col}' has {n_miss} missing values.")
            
    # Check duplicate transaction IDs
    if "transaction_id" in df.columns:
        dups = int(df["transaction_id"].duplicated().sum())
        report["duplicate_tx_ids"] = dups
        if dups > 0:
            report["warnings"].append(f"Found {dups} duplicate transaction IDs.")
            
    # Check missing customer IDs
    if "customer_id" in df.columns:
        n_null_cust = int(df["customer_id"].isna().sum())
        report["missing_customer_ids"] = n_null_cust
        report["total_customers"] = int(df["customer_id"].nunique(dropna=True))
        if n_null_cust > 0:
            report["warnings"].append(f"Found {n_null_cust} records with missing customer ID.")
            
    # Check invalid amounts (<= 0 or non-numeric)
    if "amount" in df.columns:
        numeric_amt = pd.to_numeric(df["amount"], errors="coerce")
        n_invalid_amt = int((numeric_amt <= 0).sum() + numeric_amt.isna().sum())
        report["invalid_amounts"] = n_invalid_amt
        if n_invalid_amt > 0:
            report["warnings"].append(f"Found {n_invalid_amt} records with zero, negative, or invalid amounts.")
            
    # Check invalid timestamps
    if "timestamp" in df.columns:
        parsed_ts = pd.to_datetime(df["timestamp"], errors="coerce")
        n_invalid_ts = int(parsed_ts.isna().sum())
        report["invalid_timestamps"] = n_invalid_ts
        if n_invalid_ts > 0:
            report["warnings"].append(f"Found {n_invalid_ts} records with unparseable timestamps.")
            
    # Check unsupported transaction types
    standard_types = {"cash_deposit", "cash_withdrawal", "bank_transfer", "card_payment", "transfer", "deposit", "withdrawal"}
    if "transaction_type" in df.columns:
        unknown_types = set(df["transaction_type"].dropna().unique()) - standard_types
        if unknown_types:
            report["unsupported_types"] = len(unknown_types)
            report["warnings"].append(f"Non-standard transaction types detected: {list(unknown_types)}")
            
    return report
