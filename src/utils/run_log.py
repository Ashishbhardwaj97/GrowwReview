import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any

from src.models.types import RunRecord
from src.config import AppConfig

class RunLogManager:
    def __init__(self, config: AppConfig):
        self.log_path = config.run_log.path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        if not os.path.exists(self.log_path):
            with open(self.log_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def _read_logs(self) -> List[Dict[str, Any]]:
        with open(self.log_path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    def _write_logs(self, logs: List[Dict[str, Any]]):
        with open(self.log_path, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2)

    def has_run(self, product: str, iso_week: str) -> bool:
        logs = self._read_logs()
        for log in logs:
            if log.get('product') == product and log.get('iso_week') == iso_week and log.get('status') == 'success':
                return True
        return False

    def record_run(self, record: RunRecord):
        logs = self._read_logs()
        record_dict = {
            "product": record.product,
            "iso_week": record.iso_week,
            "run_at": record.run_at.isoformat(),
            "docs_heading_id": record.docs_heading_id,
            "gmail_draft_id": record.gmail_draft_id,
            "gmail_thread_id": record.gmail_thread_id,
            "status": record.status
        }
        logs.append(record_dict)
        self._write_logs(logs)

