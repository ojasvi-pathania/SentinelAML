import pandas as pd
import numpy as np

def engineer_aml_features(
    df: pd.DataFrame,
    reporting_threshold: float = 10000.0,
    structuring_min: float = 9000.0
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Computes transaction-level and customer-level AML features.
    Returns (tx_features_df, customer_features_df).
    """
    if df is None or df.empty:
        return pd.DataFrame(), pd.DataFrame()
        
    tx_df = df.copy()
    
    # 1. Ensure clean datatypes
    tx_df["amount"] = pd.to_numeric(tx_df["amount"], errors="coerce").fillna(0.0)
    tx_df["dt"] = pd.to_datetime(tx_df["timestamp"], errors="coerce")
    tx_df = tx_df.sort_values(["customer_id", "dt"]).reset_index(drop=True)
    
    # 2. Transaction-level features
    # Round amount flag (e.g., divisible by 1000 or 500)
    tx_df["is_round_amount"] = (tx_df["amount"] % 500 == 0) & (tx_df["amount"] > 0)
    
    # Near threshold deposit flag
    tx_df["is_near_threshold"] = (
        (tx_df["amount"] >= structuring_min) & 
        (tx_df["amount"] < reporting_threshold) & 
        (tx_df["transaction_type"].str.lower().str.contains("deposit|cash", regex=True, na=False))
    )

    # Customer historical mean & std up to current transaction
    cust_stats = tx_df.groupby("customer_id")["amount"].agg(["mean", "std", "count"]).reset_index()
    cust_stats["std"] = cust_stats["std"].fillna(0.0)
    
    tx_df = tx_df.merge(cust_stats, on="customer_id", how="left")
    tx_df["amount_zscore"] = np.where(
        tx_df["std"] > 0,
        (tx_df["amount"] - tx_df["mean"]) / tx_df["std"],
        0.0
    )
    tx_df["amount_deviation_ratio"] = np.where(
        tx_df["mean"] > 0,
        tx_df["amount"] / tx_df["mean"],
        1.0
    )
    
    # Rapid incoming to outgoing cashout check
    # Check time gap to previous transaction for same customer
    tx_df["prev_dt"] = tx_df.groupby("customer_id")["dt"].shift(1)
    tx_df["prev_type"] = tx_df.groupby("customer_id")["transaction_type"].shift(1)
    tx_df["prev_amount"] = tx_df.groupby("customer_id")["amount"].shift(1)
    
    tx_df["time_since_prev_min"] = (tx_df["dt"] - tx_df["prev_dt"]).dt.total_seconds() / 60.0
    
    # Rapid cashout signal: withdrawal/outgoing transfer shortly after incoming transfer/deposit
    tx_df["is_rapid_cashout"] = (
        (tx_df["time_since_prev_min"] <= 120) &
        (tx_df["prev_type"].astype(str).str.contains("transfer|deposit", case=False, na=False)) &
        (tx_df["transaction_type"].astype(str).str.contains("withdrawal|out", case=False, na=False)) &
        (tx_df["amount"] >= 0.7 * tx_df["prev_amount"])
    )

    # Rolling 24h & 7-day transaction counts per customer
    tx_df.set_index("dt", inplace=True)
    tx_df["rolling_tx_count_24h"] = (
        tx_df.groupby("customer_id")["transaction_id"]
        .transform(lambda s: s.rolling("24h").count())
    )
    tx_df["rolling_tx_sum_24h"] = (
        tx_df.groupby("customer_id")["amount"]
        .transform(lambda s: s.rolling("24h").sum())
    )
    tx_df["rolling_tx_count_7d"] = (
        tx_df.groupby("customer_id")["transaction_id"]
        .transform(lambda s: s.rolling("7D").count())
    )
    tx_df.reset_index(inplace=True)
    
    # 3. Customer-level aggregate features
    cust_records = []
    for cust_id, group in tx_df.groupby("customer_id"):
        n_tx = len(group)
        tot_amt = group["amount"].sum()
        avg_amt = group["amount"].mean()
        med_amt = group["amount"].median()
        max_amt = group["amount"].max()
        std_amt = group["amount"].std() if n_tx > 1 else 0.0
        
        d_min = group["dt"].min()
        d_max = group["dt"].max()
        active_days = max(1, (d_max - d_min).days + 1)
        tx_per_active_day = n_tx / active_days
        
        n_cash_dep = (group["transaction_type"] == "cash_deposit").sum()
        n_cash_wd = (group["transaction_type"] == "cash_withdrawal").sum()
        n_transfer = (group["transaction_type"] == "bank_transfer").sum()
        
        near_thresh_count = group["is_near_threshold"].sum()
        near_thresh_ratio = near_thresh_count / n_tx if n_tx > 0 else 0.0
        
        max_24h_count = group["rolling_tx_count_24h"].max()
        max_24h_sum = group["rolling_tx_sum_24h"].max()
        
        n_countries = group["country"].nunique()
        n_types = group["transaction_type"].nunique()
        
        n_rapid_cashouts = group["is_rapid_cashout"].sum()
        n_round_amts = group["is_round_amount"].sum()
        
        max_zscore = group["amount_zscore"].max()
        
        cust_records.append({
            "customer_id": cust_id,
            "tx_count": n_tx,
            "total_amount": round(tot_amt, 2),
            "avg_amount": round(avg_amt, 2),
            "median_amount": round(med_amt, 2),
            "max_amount": round(max_amt, 2),
            "std_amount": round(std_amt, 2) if not np.isnan(std_amt) else 0.0,
            "active_days": active_days,
            "tx_per_active_day": round(tx_per_active_day, 2),
            "cash_deposit_count": int(n_cash_dep),
            "cash_withdrawal_count": int(n_cash_wd),
            "transfer_count": int(n_transfer),
            "near_threshold_count": int(near_thresh_count),
            "near_threshold_ratio": round(near_thresh_ratio, 4),
            "max_rolling_tx_24h": int(max_24h_count),
            "max_rolling_sum_24h": round(max_24h_sum, 2),
            "countries_count": int(n_countries),
            "types_count": int(n_types),
            "rapid_cashout_count": int(n_rapid_cashouts),
            "round_amount_count": int(n_round_amts),
            "max_amount_zscore": round(max_zscore, 2) if not np.isnan(max_zscore) else 0.0
        })
        
    cust_df = pd.DataFrame(cust_records)
    
    return tx_df, cust_df
