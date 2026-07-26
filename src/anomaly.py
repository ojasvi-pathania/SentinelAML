import pandas as pd
import numpy as np

class AMLAnomalyDetector:
    """
    Unsupervised Anomaly Detector using Isolation Forest.
    Calculates normalized anomaly scores (0.0 to 1.0) on customer-level features.
    Provides graceful fallback if scikit-learn is missing or fails.
    """
    def __init__(self, contamination: float = 0.08, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state

    def fit_predict(self, cust_df: pd.DataFrame) -> pd.DataFrame:
        """
        Fits Isolation Forest on customer features and appends 'anomaly_score' (0..1)
        and 'is_anomaly' (bool).
        """
        df = cust_df.copy()
        
        if df.empty or len(df) < 5:
            df["anomaly_score"] = 0.0
            df["is_anomaly"] = False
            return df
            
        feature_cols = [
            "tx_count", "total_amount", "avg_amount", "max_amount", "std_amount",
            "tx_per_active_day", "near_threshold_count", "near_threshold_ratio",
            "max_rolling_tx_24h", "countries_count", "rapid_cashout_count",
            "round_amount_count", "max_amount_zscore"
        ]
        
        # Ensure all columns exist
        available_cols = [col for col in feature_cols if col in df.columns]
        
        if not available_cols:
            df["anomaly_score"] = 0.0
            df["is_anomaly"] = False
            return df

        X = df[available_cols].fillna(0.0).values
        
        try:
            from sklearn.ensemble import IsolationForest
            from sklearn.preprocessing import StandardScaler
            
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            iso = IsolationForest(
                contamination=self.contamination,
                random_state=self.random_state,
                n_estimators=100
            )
            
            # Predict returns -1 for anomaly, 1 for normal
            preds = iso.fit_predict(X_scaled)
            # decision_function returns negative values for anomalies, positive for normal
            raw_scores = iso.decision_function(X_scaled)
            
            # Min-max scale raw scores so higher score means MORE anomalous
            # raw_scores range roughly -0.5 to 0.5. Invert it.
            inv_scores = -raw_scores
            min_s, max_s = inv_scores.min(), inv_scores.max()
            
            if max_s > min_s:
                norm_scores = (inv_scores - min_s) / (max_s - min_s)
            else:
                norm_scores = np.zeros(len(df))
                
            df["anomaly_score"] = np.round(norm_scores, 3)
            df["is_anomaly"] = preds == -1
            
        except Exception as e:
            # Fallback heuristic if sklearn unavailable or errors
            # Calculate simple z-score based anomaly index
            z_sum = np.zeros(len(df))
            for col in available_cols:
                vals = df[col].values
                std = np.std(vals)
                if std > 0:
                    z_sum += np.abs((vals - np.mean(vals)) / std)
            max_z = z_sum.max() if len(z_sum) > 0 and z_sum.max() > 0 else 1.0
            df["anomaly_score"] = np.round(z_sum / max_z, 3)
            df["is_anomaly"] = df["anomaly_score"] > 0.75
            
        return df
