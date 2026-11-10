"""
Real-time streaming metrics and structured JSONL logging for VisionStream AI.
Enforces strict privacy: NEVER logs raw frame pixels or image bytes.
"""
from datetime import datetime, timezone
from enum import Enum
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import time
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from src.streaming.config import settings


class StreamStatus(str, Enum):
    INITIALIZING = "INITIALIZING"
    CONNECTED = "CONNECTED"
    STREAMING = "STREAMING"
    RECONNECTING = "RECONNECTING"
    DISCONNECTED = "DISCONNECTED"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


class StreamErrorCategory(str, Enum):
    CONNECTION_REFUSED = "CONNECTION_REFUSED"
    STREAM_TIMEOUT = "STREAM_TIMEOUT"
    RTSP_AUTH_FAILURE = "RTSP_AUTH_FAILURE"
    CODEC_ERROR = "CODEC_ERROR"
    PIPELINE_ERROR = "PIPELINE_ERROR"
    FRAME_DECODE_ERROR = "FRAME_DECODE_ERROR"
    INFERENCE_ERROR = "INFERENCE_ERROR"


class StreamingLogEntry(BaseModel):
    timestamp: str
    stream_id: str
    connection_status: str
    frame_sequence: Optional[int] = None
    source_width: Optional[int] = None
    source_height: Optional[int] = None
    inference_ms: Optional[float] = None
    processing_ms: Optional[float] = None
    detection_count: Optional[int] = None
    track_count: Optional[int] = None
    dropped_frames_cumulative: Optional[int] = None
    reconnect_count: Optional[int] = None
    error_category: Optional[str] = None


class StreamingMetricsCollector:
    """Collects and aggregates streaming performance metrics."""
    def __init__(self, stream_id: str):
        self.stream_id = stream_id
        self.start_time = time.time()
        
        # Frame counters
        self.frames_received = 0
        self.frames_decoded = 0
        self.frames_processed = 0
        self.frames_dropped = 0
        
        # Detection & tracking counters
        self.total_persons_detected = 0
        self.total_tracks_assigned = 0
        self.unique_track_ids = set()
        
        # Connection resilience
        self.reconnect_count = 0
        self.last_frame_timestamp = 0.0
        
        # Latency records (milliseconds)
        self.inference_latencies = []
        self.processing_latencies = []
        
    def record_frame_received(self):
        self.frames_received += 1

    def record_frame_decoded(self):
        self.frames_decoded += 1

    def record_frame_dropped(self):
        self.frames_dropped += 1

    def record_reconnect(self):
        self.reconnect_count += 1

    def record_processed_frame(
        self,
        inference_ms: float,
        processing_ms: float,
        detection_count: int,
        track_ids: list[int],
    ):
        self.frames_processed += 1
        self.last_frame_timestamp = time.time()
        self.inference_latencies.append(inference_ms)
        self.processing_latencies.append(processing_ms)
        self.total_persons_detected += detection_count
        self.total_tracks_assigned += len(track_ids)
        for tid in track_ids:
            if tid is not None and tid > 0:
                self.unique_track_ids.add(tid)

    def get_summary(self) -> Dict[str, Any]:
        uptime_sec = max(time.time() - self.start_time, 0.001)
        
        # Rates
        source_fps = round(self.frames_received / uptime_sec, 2)
        decode_fps = round(self.frames_decoded / uptime_sec, 2)
        pipeline_fps = round(self.frames_processed / uptime_sec, 2)
        
        # Latency statistics
        if self.inference_latencies:
            sorted_inf = sorted(self.inference_latencies)
            inf_mean = round(sum(sorted_inf) / len(sorted_inf), 2)
            inf_median = round(sorted_inf[len(sorted_inf) // 2], 2)
            p95_idx = min(int(len(sorted_inf) * 0.95), len(sorted_inf) - 1)
            inf_p95 = round(sorted_inf[p95_idx], 2)
        else:
            inf_mean = inf_median = inf_p95 = 0.0

        if self.processing_latencies:
            sorted_proc = sorted(self.processing_latencies)
            proc_mean = round(sum(sorted_proc) / len(sorted_proc), 2)
        else:
            proc_mean = 0.0

        return {
            "stream_id": self.stream_id,
            "uptime_seconds": round(uptime_sec, 2),
            "frames_received": self.frames_received,
            "frames_decoded": self.frames_decoded,
            "frames_processed": self.frames_processed,
            "frames_dropped": self.frames_dropped,
            "source_fps": source_fps,
            "decode_fps": decode_fps,
            "pipeline_fps": pipeline_fps,
            "inference_mean_ms": inf_mean,
            "inference_median_ms": inf_median,
            "inference_p95_ms": inf_p95,
            "processing_mean_ms": proc_mean,
            "unique_persons_tracked": len(self.unique_track_ids),
            "total_detections": self.total_persons_detected,
            "reconnect_count": self.reconnect_count,
        }


class StructuredStreamingLogger:
    """Writes JSONL audit records with log rotation to logs/streaming_access.jsonl."""
    def __init__(
        self,
        log_file: str = settings.log_file,
        max_bytes: int = settings.max_log_bytes,
        backup_count: int = settings.backup_count,
    ):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(f"visionstream.streaming_access.{hash(str(self.log_file))}")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        if not self.logger.handlers:
            handler = RotatingFileHandler(
                filename=str(self.log_file),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(handler)

    def log(self, entry: StreamingLogEntry) -> None:
        """Write single validated JSON record line."""
        record_json = entry.model_dump_json(exclude_none=False)
        self.logger.info(record_json)


def get_utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()
