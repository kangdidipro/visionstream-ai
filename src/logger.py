"""
Detection logger module for streaming JSONL / CSV structured logs.
"""
import csv
import json
from pathlib import Path
from typing import Dict, Any, Optional


class DetectionLogger:
    def __init__(self, log_path: Path, log_format: str = "jsonl"):
        self.log_path = Path(log_path)
        self.log_format = log_format.lower()
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._file = open(self.log_path, "w", encoding="utf-8", newline="")
        self._csv_writer = None
        
        if self.log_format == "csv":
            fieldnames = [
                "stream_id",
                "tracking_session_id",
                "frame_number",
                "timestamp",
                "track_id",
                "confidence",
                "bbox_x1",
                "bbox_y1",
                "bbox_x2",
                "bbox_y2"
            ]
            self._csv_writer = csv.DictWriter(self._file, fieldnames=fieldnames)
            self._csv_writer.writeheader()

    def log_record(self, record: Dict[str, Any]):
        if self.log_format == "csv" and self._csv_writer:
            self._csv_writer.writerow(record)
        else:
            self._file.write(json.dumps(record) + "\n")
        self._file.flush()

    def close(self):
        if self._file and not self._file.closed:
            self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
