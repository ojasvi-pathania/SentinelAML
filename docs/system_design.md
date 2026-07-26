# SentinelAML — Technical System Design & Architecture

## 1. System Overview

**SentinelAML** is an enterprise-grade, query-aware suspicious activity investigation platform designed for banking compliance teams. Unlike legacy AML systems that run static, non-adaptive pipelines across the entire dataset for every query, SentinelAML dynamically interprets natural-language analyst intent, extracts target parameters, constructs a minimal tool execution workflow, skips redundant computations, and synthesizes factual compliance evidence.

---

## 2. Architectural Blueprint & Data Flow

```text
 ┌─────────────────────────────────────────────────────────────┐
 │                    Analyst Query Input                      │
 │      "Find structuring patterns in the last 30 days"        │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                  Hybrid Intent Extractor                    │
 │   • Checks st.secrets / os.environ (ANTHROPIC_API_KEY)     │
 │   • Claude 3.5 Haiku (Primary) OR Regex (Fallback)          │
 │   • Extracts: intent, customer_id, segment, timeframe,      │
 │     country, amount_threshold, pattern                      │
 │   • Produces clean explanation & recommendation policy      │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                  Adaptive Dynamic Planner                   │
 │   • Evaluates 15 available analytical tools                 │
 │   • Selects required tool dependency chain                  │
 │   • Skips redundant detectors (e.g. skips EDA for C0012)    │
 │   • Generates tool selection & skip rationale per tool      │
 │   • Computes optimization metrics (% computation saved)     │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                 Targeted Analytics Engine                   │
 │   • Data Slicing / Filtering Tool                           │
 │   • EDA Tool (Exploratory Distributions)                    │
 │   • Feature Engineering (24h rolling, near-CTR ratios)     │
 │   • Rule Detectors (Structuring, Velocity, Rapid Cash-Out) │
 │   • Isolation Forest ML Anomaly Model                       │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │               Risk Scoring & Evidence Synthesis             │
 │   • Composite 0–100 Risk Index (Low, Medium, High)          │
 │   • Evidence Matrix (Rule signals & Tx count)               │
 │   • Investigation Timeline (Chronological transactions)     │
 │   • Compliance Action Escalation (SAR filing, EDD, L1)      │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │               Institutional UI & Audit Export               │
 │   • Analyst Workspace (Query, Findings, Workflow JSON)      │
 │   • Risk & Alert Analytics Dashboards                       │
 │   • Entity Deep-Dive & HTML/PDF Case Report Download        │
 └──────────────────────────────┘
```

---

## 3. Core Component Specifications

### 3.1 Hybrid Intent Extractor (`src/intent_parser.py`)
- **Primary Engine**: Anthropic Claude 3.5 Haiku (`claude-3-5-haiku-20241022`) when `ANTHROPIC_API_KEY` is loaded from `st.secrets` or `os.environ`.
- **Fallback Engine**: High-precision deterministic regex pattern matcher.
- **Diagnostic Logging**: Captures `configured_provider`, `active_engine`, `routing_reason`, `model_name`, `request_status`, `response_parse_status`, `fallback_used`, `sanitized_error`, and `execution_time_ms`.
- **Policy Semantics**:
  ```json
  "explanation_policy": {
      "basic_explanation_enabled": true,
      "detailed_explanation_requested": false
  },
  "recommendation_policy": {
      "default_recommendation_enabled": true,
      "explicit_recommendation_requested": false
  }
  ```

---

## 4. Evidence Matrix and Investigation Timeline

### 4.1 Evidence Matrix
The Evidence Matrix resolves "black-box" AI concerns by exposing an empirical tabular audit trail for every flagged customer account:
- **Detected Pattern**: Exact rule triggered (e.g. `Structuring Pattern Detected`, `High Velocity Spikes`).
- **Supporting Transaction Count**: Total number of transactions contributing to the alert signal.
- **Relevant Transaction IDs**: List of specific transaction reference IDs (e.g. `TX0000042`, `TX0000089`).
- **Amount & Behavioral Evidence**: Exact dollar values and timestamps.
- **Signal Strength & Risk Contribution**: Weight of rule signal in the composite 0–100 risk score calculation.

### 4.2 Investigation Timeline
The Investigation Timeline provides a interactive chronological ledger plot visualizing:
- **Chronological Transaction Flow**: Inbound cash/wires vs outbound cash withdrawals.
- **Structuring Clusters**: Concentrated near-CTR deposits ($9,000–$9,999) highlighted visually.
- **Pass-Through Velocity**: Rapid cash-out deltas (<60 minutes) flagged along time axis.
- **Suspicious Sequence Highlighting**: Enables compliance analysts to trace exact fund flows before drafting SAR filings.
