from unittest.mock import patch, MagicMock
from src.ingestion.play_store import fetch_reviews
from src.config import IngestionConfig
import datetime

@patch('src.ingestion.play_store.reviews')
def test_fetch_reviews(mock_reviews):
    # Mock return value of google_play_scraper.reviews
    mock_reviews.return_value = (
        [
            {
                "reviewId": "test_id_1",
                "content": "test content 1",
                "score": 5,
                "reviewCreatedVersion": "1.0",
                "at": datetime.datetime.now()
            },
            {
                "reviewId": "test_id_2",
                "content": "test content 2",
                "score": 4,
                "reviewCreatedVersion": "1.1",
                "at": datetime.datetime.now()
            }
        ],
        None # Continuation token
    )
    
    config = IngestionConfig(window_weeks=1, max_reviews=10, language="en")
    result = fetch_reviews("com.test", config, iso_week="2026-W23")
    
    assert len(result) == 2
    assert result[0].review_id == "test_id_1"
    assert result[1].rating == 4
    mock_reviews.assert_called_once()
