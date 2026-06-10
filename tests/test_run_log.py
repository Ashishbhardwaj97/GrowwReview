import os
import pytest
from datetime import datetime
from src.utils.run_log import RunLogManager
from src.models.types import RunRecord

def test_run_log_manager(tmp_path, mock_config):
    log_file = tmp_path / "test_run_log.json"
    mock_config.run_log.path = str(log_file)
    
    manager = RunLogManager(mock_config)
    
    # Check if file was created
    assert log_file.exists()
    
    # Should not have run yet
    assert not manager.has_run("groww", "2026-W23")
    
    # Record a run
    record = RunRecord(
        product="groww",
        iso_week="2026-W23",
        run_at=datetime.now(),
        docs_heading_id="h.abc",
        gmail_draft_id="d.123",
        gmail_thread_id=None,
        status="success"
    )
    manager.record_run(record)
    
    # Should now return True for has_run
    assert manager.has_run("groww", "2026-W23")
    assert not manager.has_run("groww", "2026-W24")
    assert not manager.has_run("other_product", "2026-W23")
