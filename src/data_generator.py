import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_synthetic_aml_data(
    num_customers=160,
    min_transactions=4200,
    reporting_threshold=10000.0,
    seed=42
):
    """
    Generates a realistic synthetic banking transaction dataset for AML analysis.
    
    Includes >=150 customers, >=4,000 transactions, customer segments (Retail, SME, Corporate,
    Business, High Net Worth, Government, NGO), multiple countries, varied payment types,
    and deliberately injected suspicious patterns (Structuring, Smurfing, High Velocity,
    Rapid Cash-Out, Unusual Amount) distributed across both historical and recent 30-day windows.
    """
    np.random.seed(seed)
    
    customer_ids = [f"C{i:04d}" for i in range(1, num_customers + 1)]
    countries = ["US", "GB", "DE", "SG", "HK", "AE", "CY", "KY", "PA", "CH", "FR", "JP"]
    high_risk_countries = ["CY", "KY", "PA", "AE"]
    tx_types = ["cash_deposit", "cash_withdrawal", "bank_transfer", "card_payment"]
    segments_pool = ["Retail", "SME", "Corporate", "Business", "High Net Worth", "Government", "NGO"]
    
    # Assign deterministic customer segments
    customer_segment_map = {}
    for idx, cust in enumerate(customer_ids):
        if idx < 40:
            seg = "Retail"
        elif idx < 70:
            seg = "SME"
        elif idx < 100:
            seg = "Corporate"
        elif idx < 120:
            seg = "Business"
        elif idx < 140:
            seg = "High Net Worth"
        elif idx < 150:
            seg = "Government"
        else:
            seg = "NGO"
        customer_segment_map[cust] = seg
    
    start_date = datetime(2026, 1, 1)
    end_date = datetime(2026, 3, 31)
    date_range_days = (end_date - start_date).days # 89-90 days
    
    records = []
    tx_counter = 1
    
    # 1. Generate normal transactions for all customers
    for cust in customer_ids:
        seg = customer_segment_map[cust]
        cust_country = np.random.choice(countries, p=[0.3, 0.15, 0.15, 0.08, 0.08, 0.05, 0.04, 0.03, 0.02, 0.04, 0.03, 0.03])
        avg_amount = np.random.uniform(100, 2500) if seg in ["Retail", "SME"] else np.random.uniform(2500, 15000)
        std_amount = avg_amount * np.random.uniform(0.2, 0.5)
        n_tx = np.random.randint(18, 32)
        
        for _ in range(n_tx):
            random_days = np.random.uniform(0, date_range_days)
            tx_time = start_date + timedelta(days=random_days)
            amt = max(10.0, np.random.normal(avg_amount, std_amount))
            t_type = np.random.choice(tx_types, p=[0.2, 0.2, 0.4, 0.2])
            tx_country = cust_country if np.random.rand() > 0.15 else np.random.choice(countries)
            
            records.append({
                "transaction_id": f"TX{tx_counter:07d}",
                "customer_id": cust,
                "segment": seg,
                "timestamp": tx_time.strftime("%Y-%m-%d %H:%M:%S"),
                "amount": round(amt, 2),
                "transaction_type": t_type,
                "country": tx_country,
                "is_suspicious_ground_truth": False,
                "pattern_ground_truth": "none"
            })
            tx_counter += 1
            
    # 2. Inject Structuring Scenarios (8 customers total)
    # 2a. Recent 30 days structuring (C0001 - C0004) - Retail segment
    recent_structuring_custs = customer_ids[0:4]
    for cust in recent_structuring_custs:
        seg = customer_segment_map[cust]
        base_day = start_date + timedelta(days=np.random.randint(65, 82))
        n_struct = np.random.randint(8, 14)
        for i in range(n_struct):
            tx_time = base_day + timedelta(hours=i * np.random.uniform(2, 6))
            amt = np.random.uniform(reporting_threshold - 950, reporting_threshold - 50)
            records.append({
                "transaction_id": f"TX{tx_counter:07d}",
                "customer_id": cust,
                "segment": seg,
                "timestamp": tx_time.strftime("%Y-%m-%d %H:%M:%S"),
                "amount": round(amt, 2),
                "transaction_type": "cash_deposit",
                "country": "US",
                "is_suspicious_ground_truth": True,
                "pattern_ground_truth": "structuring"
            })
            tx_counter += 1

    # 2b. Historical structuring (C0005 - C0008) - Retail/SME
    hist_structuring_custs = customer_ids[4:8]
    for cust in hist_structuring_custs:
        seg = customer_segment_map[cust]
        base_day = start_date + timedelta(days=np.random.randint(20, 50))
        n_struct = np.random.randint(8, 14)
        for i in range(n_struct):
            tx_time = base_day + timedelta(hours=i * np.random.uniform(2, 6))
            amt = np.random.uniform(reporting_threshold - 950, reporting_threshold - 50)
            records.append({
                "transaction_id": f"TX{tx_counter:07d}",
                "customer_id": cust,
                "segment": seg,
                "timestamp": tx_time.strftime("%Y-%m-%d %H:%M:%S"),
                "amount": round(amt, 2),
                "transaction_type": "cash_deposit",
                "country": "US",
                "is_suspicious_ground_truth": True,
                "pattern_ground_truth": "structuring"
            })
            tx_counter += 1

    # 3. Inject High Velocity Scenarios (5 customers) - days 65 to 85 (March)
    velocity_custs = customer_ids[10:15]
    for cust in velocity_custs:
        seg = customer_segment_map[cust]
        burst_day = start_date + timedelta(days=np.random.randint(65, 85))
        n_burst = np.random.randint(25, 40)
        for i in range(n_burst):
            tx_time = burst_day + timedelta(minutes=i * np.random.uniform(10, 45))
            amt = np.random.uniform(200, 4500)
            records.append({
                "transaction_id": f"TX{tx_counter:07d}",
                "customer_id": cust,
                "segment": seg,
                "timestamp": tx_time.strftime("%Y-%m-%d %H:%M:%S"),
                "amount": round(amt, 2),
                "transaction_type": np.random.choice(["bank_transfer", "card_payment"]),
                "country": np.random.choice(high_risk_countries),
                "is_suspicious_ground_truth": True,
                "pattern_ground_truth": "high_velocity"
            })
            tx_counter += 1

    # 4. Inject Rapid Cash-Out Scenarios (5 customers) - Corporate / Business segment
    rapid_cashout_custs = customer_ids[60:65]
    for idx, cust in enumerate(rapid_cashout_custs):
        seg = customer_segment_map[cust]
        for j in range(3):
            day_offset = 70 + j * 5 if idx % 2 == 0 else 20 + j * 10
            base_time = start_date + timedelta(days=day_offset)
            in_amt = np.random.uniform(15000, 45000)
            records.append({
                "transaction_id": f"TX{tx_counter:07d}",
                "customer_id": cust,
                "segment": seg,
                "timestamp": base_time.strftime("%Y-%m-%d %H:%M:%S"),
                "amount": round(in_amt, 2),
                "transaction_type": "bank_transfer",
                "country": "KY",
                "is_suspicious_ground_truth": True,
                "pattern_ground_truth": "rapid_cash_out"
            })
            tx_counter += 1
            out_time = base_time + timedelta(minutes=np.random.uniform(5, 35))
            records.append({
                "transaction_id": f"TX{tx_counter:07d}",
                "customer_id": cust,
                "segment": seg,
                "timestamp": out_time.strftime("%Y-%m-%d %H:%M:%S"),
                "amount": round(in_amt * 0.96, 2),
                "transaction_type": "cash_withdrawal",
                "country": "US",
                "is_suspicious_ground_truth": True,
                "pattern_ground_truth": "rapid_cash_out"
            })
            tx_counter += 1

    # 5. Inject Smurfing / Coordinated Transfers (Group of 6 customers to 1 target)
    smurf_custs = customer_ids[30:36]
    target_time = start_date + timedelta(days=75)
    for cust in smurf_custs:
        seg = customer_segment_map[cust]
        for j in range(2):
            tx_time = target_time + timedelta(hours=j * 3 + np.random.uniform(0, 1))
            amt = np.random.uniform(8500, 9800)
            records.append({
                "transaction_id": f"TX{tx_counter:07d}",
                "customer_id": cust,
                "segment": seg,
                "timestamp": tx_time.strftime("%Y-%m-%d %H:%M:%S"),
                "amount": round(amt, 2),
                "transaction_type": "bank_transfer",
                "country": "PA",
                "is_suspicious_ground_truth": True,
                "pattern_ground_truth": "smurfing"
            })
            tx_counter += 1

    # 6. Inject High Net Worth Unusual Massive Amount Scenarios (4 customers)
    unusual_custs = customer_ids[120:124]
    for cust in unusual_custs:
        seg = customer_segment_map[cust]
        tx_time = start_date + timedelta(days=np.random.randint(65, 85))
        amt = np.random.uniform(75000, 250000)
        records.append({
            "transaction_id": f"TX{tx_counter:07d}",
            "customer_id": cust,
            "segment": seg,
            "timestamp": tx_time.strftime("%Y-%m-%d %H:%M:%S"),
            "amount": round(amt, 2),
            "transaction_type": "bank_transfer",
            "country": np.random.choice(high_risk_countries),
            "is_suspicious_ground_truth": True,
            "pattern_ground_truth": "unusual_amount"
        })
        tx_counter += 1

    df = pd.DataFrame(records)
    df["dt"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("dt").reset_index(drop=True).drop(columns=["dt"])
    
    return df
