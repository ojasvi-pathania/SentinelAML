class AMLDynamicPlanner:
    """
    Dynamic Execution Planner for AML Queries.
    Maps intent and filters into query-specific tool chains while skipping redundant tools.
    Provides detailed selection & skip rationale per tool and computes efficiency metrics.
    """
    ALL_AVAILABLE_TOOLS = [
        "data_ingestion_tool",
        "data_validation_tool",
        "filtering_tool",
        "eda_tool",
        "feature_engineering_tool",
        "structuring_detector_tool",
        "velocity_detector_tool",
        "rapid_cashout_detector_tool",
        "anomaly_detection_tool",
        "customer_lookup_tool",
        "risk_classification_tool",
        "explanation_tool",
        "recommendation_tool",
        "visualization_tool",
        "report_export_tool"
    ]

    DEFAULT_TOOL_DESCRIPTIONS = {
        "data_ingestion_tool": "Ingests raw transaction CSV data stream into memory.",
        "data_validation_tool": "Profiles schema completeness, duplicates, and invalid amounts.",
        "filtering_tool": "Filters dataset by date window, amount, jurisdiction, or segment.",
        "eda_tool": "Computes exploratory distributions for country, channel, and volume.",
        "feature_engineering_tool": "Computes rolling 24h count/sum, near-threshold ratios, and cash-out time deltas.",
        "structuring_detector_tool": "Evaluates near-threshold deposit frequency (e.g. $9,000–$9,999).",
        "velocity_detector_tool": "Evaluates high-frequency 24h burst activity.",
        "rapid_cashout_detector_tool": "Evaluates rapid pass-through deposit and immediate cash-out deltas.",
        "anomaly_detection_tool": "Runs unsupervised Isolation Forest ML model for high-dimensional outliers.",
        "customer_lookup_tool": "Isolates transactions and entity baseline for a single customer ID.",
        "risk_classification_tool": "Calculates composite 0-100 risk score (Low, Medium, High).",
        "explanation_tool": "Synthesizes factual natural language evidence citing exact dollar amounts.",
        "recommendation_tool": "Generates compliance escalation actions (SAR assessment, EDD review, L1 review).",
        "visualization_tool": "Renders interactive Plotly charts and risk gauges.",
        "report_export_tool": "Exports audit plan JSON and HTML compliance reports."
    }

    def create_plan(self, parsed_intent: dict) -> dict:
        intent = parsed_intent.get("intent", "broad_analysis")
        cust_id = parsed_intent.get("customer_id")
        country = parsed_intent.get("country")
        segment = parsed_intent.get("segment")
        
        selected_tools = ["data_ingestion_tool"]
        selected_tool_reasons = {
            "data_ingestion_tool": "Required to ingest raw transaction dataset for analysis."
        }
        skipped_tool_reasons = {}
        reasoning_steps = ["Ingest current dataset."]
        
        if intent == "structuring_search":
            selected_tools.extend([
                "filtering_tool",
                "eda_tool",
                "feature_engineering_tool",
                "structuring_detector_tool",
                "risk_classification_tool",
                "explanation_tool",
                "recommendation_tool"
            ])
            selected_tool_reasons["filtering_tool"] = "Filters dataset by specified date window or amount boundaries."
            selected_tool_reasons["eda_tool"] = "Performs EDA to profile structuring volume distributions."
            selected_tool_reasons["feature_engineering_tool"] = "Computes near-threshold deposit ratios and 24h window aggregations."
            selected_tool_reasons["structuring_detector_tool"] = "Runs deterministic structuring rule detector."
            selected_tool_reasons["risk_classification_tool"] = "Calculates composite risk score for accounts exhibiting structuring."
            selected_tool_reasons["explanation_tool"] = "Synthesizes evidence explaining structuring transactions."
            selected_tool_reasons["recommendation_tool"] = "Provides compliance escalation guidance for structuring alerts."
            
            reasoning_steps.append("Query specifically targets structuring patterns. Apply date/amount filters, compute near-threshold deposit features, run structuring detector, score risk, and generate evidence explanations. Skip generic velocity, rapid cashout, and ML anomaly models.")

        elif intent == "threshold_count_search":
            selected_tools.extend([
                "filtering_tool",
                "feature_engineering_tool",
                "risk_classification_tool",
                "explanation_tool"
            ])
            selected_tool_reasons["filtering_tool"] = "Filters dataset by transaction count and amount threshold."
            selected_tool_reasons["feature_engineering_tool"] = "Aggregates transaction counts and sums per customer account."
            selected_tool_reasons["risk_classification_tool"] = "Scores composite risk based on count threshold breaches."
            selected_tool_reasons["explanation_tool"] = "Generates factual summary of threshold breaches."
            
            reasoning_steps.append("Query asks for threshold/count aggregations. Filter dataset by amount and transaction count per customer, calculate basic risk score, and present explanation. Skip ML anomaly model and unrequested pattern detectors.")

        elif intent in ["single_customer_investigation", "explanation_request", "recommendation_request"]:
            selected_tools.extend([
                "customer_lookup_tool",
                "feature_engineering_tool",
                "structuring_detector_tool",
                "velocity_detector_tool",
                "rapid_cashout_detector_tool",
                "risk_classification_tool",
                "explanation_tool",
                "recommendation_tool"
            ])
            selected_tool_reasons["customer_lookup_tool"] = f"Isolates transaction history specifically for customer account {cust_id}."
            selected_tool_reasons["feature_engineering_tool"] = f"Computes entity behavioral features for {cust_id}."
            selected_tool_reasons["structuring_detector_tool"] = "Evaluates structuring patterns for target account."
            selected_tool_reasons["velocity_detector_tool"] = "Evaluates transaction velocity for target account."
            selected_tool_reasons["rapid_cashout_detector_tool"] = "Evaluates rapid cashout patterns for target account."
            selected_tool_reasons["risk_classification_tool"] = "Calculates composite risk score for target account."
            selected_tool_reasons["explanation_tool"] = "Provides empirical factual evidence for target account."
            selected_tool_reasons["recommendation_tool"] = "Provides compliance escalation guidance for target account."
            
            reasoning_steps.append(f"Targeted single-customer investigation for {cust_id}. Isolate customer transactions, compute customer-level baseline features, run all rule checks against this customer, calculate composite risk, and provide detailed explanation & escalation recommendation. Skip dataset-wide EDA.")

        elif intent == "velocity_investigation":
            selected_tools.extend([
                "filtering_tool",
                "eda_tool",
                "feature_engineering_tool",
                "velocity_detector_tool",
                "risk_classification_tool",
                "explanation_tool",
                "recommendation_tool"
            ])
            selected_tool_reasons["filtering_tool"] = "Filters transactions by date or channel."
            selected_tool_reasons["eda_tool"] = "Performs EDA to profile transaction frequency distributions."
            selected_tool_reasons["feature_engineering_tool"] = "Computes rolling 24h transaction counts and velocity metrics."
            selected_tool_reasons["velocity_detector_tool"] = "Executes high-velocity burst detector."
            selected_tool_reasons["risk_classification_tool"] = "Scores risk for accounts breaching velocity limits."
            selected_tool_reasons["explanation_tool"] = "Explains high-velocity burst transactions."
            selected_tool_reasons["recommendation_tool"] = "Provides escalation guidance for high-velocity alerts."
            
            reasoning_steps.append("Query targets high transaction velocity. Build rolling 24-hour transaction frequency features, execute velocity detector, score risk, and display explanation. Skip structuring and ML anomaly tools.")

        elif intent == "high_risk_ranking":
            selected_tools.extend([
                "feature_engineering_tool",
                "structuring_detector_tool",
                "velocity_detector_tool",
                "rapid_cashout_detector_tool",
                "anomaly_detection_tool",
                "risk_classification_tool",
                "explanation_tool"
            ])
            selected_tool_reasons["feature_engineering_tool"] = "Computes complete behavioral feature matrix for all accounts."
            selected_tool_reasons["structuring_detector_tool"] = "Evaluates structuring patterns across all accounts."
            selected_tool_reasons["velocity_detector_tool"] = "Evaluates velocity patterns across all accounts."
            selected_tool_reasons["rapid_cashout_detector_tool"] = "Evaluates rapid cashout patterns across all accounts."
            selected_tool_reasons["anomaly_detection_tool"] = "Runs Isolation Forest ML model to detect multivariate outliers."
            selected_tool_reasons["risk_classification_tool"] = "Calculates composite risk index for ranking."
            selected_tool_reasons["explanation_tool"] = "Synthesizes evidence explaining top risk scores."
            
            reasoning_steps.append("Query asks for top high-risk customers. Compute all behavioral features, run rule detectors & ML anomaly model, rank by risk score, and generate explanations. Skip preliminary EDA.")

        elif intent == "country_investigation":
            selected_tools.extend([
                "filtering_tool",
                "eda_tool",
                "feature_engineering_tool",
                "risk_classification_tool",
                "explanation_tool"
            ])
            selected_tool_reasons["filtering_tool"] = f"Isolates transactions originating from or terminating in jurisdiction {country}."
            selected_tool_reasons["eda_tool"] = f"Performs EDA on jurisdiction {country} activity."
            selected_tool_reasons["feature_engineering_tool"] = "Computes jurisdiction transaction metrics."
            selected_tool_reasons["risk_classification_tool"] = "Calculates risk for accounts operating in target jurisdiction."
            selected_tool_reasons["explanation_tool"] = "Synthesizes jurisdiction evidence."
            
            reasoning_steps.append(f"Query filters by jurisdiction ({country}). Isolate jurisdiction transactions, run rule checks, score customer risk within country, and show evidence. Skip global EDA.")

        elif intent == "segment_investigation":
            selected_tools.extend([
                "filtering_tool",
                "eda_tool",
                "feature_engineering_tool",
                "risk_classification_tool",
                "explanation_tool",
                "recommendation_tool"
            ])
            selected_tool_reasons["filtering_tool"] = f"Isolates accounts belonging to customer segment '{segment}'."
            selected_tool_reasons["eda_tool"] = f"Profiles exploratory distributions for segment '{segment}'."
            selected_tool_reasons["feature_engineering_tool"] = "Computes segment behavioral features."
            selected_tool_reasons["risk_classification_tool"] = "Calculates composite risk index for segment accounts."
            selected_tool_reasons["explanation_tool"] = f"Synthesizes evidence for segment '{segment}' accounts."
            selected_tool_reasons["recommendation_tool"] = "Provides compliance escalation guidance for segment alerts."
            
            reasoning_steps.append(f"Query targets customer segment '{segment}'. Isolate segment accounts, perform segment EDA, compute features, calculate composite risk, and present findings.")

        else: # broad_analysis
            selected_tools.extend([
                "data_validation_tool",
                "eda_tool",
                "feature_engineering_tool",
                "structuring_detector_tool",
                "velocity_detector_tool",
                "rapid_cashout_detector_tool",
                "anomaly_detection_tool",
                "risk_classification_tool",
                "explanation_tool",
                "recommendation_tool",
                "visualization_tool"
            ])
            selected_tool_reasons["data_validation_tool"] = "Profiles schema completeness, duplicates, and invalid values."
            selected_tool_reasons["eda_tool"] = "Computes exploratory distributions across all countries and transaction channels."
            selected_tool_reasons["feature_engineering_tool"] = "Computes complete behavioral feature matrix across all accounts."
            selected_tool_reasons["structuring_detector_tool"] = "Evaluates structuring patterns across all accounts."
            selected_tool_reasons["velocity_detector_tool"] = "Evaluates transaction velocity patterns."
            selected_tool_reasons["rapid_cashout_detector_tool"] = "Evaluates rapid cashout pass-through patterns."
            selected_tool_reasons["anomaly_detection_tool"] = "Runs Isolation Forest ML model for multivariate outlier detection."
            selected_tool_reasons["risk_classification_tool"] = "Calculates 0-100 composite risk scores across portfolio."
            selected_tool_reasons["explanation_tool"] = "Synthesizes factual natural language evidence explanations."
            selected_tool_reasons["recommendation_tool"] = "Generates compliance escalation guidance for all risk tiers."
            selected_tool_reasons["visualization_tool"] = "Renders interactive Plotly risk charts."
            
            reasoning_steps.append("Broad dataset investigation requested. Execute complete pipeline: validate data, perform full exploratory data analysis (EDA), engineer all features, run all rule detectors and ML anomaly model, calculate comprehensive risk scores, and build summary dashboards.")

        # Determine skipped tools and generate reasons
        skipped_tools = [t for t in self.ALL_AVAILABLE_TOOLS if t not in selected_tools]
        
        for t in skipped_tools:
            if t == "eda_tool":
                skipped_tool_reasons[t] = f"Skipped because this investigation targets a single customer account ({cust_id}) rather than dataset-wide distributions."
            elif t == "customer_lookup_tool":
                skipped_tool_reasons[t] = "Skipped because query does not specify a single target customer ID."
            elif t == "anomaly_detection_tool":
                skipped_tool_reasons[t] = "Skipped because query targets specific rule patterns rather than unsupervised multivariate ML anomalies."
            elif t == "structuring_detector_tool":
                skipped_tool_reasons[t] = "Skipped because query does not request structuring deposit analysis."
            elif t == "velocity_detector_tool":
                skipped_tool_reasons[t] = "Skipped because query does not request transaction velocity burst analysis."
            elif t == "rapid_cashout_detector_tool":
                skipped_tool_reasons[t] = "Skipped because query does not request rapid cashout pass-through analysis."
            elif t == "data_validation_tool":
                skipped_tool_reasons[t] = "Skipped preliminary schema profiling to optimize query latency."
            elif t == "filtering_tool":
                skipped_tool_reasons[t] = "Skipped dataset slicing because query evaluates the complete baseline dataset."
            elif t == "visualization_tool":
                skipped_tool_reasons[t] = "Skipped dashboard rendering for text/table focused query."
            elif t == "report_export_tool":
                skipped_tool_reasons[t] = "Skipped automated report generation until requested by analyst."
            else:
                skipped_tool_reasons[t] = "Optimized out as unnecessary for this query intent."

        exec_count = len(selected_tools)
        skip_count = len(skipped_tools)
        total_count = len(self.ALL_AVAILABLE_TOOLS)
        comp_saved_pct = round((skip_count / total_count) * 100, 1)

        return {
            "detected_intent": intent,
            "extracted_filters": {k: v for k, v in parsed_intent.items() if v is not None and k != "query"},
            "selected_tools": selected_tools,
            "execution_order": selected_tools,
            "selected_tool_reasons": selected_tool_reasons,
            "skipped_tools": skipped_tools,
            "skipped_tool_reasons": skipped_tool_reasons,
            "reason_for_plan": " ".join(reasoning_steps),
            "optimization_metrics": {
                "executed_tools_count": exec_count,
                "skipped_tools_count": skip_count,
                "total_available_tools": total_count,
                "computation_saved_percent": comp_saved_pct
            }
        }
