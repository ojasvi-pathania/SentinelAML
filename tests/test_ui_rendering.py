import pytest
from app import render_html

def test_render_html_unindented():
    """
    Verifies that render_html helper strips all leading whitespace from multiline HTML string
    so Markdown never parses HTML elements as indented code blocks.
    """
    sample_raw = """
    <div class="plan-card">
        <div class="reason-box">Execution Rationale</div>
        <span class="tool-badge-executed">✓ data_ingestion_tool</span>
        <span class="tool-badge-skipped">⚡ anomaly_detector</span>
    </div>
    """
    clean_lines = [line.strip() for line in sample_raw.splitlines() if line.strip()]
    
    # Assert every line starts at column 0 with 0 leading spaces
    for line in clean_lines:
        assert not line.startswith(" "), f"Line starts with whitespace: '{line}'"
        assert not line.startswith("\t"), f"Line starts with tab: '{line}'"
        
    assert "<div class=\"reason-box\">Execution Rationale</div>" in clean_lines
    assert "<span class=\"tool-badge-executed\">✓ data_ingestion_tool</span>" in clean_lines
