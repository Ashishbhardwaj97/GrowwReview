import numpy as np
from unittest.mock import patch, MagicMock
import pytest
from src.embedding.embedder import SentenceTransformerEmbedder, get_embedder

@patch('src.embedding.embedder.SentenceTransformer')
def test_sentence_transformer_embedder(mock_st, mock_clean_reviews):
    mock_model = MagicMock()
    # Mock encode to return a numpy array of shape (num_reviews, 384)
    mock_model.encode.return_value = np.zeros((len(mock_clean_reviews), 384))
    mock_st.return_value = mock_model
    
    embedder = SentenceTransformerEmbedder("test-model")
    embedded_reviews = embedder.embed(mock_clean_reviews)
    
    assert len(embedded_reviews) == len(mock_clean_reviews)
    assert len(embedded_reviews[0].embedding) == 384
    mock_model.encode.assert_called_once()
    
    # Test empty list
    assert embedder.embed([]) == []

@patch('src.embedding.embedder.SentenceTransformer')
def test_get_embedder(mock_st, mock_config):
    embedder = get_embedder(mock_config)
    assert isinstance(embedder, SentenceTransformerEmbedder)
    
    mock_config.embedding.provider = "unsupported"
    with pytest.raises(ValueError):
        get_embedder(mock_config)
