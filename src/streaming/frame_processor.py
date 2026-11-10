"""
Frame processor integrating YOLOv8 CPU inference with per-stream ByteTrack tracking.
Directly reuses the authoritative baseline model and PersonTracker interface.
"""
import hashlib
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from src.detector import PersonTracker
from src.streaming.config import StreamingConfig, settings
from src.streaming.stream_metrics import (
    StreamErrorCategory,
    StreamingLogEntry,
    StreamingMetricsCollector,
    StructuredStreamingLogger,
    get_utc_timestamp,
)


class StreamFrameProcessor:
    """
    Stateful real-time frame processor for a single RTSP stream.
    Manages isolated ByteTrack tracker state per stream instance.
    """
    def __init__(
        self,
        config: Optional[StreamingConfig] = None,
        metrics_collector: Optional[StreamingMetricsCollector] = None,
        logger: Optional[StructuredStreamingLogger] = None,
    ):
        self.config = config or settings
        self.metrics = metrics_collector or StreamingMetricsCollector(stream_id=self.config.stream_id)
        self.logger = logger or StructuredStreamingLogger(log_file=self.config.log_file)
        self.tracker: Optional[PersonTracker] = None
        self._is_initialized = False

    def verify_model_integrity(self) -> Tuple[bool, str]:
        """Verify baseline model SHA256 before loading."""
        model_p = Path(self.config.model_path)
        if not model_p.exists():
            return False, f"Model file not found at: {self.config.model_path}"

        sha256_hash = hashlib.sha256()
        with open(model_p, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        actual_hash = sha256_hash.hexdigest().lower()

        if actual_hash != self.config.expected_sha256.lower():
            return False, f"Hash mismatch! Expected {self.config.expected_sha256}, got {actual_hash}"
        return True, actual_hash

    def initialize(self) -> None:
        """Verify model hash and instantiate isolated PersonTracker."""
        valid, msg = self.verify_model_integrity()
        if not valid:
            raise RuntimeError(f"Integrity check failed: {msg}")

        # Instantiate PersonTracker with configured thresholds
        self.tracker = PersonTracker(
            model_path=self.config.model_path,
            conf_threshold=self.config.conf_threshold,
            iou_threshold=self.config.iou_threshold,
            target_class_id=self.config.target_class_id,
        )
        self._is_initialized = True

    def reset_tracker(self) -> None:
        """Reset ByteTrack tracker state after prolonged connection drop."""
        if self._is_initialized:
            self.tracker = PersonTracker(
                model_path=self.config.model_path,
                conf_threshold=self.config.conf_threshold,
                iou_threshold=self.config.iou_threshold,
                target_class_id=self.config.target_class_id,
            )

    def process_frame(
        self,
        frame: np.ndarray,
        frame_seq: int,
    ) -> Tuple[List[Dict[str, Any]], float, float]:
        """
        Run person detection and ByteTrack tracking on incoming frame.
        
        Returns:
            tracks: list of tracked objects ({track_id, bbox, confidence, class_id})
            inference_ms: YOLO forward pass latency (ms)
            total_processing_ms: full processing latency including tracking (ms)
        """
        if not self._is_initialized or self.tracker is None:
            raise RuntimeError("Frame processor is not initialized.")

        t_start = time.perf_counter()
        img_h, img_w = frame.shape[:2]

        try:
            # PersonTracker.process_frame runs YOLO + ByteTrack
            tracks, inference_ms = self.tracker.process_frame(frame, persist=True)
            t_end = time.perf_counter()
            total_processing_ms = (t_end - t_start) * 1000.0

            track_ids = [t["track_id"] for t in tracks if t.get("track_id") is not None]
            det_count = len(tracks)

            # Record metrics
            self.metrics.record_processed_frame(
                inference_ms=inference_ms,
                processing_ms=total_processing_ms,
                detection_count=det_count,
                track_ids=track_ids,
            )

            # Emit structured JSONL log line
            self.logger.log(
                StreamingLogEntry(
                    timestamp=get_utc_timestamp(),
                    stream_id=self.config.stream_id,
                    connection_status="STREAMING",
                    frame_sequence=frame_seq,
                    source_width=img_w,
                    source_height=img_h,
                    inference_ms=round(inference_ms, 2),
                    processing_ms=round(total_processing_ms, 2),
                    detection_count=det_count,
                    track_count=len(track_ids),
                    dropped_frames_cumulative=self.metrics.frames_dropped,
                    reconnect_count=self.metrics.reconnect_count,
                    error_category=None,
                )
            )

            return tracks, inference_ms, total_processing_ms

        except Exception as e:
            t_end = time.perf_counter()
            total_processing_ms = (t_end - t_start) * 1000.0
            self.logger.log(
                StreamingLogEntry(
                    timestamp=get_utc_timestamp(),
                    stream_id=self.config.stream_id,
                    connection_status="ERROR",
                    frame_sequence=frame_seq,
                    source_width=img_w,
                    source_height=img_h,
                    inference_ms=0.0,
                    processing_ms=round(total_processing_ms, 2),
                    detection_count=0,
                    track_count=0,
                    dropped_frames_cumulative=self.metrics.frames_dropped,
                    reconnect_count=self.metrics.reconnect_count,
                    error_category=StreamErrorCategory.INFERENCE_ERROR.value,
                )
            )
            raise e
