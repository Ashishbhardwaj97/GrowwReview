import os
import yaml
from dataclasses import dataclass
from typing import List, Dict, Any
from dotenv import load_dotenv

@dataclass
class ProductConfig:
    name: str
    play_store_id: str
    display_name: str

@dataclass
class IngestionConfig:
    window_weeks: int
    max_reviews: int
    language: str

@dataclass
class EmbeddingConfig:
    provider: str
    model: str
    batch_size: int

@dataclass
class UmapConfig:
    n_neighbors: int
    n_components: int
    min_dist: float

@dataclass
class HdbscanConfig:
    min_cluster_size: int
    min_samples: int

@dataclass
class ClusteringConfig:
    umap: UmapConfig
    hdbscan: HdbscanConfig

@dataclass
class LlmConfig:
    provider: str
    model: str
    max_tokens_per_run: int
    temperature: float
    api_key: str
    rpm_limit: int = 30
    tpm_limit: int = 12000

@dataclass
class PreprocessingConfig:
    pii_scrub: bool
    min_review_length: int

@dataclass
class DeliveryConfig:
    google_doc_id: str
    stakeholders: List[str]
    draft_only: bool
    email_subject_template: str

@dataclass
class McpServerConfig:
    url: str

@dataclass
class RunLogConfig:
    path: str

@dataclass
class AppConfig:
    product: ProductConfig
    ingestion: IngestionConfig
    embedding: EmbeddingConfig
    clustering: ClusteringConfig
    llm: LlmConfig
    preprocessing: PreprocessingConfig
    delivery: DeliveryConfig
    mcp_server: McpServerConfig
    run_log: RunLogConfig

def load_config(config_path: str = "config.yaml") -> AppConfig:
    load_dotenv()
    
    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
        
    groq_api_key = os.environ.get("GROQ_API_KEY", "")
        
    return AppConfig(
        product=ProductConfig(**raw.get("product", {})),
        ingestion=IngestionConfig(**raw.get("ingestion", {})),
        embedding=EmbeddingConfig(**raw.get("embedding", {})),
        clustering=ClusteringConfig(
            umap=UmapConfig(**raw.get("clustering", {}).get("umap", {})),
            hdbscan=HdbscanConfig(**raw.get("clustering", {}).get("hdbscan", {}))
        ),
        llm=LlmConfig(**raw.get("llm", {}), api_key=groq_api_key),
        preprocessing=PreprocessingConfig(**raw.get("preprocessing", {})),
        delivery=DeliveryConfig(**raw.get("delivery", {})),
        mcp_server=McpServerConfig(**raw.get("mcp_server", {})),
        run_log=RunLogConfig(**raw.get("run_log", {}))
    )
