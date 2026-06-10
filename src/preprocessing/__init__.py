from typing import List
from src.models.types import RawReview, CleanReview
from src.config import PreprocessingConfig
from .pii_scrubber import scrub_pii
from .normaliser import normalise_text, is_valid_review

def preprocess(raw_reviews: List[RawReview], config: PreprocessingConfig) -> List[CleanReview]:
    """
    Chains PII scrubbing, normalisation, and deduplication.
    Returns a list of CleanReview objects.
    """
    seen_ids = set()
    seen_texts = set()
    clean_reviews = []
    
    for raw in raw_reviews:
        # Deduplication by ID
        if raw.review_id in seen_ids:
            continue
        seen_ids.add(raw.review_id)
        
        # PII Scrub
        scrubbed_text = raw.text
        if config.pii_scrub:
            scrubbed_text = scrub_pii(scrubbed_text)
            
        # Normalise
        norm_text = normalise_text(scrubbed_text)
        
        # Filter
        if not is_valid_review(norm_text, config.min_review_length):
            continue
            
        # Deduplication by exact normalised text
        is_duplicate = False
        if norm_text in seen_texts:
            is_duplicate = True
        else:
            seen_texts.add(norm_text)
            
        clean = CleanReview(
            review_id=raw.review_id,
            original_text=raw.text,
            clean_text=norm_text,
            rating=raw.rating,
            created_at=raw.created_at,
            is_duplicate=is_duplicate
        )
        
        if not is_duplicate:
            clean_reviews.append(clean)
            
    return clean_reviews
