import re
import os
import json
import time
import urllib.request
import urllib.error

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    from google import genai
    from google.genai import types
    HAS_GENAI_SDK = True
except ImportError:
    HAS_GENAI_SDK = False

# Centralized Default Gemini Model Configuration
DEFAULT_GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite"
)

PLACEHOLDER_KEYS = [
    "PASTE_REAL_GEMINI_KEY_HERE",
    "your_gemini_api_key_here",
    "your_anthropic_api_key_here",
    "your_openai_api_key_here",
    "your_llm_api_key_here"
]

class AMLIntentParser:
    """
    Hybrid Natural Language Intent Parser for AML Queries.
    Supports Google Gemini, Anthropic Claude & OpenAI LLMs with safe deterministic fallback.
    Exposes transparent, sanitized diagnostics and routing reasons without exposing secrets.
    """
    def __init__(self):
        self.gemini_model = self.resolve_gemini_model()
        self.last_diagnostics = {
            "provider": "Deterministic Engine",
            "api_key_configured": False,
            "key_source": "unavailable",
            "requested_model": self.gemini_model,
            "selected_model": self.gemini_model,
            "http_error": None,
            "model_name": self.gemini_model,
            "active_engine": "Rule-Based Fallback",
            "request_status": "No Key Configured",
            "response_parse_status": "N/A",
            "fallback_used": True,
            "routing_reason": "Default Rule Engine Routing",
            "execution_time_ms": 0.0,
            "sanitized_error": "Configuration Error: GEMINI_API_KEY was not found."
        }

    def resolve_gemini_model(self) -> str:
        """
        Centralized single source of truth for resolving the configured Gemini model.
        Precedence:
        1. Streamlit session state (if available)
        2. Streamlit secrets (`GEMINI_MODEL` or `gemini_model`)
        3. Environment variable `GEMINI_MODEL`
        4. Central default (`DEFAULT_GEMINI_MODEL`)
        """
        try:
            import streamlit as st
            if "gemini_model" in st.session_state and st.session_state["gemini_model"]:
                return str(st.session_state["gemini_model"]).strip()
            if "GEMINI_MODEL" in st.session_state and st.session_state["GEMINI_MODEL"]:
                return str(st.session_state["GEMINI_MODEL"]).strip()
            if hasattr(st, "secrets"):
                if "GEMINI_MODEL" in st.secrets and st.secrets["GEMINI_MODEL"]:
                    return str(st.secrets["GEMINI_MODEL"]).strip()
                if "gemini_model" in st.secrets and st.secrets["gemini_model"]:
                    return str(st.secrets["gemini_model"]).strip()
        except Exception:
            pass

        env_val = os.getenv("GEMINI_MODEL", "").strip()
        if env_val:
            return env_val

        return DEFAULT_GEMINI_MODEL

    def parse(self, query: str) -> dict:
        t0 = time.time()
        self.gemini_model = self.resolve_gemini_model()
        
        # 1. Resolve API Key & Key Source (Streamlit secrets first, then os.environ / .env)
        api_key = None
        key_source = "unavailable"
        provider_name = "gemini"
        
        try:
            import streamlit as st
            if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"]:
                val = str(st.secrets["GEMINI_API_KEY"]).strip()
                if val and val not in PLACEHOLDER_KEYS and not val.startswith("PASTE_") and not val.startswith("your_"):
                    api_key = val
                    key_source = "Streamlit secrets"
                    provider_name = "gemini"
            elif "GOOGLE_API_KEY" in st.secrets and st.secrets["GOOGLE_API_KEY"]:
                val = str(st.secrets["GOOGLE_API_KEY"]).strip()
                if val and val not in PLACEHOLDER_KEYS and not val.startswith("PASTE_") and not val.startswith("your_"):
                    api_key = val
                    key_source = "Streamlit secrets"
                    provider_name = "gemini"
            elif "ANTHROPIC_API_KEY" in st.secrets and st.secrets["ANTHROPIC_API_KEY"]:
                val = str(st.secrets["ANTHROPIC_API_KEY"]).strip()
                if val and val not in PLACEHOLDER_KEYS and not val.startswith("PASTE_") and not val.startswith("your_"):
                    api_key = val
                    key_source = "Streamlit secrets"
                    provider_name = "anthropic"
            elif "OPENAI_API_KEY" in st.secrets and st.secrets["OPENAI_API_KEY"]:
                val = str(st.secrets["OPENAI_API_KEY"]).strip()
                if val and val not in PLACEHOLDER_KEYS and not val.startswith("PASTE_") and not val.startswith("your_"):
                    api_key = val
                    key_source = "Streamlit secrets"
                    provider_name = "openai"
        except Exception:
            pass
            
        if not api_key:
            for env_var, p_name in [("GEMINI_API_KEY", "gemini"), ("GOOGLE_API_KEY", "gemini"), ("ANTHROPIC_API_KEY", "anthropic"), ("OPENAI_API_KEY", "openai")]:
                val = os.getenv(env_var, "").strip()
                if val and val not in PLACEHOLDER_KEYS and not val.startswith("PASTE_") and not val.startswith("your_"):
                    api_key = val
                    key_source = "Environment / .env"
                    provider_name = p_name
                    break
                
        provider_setting = os.getenv("LLM_PROVIDER", provider_name).lower()

        # 2. Check if LLM call should be made
        if api_key or provider_setting == "mock":
            try:
                ai_extracted = self._parse_with_ai(query, api_key, provider_setting, key_source, t0)
                if ai_extracted:
                    engine_label = f"LLM-Based ({self._get_provider_label(provider_setting)})"
                    ai_extracted["intent_engine"] = engine_label
                    ai_extracted["diagnostics"] = self.last_diagnostics
                    self._apply_policy_semantics(ai_extracted)
                    self._clean_redundant_fields(ai_extracted)
                    return ai_extracted
            except Exception as e:
                latency = round((time.time() - t0) * 1000, 1)
                err_text, sanitized_err = self._classify_error(e, self.gemini_model)

                self.last_diagnostics = {
                    "provider": "Google Gemini" if provider_setting in ["gemini", "auto", "mock"] else "LLM Service",
                    "api_key_configured": True if api_key else False,
                    "key_source": key_source,
                    "requested_model": self.gemini_model,
                    "selected_model": self.gemini_model,
                    "model_name": self.gemini_model,
                    "active_engine": "Rule-Based Fallback",
                    "request_status": "Failed",
                    "response_parse_status": "Failed" if "Parse" not in sanitized_err else "Response Parse Error",
                    "fallback_used": True,
                    "http_error": err_text,
                    "routing_reason": "LLM Service Exception — Fallback Activated",
                    "execution_time_ms": latency,
                    "sanitized_error": sanitized_err
                }
        else:
            self.last_diagnostics = {
                "provider": "Deterministic Engine",
                "api_key_configured": False,
                "key_source": "unavailable",
                "requested_model": self.gemini_model,
                "selected_model": self.gemini_model,
                "model_name": self.gemini_model,
                "active_engine": "Rule-Based Fallback",
                "request_status": "No Key Configured",
                "response_parse_status": "N/A",
                "fallback_used": True,
                "http_error": "No API Key Configured",
                "routing_reason": "No API Key Configured in Environment, .env, or Streamlit Secrets",
                "execution_time_ms": round((time.time() - t0) * 1000, 1),
                "sanitized_error": "Configuration Error: GEMINI_API_KEY was not found."
            }

        extracted = self._parse_deterministic(query)
        extracted["intent_engine"] = "Rule-Based Fallback"
        extracted["diagnostics"] = self.last_diagnostics
        self._apply_policy_semantics(extracted)
        self._clean_redundant_fields(extracted)
        return extracted

    def _classify_error(self, e: Exception, requested_model: str) -> tuple:
        err_str = str(e)
        err_type = type(e).__name__

        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower() or "rate" in err_str.lower():
            sanitized = "Quota Error: Gemini API rate limit or quota exceeded."
        elif "401" in err_str or "403" in err_str or "API_KEY_INVALID" in err_str or "unauthorized" in err_str.lower() or "auth" in err_str.lower():
            sanitized = "Authentication Error: The Gemini API rejected the configured credentials."
        elif "404" in err_str or "NOT_FOUND" in err_str:
            sanitized = f"Model Configuration Error: The model '{requested_model}' is unavailable or unsupported."
        elif "JSON" in err_str or "json" in err_str or "Parse" in err_str or "JSONDecodeError" in err_type:
            sanitized = "Response Parse Error: Failed to parse structured JSON from Gemini output."
        elif "ConnectError" in err_type or "getaddrinfo" in err_str or "Connection" in err_type or "timeout" in err_str.lower():
            sanitized = "Network Error: Unable to connect to Gemini API endpoint."
        else:
            sanitized = f"API Error: {err_type} during Gemini execution."

        return err_str, sanitized

    def _get_provider_label(self, provider_setting: str) -> str:
        if provider_setting in ["gemini", "auto", "mock"]:
            return "Gemini"
        elif provider_setting == "anthropic":
            return "Claude"
        elif provider_setting == "openai":
            return "OpenAI"
        return "Gemini"

    def _parse_with_ai(self, query: str, api_key: str, provider_setting: str, key_source: str, t0: float) -> dict:
        """
        Invokes LLM for structured intent parsing. Supports Gemini, Anthropic, OpenAI, or Mock.
        """
        if provider_setting == "mock" or os.getenv("MOCK_LLM_RESPONSE") == "true":
            latency = round((time.time() - t0) * 1000, 1)
            self.last_diagnostics = {
                "provider": "Google Gemini (Mock)",
                "api_key_configured": True,
                "key_source": "mock_configuration",
                "requested_model": self.gemini_model,
                "selected_model": self.gemini_model,
                "model_name": self.gemini_model,
                "active_engine": "Google Gemini",
                "request_status": "Success",
                "response_parse_status": "Success",
                "fallback_used": False,
                "http_error": None,
                "routing_reason": f"Natural Language Query Processed via Gemini Model ({self.gemini_model})",
                "execution_time_ms": latency,
                "sanitized_error": None
            }
            parsed = self._parse_deterministic(query)
            parsed["ai_confidence"] = 0.98
            return parsed

        if provider_setting == "anthropic" or os.getenv("ANTHROPIC_API_KEY"):
            return self._call_anthropic_api(query, api_key, key_source, t0)
        elif provider_setting == "openai" or os.getenv("OPENAI_API_KEY"):
            return self._call_openai_api(query, api_key, key_source, t0)
            
        # Default to Google Gemini API
        return self._call_gemini_api(query, api_key, key_source, t0)

    def _call_gemini_api(self, query: str, api_key: str, key_source: str, t0: float) -> dict:
        requested_model = self.resolve_gemini_model()
        self.gemini_model = requested_model
        prompt = self._build_prompt(query)
        
        # 1. Attempt single SDK request if HAS_GENAI_SDK
        if HAS_GENAI_SDK:
            client = genai.Client(api_key=api_key)
            
            # Optional diagnostic check for models listing
            try:
                raw_models = list(client.models.list())
            except Exception:
                pass
                
            response = client.models.generate_content(
                model=requested_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type="application/json"
                )
            )
            text_content = response.text
            if not text_content:
                raise ValueError("Empty response text returned from Gemini API")
                
            try:
                parsed_json = self._extract_json_from_text(text_content)
            except Exception as e_json:
                raise ValueError(f"Response Parse Error: {str(e_json)}")
                
            latency = round((time.time() - t0) * 1000, 1)
            
            self.last_diagnostics = {
                "provider": "Google Gemini",
                "api_key_configured": True,
                "key_source": key_source,
                "requested_model": requested_model,
                "selected_model": requested_model,
                "model_name": requested_model,
                "active_engine": "Google Gemini",
                "request_status": "Success",
                "response_parse_status": "Success",
                "fallback_used": False,
                "http_error": None,
                "routing_reason": f"Natural Language Query Processed via Google Gemini Engine ({requested_model})",
                "execution_time_ms": latency,
                "sanitized_error": None
            }
            parsed_json["query"] = query
            return parsed_json

        # 2. Single HTTP REST API request if SDK unavailable
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{requested_model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json"
            }
        }
        
        req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=6) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            text_content = res_data["candidates"][0]["content"]["parts"][0]["text"]
            try:
                parsed_json = self._extract_json_from_text(text_content)
            except Exception as e_json:
                raise ValueError(f"Response Parse Error: {str(e_json)}")
            
            latency = round((time.time() - t0) * 1000, 1)
            self.last_diagnostics = {
                "provider": "Google Gemini",
                "api_key_configured": True,
                "key_source": key_source,
                "requested_model": requested_model,
                "selected_model": requested_model,
                "model_name": requested_model,
                "active_engine": "Google Gemini",
                "request_status": "Success",
                "response_parse_status": "Success",
                "fallback_used": False,
                "http_error": None,
                "routing_reason": f"Natural Language Query Processed via Google Gemini HTTP Engine ({requested_model})",
                "execution_time_ms": latency,
                "sanitized_error": None
            }
            parsed_json["query"] = query
            return parsed_json

    def _call_anthropic_api(self, query: str, api_key: str, key_source: str, t0: float) -> dict:
        prompt = self._build_prompt(query)
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        body = {
            "model": "claude-3-5-haiku-20241022",
            "max_tokens": 450,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=6) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            text_content = res_data["content"][0]["text"]
            parsed_json = self._extract_json_from_text(text_content)
            
            latency = round((time.time() - t0) * 1000, 1)
            self.last_diagnostics = {
                "provider": "Anthropic Claude",
                "api_key_configured": True,
                "key_source": key_source,
                "model_name": "claude-3-5-haiku-20241022",
                "active_engine": "LLM-Based (Claude)",
                "request_status": "Success",
                "response_parse_status": "Success",
                "fallback_used": False,
                "http_error": None,
                "routing_reason": "Natural Language Query Processed via Claude Engine",
                "execution_time_ms": latency,
                "sanitized_error": None
            }
            parsed_json["query"] = query
            return parsed_json

    def _call_openai_api(self, query: str, api_key: str, key_source: str, t0: float) -> dict:
        prompt = self._build_prompt(query)
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        body = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "response_format": {"type": "json_object"}
        }
        
        req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=6) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            text_content = res_data["choices"][0]["message"]["content"]
            parsed_json = json.loads(text_content)
            
            latency = round((time.time() - t0) * 1000, 1)
            self.last_diagnostics = {
                "provider": "OpenAI GPT",
                "api_key_configured": True,
                "key_source": key_source,
                "model_name": "gpt-4o-mini",
                "active_engine": "LLM-Based (OpenAI)",
                "request_status": "Success",
                "response_parse_status": "Success",
                "fallback_used": False,
                "http_error": None,
                "routing_reason": "Natural Language Query Processed via OpenAI GPT Engine",
                "execution_time_ms": latency,
                "sanitized_error": None
            }
            parsed_json["query"] = query
            return parsed_json

    def _build_prompt(self, query: str) -> str:
        return f"""You are an expert AML intent parser. Analyze the analyst query and return ONLY a valid JSON object matching this schema:
{{
  "intent": "single_customer_investigation" | "structuring_search" | "velocity_investigation" | "smurfing_search" | "segment_investigation" | "country_investigation" | "threshold_count_search" | "high_risk_ranking" | "broad_analysis" | "explanation_request" | "recommendation_request",
  "target_pattern": "structuring" | "high_velocity" | "rapid_cash_out" | "smurfing" | "unusual_amount" | null,
  "customer_id": "C0012" | null,
  "last_n_days": 30 | null,
  "country": "US" | "KY" | "AE" | "PA" | null,
  "amount_threshold": 10000.0 | null,
  "amount_condition": "below" | "above" | null,
  "min_tx_count": 10 | null,
  "segment": "Retail" | "SME" | "Corporate" | "Business" | "High Net Worth" | "Government" | "NGO" | null,
  "risk_category": "High" | "Medium" | "Low" | null,
  "detailed_explanation_requested": true | false,
  "explicit_recommendation_requested": true | false
}}
Query: "{query}"
JSON:"""

    def _extract_json_from_text(self, text: str) -> dict:
        """
        Safely extracts JSON from raw text or code-fence-wrapped markdown blocks.
        """
        code_fence_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if code_fence_match:
            return json.loads(code_fence_match.group(1))
            
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
            
        return json.loads(text)

    def _apply_policy_semantics(self, parsed: dict):
        """
        Applies clean, non-redundant explanation and recommendation policy semantics.
        """
        detailed_exp = parsed.pop("requires_explanation", None)
        if detailed_exp is None:
            detailed_exp = parsed.pop("detailed_explanation_requested", False)
            
        explicit_rec = parsed.pop("requires_recommendation", None)
        if explicit_rec is None:
            explicit_rec = parsed.pop("explicit_recommendation_requested", False)

        parsed["explanation_policy"] = {
            "basic_explanation_enabled": True,
            "detailed_explanation_requested": bool(detailed_exp)
        }
        parsed["recommendation_policy"] = {
            "default_recommendation_enabled": True,
            "explicit_recommendation_requested": bool(explicit_rec)
        }

    def _clean_redundant_fields(self, parsed: dict):
        """
        Removes any leftover top-level redundant flags to ensure clean output schema.
        """
        parsed.pop("requires_explanation", None)
        parsed.pop("requires_recommendation", None)

    def _parse_deterministic(self, query: str) -> dict:
        """
        High-precision deterministic regex & keyword parser.
        """
        q_lower = query.strip().lower()
        
        extracted = {
            "query": query,
            "intent": "broad_analysis",
            "target_pattern": None,
            "customer_id": None,
            "last_n_days": None,
            "country": None,
            "amount_threshold": None,
            "amount_condition": None,
            "min_tx_count": None,
            "segment": None,
            "risk_category": None,
            "detailed_explanation_requested": False,
            "explicit_recommendation_requested": False
        }
        
        # 1. Customer ID
        cust_match = re.search(r'\b(c\d{3,5})\b', q_lower)
        if cust_match:
            extracted["customer_id"] = cust_match.group(1).upper()
        else:
            cust_num_match = re.search(r'customer\s*(?:id)?\s*#?\s*(c?\d+)', q_lower)
            if cust_num_match:
                val = cust_num_match.group(1).upper()
                if not val.startswith("C"):
                    val = f"C{int(val):04d}"
                extracted["customer_id"] = val

        # 2. Date / Days Range
        days_match = re.search(r'last\s*(\d+)\s*days?', q_lower) or re.search(r'past\s*(\d+)\s*days?', q_lower)
        if days_match:
            extracted["last_n_days"] = int(days_match.group(1))
        elif "past month" in q_lower or "last month" in q_lower or "30 days" in q_lower or "recent" in q_lower:
            extracted["last_n_days"] = 30
        elif "past week" in q_lower or "last week" in q_lower or "7 days" in q_lower:
            extracted["last_n_days"] = 7

        # 3. Country / Jurisdiction
        country_map = {
            "us": "US", "usa": "US", "united states": "US",
            "uk": "GB", "gb": "GB", "united kingdom": "GB",
            "germany": "DE", "de": "DE",
            "singapore": "SG", "sg": "SG",
            "hong kong": "HK", "hk": "HK",
            "uae": "AE", "dubai": "AE", "ae": "AE",
            "cyprus": "CY", "cy": "CY",
            "cayman": "KY", "ky": "KY",
            "panama": "PA", "pa": "PA",
            "switzerland": "CH", "ch": "CH"
        }
        for kw, code in country_map.items():
            if re.search(rf'\b{kw}\b', q_lower):
                extracted["country"] = code
                break

        # 4. Customer Segment
        segment_map = {
            "retail": "Retail",
            "sme": "SME",
            "corporate": "Corporate",
            "business": "Business",
            "high net worth": "High Net Worth",
            "high-net-worth": "High Net Worth",
            "hnw": "High Net Worth",
            "government": "Government",
            "ngo": "NGO"
        }
        for kw, seg in segment_map.items():
            if re.search(rf'\b{kw}\b', q_lower):
                extracted["segment"] = seg
                break

        # 5. Amount & Thresholds
        amt_match = re.search(r'(below|under|less than|<|above|over|more than|>)\s*\$?([0-9,]+)', q_lower)
        if amt_match:
            cond_str = amt_match.group(1)
            extracted["amount_condition"] = "below" if cond_str in ["below", "under", "less than", "<"] else "above"
            extracted["amount_threshold"] = float(amt_match.group(2).replace(",", ""))
            
        # 6. Minimum Count
        cnt_match = re.search(r'(\d+)\s*(?:or more|at least|\+)?\s*transactions', q_lower) or re.search(r'(\d+)\s*or more', q_lower)
        if cnt_match:
            extracted["min_tx_count"] = int(cnt_match.group(1))

        # 7. Risk Category
        if "high risk" in q_lower or "high-risk" in q_lower:
            extracted["risk_category"] = "High"
        elif "medium risk" in q_lower or "medium-risk" in q_lower:
            extracted["risk_category"] = "Medium"

        # 8. Explanation / Recommendation Flags
        if "why" in q_lower or "explain" in q_lower or "reason" in q_lower or "evidence" in q_lower:
            extracted["detailed_explanation_requested"] = True
        if "action" in q_lower or "recommend" in q_lower or "what should be done" in q_lower or "escalat" in q_lower or "sar" in q_lower:
            extracted["explicit_recommendation_requested"] = True

        # 9. Intent Determination
        if extracted["customer_id"]:
            extracted["intent"] = "single_customer_investigation"
            if extracted["detailed_explanation_requested"]:
                extracted["intent"] = "explanation_request"
            elif extracted["explicit_recommendation_requested"]:
                extracted["intent"] = "recommendation_request"
        elif "structuring" in q_lower or "near threshold" in q_lower or "just below" in q_lower or "split" in q_lower:
            extracted["intent"] = "structuring_search"
            extracted["target_pattern"] = "structuring"
        elif "smurf" in q_lower or "coordinated" in q_lower:
            extracted["intent"] = "smurfing_search"
            extracted["target_pattern"] = "smurfing"
        elif re.search(r'moved|rapid|fast|quick|velocity|cash-out', q_lower):
            extracted["intent"] = "velocity_investigation"
            extracted["target_pattern"] = "high_velocity"
        elif extracted["amount_threshold"] is not None or extracted["min_tx_count"] is not None:
            extracted["intent"] = "threshold_count_search"
        elif "high risk" in q_lower or "show suspicious customer" in q_lower or "sar" in q_lower:
            extracted["intent"] = "high_risk_ranking"
        elif extracted["country"] is not None:
            extracted["intent"] = "country_investigation"
        elif extracted["segment"] is not None:
            extracted["intent"] = "segment_investigation"
        elif "analyse" in q_lower or "complete dataset" in q_lower or "full analysis" in q_lower or re.search(r'\ball\b', q_lower):
            extracted["intent"] = "broad_analysis"
            
        return extracted
