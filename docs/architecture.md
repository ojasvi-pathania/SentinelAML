# SentinelAML Architecture Documentation

## Overview

SentinelAML is an agentic Anti-Money Laundering (AML) investigation platform. It provides dynamic query planning, rule-based pattern detection, machine-learning anomaly scoring, evidence-backed natural language explanations, and regulatory escalation guidance.

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     USER INTERFACE                      │
│                  (Streamlit Multi-Tab)                  │
└────────────────────────────┬────────────────────────────┘
                             │ Natural Language Query
                             ▼
┌─────────────────────────────────────────────────────────┐
│                    INTENT PARSER                        │
│          - Regex & Keyword Entity Extractor             │
└────────────────────────────┬────────────────────────────┘
                             │ Parsed Intent & Filters
                             ▼
┌─────────────────────────────────────────────────────────┐
│                   DYNAMIC PLANNER                       │
│    - Evaluates query goal                               │
│    - Selects tool chain & skips unnecessary modules     │
└────────────────────────────┬────────────────────────────┘
                             │ Tool Execution Chain
                             ▼
┌─────────────────────────────────────────────────────────┐
│                 ANALYTICAL TOOL SUITE                   │
│   ┌─────────────────────┬───────────────────────────┐   │
│   │ Data Ingestion      │ Filtering & Validation    │   │
│   ├─────────────────────┼───────────────────────────┤   │
│   │ Feature Engineering │ Rule Detectors            │   │
│   ├─────────────────────┼───────────────────────────┤   │
│   │ Isolation Forest    │ Risk Scoring Engine       │   │
│   └─────────────────────┴───────────────────────────┘   │
└────────────────────────────┬────────────────────────────┘
                             │ Risk Scores & Flagged Txs
                             ▼
┌─────────────────────────────────────────────────────────┐
│                EXPLANATION & ESCALATION                 │
│   - Factual natural language summary                     │
│   - Actionable escalation recommendation (SAR/EDD/Review)│
└─────────────────────────────────────────────────────────┘
```

## Modular Components

1. **Synthetic Data Generator** (`src/data_generator.py`): Injects realistic customer baselines and labelled suspicious scenarios (Structuring, Smurfing, Velocity, Rapid Cash-Out, Unusual Amount).
2. **Column Mapper & Ingestion** (`src/data_loader.py`): Flexible schema parser mapping variant column names.
3. **Data Quality Validator** (`src/validation.py`): Non-crashing validation checks for missing values, invalid amounts, timestamp syntax, and duplicate IDs.
4. **Feature Engineering Engine** (`src/features.py`): Computes rolling transaction frequency, near-threshold ratios, time deltas between incoming and outgoing funds, and cross-border statistics.
5. **Rule Detection Suite** (`src/rules.py`): Deterministic explainable AML pattern rules.
6. **ML Anomaly Detector** (`src/anomaly.py`): Isolation Forest unsupervised model with robust fallback handling.
7. **Risk Scoring Engine** (`src/risk.py`): Weighted signal composite 0-100 score mapped to Low, Medium, and High risk tiers.
8. **Explanation Engine** (`src/explanations.py`): Natural language synthesis referencing specific amounts, timestamps, and transaction IDs.
9. **Recommendation Engine** (`src/recommendations.py`): Proportional escalation matrix (Monitor, Flag for Analyst Review, Compliance Review, SAR/STR filing assessment).
10. **Report Exporters** (`src/reports.py`): Generates downloadable CSV exports, HTML case reports, and JSON execution plan logs.
