"""
Configuration schemas and settings for VisionStream AI pipeline.
"""
from pathlib import Path
from pydantic import BaseModel, Field


class PipelineConfig(BaseModel):
    # Stream & Session Identity
    stream_id: str = Field(default="stream-cam-01", description="Identifier for the input stream/camera")
    tracking_session_id: str = Field(default="", description="Unique tracking session identifier")

    # Model settings
    model_path: str = Field(default="/app/data/models/yolov8n.pt", description="Path to YOLO model checkpoint")
    conf_threshold: float = Field(default=0.35, ge=0.0, le=1.0, description="Confidence threshold for person class")
    iou_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="NMS IoU threshold")
    target_class_id: int = Field(default=0, description="COCO class ID for person (0)")

    # Tracking settings
    tracker_type: str = Field(default="bytetrack.yaml", description="Tracker configuration file")
    
    # Video I/O
    input_video: str = Field(..., description="Path to input video file")
    output_video: str = Field(default="", description="Path to annotated output video file")
    max_frames: int = Field(default=0, description="Max frames to process (0 = all)")

    # Logging & Benchmarking
    log_format: str = Field(default="jsonl", description="Log format: jsonl or csv")
    log_dir: str = Field(default="/app/logs", description="Directory to store structured detection logs")
    benchmark_dir: str = Field(default="/app/reports", description="Directory to store benchmark summary")
