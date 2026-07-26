import os

def generate_aml_explanation(
    cust_id: str,
    risk_result: dict,
    cust_row: dict = None
) -> dict:
    """
    Generates evidence-backed, human-readable AML explanations.
    Uses deterministic factual synthesis.
    """
    risk_score = risk_result.get("risk_score", 0.0)
    risk_level = risk_result.get("risk_level", "Low")
    triggered_patterns = risk_result.get("triggered_patterns", [])
    evidence_list = risk_result.get("all_evidence", [])
    rule_results = risk_result.get("rule_results", {})
    
    # Collect all supporting transaction IDs
    all_tx_ids = []
    for r_key, r_res in rule_results.items():
        if isinstance(r_res, dict) and r_res.get("triggered", False):
            all_tx_ids.extend(r_res.get("supporting_tx_ids", []))
    all_tx_ids = sorted(list(set(all_tx_ids)))
    
    # Construct Short Explanation
    if not triggered_patterns:
        short_exp = f"Customer {cust_id} exhibits a low risk score of {risk_score}/100 with standard transactional behavior."
    else:
        patterns_str = ", ".join(triggered_patterns)
        short_exp = (
            f"Customer {cust_id} evaluated with a {risk_level} risk score of {risk_score}/100. "
            f"Triggered indicators: {patterns_str}. {risk_result.get('strongest_evidence', '')}"
        )
        
    # Construct Detailed Explanation
    detailed_lines = [
        f"### Compliance Assessment Summary for Customer {cust_id}",
        f"- **Calculated Risk Score**: {risk_score} / 100 ({risk_level} Risk Category)",
        f"- **Triggered Patterns**: {', '.join(triggered_patterns) if triggered_patterns else 'None'}",
        f"- **Total Flagged Transactions**: {len(all_tx_ids)}",
        ""
    ]
    
    if evidence_list:
        detailed_lines.append("#### Empirical Key Findings:")
        for idx, ev in enumerate(evidence_list, 1):
            detailed_lines.append(f"{idx}. {ev}")
    else:
        detailed_lines.append("No specific rule thresholds or statistical anomalies were breached during analysis.")
        
    detailed_lines.append("\n*Note: This automated assessment provides risk signals based on pattern detection. Final determination requires human analyst validation.*")
    detailed_exp = "\n".join(detailed_lines)
    
    # Structured evidence table data
    evidence_table = []
    for r_key, r_res in rule_results.items():
        if isinstance(r_res, dict):
            evidence_table.append({
                "Rule Name": r_res.get("rule_name", r_key),
                "Status": "TRIGGERED" if r_res.get("triggered", False) else "Clear",
                "Signal Strength": f"{r_res.get('signal_strength', 0.0)*100:.0f}%",
                "Key Evidence": r_res.get("human_readable_reason", ""),
                "Supporting Tx Count": len(r_res.get("supporting_tx_ids", []))
            })
            
    return {
        "customer_id": cust_id,
        "short_explanation": short_exp,
        "detailed_explanation": detailed_exp,
        "triggered_rule_names": triggered_patterns,
        "evidence_table": evidence_table,
        "related_tx_ids": all_tx_ids
    }
