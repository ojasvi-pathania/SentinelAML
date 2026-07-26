# SentinelAML — Hackathon Presentation Content

---

## Slide 1: Product Overview & Value Proposition

### 1. Problem Statement
Traditional Anti-Money Laundering (AML) software relies on static, rigid data processing pipelines. Analysts waste significant time manually navigating fixed dashboards that run identical expensive computations regardless of whether the analyst is asking for a single customer lookup or a broad pattern search.

### 2. Proposed Solution
**SentinelAML** is an institutional AI-powered, query-aware AML investigation platform. It accepts natural-language questions about transaction data, dynamically interprets analyst intent, builds a query-specific tool execution plan, runs only required tools, and presents evidence-backed risk scores and escalation guidance.

### 3. Core User Workflow
1. **Natural Language Query**: Analyst inputs a targeted query (e.g. *"Is customer C0012 suspicious?"* or *"Analyse suspicious retail accounts"*).
2. **Hybrid Intent Engine**: Claude LLM Model (when API key is present) or Rule-Based Fallback extracts intent, entity parameters, and customer segment.
3. **Dynamic Tool Planning**: Agent selects required analytical tools (including EDA) and skips redundant modules, logging clear selection/skip rationale.
4. **Targeted Execution**: System runs relevant feature extractors, rule engines, and unsupervised ML anomaly models.
5. **Evidence & Escalation**: Agent presents empirical evidence matrix, interactive timeline, composite risk score, and recommended regulatory action (e.g. SAR filing).

---

## Slide 2: Ground-Truth Evaluation

### 1. Synthetic Benchmark Performance Summary

| Operating Mode | High Risk Cutoff | Precision | Recall | F1-Score | Confusion Matrix (TP / FP / FN / TN) | Analyst Objective |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Precision First (Default)** | 70.0 | **100.0%** | **39.3%** | **56.4%** | 11 TP / 0 FP / 17 FN / 132 TN | Minimizes false positive alerts & analyst fatigue |
| **Balanced (F1 Optimal)** | 50.0 | **92.8%** | **85.7%** | **89.0%** | 24 TP / 2 FP / 4 FN / 130 TN | Optimizes F1-score for balanced monitoring |
| **Recall First (High Sensitivity)** | 40.0 | **86.7%** | **92.8%** | **89.6%** | 26 TP / 4 FP / 2 FN / 128 TN | Maximizes detection of suspicious accounts |

> **Design Statement**: *Thresholds are configurable to balance detection sensitivity against analyst alert fatigue.*

*Synthetic Dataset Disclaimer: Evaluated against 160 synthetic benchmark customer accounts (28 injected suspicious accounts). Demonstration metrics only; not representative of production banking data.*

---

### 2. Speaker Notes & Q&A Preparation

#### Q: "Why is recall not 100%?"
> **Recommended Speaker Answer**:
> "AML detection involves an inherent precision–recall trade-off. The current operating configuration is designed to avoid overwhelming analysts with low-quality alerts. SentinelAML allows thresholds to be adjusted so institutions can prioritize precision, balanced performance, or higher recall according to their compliance policy."
