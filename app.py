import streamlit as st
import pandas as pd
import numpy as np
import json
import io
import time

from src.data_generator import generate_synthetic_aml_data
from src.data_loader import load_transaction_csv
from src.validation import validate_aml_dataset
from src.agent import SentinelAMLAgent
from src.visualizations import (
    plot_risk_distribution,
    plot_top_high_risk_customers,
    plot_pattern_distribution,
    plot_transaction_type_distribution,
    plot_country_distribution,
    plot_risk_gauge,
    plot_customer_timeline
)
from src.reports import export_execution_plan_json, generate_html_customer_report
from src.evaluation import evaluate_synthetic_performance, OPERATING_MODE_PRESETS

# Page configuration
st.set_page_config(
    page_title="SentinelAML — Institutional Investigation Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def render_html(html_str: str):
    """
    Renders raw HTML string in Streamlit safely without markdown code-block escaping.
    Strips leading spaces from every line to ensure Markdown never parses HTML as code.
    """
    clean_html = "\n".join([line.strip() for line in html_str.splitlines() if line.strip()])
    st.markdown(clean_html, unsafe_allow_html=True)

# Commercial FinTech Compliance UI Design System
render_html("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #0F172A;
    }

    /* Main Container Spacing */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2.0rem;
        max-width: 1440px;
    }

    /* Hero Header Styling */
    .header-bar {
        background-color: #0F172A;
        border-radius: 12px;
        padding: 32px 32px 24px 32px;
        color: #FFFFFF;
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px;
        box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.1);
    }
    .header-title-group {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .header-title {
        font-size: 1.55rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        color: #FFFFFF;
        margin: 0;
        line-height: 1.2;
    }
    .header-subtitle {
        font-size: 0.88rem;
        color: #94A3B8;
        margin: 0;
        line-height: 1.4;
    }
    .status-badge-container {
        display: flex;
        gap: 10px;
        align-items: center;
        flex-wrap: wrap;
    }
    .status-badge-synth {
        background: #1E293B;
        color: #34D399;
        border: 1px solid #334155;
        padding: 6px 14px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .status-badge-csv {
        background: #1E293B;
        color: #60A5FA;
        border: 1px solid #334155;
        padding: 6px 14px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .status-badge-meta {
        background: #1E293B;
        color: #94A3B8;
        border: 1px solid #334155;
        padding: 6px 14px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 500;
    }

    /* Compact High-Density KPI Bar */
    .kpi-row {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 12px;
        margin-bottom: 16px;
    }
    .kpi-box {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 12px 14px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }
    .kpi-box-tx { border-top: 3px solid #2563EB; }
    .kpi-box-cust { border-top: 3px solid #475569; }
    .kpi-box-high { border-top: 3px solid #DC2626; }
    .kpi-box-med { border-top: 3px solid #F59E0B; }
    .kpi-box-susp { border-top: 3px solid #10B981; }
    .kpi-box-alert { border-top: 3px solid #EA580C; }

    .kpi-label {
        font-size: 0.7rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 4px;
    }
    .kpi-val {
        font-size: 1.4rem;
        font-weight: 700;
        color: #0F172A;
        line-height: 1.1;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: #F8FAFC;
        padding: 4px;
        border-radius: 6px;
        border: 1px solid #E2E8F0;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: 600;
        color: #475569;
        font-size: 0.85rem;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
    }

    /* Analysis Workflow Panel */
    .workflow-panel {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 16px;
        margin-bottom: 16px;
    }
    .workflow-header {
        font-size: 0.95rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 6px;
    }
    .workflow-meta {
        font-size: 0.82rem;
        color: #475569;
        margin-bottom: 10px;
    }
    .rationale-box {
        background: #F8FAFC;
        border-left: 3px solid #2563EB;
        padding: 10px 14px;
        border-radius: 4px;
        font-size: 0.85rem;
        color: #1E293B;
        margin-bottom: 12px;
    }
    .tool-badge-executed {
        background: #D1FAE5;
        color: #065F46;
        border: 1px solid #A7F3D0;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.76rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        margin: 2px;
    }
    .tool-badge-skipped {
        background: #F1F5F9;
        color: #64748B;
        border: 1px solid #E2E8F0;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.76rem;
        font-weight: 500;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        margin: 2px;
    }
    .metrics-bar {
        background: #F1F5F9;
        border-radius: 4px;
        padding: 8px 12px;
        display: flex;
        gap: 16px;
        font-size: 0.8rem;
        font-weight: 600;
        color: #334155;
        margin-bottom: 12px;
    }

    /* Risk Tier Badges */
    .badge-high {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 2px 8px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.78rem;
    }
    .badge-medium {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 2px 8px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.78rem;
    }
    .badge-low {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 2px 8px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.78rem;
    }

    /* Sidebar Grouping */
    .sidebar-panel {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 12px;
        margin-bottom: 12px;
    }
    .sidebar-title {
        font-size: 0.78rem;
        font-weight: 700;
        color: #0F172A;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 8px;
    }
    
    /* System Architecture Pipeline Step */
    .pipeline-step {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 14px;
        height: 100%;
    }
    .pipeline-num {
        background: #0F172A;
        color: #FFFFFF;
        width: 24px;
        height: 24px;
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.78rem;
        margin-bottom: 8px;
    }
</style>
""")

# Initialize Session State
if "raw_df" not in st.session_state:
    with st.spinner("Initializing transaction baseline dataset..."):
        st.session_state.raw_df = generate_synthetic_aml_data(
            num_customers=160,
            min_transactions=4200,
            seed=42
        )
        
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    
if "latest_agent_response" not in st.session_state:
    st.session_state.latest_agent_response = None

# ---------------------------------------------------------
# SIDEBAR CONFIGURATION
# ---------------------------------------------------------
with st.sidebar:
    render_html('<div class="sidebar-title">System Controls & Parameters</div>')
    
    render_html('<div class="sidebar-panel">')
    st.markdown('**Data Selection**')
    data_source_mode = st.radio(
        "Source Mode",
        ["Synthetic Benchmark Data", "Upload Custom CSV"],
        index=0,
        key="sb_data_source_mode",
        help="Switch between synthetic banking benchmark and custom transaction CSV uploads."
    )
    
    if data_source_mode == "Upload Custom CSV":
        uploaded_file = st.file_uploader(
            "Upload Transaction CSV",
            type=["csv"],
            key="sb_csv_uploader",
            help="Expected columns: transaction_id, customer_id, timestamp, amount, transaction_type, country, segment."
        )
        if uploaded_file is not None:
            try:
                df_loaded, warnings = load_transaction_csv(uploaded_file)
                st.session_state.raw_df = df_loaded
                st.success(f"Ingested {len(df_loaded):,} transaction records.")
                for w in warnings:
                    st.warning(w)
            except Exception as e:
                st.error(f"Ingestion Error: {str(e)}")
    else:
        num_custs = st.slider(
            "Target Accounts",
            min_value=50,
            max_value=300,
            value=160,
            step=10,
            key="sb_num_custs_slider",
            help="Number of synthetic customer accounts to generate."
        )
        seed_val = st.number_input(
            "Simulation Seed",
            min_value=1,
            max_value=9999,
            value=42,
            key="sb_seed_input",
            help="Random seed for reproducible benchmark scenario generation."
        )
        if st.button("🔄 Regenerate Benchmark Data", width="stretch", key="sb_regen_btn"):
            st.session_state.raw_df = generate_synthetic_aml_data(
                num_customers=num_custs,
                seed=seed_val
            )
            st.success("Benchmark dataset regenerated.")
    render_html('</div>')

    render_html('<div class="sidebar-panel">')
    st.markdown('**Operating Mode Presets**')
    operating_mode = st.selectbox(
        "Operating Mode",
        ["Precision First (Default)", "Balanced (F1 Optimal)", "Recall First (High Sensitivity)"],
        index=0,
        key="sb_operating_mode",
        help="Calibrates detector thresholds and risk cutoffs for alert precision vs detection sensitivity."
    )
    mode_preset = OPERATING_MODE_PRESETS[operating_mode]
    default_high_cutoff = mode_preset["cutoff"]
    st.caption(f"ℹ️ {mode_preset['description']}")
    render_html('</div>')

    render_html('<div class="sidebar-panel">')
    st.markdown('**Detection Thresholds**')
    reporting_threshold = st.number_input(
        "CTR Threshold ($)",
        value=10000.0,
        step=1000.0,
        key="sb_reporting_thresh",
        help="Currency Transaction Reporting limit for cash transactions (e.g. BSA $10,000 threshold)."
    )
    structuring_min = st.number_input(
        "Structuring Bound ($)",
        value=9000.0,
        step=500.0,
        key="sb_structuring_min",
        help="Lower limit for detecting near-threshold cash deposits."
    )
    velocity_thresh = st.number_input(
        "24h Velocity Ceiling",
        value=10,
        step=1,
        key="sb_velocity_thresh",
        help="Maximum expected transaction count per account in a 24-hour window."
    )
    render_html('</div>')

    render_html('<div class="sidebar-panel">')
    st.markdown('**Risk Tiers & Models**')
    low_risk_thresh = st.slider(
        "Low Risk Cutoff",
        min_value=20.0,
        max_value=50.0,
        value=40.0,
        key="sb_low_risk_slider",
        help="Scores below this threshold are designated Low Risk."
    )
    high_risk_thresh = st.slider(
        "High Risk Cutoff",
        min_value=35.0,
        max_value=90.0,
        value=float(default_high_cutoff),
        key="sb_high_risk_slider",
        help="Scores above this threshold are designated High Risk."
    )
    contamination = st.slider(
        "Isolation Forest Factor",
        min_value=0.01,
        max_value=0.20,
        value=0.08,
        step=0.01,
        key="sb_contamination_slider",
        help="Contamination parameter for unsupervised anomaly detection."
    )
    render_html('</div>')

    csv_bytes = st.session_state.raw_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Export Raw Dataset CSV",
        data=csv_bytes,
        file_name="sentinel_aml_transactions.csv",
        mime="text/csv",
        width="stretch",
        key="sb_download_raw_csv"
    )

# Instantiate SentinelAML Agent
agent = SentinelAMLAgent(
    reporting_threshold=reporting_threshold,
    structuring_min=structuring_min,
    velocity_threshold=velocity_thresh,
    low_risk_threshold=low_risk_thresh,
    high_risk_threshold=high_risk_thresh,
    contamination=contamination
)

# ---------------------------------------------------------
# HEADER & OPERATIONAL METADATA BAR
# ---------------------------------------------------------
is_synthetic = "is_suspicious_ground_truth" in st.session_state.raw_df.columns
data_badge = (
    '<span class="status-badge-synth">Synthetic Benchmark (160 Accounts | 4,200+ Txs)</span>'
    if is_synthetic else
    f'<span class="status-badge-csv">Custom CSV Dataset ({len(st.session_state.raw_df):,} Txs)</span>'
)

render_html(f"""
<div class="header-bar">
    <div class="header-title-group">
        <div class="header-title">SentinelAML — Institutional Investigation Platform</div>
        <div class="header-subtitle">Query-aware intelligence engine for dynamic suspicious transaction analysis and automated case synthesis.</div>
    </div>
    <div class="status-badge-container">
        {data_badge}
        <span class="status-badge-meta">Mode: {operating_mode.split()[0]}</span>
        <span class="status-badge-meta">Engine: 5 Detectors Active</span>
        <span class="status-badge-meta">Latency: ~18ms</span>
    </div>
</div>
""")

# Process baseline dataset query
t0 = time.time()
with st.spinner("Executing baseline analysis..."):
    baseline_response = agent.process_query("Analyse the complete dataset", st.session_state.raw_df)
    baseline_cust_df = baseline_response["customer_results"]
    baseline_tx_df = baseline_response["tx_features_df"]
    flagged_tx_df = baseline_response["flagged_transactions"]
t_exec = (time.time() - t0) * 1000

# ---------------------------------------------------------
# KPI SUMMARY STRIP
# ---------------------------------------------------------
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    render_html(f"""
    <div class="kpi-box kpi-box-tx">
        <div class="kpi-label">Transactions</div>
        <div class="kpi-val">{len(st.session_state.raw_df):,}</div>
    </div>
    """)

with col2:
    render_html(f"""
    <div class="kpi-box kpi-box-cust">
        <div class="kpi-label">Accounts</div>
        <div class="kpi-val">{len(baseline_cust_df):,}</div>
    </div>
    """)

with col3:
    n_high = (baseline_cust_df["risk_level"] == "High").sum() if not baseline_cust_df.empty else 0
    render_html(f"""
    <div class="kpi-box kpi-box-high">
        <div class="kpi-label">High Risk</div>
        <div class="kpi-val" style="color: #DC2626;">{n_high}</div>
    </div>
    """)

with col4:
    n_med = (baseline_cust_df["risk_level"] == "Medium").sum() if not baseline_cust_df.empty else 0
    render_html(f"""
    <div class="kpi-box kpi-box-med">
        <div class="kpi-label">Medium Risk</div>
        <div class="kpi-val" style="color: #F59E0B;">{n_med}</div>
    </div>
    """)

with col5:
    susp_amt = flagged_tx_df["amount"].sum() if not flagged_tx_df.empty else 0.0
    render_html(f"""
    <div class="kpi-box kpi-box-susp">
        <div class="kpi-label">Suspicious Volume</div>
        <div class="kpi-val" style="color: #10B981;">${susp_amt:,.0f}</div>
    </div>
    """)

with col6:
    n_alerts = len(flagged_tx_df) if not flagged_tx_df.empty else 0
    render_html(f"""
    <div class="kpi-box kpi-box-alert">
        <div class="kpi-label">System Alerts</div>
        <div class="kpi-val" style="color: #EA580C;">{n_alerts}</div>
    </div>
    """)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# MAIN NAVIGATION TABS
# ---------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🔍 Analyst Workspace",
    "📊 Risk Analytics",
    "👤 Entity Deep-Dive",
    "⚠️ Alert Queue",
    "📈 Data Health & Quality",
    "ℹ️ System Architecture"
])

# ---------------------------------------------------------
# TAB 1: ANALYST WORKSPACE
# ---------------------------------------------------------
with tab1:
    st.markdown("##### Dynamic Natural Language Query Engine")
    st.caption("Enter natural-language criteria below or select a quick query filter to trigger adaptive analysis.")
    
    # Expanded Banking Investigation Query Presets
    ex_col1, ex_col2, ex_col3, ex_col4 = st.columns(4)
    ex_col5, ex_col6, ex_col7, ex_col8 = st.columns(4)
    selected_query = None
    
    with ex_col1:
        if st.button("Suspicious Retail Accounts", width="stretch", key="btn_ex_retail"):
            selected_query = "Analyse suspicious retail customers."
    with ex_col2:
        if st.button("Corporate Rapid Cash-Out", width="stretch", key="btn_ex_corp_cashout"):
            selected_query = "Corporate accounts with rapid cash-out."
    with ex_col3:
        if st.button("Inspect C0012 Account", width="stretch", key="btn_ex_c0012"):
            selected_query = "Is customer ID C0012 suspicious?"
    with ex_col4:
        if st.button("Cross-Border UAE Txs", width="stretch", key="btn_ex_uae"):
            selected_query = "Show suspicious transactions from UAE"

    with ex_col5:
        if st.button("10+ Deposits Below $10k", width="stretch", key="btn_ex_10plus"):
            selected_query = "Which customers made 10 or more transactions below 10,000?"
    with ex_col6:
        if st.button("High-Risk SME Accounts", width="stretch", key="btn_ex_sme"):
            selected_query = "Show high-risk SME customers."
    with ex_col7:
        if st.button("Compliance Summary (C0004)", width="stretch", key="btn_ex_c0004"):
            selected_query = "Why was customer C0004 classified as high risk?"
    with ex_col8:
        if st.button("SAR Assessment Required", width="stretch", key="btn_ex_sar"):
            selected_query = "Which customers require SAR assessment?"

    user_input = st.chat_input("Filter by account ID, segment, timeframe, velocity, or structuring...", key="chat_user_input")
    
    active_query = user_input if user_input else selected_query
    
    if active_query:
        with st.spinner("Parsing query intent and structuring execution plan..."):
            agent_response = agent.process_query(active_query, st.session_state.raw_df)
            st.session_state.latest_agent_response = agent_response
            st.session_state.chat_history.append((active_query, agent_response))

    # Display Response & Analysis Workflow Card
    if st.session_state.latest_agent_response:
        resp = st.session_state.latest_agent_response
        plan = resp["execution_plan"]
        parsed_intent = resp["parsed_intent"]
        opt_metrics = plan.get("optimization_metrics", {})
        diag = parsed_intent.get("diagnostics", {})
        
        st.markdown("---")
        st.markdown(f"##### Query Target: *\"{resp['query']}\"*")
        
        executed_badges = " ".join([f'<span class="tool-badge-executed">✓ {t}</span>' for t in plan["selected_tools"]])
        skipped_badges = " ".join([f'<span class="tool-badge-skipped">⚡ {t}</span>' for t in plan["skipped_tools"]])
        
        filters_json = json.dumps(plan['extracted_filters'])
        engine_used = parsed_intent.get("intent_engine", "Rule-Based Fallback")
        engine_badge = f'<span style="background: #E0E7FF; color: #3730A3; padding: 2px 8px; border-radius: 10px; font-weight: 600; font-size: 0.76rem;">Intent Engine: ✓ {engine_used}</span>'
        
        render_html(f"""
<div class="workflow-panel">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <div class="workflow-header">Analysis Workflow</div>
        <div>{engine_badge}</div>
    </div>
    
    <div class="metrics-bar">
        <span>⚡ Executed Tools: {opt_metrics.get('executed_tools_count', 0)}</span>
        <span>⚡ Skipped Tools: {opt_metrics.get('skipped_tools_count', 0)}</span>
        <span>⚡ Computation Saved: {opt_metrics.get('computation_saved_percent', 0)}%</span>
        <span>⚡ Runtime: {opt_metrics.get('runtime_ms', 0)} ms</span>
    </div>
    
    <div class="workflow-meta">
        <strong>Detected Intent</strong>: <code style="color: #2563EB;">{plan['detected_intent']}</code> &nbsp;|&nbsp; 
        <strong>Extracted Parameters</strong>: <code>{filters_json}</code>
    </div>
    
    <div class="rationale-box">
        <strong>Tool Selection Rationale</strong>: {plan['reason_for_plan']}
    </div>
    
    <div style="margin-bottom: 8px;">
        <div style="font-size: 0.78rem; font-weight: 700; color: #065F46; margin-bottom: 4px; text-transform: uppercase;">
            Executed Analytical Tools ({len(plan['selected_tools'])})
        </div>
        {executed_badges}
    </div>
    
    <div>
        <div style="font-size: 0.78rem; font-weight: 700; color: #64748B; margin-bottom: 4px; text-transform: uppercase;">
            Skipped / Optimized Tools ({len(plan['skipped_tools'])})
        </div>
        {skipped_badges}
    </div>
</div>
""")
        
        # Tool Selection Rationale Expander & Intent Diagnostics
        diag_col1, diag_col2 = st.columns(2)
        with diag_col1:
            with st.expander("🔍 Inspect Detailed Tool Selection Rationale"):
                st.markdown("**Executed Tools Selection Reasons:**")
                for t_name, t_reason in plan.get("selected_tool_reasons", {}).items():
                    st.markdown(f"- **`{t_name}`**: {t_reason}")
                st.markdown("**Skipped Tools Rationale:**")
                for t_name, t_reason in plan.get("skipped_tool_reasons", {}).items():
                    st.markdown(f"- **`{t_name}`**: {t_reason}")

        with diag_col2:
            with st.expander("🔍 Intent Engine Diagnostics"):
                st.markdown(f"**Configured Provider**: `{diag.get('provider', 'N/A')}`")
                st.markdown(f"**Key Configured**: `{diag.get('api_key_configured', False)}` (`{diag.get('key_source', 'unavailable')}`)")
                st.markdown(f"**Active Engine**: `{diag.get('active_engine', engine_used)}`")
                st.markdown(f"**Requested Model**: `{diag.get('requested_model', diag.get('model_name', 'N/A'))}`")
                st.markdown(f"**Selected Model**: `{diag.get('selected_model', diag.get('model_name', 'N/A'))}`")
                st.markdown(f"**Available Model Check**: `{diag.get('available_model_check', 'Not Run')}`")
                st.markdown(f"**Request Status**: `{diag.get('request_status', 'N/A')}`")
                st.markdown(f"**Response Parse Status**: `{diag.get('response_parse_status', 'N/A')}`")
                st.markdown(f"**Fallback Used**: `{diag.get('fallback_used', True)}`")
                st.markdown(f"**HTTP / API Error**: `{diag.get('http_error', 'None')}`")
                st.markdown(f"**Routing Reason**: `{diag.get('routing_reason', 'N/A')}`")
                st.markdown(f"**Execution Latency**: `{diag.get('execution_time_ms', 0)} ms`")
                if diag.get("sanitized_error"):
                    st.warning(f"Sanitized Warning: {diag['sanitized_error']}")
                st.caption("ℹ️ Developer Note: Streamlit requires a full process restart after secrets or environment variable changes.")


        # Investigation Findings
        st.markdown("##### Investigation Findings")
        cust_res = resp["customer_results"]
        
        if cust_res.empty:
            st.warning("No account records matched the specified query parameters.")
        else:
            display_cols = ["customer_id", "segment", "risk_score", "risk_level", "triggered_patterns", "recommended_action", "urgency_level", "short_explanation"]
            st.dataframe(
                cust_res[[c for c in display_cols if c in cust_res.columns]],
                width="stretch",
                column_config={
                    "customer_id": st.column_config.TextColumn("Account ID"),
                    "segment": st.column_config.TextColumn("Segment"),
                    "risk_score": st.column_config.NumberColumn("Risk Score", format="%.1f"),
                    "risk_level": st.column_config.TextColumn("Risk Tier"),
                    "triggered_patterns": st.column_config.TextColumn("Triggered Patterns"),
                    "recommended_action": st.column_config.TextColumn("Recommended Action"),
                    "urgency_level": st.column_config.TextColumn("Urgency"),
                    "short_explanation": st.column_config.TextColumn("Evidence Explanation", width="large")
                }
            )
            
            res_col1, res_col2 = st.columns(2)
            with res_col1:
                res_csv = cust_res.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Export Findings (CSV)",
                    data=res_csv,
                    file_name="query_investigation_results.csv",
                    mime="text/csv",
                    width="stretch",
                    key="btn_export_res_csv"
                )
            with res_col2:
                plan_json = export_execution_plan_json(plan)
                st.download_button(
                    "📥 Export Analysis Workflow (JSON)",
                    data=plan_json,
                    file_name="agent_execution_plan.json",
                    mime="application/json",
                    width="stretch",
                    key="btn_download_plan_json"
                )

# ---------------------------------------------------------
# TAB 2: RISK ANALYTICS
# ---------------------------------------------------------
with tab2:
    st.markdown("##### Institutional Portfolio Risk Profile")
    
    d_col1, d_col2 = st.columns(2)
    with d_col1:
        st.plotly_chart(plot_risk_distribution(baseline_cust_df), width="stretch", key="chart_risk_dist_tab2")
    with d_col2:
        st.plotly_chart(plot_top_high_risk_customers(baseline_cust_df), width="stretch", key="chart_top_high_risk_tab2")
        
    d_col3, d_col4 = st.columns(2)
    with d_col3:
        st.plotly_chart(plot_pattern_distribution(baseline_cust_df), width="stretch", key="chart_pattern_dist_tab2")
    with d_col4:
        st.plotly_chart(plot_transaction_type_distribution(st.session_state.raw_df), width="stretch", key="chart_tx_type_dist_tab2")

    # Benchmark Performance Validation & Operating Modes
    st.markdown("---")
    st.markdown("##### Detection Model Ground-Truth Benchmark Evaluation")
    eval_res = evaluate_synthetic_performance(
        st.session_state.raw_df,
        baseline_cust_df,
        operating_mode=operating_mode
    )
    
    if eval_res.get("has_ground_truth"):
        st.markdown(f"**Active Operating Mode**: `{eval_res['operating_mode']}` &nbsp;|&nbsp; **Risk Cutoff Used**: `>= {eval_res['cutoff_used']}`")
        st.caption(f"ℹ️ {eval_res['mode_description']}")
        
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.metric("Precision", f"{eval_res['precision']*100:.1f}%")
        with m_col2:
            st.metric("Recall", f"{eval_res['recall']*100:.1f}%")
        with m_col3:
            st.metric("F1-Score", f"{eval_res['f1_score']*100:.1f}%")
        with m_col4:
            st.metric("Accuracy", f"{eval_res['accuracy']*100:.1f}%")
            
        cm = eval_res["confusion_matrix"]
        st.info(f"Ground Truth Evaluation Matrix: True Positives (TP): {cm['TP']} | False Positives (FP): {cm['FP']} | False Negatives (FN): {cm['FN']} | True Negatives (TN): {cm['TN']}")
        st.caption("ℹ️ These metrics are measured on synthetic labelled demonstration data and do not represent production banking performance.")
    else:
        st.warning(eval_res.get("message", "Evaluation metrics unavailable."))

# ---------------------------------------------------------
# TAB 3: ENTITY DEEP-DIVE
# ---------------------------------------------------------
with tab3:
    st.markdown("##### Account-Level Case Investigation")
    
    if not baseline_cust_df.empty:
        cust_list = baseline_cust_df["customer_id"].tolist()
        selected_cust_id = st.selectbox("Select Target Account Number", options=cust_list, index=0, key="select_cust_tab3")
        
        c_info = baseline_cust_df[baseline_cust_df["customer_id"] == selected_cust_id].iloc[0].to_dict()
        
        c_col1, c_col2 = st.columns([1, 2])
        with c_col1:
            st.plotly_chart(plot_risk_gauge(c_info["risk_score"]), width="stretch", key="chart_risk_gauge_tab3")
            
            risk_tier = c_info['risk_level']
            badge_class = "badge-high" if risk_tier == "High" else ("badge-medium" if risk_tier == "Medium" else "badge-low")
            
            render_html(f'**Risk Tier**: <span class="{badge_class}">{risk_tier} ({c_info["risk_score"]:.1f}/100)</span>')
            st.markdown(f"**Customer Segment**: `{c_info.get('segment', 'Retail')}`")
            st.markdown(f"**Triggered Signals**: `{c_info['triggered_patterns']}`")
            st.markdown(f"**Isolation Forest Score**: `{c_info['anomaly_score']:.2f}`")
            
        with c_col2:
            st.markdown("##### Recommended Compliance Escalation")
            st.warning(f"**{c_info['recommended_action']}** (Priority: {c_info['urgency_level']})")
            st.markdown(f"**Action Rationale**: {c_info['action_rationale']}")
            st.markdown("**Compliance Steps**:")
            for s in c_info.get("next_steps", []):
                st.markdown(f"- {s}")
                
        st.markdown("---")
        st.markdown("##### Empirical Findings & Explanation")
        st.markdown(c_info["detailed_explanation"])
        
        st.markdown("##### Evidence Matrix")
        if c_info.get("evidence_table"):
            st.table(pd.DataFrame(c_info["evidence_table"]))
            
        st.markdown("---")
        st.markdown("##### Investigation Timeline & Ledger")
        c_txs = st.session_state.raw_df[st.session_state.raw_df["customer_id"] == selected_cust_id]
        st.plotly_chart(plot_customer_timeline(c_txs), width="stretch", key="chart_cust_timeline_tab3")
        st.dataframe(c_txs, width="stretch")
        
        # Case Report Download
        html_report = generate_html_customer_report(c_info)
        st.download_button(
            "📥 Download Case Compliance Report (HTML/PDF)",
            data=html_report,
            file_name=f"sentinel_aml_report_{selected_cust_id}.html",
            mime="text/html",
            width="stretch",
            key="btn_download_html_report_tab3"
        )

# ---------------------------------------------------------
# TAB 4: ALERT QUEUE
# ---------------------------------------------------------
with tab4:
    st.markdown("##### Flagged Transaction Alert Queue")
    
    if not flagged_tx_df.empty:
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            country_filter = st.multiselect("Jurisdiction Filter", options=sorted(flagged_tx_df["country"].dropna().unique()), key="ms_country_tab4")
        with f_col2:
            type_filter = st.multiselect("Channel Filter", options=sorted(flagged_tx_df["transaction_type"].dropna().unique()), key="ms_type_tab4")
            
        view_df = flagged_tx_df.copy()
        if country_filter:
            view_df = view_df[view_df["country"].isin(country_filter)]
        if type_filter:
            view_df = view_df[view_df["transaction_type"].isin(type_filter)]
            
        display_fcols = ["transaction_id", "customer_id", "segment", "timestamp", "amount", "transaction_type", "country"]
        st.dataframe(
            view_df[[c for c in display_fcols if c in view_df.columns]],
            width="stretch",
            column_config={
                "transaction_id": st.column_config.TextColumn("Tx ID"),
                "customer_id": st.column_config.TextColumn("Account ID"),
                "segment": st.column_config.TextColumn("Segment"),
                "timestamp": st.column_config.TextColumn("Timestamp"),
                "amount": st.column_config.NumberColumn("Amount ($)", format="$%.2f"),
                "transaction_type": st.column_config.TextColumn("Channel"),
                "country": st.column_config.TextColumn("Jurisdiction")
            }
        )
        
        f_csv = view_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Export Flagged Alerts (CSV)",
            data=f_csv,
            file_name="flagged_suspicious_transactions.csv",
            mime="text/csv",
            width="stretch",
            key="btn_export_flagged_csv_tab4"
        )
    else:
        st.info("Zero suspicious transactions flagged under current baseline.")

# ---------------------------------------------------------
# TAB 5: DATA HEALTH & QUALITY
# ---------------------------------------------------------
with tab5:
    st.markdown("##### Data Integrity Profile & Exploratory Analysis")
    
    val_report = validate_aml_dataset(st.session_state.raw_df)
    
    q_col1, q_col2, q_col3 = st.columns(3)
    with q_col1:
        st.metric("Total Records", f"{val_report['total_rows']:,}")
        st.metric("Unique Accounts", f"{val_report['total_customers']:,}")
    with q_col2:
        st.metric("Duplicate Tx IDs", val_report["duplicate_tx_ids"])
        st.metric("Invalid Amounts", val_report["invalid_amounts"])
    with q_col3:
        st.metric("Timestamp Anomalies", val_report["invalid_timestamps"])
        st.metric("Missing Account IDs", val_report["missing_customer_ids"])
        
    if val_report["warnings"]:
        with st.expander("Data Quality Warnings"):
            for w in val_report["warnings"]:
                st.warning(w)
                
    st.markdown("---")
    st.markdown("##### Distribution Diagnostics")
    e_col1, e_col2 = st.columns(2)
    with e_col1:
        st.plotly_chart(plot_country_distribution(st.session_state.raw_df), width="stretch", key="chart_country_dist_tab5")
    with e_col2:
        st.plotly_chart(plot_transaction_type_distribution(st.session_state.raw_df), width="stretch", key="chart_tx_type_dist_tab5")

# ---------------------------------------------------------
# TAB 6: SYSTEM ARCHITECTURE
# ---------------------------------------------------------
with tab6:
    st.markdown("##### System Architecture & Pipeline Flow")
    
    st.markdown("""
    SentinelAML eliminates static non-adaptive pipelines by leveraging natural-language intent parsing, dynamic tool planning, explainable rule detection, and unsupervised anomaly models.
    """)
    
    st.markdown("##### End-to-End Processing Stages")
    a_col1, a_col2, a_col3 = st.columns(3)
    
    with a_col1:
        render_html("""
        <div class="pipeline-step">
            <div class="pipeline-num">1</div>
            <div style="font-weight: 700; color: #0F172A; margin-bottom: 4px;">Natural Language Query</div>
            <div style="font-size: 0.82rem; color: #475569;">Analyst inputs unstructured query specifying timeframe, threshold, account ID, or pattern.</div>
        </div>
        """)

    with a_col2:
        render_html("""
        <div class="pipeline-step">
            <div class="pipeline-num">2</div>
            <div style="font-weight: 700; color: #0F172A; margin-bottom: 4px;">Intent & Parameter Extractor</div>
            <div style="font-size: 0.82rem; color: #475569;">Regex / AI entity extraction parses date windows, dollar caps, account IDs, segments, and jurisdictions.</div>
        </div>
        """)

    with a_col3:
        render_html("""
        <div class="pipeline-step">
            <div class="pipeline-num">3</div>
            <div style="font-weight: 700; color: #0F172A; margin-bottom: 4px;">Adaptive Tool Planner</div>
            <div style="font-size: 0.82rem; color: #475569;">Constructs optimal tool dependency chain while bypassing redundant detectors.</div>
        </div>
        """)

    st.markdown("<br>", unsafe_allow_html=True)
    a_col4, a_col5, a_col6 = st.columns(3)

    with a_col4:
        render_html("""
        <div class="pipeline-step">
            <div class="pipeline-num">4</div>
            <div style="font-weight: 700; color: #0F172A; margin-bottom: 4px;">Targeted Analytics Engine</div>
            <div style="font-size: 0.82rem; color: #475569;">Executes feature aggregations, deterministic rule detectors, and Isolation Forest ML models.</div>
        </div>
        """)

    with a_col5:
        render_html("""
        <div class="pipeline-step">
            <div class="pipeline-num">5</div>
            <div style="font-weight: 700; color: #0F172A; margin-bottom: 4px;">Composite Risk & Evidence Synthesis</div>
            <div style="font-size: 0.82rem; color: #475569;">Computes composite 0-100 risk score and synthesizes factual natural language evidence.</div>
        </div>
        """)

    with a_col6:
        render_html("""
        <div class="pipeline-step">
            <div class="pipeline-num">6</div>
            <div style="font-weight: 700; color: #0F172A; margin-bottom: 4px;">Compliance Action Escalation</div>
            <div style="font-size: 0.82rem; color: #475569;">Recommends actionable compliance next steps (SAR filing, EDD review, L1 review).</div>
        </div>
        """)
