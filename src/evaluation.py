import pandas as pd
import numpy as np

OPERATING_MODE_PRESETS = {
    "Precision First (Default)": {
        "cutoff": 70.0,
        "description": "Reduces false positives and analyst alert fatigue by requiring strong multi-rule trigger signals before flagging High Risk."
    },
    "Balanced (F1 Optimal)": {
        "cutoff": 50.0,
        "description": "Optimizes F1-score by balancing high detection sensitivity with manageable alert volume."
    },
    "Recall First (High Sensitivity)": {
        "cutoff": 40.0,
        "description": "Captures maximum suspicious cases across Medium & High risk tiers, accepting higher alert volume for comprehensive coverage."
    }
}

def evaluate_synthetic_performance(
    raw_df: pd.DataFrame,
    cust_results_df: pd.DataFrame,
    high_risk_cutoff: float = None,
    operating_mode: str = "Precision First (Default)"
) -> dict:
    """
    Evaluates detector performance against synthetic ground-truth labels.
    Calculates Precision, Recall, F1-Score, and Confusion Matrix under active Operating Mode.
    Clearly labeled as SYNTHETIC DEMONSTRATION METRICS ONLY.
    """
    if raw_df.empty or cust_results_df.empty or "is_suspicious_ground_truth" not in raw_df.columns:
        return {
            "has_ground_truth": False,
            "message": "Ground-truth labels not available for imported CSV."
        }

    mode_info = OPERATING_MODE_PRESETS.get(operating_mode, OPERATING_MODE_PRESETS["Precision First (Default)"])
    cutoff = high_risk_cutoff if high_risk_cutoff is not None else mode_info["cutoff"]
        
    # Get ground truth per customer
    gt_cust = raw_df.groupby("customer_id")["is_suspicious_ground_truth"].any().reset_index()
    
    # Merge with model results
    merged = cust_results_df.merge(gt_cust, on="customer_id", how="inner")
    
    if merged.empty:
        return {"has_ground_truth": False, "message": "No matching customer ground truth found."}

    # Predicted positive = Risk Score >= cutoff
    y_true = merged["is_suspicious_ground_truth"].astype(bool).values
    y_pred = (merged["risk_score"] >= cutoff).values
    
    tp = int(np.sum(y_true & y_pred))
    fp = int(np.sum(~y_true & y_pred))
    fn = int(np.sum(y_true & ~y_pred))
    tn = int(np.sum(~y_true & ~y_pred))
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / len(y_true) if len(y_true) > 0 else 0.0
    
    return {
        "has_ground_truth": True,
        "operating_mode": operating_mode,
        "cutoff_used": cutoff,
        "mode_description": mode_info["description"],
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "accuracy": round(accuracy, 4),
        "confusion_matrix": {
            "TP": tp,
            "FP": fp,
            "FN": fn,
            "TN": tn
        },
        "disclaimer": "DEMONSTRATION METRIC ONLY: Evaluated against synthetic benchmark labels."
    }
