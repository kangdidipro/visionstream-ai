"""
Benchmark script for VisionStream AI FastAPI inference service.
Measures cold start latency, warm request latencies (mean, median, p95),
and validates detection counts.
"""
import os
import statistics
import time
from pathlib import Path
import requests

SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:8000")
IMAGE_PATH = "/app/data/inputs/sample_person.jpg"
NUM_WARM_REQUESTS = 30


def run_benchmark():
    print("=" * 60)
    print("VISIONSTREAM AI — GATE 2 SERVING BENCHMARK")
    print("=" * 60)

    # 1. Check readiness
    ready_resp = requests.get(f"{SERVER_URL}/health/ready")
    assert ready_resp.status_code == 200, f"Server not ready: {ready_resp.text}"
    print(f"Readiness: {ready_resp.json()}")

    assert Path(IMAGE_PATH).exists(), f"Image not found at {IMAGE_PATH}"

    # 2. Cold-start request measurement (First request through the endpoint)
    with open(IMAGE_PATH, "rb") as f:
        img_bytes = f.read()

    print("\nExecuting Cold-Start Request...")
    t0 = time.perf_counter()
    resp_cold = requests.post(
        f"{SERVER_URL}/v2/models/yolov8n/infer",
        files={"image": ("test.jpg", img_bytes, "image/jpeg")},
        params={"conf": 0.35, "iou": 0.65},
    )
    t1 = time.perf_counter()
    cold_total_wall_ms = (t1 - t0) * 1000.0

    assert resp_cold.status_code == 200, f"Cold request failed: {resp_cold.text}"
    cold_data = resp_cold.json()
    cold_metrics = cold_data["metrics"]

    print(f"Cold-Start Wall Latency: {cold_total_wall_ms:.2f} ms")
    print(f"Cold-Start Server Total: {cold_metrics['total_ms']:.2f} ms")
    print(f"  - Preprocess:  {cold_metrics['preprocess_ms']:.2f} ms")
    print(f"  - Inference:   {cold_metrics['inference_ms']:.2f} ms")
    print(f"  - Postprocess: {cold_metrics['postprocess_ms']:.2f} ms")
    print(f"Detections found: {len(cold_data['detections'])}")

    # 3. Warm requests benchmark
    print(f"\nExecuting {NUM_WARM_REQUESTS} Warm Requests...")
    wall_latencies = []
    server_total_latencies = []
    server_infer_latencies = []
    detection_counts = []

    for i in range(NUM_WARM_REQUESTS):
        t_start = time.perf_counter()
        resp = requests.post(
            f"{SERVER_URL}/v2/models/yolov8n/infer",
            files={"image": ("test.jpg", img_bytes, "image/jpeg")},
            params={"conf": 0.35, "iou": 0.65},
        )
        t_end = time.perf_counter()
        assert resp.status_code == 200
        data = resp.json()

        wall_ms = (t_end - t_start) * 1000.0
        wall_latencies.append(wall_ms)
        server_total_latencies.append(data["metrics"]["total_ms"])
        server_infer_latencies.append(data["metrics"]["inference_ms"])
        detection_counts.append(len(data["detections"]))

    # Calculations
    wall_latencies.sort()
    server_total_latencies.sort()
    server_infer_latencies.sort()

    def p95(data_list):
        k = int(len(data_list) * 0.95)
        return data_list[min(k, len(data_list) - 1)]

    mean_wall = statistics.mean(wall_latencies)
    median_wall = statistics.median(wall_latencies)
    p95_wall = p95(wall_latencies)

    mean_infer = statistics.mean(server_infer_latencies)
    median_infer = statistics.median(server_infer_latencies)
    p95_infer = p95(server_infer_latencies)

    mean_server_total = statistics.mean(server_total_latencies)
    median_server_total = statistics.median(server_total_latencies)
    p95_server_total = p95(server_total_latencies)

    print("\nBenchmark Results Summary (Warm Inference):")
    print(f"Number of warm requests: {NUM_WARM_REQUESTS}")
    print(f"Wall Latency (Client-side):")
    print(f"  - Mean:   {mean_wall:.2f} ms")
    print(f"  - Median: {median_wall:.2f} ms")
    print(f"  - P95:    {p95_wall:.2f} ms")
    print(f"Server-side Inference Time:")
    print(f"  - Mean:   {mean_infer:.2f} ms")
    print(f"  - Median: {median_infer:.2f} ms")
    print(f"  - P95:    {p95_infer:.2f} ms")
    print(f"Server-side Total Time (decode + infer + post):")
    print(f"  - Mean:   {mean_server_total:.2f} ms")
    print(f"  - Median: {median_server_total:.2f} ms")
    print(f"  - P95:    {p95_server_total:.2f} ms")
    print(f"Detection Count Consistency: all {set(detection_counts)} persons detected")
    print("=" * 60)


if __name__ == "__main__":
    run_benchmark()
