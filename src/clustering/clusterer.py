import json
import argparse
from typing import List, Dict, Any
import numpy as np

import umap
import hdbscan

from src.models.types import EmbeddedReview, Cluster, CleanReview
from src.config import ClusteringConfig
from src.utils.helpers import setup_logging
import logging

logger = logging.getLogger(__name__)

class Clusterer:
    def __init__(self, config: ClusteringConfig):
        self.config = config
        
    def cluster(self, embedded_reviews: List[EmbeddedReview]) -> List[Cluster]:
        if not embedded_reviews:
            return []
            
        n_reviews = len(embedded_reviews)
        min_cluster_size = self.config.hdbscan.min_cluster_size
        
        # Low data guard: if we have fewer reviews than min_cluster_size, group them all
        if n_reviews < min_cluster_size:
            logger.warning(f"Low data guard triggered: {n_reviews} reviews is less than min_cluster_size {min_cluster_size}.")
            return self._create_miscellaneous_cluster(embedded_reviews)
            
        embeddings = np.array([er.embedding for er in embedded_reviews])
        
        # UMAP Projection
        logger.info(f"Projecting {n_reviews} embeddings using UMAP...")
        n_neighbors = min(self.config.umap.n_neighbors, n_reviews - 1)
        if n_neighbors < 2:
            n_neighbors = 2
            
        reducer = umap.UMAP(
            n_neighbors=n_neighbors,
            n_components=self.config.umap.n_components,
            min_dist=self.config.umap.min_dist,
            random_state=42 # for reproducibility
        )
        projected = reducer.fit_transform(embeddings)
        
        # HDBSCAN Clustering
        logger.info("Clustering projected vectors using HDBSCAN...")
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=self.config.hdbscan.min_cluster_size,
            min_samples=self.config.hdbscan.min_samples,
            gen_min_span_tree=True
        )
        cluster_labels = clusterer.fit_predict(projected)
        
        # Group reviews by cluster
        clusters_dict: Dict[int, List[CleanReview]] = {}
        for i, label in enumerate(cluster_labels):
            if label == -1:
                # Noise cluster, we can skip or log it
                continue
            
            if label not in clusters_dict:
                clusters_dict[label] = []
            clusters_dict[label].append(embedded_reviews[i].review)
            
        logger.info(f"Found {len(clusters_dict)} clusters (excluding noise).")
        
        # Assemble Cluster objects
        clusters = []
        for label, reviews in clusters_dict.items():
            avg_rating = sum(r.rating for r in reviews) / len(reviews)
            clusters.append(Cluster(
                cluster_id=int(label),
                reviews=reviews,
                avg_rating=float(avg_rating),
                size=len(reviews)
            ))
            
        # Rank clusters by size descending
        clusters.sort(key=lambda c: c.size, reverse=True)
        return clusters

    def _create_miscellaneous_cluster(self, embedded_reviews: List[EmbeddedReview]) -> List[Cluster]:
        reviews = [er.review for er in embedded_reviews]
        avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 0.0
        cluster = Cluster(
            cluster_id=0,
            reviews=reviews,
            avg_rating=float(avg_rating),
            size=len(reviews)
        )
        return [cluster]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the clustering module")
    parser.add_argument("--input", type=str, required=True, help="Path to JSON file with embeddings to test")
    args = parser.parse_args()
    
    from datetime import datetime
    
    # Simple script to test with a raw json if needed
    print(f"Loading embeddings from {args.input} (make sure it fits List[EmbeddedReview] format)")
