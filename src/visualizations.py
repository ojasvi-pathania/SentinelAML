import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Standardized FinTech Compliance Color Palette
COLOR_MAP = {
    "High": "#DC2626",      # Crimson Red
    "Medium": "#F59E0B",    # Amber Yellow
    "Low": "#10B981"        # Emerald Green
}

FONT_FAMILY = "Plus Jakarta Sans, Inter, sans-serif"

def _apply_common_chart_style(fig, title_text: str):
    """
    Applies unified financial compliance theme to Plotly figures.
    """
    fig.update_layout(
        title={
            'text': title_text,
            'font': {'size': 16, 'family': FONT_FAMILY, 'color': '#0F172A', 'weight': 700},
            'x': 0.02,
            'xanchor': 'left'
        },
        font={'family': FONT_FAMILY, 'color': '#475569'},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=55, b=35, l=35, r=35),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=12, family=FONT_FAMILY)
        )
    )
    fig.update_xaxes(showgrid=True, gridcolor='#F1F5F9', zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor='#F1F5F9', zeroline=False)
    return fig

def plot_risk_distribution(cust_results_df: pd.DataFrame):
    """
    Renders risk level breakdown pie/donut chart.
    """
    if cust_results_df.empty or "risk_level" not in cust_results_df.columns:
        fig = go.Figure()
        return _apply_common_chart_style(fig, "Customer Risk Level Distribution (No Data)")
        
    counts = cust_results_df["risk_level"].value_counts().reset_index()
    counts.columns = ["Risk Level", "Customer Count"]
    
    fig = px.pie(
        counts,
        values="Customer Count",
        names="Risk Level",
        color="Risk Level",
        color_discrete_map=COLOR_MAP,
        hole=0.5
    )
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        marker=dict(line=dict(color='#FFFFFF', width=2))
    )
    return _apply_common_chart_style(fig, "Customer Risk Level Distribution")

def plot_top_high_risk_customers(cust_results_df: pd.DataFrame, top_n=10):
    """
    Renders horizontal bar chart of top high risk customers.
    """
    if cust_results_df.empty or "risk_score" not in cust_results_df.columns:
        fig = go.Figure()
        return _apply_common_chart_style(fig, "Top High Risk Customers (No Data)")
        
    df_top = cust_results_df.head(top_n).sort_values("risk_score", ascending=True)
    
    fig = px.bar(
        df_top,
        x="risk_score",
        y="customer_id",
        color="risk_level",
        color_discrete_map=COLOR_MAP,
        orientation="h",
        text="risk_score"
    )
    fig.update_traces(texttemplate='%{text:.1f}', textposition='outside', marker=dict(cornerradius=4))
    fig.update_layout(xaxis_title="Risk Score (0-100)", yaxis_title="Customer ID")
    return _apply_common_chart_style(fig, f"Top {top_n} Highest Risk Customers")

def plot_pattern_distribution(cust_results_df: pd.DataFrame):
    """
    Renders frequency count of triggered suspicious patterns.
    """
    if cust_results_df.empty or "triggered_patterns_list" not in cust_results_df.columns:
        fig = go.Figure()
        return _apply_common_chart_style(fig, "Triggered Patterns (No Data)")
        
    patterns = []
    for plist in cust_results_df["triggered_patterns_list"]:
        if isinstance(plist, list):
            patterns.extend(plist)
            
    if not patterns:
        fig = go.Figure()
        return _apply_common_chart_style(fig, "Triggered AML Patterns (None Detected)")
        
    df_p = pd.DataFrame(patterns, columns=["Pattern"]).value_counts().reset_index()
    df_p.columns = ["Pattern", "Count"]
    
    fig = px.bar(
        df_p,
        x="Pattern",
        y="Count",
        color="Count",
        color_continuous_scale=["#FECACA", "#EF4444", "#991B1B"]
    )
    fig.update_traces(marker=dict(cornerradius=4))
    fig.update_layout(xaxis_title="Suspicious Pattern", yaxis_title="Trigger Count", coloraxis_showscale=False)
    return _apply_common_chart_style(fig, "Triggered AML Suspicious Patterns Frequency")

def plot_transaction_type_distribution(tx_df: pd.DataFrame):
    """
    Renders transaction channel/type breakdown.
    """
    if tx_df.empty or "transaction_type" not in tx_df.columns:
        fig = go.Figure()
        return _apply_common_chart_style(fig, "Transaction Types (No Data)")
        
    df_t = tx_df["transaction_type"].value_counts().reset_index()
    df_t.columns = ["Transaction Type", "Count"]
    
    fig = px.bar(
        df_t,
        x="Transaction Type",
        y="Count",
        color="Transaction Type",
        color_discrete_sequence=["#2563EB", "#3B82F6", "#60A5FA", "#93C5FD"]
    )
    fig.update_traces(marker=dict(cornerradius=4))
    fig.update_layout(xaxis_title="Channel / Type", yaxis_title="Transaction Count", showlegend=False)
    return _apply_common_chart_style(fig, "Transaction Channel Distribution")

def plot_country_distribution(tx_df: pd.DataFrame):
    """
    Renders geographical distribution of transactions.
    """
    if tx_df.empty or "country" not in tx_df.columns:
        fig = go.Figure()
        return _apply_common_chart_style(fig, "Country Distribution (No Data)")
        
    df_c = tx_df["country"].value_counts().reset_index()
    df_c.columns = ["Country", "Transaction Count"]
    
    fig = px.bar(
        df_c,
        x="Country",
        y="Transaction Count",
        color="Transaction Count",
        color_continuous_scale=["#DBEAFE", "#2563EB", "#1E3A8A"]
    )
    fig.update_traces(marker=dict(cornerradius=4))
    fig.update_layout(xaxis_title="Jurisdiction Code", yaxis_title="Transaction Count", coloraxis_showscale=False)
    return _apply_common_chart_style(fig, "Geographical Jurisdiction Breakdown")

def plot_risk_gauge(score: float):
    """
    Renders single customer risk score gauge.
    """
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Composite Risk Index", 'font': {'size': 18, 'family': FONT_FAMILY, 'color': '#0F172A', 'weight': 700}},
        number={'font': {'size': 42, 'family': FONT_FAMILY, 'color': '#0F172A', 'weight': 800}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': '#CBD5E1'},
            'bar': {'color': "#0F172A", 'thickness': 0.3},
            'bgcolor': "white",
            'borderwidth': 1,
            'bordercolor': "#E2E8F0",
            'steps': [
                {'range': [0, 40], 'color': "rgba(16, 185, 129, 0.25)"},
                {'range': [40, 70], 'color': "rgba(245, 158, 11, 0.25)"},
                {'range': [70, 100], 'color': "rgba(220, 38, 38, 0.25)"}
            ],
            'threshold': {
                'line': {'color': "#DC2626", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': FONT_FAMILY},
        margin=dict(t=50, b=20, l=30, r=30),
        height=260
    )
    return fig

def plot_customer_timeline(cust_tx_df: pd.DataFrame):
    """
    Renders transaction timeline scatter chart for a single customer.
    """
    if cust_tx_df.empty:
        fig = go.Figure()
        return _apply_common_chart_style(fig, "Customer Timeline (No Data)")
        
    df = cust_tx_df.copy()
    df["dt"] = pd.to_datetime(df["timestamp"])
    
    fig = px.scatter(
        df,
        x="dt",
        y="amount",
        color="transaction_type",
        size="amount",
        hover_data=["transaction_id", "country"],
        color_discrete_sequence=["#2563EB", "#10B981", "#F59E0B", "#DC2626"]
    )
    fig.update_traces(marker=dict(opacity=0.85, line=dict(width=1, color='#FFFFFF')))
    fig.update_layout(xaxis_title="Timestamp", yaxis_title="Amount ($)")
    return _apply_common_chart_style(fig, "Customer Transaction Activity Timeline")
