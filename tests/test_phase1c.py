import datetime
from src.preprocessing.pii_scrubber import scrub_pii
from src.preprocessing.normaliser import normalise_text, is_valid_review
from src.preprocessing import preprocess
from src.config import PreprocessingConfig
from src.models.types import RawReview

def test_scrub_pii():
    text = "Contact me at test@example.com or call +919876543210. Aadhaar: 1234 5678 9012"
    scrubbed = scrub_pii(text)
    assert "test@example.com" not in scrubbed
    assert "+919876543210" not in scrubbed
    assert "1234 5678 9012" not in scrubbed
    assert scrubbed.count("[REDACTED]") == 3

def test_normalise_text():
    text = "This   IS a TeSt \n\n Review  "
    norm = normalise_text(text)
    assert norm == "this is a test review"

def test_is_valid_review():
    assert is_valid_review("This is a good app, I love it!")
    assert not is_valid_review("ok") # Too short
    assert not is_valid_review("⭐⭐⭐⭐⭐ 😊😊😊😊😊", min_length=10) # Mostly emoji

def test_preprocess():
    now = datetime.datetime.now()
    raw_reviews = [
        RawReview("1", "Hello! email@test.com", 5, "1.0", now),
        RawReview("2", "ok", 1, "1.0", now), # Too short, should be filtered
        RawReview("3", "Hello! email@test.com", 5, "1.0", now), # Duplicate by exact text
        RawReview("1", "Different text same ID", 4, "1.0", now) # Duplicate by ID
    ]
    
    config = PreprocessingConfig(pii_scrub=True, min_review_length=10)
    clean_reviews = preprocess(raw_reviews, config)
    
    assert len(clean_reviews) == 1
    assert clean_reviews[0].review_id == "1"
    assert clean_reviews[0].clean_text == "hello! [redacted]"
