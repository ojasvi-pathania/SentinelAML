# SentinelAML — Query-Aware Suspicious Activity Investigation Platform

> **SentinelAML** is an enterprise-grade AI-powered AML investigation platform that accepts natural-language analyst queries and dynamically plans which analytical tools to execute.

---

## Key Platform Capabilities

1. **Query-Aware Dynamic Planning**:
   - Eliminates rigid static pipelines. For every query, SentinelAML constructs an adaptive tool chain and skips redundant detectors.
   - Computes real-time **Planner Optimization Metrics** (e.g. `53.3% computation saved`, `18ms execution`).

2. **First-Class EDA Tool Orchestration**:
   - Exploratory Data Analysis (`eda_tool`) is an active tool in the planner registry. It is executed for broad/segment queries and skipped for single-account investigations with clear audit rationale.

3. **Hybrid Intent Engine with Automatic Fallback**:
   - Supports LLM AI intent extraction (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or `LLM_API_KEY`).
   - Automatically falls back to a deterministic regex/keyword parser if no API key is present or if offline.
   - UI explicitly badges the engine used (`✓ AI Model` or `✓ Rule-Based Fallback`).

4. **Customer Segmentation Support**:
   - Synthetic dataset includes customer segments: `Retail`, `SME`, `Corporate`, `Business`, `High Net Worth`, `Government`, `NGO`.
   - Analysts can filter queries by segment (e.g., *"Show suspicious retail accounts"*, *"Analyse corporate accounts with rapid cash-out"*).

5. **Explainable Rule Detectors & ML Anomaly Model**:
   - Deterministic rule detectors: Structuring, Velocity, Rapid Cash-Out, Smurfing, Unusual Amount.
   - Unsupervised Isolation Forest ML model for high-dimensional outlier scoring.

6. **Composite Risk Index & Evidence Synthesis**:
   - 0–100 risk score mapped to Low (0–39), Medium (40–69), and High (70–100) tiers.
   - Factual evidence summaries citing exact transaction IDs, dates, and amounts.

7. **Audit-Ready Reporting**:
   - Export enriched execution plan JSON detailing selection/skip rationale per tool.
   - Download HTML/PDF case compliance reports for individual accounts.

---

## 📁 Repository Structure

```text
C:\Users\Manish Pathania\.gemini\antigravity\scratch\SentinelAML\
├── app.py                      # Main Streamlit institutional application
├── README.md                   # Complete system documentation
├── AGENTS.md                   # Agentic architecture breakdown
├── src/                        # Core Python analytical engine
│   ├── agent.py                # SentinelAML orchestrator agent
│   ├── planner.py              # Query-aware dynamic execution planner & metrics
│   ├── intent_parser.py        # Hybrid AI & deterministic intent parser
│   ├── rules.py                # Explainable rule detectors (Structuring, Velocity, etc.)
│   ├── risk.py                 # Composite 0-100 risk scoring engine
│   ├── anomaly.py              # ML Isolation Forest anomaly detector
│   ├── features.py             # Feature engineering & aggregations
│   ├── data_generator.py       # Synthetic banking data generator with segments
│   ├── data_loader.py          # Flexible CSV ingestion & segment normalizer
│   ├── validation.py           # Data quality & schema validator
│   ├── visualizations.py       # FinTech Plotly chart definitions
│   ├── explanations.py        # Natural language evidence synthesizer
│   ├── recommendations.py     # Compliance escalation action engine
│   ├── evaluation.py          # Benchmark metrics calculator
│   └── reports.py              # CSV, JSON, and HTML report exporters
├── tests/                      # Automated unit test suite
│   ├── test_intent_parser.py
│   ├── test_planner.py
│   ├── test_risk.py
│   ├── test_rules.py
│   └── test_ui_rendering.py
└── docs/                       # Technical documentation & case studies
    ├── architecture.md
    ├── system_design.md
    ├── case_study.md
    ├── demo_script.md
    └── presentation_content.md
```

---

## Quickstart & Installation

```bash
# 1. Clone repository & install dependencies
pip install -r requirements.txt

# 2. Run automated test suite
pytest tests

# 3. Launch SentinelAML Streamlit application
streamlit run app.py
```

---

## Documentation Links

- **Technical System Design**: [docs/system_design.md](file:///C:/Users/Manish%20Pathania/.gemini/antigravity/scratch/SentinelAML/docs/system_design.md)
- **End-to-End Investigation Case Study**: [docs/case_study.md](file:///C:/Users/Manish%20Pathania/.gemini/antigravity/scratch/SentinelAML/docs/case_study.md)
- **Agent Architecture Breakdown**: [AGENTS.md](file:///C:/Users/Manish%20Pathania/.gemini/antigravity/scratch/SentinelAML/AGENTS.md)
- **Demo Script**: [docs/demo_script.md](file:///C:/Users/Manish%20Pathania/.gemini/antigravity/scratch/SentinelAML/docs/demo_script.md)
