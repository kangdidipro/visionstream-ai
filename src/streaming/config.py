"""
Configuration models for VisionStream AI GStreamer & RTSP streaming ingestion.
"""
import os
from pathlib import Path
from pydantic import BaseModel, Field


class StreamingConfig(BaseModel):
    # Stream identification
    stream_id: str = Field(default="stream-cam-01", description="Unique identifier for the camera stream")
    rtsp_url: str = Field(
        default_factory=lambda: os.getenv("RTSP_URL", "rtsp://mediamtx:8554/live/stream1")
    )
    
    # Model baseline configuration
    model_path: str = Field(
        default_factory=lambda: os.getenv("MODEL_PATH", "/app/data/models/yolov8n.pt")
    )
    expected_sha256: str = "f59b3d833e2ff32e194b5bb8e08d211dc7c5bdf144b90d2c8412c47ccfc83b36"
    conf_threshold: float = 0.35
    iou_threshold: float = 0.65
    target_class_id: int = 0
    target_class_name: str = "person"
    device: str = "cpu"

    # GStreamer ingestion parameters
    rtsp_transport: str = "tcp"  # tcp or udp
    jitter_buffer_ms: int = 200
    queue_max_buffers: int = 2
    queue_leaky_mode: str = "downstream"  # downstream drops oldest when full
    appsink_max_buffers: int = 2
    appsink_drop: bool = True
    
    # Target frame format
    target_format: str = "BGR"
    
    # Stream resilience parameters
    connection_timeout_sec: float = 10.0
    max_reconnect_attempts: int = 5
    initial_retry_delay_sec: float = 1.0
    max_retry_delay_sec: float = 8.0
    reconnect_backoff_factor: float = 2.0
    tracker_reset_outage_sec: float = 5.0

    # Logging & Persistence
    log_file: str = "/app/logs/streaming_access.jsonl"
    max_log_bytes: int = 20 * 1024 * 1024  # 20 MB
    backup_count: int = 5


settings = StreamingConfig()
