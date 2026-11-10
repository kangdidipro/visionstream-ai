"""
Integration test script for Sprint 1 Docker person detection and tracking pipeline.
Can be executed directly via `python3 src/test_runner.py` inside Docker.
"""
import json
import sys
import tempfile
from pathlib import Path
import cv2

from src.config import PipelineConfig
from src.pipeline import run_pipeline


def run_tests():
    print(">>> [TEST 1/5] Verifying CPU PyTorch and OpenCV environment...")
    import torch
    if torch.cuda.is_available():
        raise AssertionError("PyTorch must run in CPU mode as specified!")
    if not cv2.__version__:
        raise AssertionError("OpenCV failed to initialize!")
    print(f"    PyTorch CPU: {torch.__version__} | OpenCV: {cv2.__version__} -> PASS")

    sample_video = Path("/app/data/inputs/people-detection.mp4")
    if not sample_video.exists():
        raise FileNotFoundError(f"Sample test video not found at {sample_video}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        out_video = tmp_path / "test_out.mp4"
        log_dir = tmp_path / "logs"
        bench_dir = tmp_path / "reports"

        print(">>> [TEST 2/5] Running pipeline execution test (30 frames)...")
        cfg = PipelineConfig(
            stream_id="test-cam-verify",
            tracking_session_id="session-test-01",
            input_video=str(sample_video),
            output_video=str(out_video),
            max_frames=30,
            log_format="jsonl",
            log_dir=str(log_dir),
            benchmark_dir=str(bench_dir)
        )

        summary = run_pipeline(cfg)

        assert summary["processed_frames"] == 30, "Frame count mismatch!"
        assert summary["average_pipeline_fps"] > 0, "FPS must be greater than 0!"
        assert summary["average_inference_latency_ms"] > 0, "Inference latency must be positive!"
        print(f"    Pipeline completed 30 frames at {summary['average_pipeline_fps']} FPS -> PASS")

        print(">>> [TEST 3/5] Verifying annotated video output...")
        assert out_video.exists(), "Output video file was not generated!"
        assert out_video.stat().st_size > 0, "Output video file is empty!"
        cap = cv2.VideoCapture(str(out_video))
        assert cap.isOpened(), "Output video could not be opened by OpenCV!"
        frame_cnt = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        assert frame_cnt == 30, f"Expected 30 frames, got {frame_cnt}"
        cap.release()
        print(f"    Annotated output video valid ({out_video.stat().st_size} bytes, {frame_cnt} frames) -> PASS")

        print(">>> [TEST 4/5] Verifying structured detection logs format and fields...")
        log_file = log_dir / f"detections_{cfg.stream_id}_{cfg.tracking_session_id}.jsonl"
        assert log_file.exists(), "Log file was not generated!"
        assert log_file.stat().st_size > 0, "Log file is empty!"

        with open(log_file, "r", encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]

        assert len(lines) > 0, "No detection records logged!"
        required_fields = [
            "stream_id", "tracking_session_id", "frame_number",
            "timestamp", "track_id", "confidence",
            "bbox_x1", "bbox_y1", "bbox_x2", "bbox_y2"
        ]
        for field in required_fields:
            assert field in lines[0], f"Missing required field '{field}' in log record!"
        assert lines[0]["stream_id"] == "test-cam-verify"
        assert lines[0]["tracking_session_id"] == "session-test-01"
        print(f"    Structured log verification passed ({len(lines)} records logged with all required fields) -> PASS")

        print(">>> [TEST 5/5] Verifying ByteTrack tracker assignment...")
        track_ids = [rec["track_id"] for rec in lines if rec["track_id"] >= 0]
        assert len(track_ids) > 0, "No valid track IDs assigned by ByteTrack!"
        print(f"    Valid tracking IDs assigned: {set(track_ids)} -> PASS")

    print("\n==================================================")
    print(" ALL 5 SPRINT 1 INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("==================================================")


if __name__ == "__main__":
    try:
        run_tests()
    except Exception as exc:
        print(f"\n[TEST ERROR]: {exc}", file=sys.stderr)
        sys.exit(1)
