import pytest
import os
from unittest.mock import patch
from src.intent_parser import AMLIntentParser

def test_intent_parser_fallback_without_key():
    # Clear env vars for test isolation
    os.environ.pop("GEMINI_API_KEY", None)
    os.environ.pop("GOOGLE_API_KEY", None)
    os.environ.pop("ANTHROPIC_API_KEY", None)
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("LLM_API_KEY", None)
    os.environ["LLM_PROVIDER"] = "auto"
    
    # Mock empty streamlit secrets to simulate missing key
    with patch("streamlit.secrets", {}):
        parser = AMLIntentParser()
        res = parser.parse("Find structuring patterns in the last 30 days.")
        
        assert res["intent"] == "structuring_search"
        assert res["intent_engine"] == "Rule-Based Fallback"
        assert res["diagnostics"]["active_engine"] == "Rule-Based Fallback"
        assert res["diagnostics"]["fallback_used"] is True
        assert res["diagnostics"]["requested_model"] == "gemini-3.5-flash-lite"
        assert "Configuration Error" in res["diagnostics"]["sanitized_error"]

def test_intent_parser_mock_gemini():
    os.environ["LLM_PROVIDER"] = "mock"
    parser = AMLIntentParser()
    res = parser.parse("Should we escalate C0012, and what evidence supports that decision?")
    
    assert res["intent_engine"] == "LLM-Based (Gemini)"
    assert res["customer_id"] == "C0012"
    assert res["explanation_policy"]["detailed_explanation_requested"] is True
    assert res["recommendation_policy"]["explicit_recommendation_requested"] is True
    assert res["diagnostics"]["requested_model"] == "gemini-3.5-flash-lite"
    assert res["diagnostics"]["fallback_used"] is False
    os.environ["LLM_PROVIDER"] = "auto"

def test_code_fence_json_extraction():
    parser = AMLIntentParser()
    raw_text = "```json\n{\"intent\": \"velocity_investigation\", \"segment\": \"Corporate\"}\n```"
    extracted = parser._extract_json_from_text(raw_text)
    assert extracted["intent"] == "velocity_investigation"
    assert extracted["segment"] == "Corporate"

def test_complex_query_1_structuring():
    with patch("streamlit.secrets", {}):
        parser = AMLIntentParser()
        res = parser.parse("Find structuring patterns in the last 30 days.")
        assert res["intent"] == "structuring_search"
        assert res["last_n_days"] == 30

def test_complex_query_2_indirect_rapid_cash_out():
    with patch("streamlit.secrets", {}):
        parser = AMLIntentParser()
        res = parser.parse("Show me customers who moved money out really fast after receiving it.")
        assert res["intent"] == "velocity_investigation"

def test_complex_query_3_multisegment_velocity():
    with patch("streamlit.secrets", {}):
        parser = AMLIntentParser()
        res = parser.parse("Among business and high-net-worth customers, identify accounts that received funds and then moved most of the money out unusually quickly, and explain which cases need escalation.")
        assert res["intent"] == "velocity_investigation"
        assert res["segment"] in ["Business", "High Net Worth"]
        assert res["explanation_policy"]["detailed_explanation_requested"] is True
        assert res["recommendation_policy"]["explicit_recommendation_requested"] is True

def test_complex_query_4_customer_escalation():
    with patch("streamlit.secrets", {}):
        parser = AMLIntentParser()
        res = parser.parse("Should customer C0012 be escalated, and what evidence supports that decision?")
        assert res["customer_id"] == "C0012"
        assert res["explanation_policy"]["detailed_explanation_requested"] is True
        assert res["recommendation_policy"]["explicit_recommendation_requested"] is True
