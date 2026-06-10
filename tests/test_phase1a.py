import datetime
import os
from src.utils.helpers import current_iso_week, iso_week_to_date_range
from src.config import load_config
from src.models.types import RawReview

def test_helpers():
    iso = current_iso_week()
    assert "-W" in iso
    
    start, end = iso_week_to_date_range("2026-W23")
    assert start.year == 2026
    assert start.month == 6
    assert start.day == 1
    
    assert end.year == 2026
    assert end.month == 6
    assert end.day == 7

def test_config():
    # Make sure we don't fail if .env is missing by setting a dummy env var
    os.environ["GROQ_API_KEY"] = "test"
    config = load_config("config.yaml")
    assert config.product.name == "groww"
    assert config.ingestion.window_weeks == 10
    assert config.llm.provider == "groq"

def test_models():
    now = datetime.datetime.now()
    review = RawReview(
        review_id="123",
        text="test",
        rating=5,
        app_version="1.0",
        created_at=now
    )
    assert review.review_id == "123"
