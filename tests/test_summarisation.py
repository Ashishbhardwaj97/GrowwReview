import json
import pytest
from unittest.mock import patch, MagicMock
from src.summarisation.summariser import GroqSummariser
from src.models.types import Cluster

@pytest.fixture
def mock_groq_response():
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = json.dumps({
        "name": "Test Theme",
        "summary": "This is a test summary",
        "quotes": ["This is a great app, really easy to use."], # Matches clean review in mock
        "action_ideas": ["Do nothing"]
    })
    response.usage = MagicMock()
    response.usage.total_tokens = 100
    return response

@patch('src.summarisation.summariser.Groq')
def test_summariser(mock_groq_class, mock_config, mock_clean_reviews, mock_groq_response):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_groq_response
    mock_groq_class.return_value = mock_client
    
    summariser = GroqSummariser(mock_config)
    
    cluster = Cluster(
        cluster_id=1,
        reviews=mock_clean_reviews,
        avg_rating=4.0,
        size=3
    )
    
    report = summariser.summarise([cluster], "2026-W23")
    
    assert report.iso_week == "2026-W23"
    assert len(report.themes) == 1
    assert report.total_reviews == 3
    
    theme = report.themes[0]
    assert theme.name == "Test Theme"
    # The quote should be validated successfully
    assert len(theme.quotes) == 1
    assert theme.quotes[0] == "This is a great app, really easy to use."

@patch('src.summarisation.summariser.Groq')
def test_summariser_invalid_quote(mock_groq_class, mock_config, mock_clean_reviews):
    mock_client = MagicMock()
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = json.dumps({
        "name": "Fabricated Theme",
        "summary": "Summary",
        "quotes": ["I totally made this quote up!"], # Should fail fuzzy match
        "action_ideas": []
    })
    mock_client.chat.completions.create.return_value = response
    mock_groq_class.return_value = mock_client
    
    summariser = GroqSummariser(mock_config)
    cluster = Cluster(cluster_id=1, reviews=mock_clean_reviews, avg_rating=5.0, size=3)
    
    report = summariser.summarise([cluster], "2026-W23")
    assert len(report.themes[0].quotes) == 0 # Quote should be discarded
