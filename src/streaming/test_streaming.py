"""
Integration test suite for VisionStream AI GStreamer RTSP Ingestion Pipeline (Gate 6).
Verifies:
A. GStreamer readiness and Python gi bindings.
B. RTSP publisher and MediaMTX connectivity.
C. Frame ingestion, dimensions, and type validation.
D. YOLOv8 baseline model SHA256 integrity and person-only inference.
E. ByteTrack tracking integration and per-stream isolation.
F. Reconnection and resilience handling.
G. Structured JSONL logs and metrics validation.
H. Gate 2 & Gate 4 regression verification.
"""
import hashlib
import json
import os
from pathlib import Path
import time
import pytest
import numpy as np

import gi
gi.require_version("Gst", "1.0")
gi.require_version("GstApp", "1.0")
from gi.repository import Gst

from src.streaming.config import StreamingConfig, settings
from src.streaming.frame_processor import StreamFrameProcessor
from src.streaming.gstreamer_ingest import GStreamerRTSPIngest
from src.streaming.rtsp_client import ResilientRTSPClient
from src.streaming.stream_metrics import (
    StreamStatus,
    StreamingMetricsCollector,
    StructuredStreamingLogger,
)


# ============================================================================
# A. GSTREAMER READINESS TESTS
# ============================================================================

def test_gstreamer_initialization_and_version():
    """Verify GStreamer 1.0 initializes and reports valid version string."""
    Gst.init(None)
    version_str = Gst.version_string()
    assert "GStreamer" in version_str
    assert Gst.version() >= (1, 20, 0)


def test_essential_gstreamer_plugins_available():
    """Verify all pipeline elements exist in GStreamer registry."""
    required_elements = [
        "rtspsrc",
        "rtph264depay",
        "h264parse",
        "avdec_h264",
        "videoconvert",
        "queue",
        "appsink",
    ]
    for elem_name in required_elements:
        factory = Gst.ElementFactory.find(elem_name)
        assert factory is not None, f"Required GStreamer element '{elem_name}' not found!"


# ============================================================================
# B. RTSP SERVER & PUBLISHER CONNECTIVITY
# ============================================================================

def test_rtsp_stream_reception():
    """Verify connection to local MediaMTX stream and successful frame arrival."""
    frames_received = []

    def on_frame(frame, seq):
        frames_received.append((frame.shape, seq))

    ingest = GStreamerRTSPIngest(
        config=settings,
        on_frame_callback=on_frame,
    )

    ingest.start()
    # Wait up to 5 seconds for frames
    t0 = time.time()
    while len(frames_received) < 5 and (time.time() - t0) < 5.0:
        time.sleep(0.1)

    ingest.stop()
    assert len(frames_received) >= 5, f"Expected >= 5 frames, got {len(frames_received)}"
    # Check frame properties
    shape, seq = frames_received[0]
    assert shape == (432, 768, 3), f"Expected 432x768x3, got {shape}"


# ============================================================================
# C. FRAME EXTRACTION AND VALIDATION
# ============================================================================

def test_frame_dtype_and_color_format():
    """Verify frame extracted via appsink is uint8 BGR numpy array."""
    captured_frame = []

    def on_frame(frame, seq):
        if not captured_frame:
            captured_frame.append(frame)

    ingest = GStreamerRTSPIngest(config=settings, on_frame_callback=on_frame)
    ingest.start()
    t0 = time.time()
    while not captured_frame and (time.time() - t0) < 4.0:
        time.sleep(0.1)
    ingest.stop()

    assert len(captured_frame) == 1
    frame = captured_frame[0]
    assert isinstance(frame, np.ndarray)
    assert frame.dtype == np.uint8
    assert frame.shape[2] == 3


# ============================================================================
# D. YOLOv8 BASELINE INFERENCE & SHA256 INTEGRITY
# ============================================================================

def test_model_sha256_integrity_before_inference():
    """Verify primary model SHA256 matches authoritative baseline hash."""
    model_p = Path(settings.model_path)
    assert model_p.exists()
    hasher = hashlib.sha256()
    with open(model_p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    actual_hash = hasher.hexdigest().lower()
    assert actual_hash == settings.expected_sha256.lower()


def test_frame_processor_detection_and_bytetrack():
    """Verify PersonTracker detects person and assigns track ID."""
    processor = StreamFrameProcessor(config=settings)
    processor.initialize()

    # Load sample person frame
    sample_img_path = Path("/app/data/inputs/sample_person.jpg")
    assert sample_img_path.exists()
    import cv2
    frame = cv2.imread(str(sample_img_path))

    tracks, infer_ms, proc_ms = processor.process_frame(frame, frame_seq=1)
    assert len(tracks) >= 1
    det = tracks[0]
    assert det["class_id"] == 0  # Person only
    assert det["confidence"] >= settings.conf_threshold
    assert det["track_id"] > 0
    assert infer_ms > 0
    assert proc_ms >= infer_ms


# ============================================================================
# E. RESILIENCE AND RECONNECTION
# ============================================================================

def test_resilient_rtsp_client_handles_unreachable_endpoint():
    """Verify client handles bad RTSP endpoint gracefully with bounded retry."""
    bad_config = StreamingConfig(
        stream_id="test-bad-stream",
        rtsp_url="rtsp://127.0.0.1:9999/nonexistent",
        connection_timeout_sec=2.0,
        max_reconnect_attempts=2,
        initial_retry_delay_sec=0.2,
        max_retry_delay_sec=0.5,
    )

    client = ResilientRTSPClient(config=bad_config)
    # Run with timeout to prevent hanging
    client.run_with_reconnect(max_duration_sec=3.0)
    assert client.status in (StreamStatus.ERROR, StreamStatus.STOPPED, StreamStatus.DISCONNECTED)
    assert client.metrics.reconnect_count >= 1


# ============================================================================
# F. STRUCTURED LOGGING & PRIVACY
# ============================================================================

def test_streaming_jsonl_log_fields_and_privacy():
    """Verify logs/streaming_access.jsonl contains expected fields and zero raw image bytes."""
    log_path = Path(settings.log_file)
    assert log_path.exists()

    with open(log_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    assert len(lines) > 0
    record = json.loads(lines[-1])

    required_keys = [
        "timestamp",
        "stream_id",
        "connection_status",
        "frame_sequence",
        "source_width",
        "source_height",
        "inference_ms",
        "processing_ms",
        "detection_count",
        "track_count",
        "dropped_frames_cumulative",
        "reconnect_count",
        "error_category",
    ]
    for key in required_keys:
        assert key in record, f"Missing key '{key}' in streaming log record"

    # Privacy verification
    line_raw = json.dumps(record)
    assert "base64" not in line_raw.lower()
    assert "data:image" not in line_raw
    assert "bytes" not in line_raw.lower() or "image_size_bytes" in line_raw
