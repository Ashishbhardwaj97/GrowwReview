import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from src.clustering.clusterer import Clusterer
from src.models.types import EmbeddedReview

def test_low_data_guard(mock_config, mock_clean_reviews):
    mock_config.clustering.hdbscan.min_cluster_size = 5 # higher than reviews count (3)
    embedded = [
        EmbeddedReview(review=mock_clean_reviews[0], embedding=[0.1, 0.2]),
        EmbeddedReview(review=mock_clean_reviews[1], embedding=[0.2, 0.3]),
        EmbeddedReview(review=mock_clean_reviews[2], embedding=[0.3, 0.4])
    ]
    
    clusterer = Clusterer(mock_config)
    clusters = clusterer.cluster(embedded)
    
    assert len(clusters) == 1
    assert clusters[0].cluster_id == 0
    assert clusters[0].size == 3
    assert clusters[0].avg_rating == sum([r.rating for r in mock_clean_reviews]) / 3

@patch('src.clustering.clusterer.umap.UMAP')
@patch('src.clustering.clusterer.hdbscan.HDBSCAN')
def test_clustering_normal(mock_hdbscan, mock_umap, mock_config, mock_clean_reviews):
    mock_config.clustering.hdbscan.min_cluster_size = 2 # lower than reviews count (3)
    embedded = [
        EmbeddedReview(review=mock_clean_reviews[0], embedding=[0.1, 0.2]),
        EmbeddedReview(review=mock_clean_reviews[1], embedding=[0.2, 0.3]),
        EmbeddedReview(review=mock_clean_reviews[2], embedding=[0.3, 0.4])
    ]
    
    # Mock UMAP projection
    mock_reducer = MagicMock()
    mock_reducer.fit_transform.return_value = np.zeros((3, 2))
    mock_umap.return_value = mock_reducer
    
    # Mock HDBSCAN prediction
    mock_hdb = MagicMock()
    # Let's say review 0 and 1 are in cluster 0, review 2 is noise (-1)
    mock_hdb.fit_predict.return_value = [0, 0, -1]
    mock_hdbscan.return_value = mock_hdb
    
    clusterer = Clusterer(mock_config)
    clusters = clusterer.cluster(embedded)
    
    assert len(clusters) == 1
    assert clusters[0].cluster_id == 0
    assert clusters[0].size == 2
    assert clusters[0].reviews[0].review_id == "r1"
    assert clusters[0].reviews[1].review_id == "r2"
    assert clusters[0].avg_rating == 3.0 # (5+1)/2

    mock_umap.assert_called_once()
    mock_hdbscan.assert_called_once()
