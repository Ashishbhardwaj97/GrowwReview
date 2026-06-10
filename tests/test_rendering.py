import pytest
from datetime import datetime
from src.rendering.docs_renderer import generate_docs_requests
from src.rendering.email_renderer import render_email_html, render_email_text, get_email_subject, generate_deep_link
from src.models.types import PulseReport, Theme

@pytest.fixture
def sample_report():
    theme = Theme(
        name="Performance",
        summary="App is slow",
        quotes=["It takes forever to load"],
        action_ideas=["Optimize loading"],
        cluster_id=1,
        size=10,
        avg_rating=2.0
    )
    return PulseReport(
        product="groww",
        iso_week="2026-W23",
        total_reviews=100,
        themes=[theme],
        generated_at=datetime.now()
    )

def test_docs_renderer(sample_report):
    requests = generate_docs_requests(sample_report)
    
    assert len(requests) > 0
    # Check if heading was generated correctly
    assert any("Groww" in str(r) and "Review Pulse" in str(r) and "2026-W23" in str(r) for r in requests)
    assert any("Performance" in str(r) for r in requests)
    assert any("App is slow" in str(r) for r in requests)
    assert any("It takes forever to load" in str(r) for r in requests)

def test_email_renderer(sample_report, mock_config):
    subject = get_email_subject(sample_report, mock_config)
    assert "2026-W23" in subject
    
    link = generate_deep_link("doc123", "h.abc")
    assert "doc123" in link
    assert "h.abc" in link
    
    html = render_email_html(sample_report, "doc123", "h.abc")
    assert "Groww — Review Pulse" in html
    assert "Performance" in html
    assert "App is slow" in html
    assert link in html
    
    text = render_email_text(sample_report, "doc123", "h.abc")
    assert "Groww — Review Pulse" in text
    assert "Performance" in text
    assert link in text
