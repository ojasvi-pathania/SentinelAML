def get_escalation_recommendation(
    cust_id: str,
    risk_score: float,
    risk_level: str,
    triggered_patterns: list
) -> dict:
    """
    Recommends proportional compliance escalation action based on risk level and pattern severity.
    """
    has_structuring = any("Structuring" in p or "Smurfing" in p for p in triggered_patterns)
    has_rapid_cashout = any("Rapid Cash-Out" in p for p in triggered_patterns)
    
    if risk_score >= 80.0 and (has_structuring or has_rapid_cashout):
        action = "Consider Regulatory Reporting Assessment (SAR / STR)"
        urgency = "URGENT (24-48 Hours)"
        rationale = (
            f"Customer {cust_id} exhibits critical risk ({risk_score}/100) with strong evidence of "
            f"structuring or rapid funds dissipation. Mandatory assessment for regulatory SAR filing."
        )
        steps = [
            "Initiate formal Suspicious Activity Report (SAR) assessment.",
            "Freeze high-risk outbound transfers pending compliance clearance.",
            "Request updated Source of Funds / Enhanced Due Diligence (EDD) documentation.",
            "Notify Senior Compliance Manager."
        ]
    elif risk_level == "High" or risk_score >= 70.0:
        action = "Escalate for Senior Compliance Review"
        urgency = "HIGH (1-2 Business Days)"
        rationale = (
            f"Customer {cust_id} scored in the High Risk tier ({risk_score}/100) due to multiple "
            f"triggered behavioral indicators ({', '.join(triggered_patterns)})."
        )
        steps = [
            "Assign to Senior AML Investigator.",
            "Perform cross-account relationship mapping.",
            "Review customer historical profile and expected transaction baseline.",
            "Determine if account restrictions are warranted."
        ]
    elif risk_level == "Medium" or risk_score >= 40.0:
        action = "Flag for Analyst Review"
        urgency = "MEDIUM (3-5 Business Days)"
        rationale = (
            f"Customer {cust_id} scored in the Medium Risk tier ({risk_score}/100). "
            f"Triggered indicators: {', '.join(triggered_patterns) if triggered_patterns else 'Statistical Anomaly'}."
        )
        steps = [
            "Assign to L1 AML Analyst for routine review.",
            "Verify documentation for largest recent transactions.",
            "Monitor transaction activity for further pattern escalation."
        ]
    else:
        action = "Maintain Standard Monitoring"
        urgency = "LOW (Routine)"
        rationale = f"Customer {cust_id} activity remains within normal risk parameters ({risk_score}/100)."
        steps = [
            "No immediate manual intervention required.",
            "Continue automated ongoing transaction monitoring."
        ]
        
    return {
        "customer_id": cust_id,
        "recommended_action": action,
        "urgency_level": urgency,
        "action_rationale": rationale,
        "next_steps": steps
    }
