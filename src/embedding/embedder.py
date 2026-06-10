import abc
from typing import List, Optional
import argparse
from sentence_transformers import SentenceTransformer

from src.models.types import CleanReview, EmbeddedReview
from src.config import AppConfig, load_config

class Embedder(abc.ABC):
    @abc.abstractmethod
    def embed(self, reviews: List[CleanReview]) -> List[EmbeddedReview]:
        """Convert a list of CleanReview into EmbeddedReview."""
        pass

class SentenceTransformerEmbedder(Embedder):
    def __init__(self, model_name: str, batch_size: int = 128):
        self.model_name = model_name
        self.batch_size = batch_size
        self.model = SentenceTransformer(model_name)
        
    def embed(self, reviews: List[CleanReview]) -> List[EmbeddedReview]:
        if not reviews:
            return []
            
        texts = [r.clean_text for r in reviews]
        embeddings = self.model.encode(texts, batch_size=self.batch_size, show_progress_bar=True)
        
        result = []
        for review, emb in zip(reviews, embeddings):
            result.append(EmbeddedReview(review=review, embedding=emb.tolist()))
            
        return result

def get_embedder(config: AppConfig) -> Embedder:
    provider = config.embedding.provider.lower()
    if provider == "sentence-transformers":
        return SentenceTransformerEmbedder(
            model_name=config.embedding.model,
            batch_size=config.embedding.batch_size
        )
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the embedding module")
    parser.add_argument("--text", type=str, required=True, help="Text to embed")
    parser.add_argument("--provider", type=str, default="sentence-transformers", help="Embedding provider")
    args = parser.parse_args()
    
    from src.models.types import CleanReview
    from datetime import datetime
    
    config = load_config()
    config.embedding.provider = args.provider
    
    embedder = get_embedder(config)
    
    dummy_review = CleanReview(
        review_id="test",
        original_text=args.text,
        clean_text=args.text,
        rating=5,
        created_at=datetime.now()
    )
    
    embedded = embedder.embed([dummy_review])
    print(f"Generated embedding of dimension: {len(embedded[0].embedding)}")
    print(f"First 5 dimensions: {embedded[0].embedding[:5]}")
