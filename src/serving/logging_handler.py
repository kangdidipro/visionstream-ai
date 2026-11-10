"""
Structured JSONL logging with log rotation for VisionStream AI inference service.
Adheres strictly to privacy rules: NEVER logs raw bytes, base64 data, or sensitive image pixels.
"""
from datetime import datetime, timezone
from enum import Enum
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel


class ErrorCategory(str, Enum):
    EMPTY_PAYLOAD = "EMPTY_PAYLOAD"
    DECODE_FAILURE = "DECODE_FAILURE"
    UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    SERVICE_UNREADY = "SERVICE_UNREADY"
    INFERENCE_EXCEPTION = "INFERENCE_EXCEPTION"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"


class InferenceLogEntry(BaseModel):
    timestamp: str
    request_id: str
    method: str
    endpoint: str
    http_status: int
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    model_sha256: Optional[str] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    image_size_bytes: Optional[int] = None
    conf_threshold: Optional[float] = None
    iou_threshold: Optional[float] = None
    detection_count: Optional[int] = None
    preprocess_ms: Optional[float] = None
    inference_ms: Optional[float] = None
    postprocess_ms: Optional[float] = None
    total_ms: Optional[float] = None
    error_category: Optional[str] = None


class StructuredInferenceLogger:
    def __init__(
        self,
        log_file: str = "/app/logs/inference_access.jsonl",
        max_bytes: int = 20 * 1024 * 1024,  # 20 MB
        backup_count: int = 5,
        logger_name: Optional[str] = None,
    ):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        name = logger_name or f"visionstream.inference_access.{hash(str(self.log_file))}"
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        # Configure RotatingFileHandler
        if not self.logger.handlers:
            handler = RotatingFileHandler(
                filename=str(self.log_file),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(handler)

    def log(self, entry: InferenceLogEntry) -> None:
        """Write single validated JSON record line."""
        record_json = entry.model_dump_json(exclude_none=False)
        self.logger.info(record_json)


def get_utc_iso_timestamp() -> str:
    """Return UTC ISO 8601 formatted timestamp with millisecond precision."""
    return datetime.now(timezone.utc).isoformat()
