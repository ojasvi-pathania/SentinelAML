# SentinelAML — 2-Minute Demonstration Script

**Target Duration**: 120 Seconds  
**Demonstrator Role**: Lead AML AI Architect

---

### [0:00 - 0:15] 1. Opening Problem Statement
> *"Traditional AML compliance software forces investigators through static, one-size-fits-all dashboards that run the exact same slow pipeline regardless of what question you're trying to answer. Today we present **SentinelAML** — a query-aware AML investigation agent that dynamically plans and executes tailored analysis based on the analyst's specific question."*

---

### [0:15 - 0:30] 2. Dataset Overview
> *"We start here on the main dashboard. SentinelAML immediately initializes with a realistic synthetic banking dataset containing over 160 customers and 4,200 multi-channel transactions. It also seamlessly accepts custom CSV uploads with automatic column mapping."*

---

### [0:30 - 0:50] 3. Targeted Query & Dynamic Execution Plan
> *"Let's ask our first natural language question: **'Find structuring patterns in the last 30 days.'**"*
>
> *(Click the pre-set button or type query)*
>
> *"Notice the **Agent Execution Plan** panel! The agent correctly recognized the structuring intent and date filter. It selected the structuring detector, risk scoring, and explanation tools — while **optimizing out and skipping** full dataset EDA and ML anomaly detection. This dynamic planning slashes investigation latency."*

---

### [0:50 - 1:15] 4. Customer Investigation & Evidence Breakdown
> *"Looking at the results, Customer **C0001** scored a High Risk score of 88/100. Let's switch to **Tab 3: Customer Investigation** to drill down."*
>
> *"Here we see the composite risk gauge, timeline, and exact empirical evidence: 'Customer executed 14 cash deposits between $9,000 and $9,999 within 4 days, immediately below the $10,000 reporting threshold.'"*
>
> *"SentinelAML automatically provides an actionable recommendation: **'Consider Regulatory Reporting Assessment (SAR / STR)'** along with concrete next steps."*

---

### [1:15 - 1:40] 5. Proving Query-Aware Plan Shift
> *"Now let's ask a completely different targeted query to prove the agent adapts: **'Which customers made 10 or more transactions below 10,000?'**"*
>
> *"Notice how the plan dynamically shifted! The agent skipped pattern rule detectors and executed an aggregation and count filtering tool chain instead, returning exactly the matching subset of customers."*

---

### [1:40 - 2:00] 6. Closing & Main Differentiator
> *"In summary, SentinelAML transforms AML investigations from static dashboards into explainable, dynamic, query-aware AI workflows — providing transparent evidence, risk scores, and regulatory escalation guidance out-of-the-box without requiring third-party API keys."*
>
> *"Thank you!"*
