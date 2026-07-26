# SentinelAML — Agentic Architecture Guide

SentinelAML is a query-aware Anti-Money Laundering (AML) investigation assistant designed for modern compliance teams. Unlike static AML systems that execute the same fixed data processing pipeline for every request, SentinelAML employs an agentic planning framework to evaluate analyst questions dynamically.

## Core Agent Components

```
Analyst Query
     │
     ▼
[Intent Parser] ──► Extracts Entities, Parameters & Target AML Patterns
     │
     ▼
[Dynamic Planner] ──► Selects Optimal Tool Execution Chain & Skips Redundant Modules
     │
     ▼
[Analytical Tools] ──► Executes Targeted Data Ingestion, Feature Eng & Detectors
     │
     ▼
[Risk Engine] ──► Computes Composite 0-100 Risk Score & Tier Assignment
     │
     ▼
[Explanation System] ──► Synthesizes Empirical Evidence & Cites Flagged Tx IDs
     │
     ▼
[Escalation Engine] ──► Recommends Proportional Regulatory & Operations Next Steps
```

### 1. Intent Parser (`src/intent_parser.py`)
- Uses deterministic regex pattern matching and keyword extraction to identify query intent, target subject (e.g. `C0012`), timeframe (`last 30 days`), threshold values (`below $10,000`), minimum transaction counts (`10 or more`), country filters (`KY`, `US`), and risk categories (`High`).

### 2. Dynamic Planner (`src/planner.py`)
- Maps parsed intent to specific tool execution sequences.
- Maintains a registry of 15 analytical tools (Data Ingestion, Filtering, EDA, Feature Engineering, Structuring Detector, Velocity Detector, Rapid Cashout Detector, ML Anomaly Model, Customer Lookup, Risk Classification, Explanation, Recommendation, Visualization, Export).
- Explicitly logs selected tools, skipped tools, and human-readable plan rationale.

### 3. Feature & Detection Engine (`src/features.py`, `src/rules.py`, `src/anomaly.py`)
- **Rule Detectors**: Deterministic detectors for Structuring, High Velocity, Rapid Cash-Out, Unusual Amount, Near-Threshold Proximity, Excessive Cross-Border, and Round Amounts.
- **ML Anomaly Detector**: Isolation Forest model computing normalized 0.0-1.0 anomaly scores with fallback logic for small datasets or missing libraries.

### 4. Risk & Explanation Engine (`src/risk.py`, `src/explanations.py`, `src/recommendations.py`)
- Computes transparent 0-100 composite risk scores.
- Assigns Low (0-39), Medium (40-69), High (70-100) risk tiers.
- Formulates objective compliance explanations using empirical data (no speculation or unsupported claims).
- Maps risk scores and pattern severity to actionable regulatory escalation recommendations (e.g. SAR/STR filing assessment).
