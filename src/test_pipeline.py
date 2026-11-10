"""
Integration test suite for Sprint 1 Docker person detection and tracking pipeline.
"""
import json
import os
from pathlib import Path
import cv2
import pytest

from src.config import PipelineConfig
from src.pipeline import run_pipeline


@pytest.fixture(scope="module")
def sample_video_path():
    path = Path("/app/data/inputs/people-detection.mp4")
    assert path.exists(), f"Sample test video not found at {path}"
    return str(path)


def test_docker_environment():
    """Verify execution environment inside Docker container."""
    import torch
    assert not torch.cuda.is_available(), "PyTorch must run in CPU mode as specified."
    assert cv2.__version__ is not None, "OpenCV must be installed and functional."


def test_pipeline_execution_and_tracking(sample_video_path, tmp_path):
    """Test short pipeline run: detection, tracking, logging, and video generation."""
    out_video = tmp_path / "test_out.mp4"
    log_dir = tmp_path / "logs"
    bench_dir = tmp_path / "reports"

    cfg = PipelineConfig(
        stream_id="test-cam-verify",
        tracking_session_id="session-pytest-01",
        input_video=sample_video_path,
        output_video=str(out_video),
        max_frames=30,
        log_format="jsonl",
        log_dir=str(log_dir),
        benchmark_dir=str(bench_dir)
    )

    summary = run_pipeline(cfg)

    # 1. Pipeline processed requested frames
    assert summary["processed_frames"] == 30
    assert summary["average_pipeline_fps"] > 0
    assert summary["average_inference_latency_ms"] > 0

    # 2. Output video exists and is valid
    assert out_video.exists()
    assert out_video.stat().st_size > 0
    cap = cv2.VideoCapture(str(out_video))
    assert cap.isOpened()
    assert int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) == 30
    cap.release()

    # 3. Detection logs exist and are structured properly
    log_file = log_dir / f"detections_{cfg.stream_id}_{cfg.tracking_session_id}.jsonl"
    assert log_file.exists()
    assert log_file.stat().st_size > 0

    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) > 0
        first_record = json.loads(lines[0])
        required_fields = [
            "stream_id", "tracking_session_id", "frame_number",
            "timestamp", "track_id", "confidence",
            "bbox_x1", "bbox_y1", "bbox_x2", "bbox_y2"
        ]
        for field in required_fields:
            assert field in first_record, f"Missing field {field} in detection log"

    # 4. Tracking session and stream ID isolation
    assert first_record["stream_id"] == "test-cam-verify"
    assert first_record["tracking_session_id"] == "session-pytest-01"
