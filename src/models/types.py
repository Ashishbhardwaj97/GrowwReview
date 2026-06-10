from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class RawReview:
    review_id: str
    text: str
    rating: int
    app_version: Optional[str]
    created_at: datetime

@dataclass
class CleanReview:
    review_id: str
    original_text: str
    clean_text: str
    rating: int
    created_at: datetime
    is_duplicate: bool = False

@dataclass
class EmbeddedReview:
    review: CleanReview
    embedding: List[float]

@dataclass
class Cluster:
    cluster_id: int
    reviews: List[CleanReview]
    avg_rating: float
    size: int

@dataclass
class Theme:
    name: str
    summary: str
    quotes: List[str]
    action_ideas: List[str]
    cluster_id: int
    size: int
    avg_rating: float

@dataclass
class PulseReport:
    product: str
    iso_week: str
    total_reviews: int
    themes: List[Theme]
    generated_at: datetime

@dataclass
class RunRecord:
    product: str
    iso_week: str
    run_at: datetime
    docs_heading_id: Optional[str]
    gmail_draft_id: Optional[str]
    gmail_thread_id: Optional[str]
    status: str
