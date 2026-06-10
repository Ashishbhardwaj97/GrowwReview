import pytest
from datetime import datetime
from src.config import (
    AppConfig, ProductConfig, IngestionConfig, EmbeddingConfig,
    UmapConfig, HdbscanConfig, ClusteringConfig, LlmConfig,
    PreprocessingConfig, DeliveryConfig, McpServerConfig, RunLogConfig
)
from src.models.types import RawReview, CleanReview, EmbeddedReview, Cluster, Theme, PulseReport

@pytest.fixture
def mock_config():
    return AppConfig(
        product=ProductConfig(name="groww", play_store_id="com.nextbillion.groww", display_name="Groww"),
        ingestion=IngestionConfig(window_weeks=2, max_reviews=100, language="en"),
        embedding=EmbeddingConfig(provider="sentence-transformers", model="all-MiniLM-L6-v2", batch_size=32),
        clustering=ClusteringConfig(
            umap=UmapConfig(n_neighbors=5, n_components=2, min_dist=0.0),
            hdbscan=HdbscanConfig(min_cluster_size=2, min_samples=2)
        ),
        llm=LlmConfig(provider="groq", model="llama-3.3-70b-versatile", max_tokens_per_run=10000, temperature=0.1, api_key="test-key"),
        preprocessing=PreprocessingConfig(pii_scrub=True, min_review_length=10),
        delivery=DeliveryConfig(google_doc_id="test_doc", stakeholders=["test@example.com"], draft_only=True, email_subject_template="Test {iso_week}"),
        mcp_server=McpServerConfig(url="http://test"),
        run_log=RunLogConfig(path="data/test_run_log.json")
    )

@pytest.fixture
def mock_raw_reviews():
    now = datetime.now()
    return [
        RawReview(review_id="r1", text="This is a great app, really easy to use.", rating=5, app_version="1.0", created_at=now),
        RawReview(review_id="r2", text="Terrible app, crashes all the time.", rating=1, app_version="1.1", created_at=now),
        RawReview(review_id="r3", text="Good app but needs more features.", rating=3, app_version="1.0", created_at=now),
    ]

@pytest.fixture
def mock_clean_reviews():
    now = datetime.now()
    return [
        CleanReview(review_id="r1", original_text="This is a great app, really easy to use.", clean_text="this is a great app really easy to use", rating=5, created_at=now),
        CleanReview(review_id="r2", original_text="Terrible app, crashes all the time.", clean_text="terrible app crashes all the time", rating=1, created_at=now),
        CleanReview(review_id="r3", original_text="Good app but needs more features.", clean_text="good app but needs more features", rating=3, created_at=now),
    ]
