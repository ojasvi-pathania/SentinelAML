import pandas as pd
import io

COLUMN_MAPPING_VARIANTS = {
    "transaction_id": ["tx_id", "transactionid", "trans_id", "id", "txn_id"],
    "customer_id": ["cust_id", "customerid", "client_id", "account_id", "user_id"],
    "timestamp": ["date", "datetime", "time", "tx_date", "trans_date", "created_at"],
    "amount": ["amt", "val", "value", "tx_amount", "sum"],
    "transaction_type": ["type", "tx_type", "channel", "category", "trans_type"],
    "country": ["location", "tx_country", "geo", "jurisdiction", "nation"],
    "segment": ["customer_segment", "cust_segment", "tier", "account_type", "client_segment"]
}

def normalize_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Normalizes column names to standard AML schema.
    Returns (normalized_df, mapping_applied).
    """
    df = df.copy()
    mapping_applied = {}
    
    col_lower_map = {str(col).strip().lower(): col for col in df.columns}
    
    for std_name, variants in COLUMN_MAPPING_VARIANTS.items():
        if std_name in col_lower_map:
            mapping_applied[col_lower_map[std_name]] = std_name
            continue
            
        found = False
        for var in variants:
            if var in col_lower_map:
                original_col = col_lower_map[var]
                mapping_applied[original_col] = std_name
                found = True
                break
                
    if mapping_applied:
        df = df.rename(columns=mapping_applied)
        
    if "segment" not in df.columns:
        df["segment"] = "Retail"
        
    return df, mapping_applied

def load_transaction_csv(file_or_path) -> tuple[pd.DataFrame, list[str]]:
    """
    Loads CSV from path or file-like stream and normalizes schema.
    Returns (df, warnings_list).
    """
    warnings = []
    try:
        if isinstance(file_or_path, str):
            df = pd.read_csv(file_or_path)
        else:
            df = pd.read_csv(file_or_path)
    except Exception as e:
        raise ValueError(f"Failed to parse CSV file: {str(e)}")
        
    df, mapping_applied = normalize_columns(df)
    
    missing_required = []
    required_cols = ["transaction_id", "customer_id", "timestamp", "amount", "transaction_type", "country"]
    for rcol in required_cols:
        if rcol not in df.columns:
            missing_required.append(rcol)
            
    if missing_required:
        warnings.append(f"Missing expected columns: {', '.join(missing_required)}. Please ensure mapping interface is used.")
        
    if mapping_applied:
        mapped_str = ", ".join([f"'{k}' -> '{v}'" for k, v in mapping_applied.items()])
        warnings.append(f"Auto-mapped column names: {mapped_str}")
        
    return df, warnings
