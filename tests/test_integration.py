import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
import argparse
import json

from src.cli import run_pipeline
from src.models.types import PulseReport, Theme

@pytest.fixture
def mock_args():
    return argparse.Namespace(
        product="groww",
        week="2026-W23",
        dry_run=False,
        draft_only=False,
        force=True, # Force run to ignore existing logs during test
        export_raw=False
    )

@pytest.fixture
def mock_pipeline_dependencies():
    with patch('src.cli.fetch_reviews') as mock_fetch, \
         patch('src.cli.get_embedder') as mock_embedder, \
         patch('src.cli.Clusterer') as mock_clusterer, \
         patch('src.cli.GroqSummariser') as mock_summariser, \
         patch('src.cli.MCPClient') as mock_mcp, \
         patch('src.cli.RunLogManager') as mock_run_log:
         
        # Setup mock implementations
        from src.models.types import RawReview, CleanReview, EmbeddedReview, Cluster
        from datetime import datetime
        now = datetime.now()
        
        # Mock fetch_reviews
        mock_fetch.return_value = [
            RawReview("r1", "This is a really good app", 5, "1.0", now),
            RawReview("r2", "This is a terrible bad app", 1, "1.0", now)
        ]
        
        # Mock embedder
        mock_emb_inst = MagicMock()
        mock_emb_inst.embed.return_value = [
            EmbeddedReview(CleanReview("r1", "Good app", "good app", 5, now), [0.1]),
            EmbeddedReview(CleanReview("r2", "Bad app", "bad app", 1, now), [0.2])
        ]
        mock_embedder.return_value = mock_emb_inst
        
        # Mock clusterer
        mock_clust_inst = MagicMock()
        mock_clust_inst.cluster.return_value = [
            Cluster(1, [CleanReview("r1", "Good app", "good app", 5, now)], 5.0, 1),
            Cluster(2, [CleanReview("r2", "Bad app", "bad app", 1, now)], 1.0, 1)
        ]
        mock_clusterer.return_value = mock_clust_inst
        
        # Mock summariser
        mock_sum_inst = MagicMock()
        mock_sum_inst.summarise.return_value = PulseReport(
            product="groww",
            iso_week="2026-W23",
            total_reviews=2,
            themes=[
                Theme("Good", "It is good", ["Good app"], [], 1, 1, 5.0),
                Theme("Bad", "It is bad", ["Bad app"], ["Fix it"], 2, 1, 1.0)
            ],
            generated_at=now
        )
        mock_summariser.return_value = mock_sum_inst
        
        # Mock MCPClient
        mock_mcp_inst = AsyncMock()
        mock_mcp_inst.find_doc_section.return_value = {"found": False}
        mock_mcp_inst.append_doc_section.return_value = {"headingId": "h.test"}
        mock_mcp_inst.find_sent_email.return_value = {"found": False}
        mock_mcp_inst.create_draft.return_value = {"draftId": "d.123"}
        mock_mcp_inst.send_draft.return_value = {"messageId": "m.456", "threadId": "t.789"}
        mock_mcp.return_value = mock_mcp_inst
        
        yield {
            "fetch": mock_fetch,
            "mcp": mock_mcp,
            "mcp_inst": mock_mcp_inst,
            "run_log": mock_run_log
        }

def test_integration_dry_run(mock_args, mock_pipeline_dependencies):
    mock_args.dry_run = True
    
    asyncio.run(run_pipeline(mock_args))
    
    # Dry run should not call MCPClient
    mock_pipeline_dependencies["mcp"].assert_not_called()

def test_integration_draft_only(mock_args, mock_pipeline_dependencies):
    mock_args.draft_only = True
    
    asyncio.run(run_pipeline(mock_args))
    
    mcp_inst = mock_pipeline_dependencies["mcp_inst"]
    mcp_inst.start.assert_called_once()
    mcp_inst.append_doc_section.assert_called_once()
    mcp_inst.create_draft.assert_called_once()
    mcp_inst.send_draft.assert_not_called() # Should not send email
    mcp_inst.stop.assert_called_once()

def test_integration_idempotency(mock_args, mock_pipeline_dependencies):
    mock_args.force = False
    
    # Mock run log to return True for has_run
    mock_run_log_inst = MagicMock()
    mock_run_log_inst.has_run.return_value = True
    mock_pipeline_dependencies["run_log"].return_value = mock_run_log_inst
    
    asyncio.run(run_pipeline(mock_args))
    
    # Fetch reviews should not be called because pipeline skipped
    mock_pipeline_dependencies["fetch"].assert_not_called()
    mock_pipeline_dependencies["mcp"].assert_not_called()

def test_integration_edge_cases(mock_args, mock_pipeline_dependencies):
    # E.g. No reviews fetched
    mock_pipeline_dependencies["fetch"].return_value = []
    
    asyncio.run(run_pipeline(mock_args))
    
    # MCP Client shouldn't be called if there are no reviews to process
    mock_pipeline_dependencies["mcp"].assert_not_called()
