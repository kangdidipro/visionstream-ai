"""
Main video processing pipeline orchestrator for VisionStream AI.
Executes frame extraction, person detection, ByteTrack tracking,
annotated video rendering, and structured logging.
"""
import argparse
import json
import time
import uuid
from pathlib import Path
from typing import Dict, Any

import cv2
from tqdm import tqdm

from src.config import PipelineConfig
from src.detector import PersonTracker
from src.logger import DetectionLogger
from src.visualizer import annotate_frame


def run_pipeline(config: PipelineConfig) -> Dict[str, Any]:
    input_path = Path(config.input_video)
    if not input_path.exists():
        raise FileNotFoundError(f"Input video not found: {input_path}")

    # Generate session ID if not provided
    session_id = config.tracking_session_id or f"sess-{uuid.uuid4().hex[:8]}"

    # Open video capture
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video file: {input_path}")

    video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    video_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_duration_sec = total_video_frames / video_fps if video_fps > 0 else 0.0

    target_frames = total_video_frames
    if config.max_frames > 0:
        target_frames = min(config.max_frames, total_video_frames)

    # Prepare output video writer
    output_writer = None
    if config.output_video:
        out_path = Path(config.output_video)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        # Use mp4v or avc1 codec
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        output_writer = cv2.VideoWriter(
            str(out_path),
            fourcc,
            video_fps,
            (video_width, video_height)
        )

    # Prepare structured logger
    log_ext = config.log_format
    log_filename = f"detections_{config.stream_id}_{session_id}.{log_ext}"
    log_full_path = Path(config.log_dir) / log_filename
    logger = DetectionLogger(log_full_path, log_format=config.log_format)

    # Initialize tracker
    tracker = PersonTracker(
        model_path=config.model_path,
        conf_threshold=config.conf_threshold,
        iou_threshold=config.iou_threshold,
        tracker_type=config.tracker_type,
        target_class_id=config.target_class_id
    )

    print("=" * 60)
    print(" VISIONSTREAM AI - PIPELINE EXECUTION")
    print(f" Stream ID            : {config.stream_id}")
    print(f" Tracking Session ID  : {session_id}")
    print(f" Input Video          : {config.input_video}")
    print(f" Resolution & FPS     : {video_width}x{video_height} @ {video_fps:.2f} FPS")
    print(f" Processing Frames    : {target_frames} / {total_video_frames}")
    print(f" Output Video         : {config.output_video or 'None'}")
    print(f" Detection Log        : {log_full_path}")
    print("=" * 60)

    # Metrics collectors
    pipeline_start_time = time.perf_counter()
    inference_times_ms = []
    frame_processing_times_sec = []
    unique_track_ids = set()
    total_detections_logged = 0

    frame_idx = 0
    pbar = tqdm(total=target_frames, desc="Processing Frames", unit="frame")

    try:
        while cap.isOpened() and frame_idx < target_frames:
            f_start = time.perf_counter()
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            # Calculate video timestamp in seconds
            timestamp_sec = round(frame_idx / video_fps, 4)

            # Detection & Tracking
            tracks, infer_ms = tracker.process_frame(frame, persist=True)
            inference_times_ms.append(infer_ms)

            # Log tracks
            for t in tracks:
                trk_id = t["track_id"]
                if trk_id >= 0:
                    unique_track_ids.add(trk_id)

                record = {
                    "stream_id": config.stream_id,
                    "tracking_session_id": session_id,
                    "frame_number": frame_idx,
                    "timestamp": timestamp_sec,
                    "track_id": trk_id,
                    "confidence": round(t["confidence"], 4),
                    "bbox_x1": round(t["bbox"][0], 2),
                    "bbox_y1": round(t["bbox"][1], 2),
                    "bbox_x2": round(t["bbox"][2], 2),
                    "bbox_y2": round(t["bbox"][3], 2),
                }
                logger.log_record(record)
                total_detections_logged += 1

            # Annotate and write output frame
            f_duration = time.perf_counter() - f_start
            frame_processing_times_sec.append(f_duration)
            current_fps = 1.0 / f_duration if f_duration > 0 else 0.0

            if output_writer is not None:
                annotated = annotate_frame(
                    frame=frame,
                    tracks=tracks,
                    frame_number=frame_idx,
                    fps=current_fps,
                    active_count=len(tracks)
                )
                output_writer.write(annotated)

            frame_idx += 1
            pbar.update(1)

    finally:
        cap.release()
        if output_writer is not None:
            output_writer.release()
        logger.close()
        pbar.close()

    total_pipeline_time_sec = time.perf_counter() - pipeline_start_time
    avg_fps = frame_idx / total_pipeline_time_sec if total_pipeline_time_sec > 0 else 0.0
    avg_inference_time_ms = sum(inference_times_ms) / len(inference_times_ms) if inference_times_ms else 0.0
    avg_pipeline_latency_ms = (sum(frame_processing_times_sec) / len(frame_processing_times_sec) * 1000.0) if frame_processing_times_sec else 0.0

    benchmark_summary = {
        "stream_id": config.stream_id,
        "tracking_session_id": session_id,
        "video_duration_sec": round(video_duration_sec, 2),
        "total_video_frames": total_video_frames,
        "processed_frames": frame_idx,
        "total_pipeline_time_sec": round(total_pipeline_time_sec, 3),
        "average_pipeline_fps": round(avg_fps, 2),
        "average_inference_latency_ms": round(avg_inference_time_ms, 2),
        "average_pipeline_frame_latency_ms": round(avg_pipeline_latency_ms, 2),
        "unique_track_ids_count": len(unique_track_ids),
        "unique_track_ids": sorted(list(unique_track_ids)),
        "total_detections_logged": total_detections_logged,
        "model_path": config.model_path,
        "conf_threshold": config.conf_threshold,
        "iou_threshold": config.iou_threshold,
        "input_video": config.input_video,
        "output_video": config.output_video,
        "log_path": str(log_full_path)
    }

    # Save benchmark summary JSON in benchmark_dir
    benchmark_dir = Path(config.benchmark_dir)
    benchmark_dir.mkdir(parents=True, exist_ok=True)
    bench_file = benchmark_dir / f"benchmark_{config.stream_id}_{session_id}.json"
    with open(bench_file, "w", encoding="utf-8") as f:
        json.dump(benchmark_summary, f, indent=2)

    print("\n" + "=" * 60)
    print(" BENCHMARK & EXECUTION SUMMARY")
    print(f" Video Duration               : {benchmark_summary['video_duration_sec']} s")
    print(f" Total Frames Processed       : {benchmark_summary['processed_frames']}")
    print(f" Total Processing Time        : {benchmark_summary['total_pipeline_time_sec']} s")
    print(f" Average Processing FPS       : {benchmark_summary['average_pipeline_fps']} FPS")
    print(f" Average Inference Latency    : {benchmark_summary['average_inference_latency_ms']} ms / frame")
    print(f" Average Pipeline Frame Latency: {benchmark_summary['average_pipeline_frame_latency_ms']} ms / frame")
    print(f" Unique Tracking IDs Count    : {benchmark_summary['unique_track_ids_count']}")
    print(f" Total Detections Logged      : {benchmark_summary['total_detections_logged']}")
    print(f" Benchmark JSON Saved         : {bench_file}")
    print("=" * 60)

    return benchmark_summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VisionStream AI Person Detection & Tracking")
    parser.add_argument("--input", "-i", type=str, default="/app/data/inputs/people-detection.mp4", help="Path to input video")
    parser.add_argument("--output", "-o", type=str, default="/app/data/outputs/annotated_tracking.mp4", help="Path to output video")
    parser.add_argument("--stream-id", type=str, default="stream-cam-01", help="Camera / Stream identifier")
    parser.add_argument("--session-id", type=str, default="", help="Tracking session identifier")
    parser.add_argument("--model", type=str, default="/app/data/models/yolov8n.pt", help="Path to YOLO weights")
    parser.add_argument("--conf", type=float, default=0.35, help="Confidence threshold")
    parser.add_argument("--iou", type=float, default=0.5, help="IoU threshold")
    parser.add_argument("--max-frames", type=int, default=0, help="Max frames to process (0 = all)")
    parser.add_argument("--log-format", type=str, default="jsonl", choices=["jsonl", "csv"], help="Log format")
    parser.add_argument("--log-dir", type=str, default="/app/logs", help="Log output directory")
    parser.add_argument("--report-dir", type=str, default="/app/reports", help="Report/Benchmark output directory")

    args = parser.parse_args()

    pipeline_cfg = PipelineConfig(
        stream_id=args.stream_id,
        tracking_session_id=args.session_id,
        model_path=args.model,
        conf_threshold=args.conf,
        iou_threshold=args.iou,
        input_video=args.input,
        output_video=args.output,
        max_frames=args.max_frames,
        log_format=args.log_format,
        log_dir=args.log_dir,
        benchmark_dir=args.report_dir
    )

    run_pipeline(pipeline_cfg)
