# VisionStream AI — Sprint 3 Gate 2 Implementation Report
## FastAPI Model Serving Implementation & Triton-Style Contract Verification

- **Project:** VisionStream AI
- **Sprint:** 3
- **Gate:** Gate 2 — FastAPI Model Serving Implementation
- **Date:** 2026-11-10
- **Author:** Senior Python Backend Engineer & ML Infrastructure Engineer
- **Environment:** Development Laptop (Host: LAPTOP-62621JIA, OS: Windows 11, Docker Desktop WSL2, AMD Ryzen 7 6800U, 16GB RAM)
- **Status:** **PASS**

---

## 1. Executive Summary

In Sprint 3 Gate 2, a lightweight, modular, and containerized FastAPI inference serving gateway was successfully implemented for the authoritative `yolov8n.pt` baseline model. The implementation isolates serving dependencies from the existing offline video pipeline, adheres strictly to the single-image stateless detection requirement without modifying stateful ByteTrack video tracking, and enforces Triton-style route naming conventions.

All 11 verification checks passed without errors, the authoritative baseline model SHA256 integrity remained completely intact, and the existing offline pipeline completed 100% of its regression suite without regressions.

---

## 2. Implemented Architecture

The serving architecture separates the API transport layer (FastAPI), schema serialization/validation (Pydantic v2), and inference logic (Modular YOLOv8 CPU Engine):

```
+-------------------------------------------------------------+
|               FastAPI Gateway (src.serving.api)             |
|                                                             |
|   GET  /health/live              (Liveness probe)           |
|   GET  /health/ready             (Readiness probe)          |
|   GET  /v2/models/yolov8n        (Model metadata)           |
|   POST /v2/models/yolov8n/infer  (Multipart image upload)   |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|            Pydantic Schemas (src.serving.schemas)           |
|   - InferenceResponse, Detection, BoundingBox, Metrics       |
|   - HealthResponse, ModelMetadataResponse                   |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|        Modular Engine Abstraction (src.serving.engine)      |
|                                                             |
|   - BaseInferenceEngine (abstract interface)                |
|   - YOLOv8InferenceEngine (CPU inference, thread-safe lock) |
|   - SHA256 verification on load                             |
|   - One-time startup loading & warmup (no per-request load) |
|   - Detection filtering (class_id=0, person only)           |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|        Authoritative Baseline Model (data/models/yolov8n.pt)|
|             Mounted Read-Only (:ro) in Container            |
+-------------------------------------------------------------+
```

Key Design Highlights:
1. **Model Loaded Once at Lifespan Startup:** The YOLO model is verified against its authoritative SHA256 hash, loaded into memory, and warmed up with a blank frame before traffic is served.
2. **Stateless Detection:** Unlike `PersonTracker` in `src/detector.py` which executes ByteTrack tracking, the serving engine utilizes stateless image detection (`model.predict()`), ensuring that concurrent single-image requests have zero state leakage across calls.
3. **Thread Safety:** Inference calls are serialized via a threading lock (`threading.Lock()`) around PyTorch prediction, avoiding internal state corruption.
4. **Safety & Clean Error Handling:** No internal tracebacks or server exceptions are leaked to clients; invalid payloads return standard HTTP 400, 413, or 415 responses with sanitized error details.

---

## 3. Files Created / Modified

### Created Files:
1. `src/serving/__init__.py`: Package init exporting public classes and application.
2. `src/serving/config.py`: Serving configuration and defaults (Pydantic-based).
3. `src/serving/schemas.py`: Request/response schemas according to specification.
4. `src/serving/engine.py`: Modular inference engine interface and YOLOv8 CPU implementation.
5. `src/serving/api.py`: FastAPI application, endpoints, lifecycle, and error handlers.
6. `src/serving/test_serving.py`: Pytest integration suite covering all 9 serving contract requirements.
7. `src/serving/benchmark.py`: Cold vs warm latency benchmark client.
8. `docker/requirements-serving.txt`: Serving-specific python dependencies (`fastapi`, `uvicorn`, `python-multipart`, `pytest`, `requests`, `httpx`).
9. `docker/Dockerfile.serving`: Multi-stage build extending `visionstream-ai:sprint-1`.
10. `docker-compose.serving.yml`: Isolated compose configuration (`visionstream-serving` project).
11. `reports/triton-model-serving-gate2-implementation.md`: This comprehensive implementation report.

### Modified Files:
*None.* Existing `docker-compose.yml`, `requirements.txt`, `src/detector.py`, `src/pipeline.py`, and existing Sprint 1/2 files remain completely untouched.

---

## 4. API Contract

The service implements the following endpoints:

### A. `GET /health/live`
- **Purpose:** Liveness probe.
- **Response:** `200 OK`
```json
{"status": "live"}
```

### B. `GET /health/ready`
- **Purpose:** Readiness probe.
- **Response:** `200 OK` (or `503 Service Unavailable` if model failed to load)
```json
{
  "status": "ready",
  "model_loaded": true,
  "model_name": "yolov8n",
  "device": "cpu"
}
```

### C. `GET /v2/models/yolov8n`
- **Purpose:** Model metadata.
- **Response:** `200 OK`
```json
{
  "name": "yolov8n",
  "versions": ["1"],
  "platform": "ultralytics_pytorch_cpu",
  "inputs": [
    {
      "name": "image",
      "datatype": "BYTES",
      "shape": [-1, -1, 3],
      "content_types": ["image/jpeg", "image/png", "image/webp", "image/bmp"]
    }
  ],
  "outputs": [
    {
      "name": "detections",
      "datatype": "JSON",
      "shape": [-1, 6],
      "target_class": {
        "id": 0,
        "name": "person"
      }
    }
  ]
}
```

### D. `POST /v2/models/yolov8n/infer`
- **Purpose:** Stateless person detection on uploaded image.
- **Parameters:**
  - `image`: Multipart file upload (JPEG/PNG/WEBP/BMP).
  - `conf`: Query param (float, default `0.35`).
  - `iou`: Query param (float, default `0.65`).
- **Response:** `200 OK`
```json
{
  "model_name": "yolov8n",
  "model_version": "1",
  "image_width": 768,
  "image_height": 432,
  "detections": [
    {
      "class_id": 0,
      "class_name": "person",
      "confidence": 0.5932,
      "bbox": {
        "x1": 471.22,
        "y1": 80.61,
        "x2": 557.57,
        "y2": 260.54
      }
    }
  ],
  "metrics": {
    "preprocess_ms": 1.37,
    "inference_ms": 56.77,
    "postprocess_ms": 0.24,
    "total_ms": 58.38
  }
}
```

> [!NOTE]
> The `/v2` route naming adheres to Triton-style conventions for forward compatibility, but the multipart upload payload represents a simplified project-specific contract and is not a claim of complete KServe v2 binary tensor protocol compatibility.

---

## 5. Docker Isolation

The serving deployment is fully isolated from the offline batch video processing container:

| Attribute | Offline Video Pipeline | FastAPI Serving Service |
|---|---|---|
| Compose File | `docker-compose.yml` | `docker-compose.serving.yml` |
| Project Name | `visionstream-ai` | `visionstream-serving` |
| Container Name | `visionstream-ai-runner` | `visionstream-serving-gateway` |
| Image Name | `visionstream-ai:sprint-1` | `visionstream-ai:serving-sprint3` |
| Exposed Port | None | `8085` (host) -> `8000` (internal) |
| Model Mount | `rw` / standard bind | `:ro` (strictly read-only) |
| Dependencies | Base requirements | Base + FastAPI, Uvicorn, Multipart |

---

## 6. Model Integrity Verification

Prior to and following all test executions and benchmarks, the authoritative model file was hashed and verified against the expected SHA256 checksum:

- **Model Path:** `data/models/yolov8n.pt`
- **Expected SHA256:** `f59b3d833e2ff32e194b5bb8e08d211dc7c5bdf144b90d2c8412c47ccfc83b36`
- **Actual Hash Before Tests:** `f59b3d833e2ff32e194b5bb8e08d211dc7c5bdf144b90d2c8412c47ccfc83b36`
- **Actual Hash After Tests:** `f59b3d833e2ff32e194b5bb8e08d211dc7c5bdf144b90d2c8412c47ccfc83b36`
- **Model Policy Status:** **PASS** (Model was mounted read-only, never overwritten or re-exported, and `best.pt` was never used as default).

---

## 7. Functional Test Results

The test suite executed inside the running container (`docker exec visionstream-serving-gateway pytest -v src/serving/test_serving.py`):

| # | Test Name | Description | Status |
|---|---|---|---|
| 1 | `test_1_container_startup_and_model_loading` | Model loaded during lifespan startup and ready | **PASS** |
| 2 | `test_2_health_live` | `GET /health/live` returns 200 `{"status": "live"}` | **PASS** |
| 3 | `test_3_health_ready` | `GET /health/ready` returns 200 and readiness status | **PASS** |
| 4 | `test_4_model_metadata_endpoint` | `GET /v2/models/yolov8n` returns platform, inputs, outputs | **PASS** |
| 5 | `test_5_valid_image_inference_and_schema` | `POST /v2/models/yolov8n/infer` matches Pydantic response schema | **PASS** |
| 6 | `test_6_detection_class_restriction` | Strict restriction to COCO class 0 (`person`) | **PASS** |
| 7 | `test_7_invalid_image_rejection` | Corrupted byte payloads return 400, non-image 415, empty 400 | **PASS** |
| 8 | `test_8_confidence_threshold_behavior` | Higher threshold strictly filters detections | **PASS** |
| 9 | `test_9_model_sha256_integrity` | Model hash matches specification | **PASS** |

**Pytest Summary:** 9 passed, 0 failed in 4.71s.

---

## 8. Performance Benchmark

Benchmark was executed against `http://localhost:8000` inside the serving container with a test image (`768x432` resolution) using 1 cold start request followed by 30 warm requests:

| Benchmark Metric | Measurement (ms) | Notes |
|---|---|---|
| **Cold-Start Wall Latency** | 63.83 ms | Includes client socket connect and request send |
| **Cold-Start Server Total** | 55.70 ms | First infer call after dummy warmup |
| - Preprocess Latency | 1.23 ms | Image byte decode into numpy BGR array |
| - Inference Latency | 54.30 ms | YOLOv8n CPU forward pass |
| - Postprocess Latency | 0.17 ms | Box filtering and schema mapping |
| **Warm Wall Latency (Client Mean)** | 43.09 ms | End-to-end request duration |
| **Warm Wall Latency (Median)** | 42.66 ms | 50th percentile |
| **Warm Wall Latency (P95)** | 50.39 ms | 95th percentile |
| **Warm Server Inference Mean** | 37.31 ms | Pure CPU model execution |
| **Warm Server Inference Median** | 37.06 ms | 50th percentile |
| **Warm Server Inference P95** | 43.05 ms | 95th percentile |
| **Warm Server Total Mean** | 39.04 ms | Total processing time on server |
| **Warm Server Total Median** | 38.80 ms | 50th percentile |
| **Warm Server Total P95** | 44.70 ms | 95th percentile |
| **Detection Count** | 1 (100% consistency) | Detected person with conf=0.5932 |

---

## 9. Regression Test Results

The existing offline video tracking pipeline was tested inside the original `visionstream-ai:sprint-1` container to ensure zero regression:

Command:
`docker run --rm -e PYTHONPATH=/app -v "C:\my-app\visionstream-ai\src:/app/src" -v "C:\my-app\visionstream-ai\data\inputs:/app/data/inputs" -v "C:\my-app\visionstream-ai\data\models:/app/data/models" visionstream-ai:sprint-1 python3 src/test_runner.py`

Results:
- `[TEST 1/5] Verifying CPU PyTorch and OpenCV environment`: **PASS** (PyTorch CPU: 2.15.0+cpu, OpenCV: 4.11.0)
- `[TEST 2/5] Running pipeline execution test (30 frames)`: **PASS** (Processed 30 frames at 9.21 FPS, 46.13 ms avg inference)
- `[TEST 3/5] Verifying annotated video output`: **PASS** (Annotated video generated valid: 199,495 bytes)
- `[TEST 4/5] Verifying structured detection logs format and fields`: **PASS** (10 records logged with all required fields)
- `[TEST 5/5] Verifying ByteTrack tracker assignment`: **PASS** (Valid tracking IDs assigned: `{1}`)

**Regression Summary:** ALL 5 SPRINT 1 INTEGRATION TESTS PASSED SUCCESSFULLY. No regressions observed.

---

## 10. Known Limitations

1. **CPU Inference Bottleneck:** Inference runs entirely on CPU (AMD Ryzen 7 6800U under WSL2). Typical warm inference latency is ~37 ms (~27 FPS theoretical maximum for single concurrent worker).
2. **Synchronous Prediction Lock:** To guarantee thread-safe operation and avoid memory corruption across concurrent requests in Python/PyTorch, inference execution is wrapped in a thread lock. High concurrent traffic will queue requests sequentially.
3. **Multipart Contract:** The API contract uses multipart image uploads instead of KServe v2 raw tensor payloads. This is intended for ease of integration with web/HTTP clients, not direct compatibility with NVIDIA Triton client SDKs.
4. **Development Only:** Testing was performed exclusively on the local development laptop; production hardening (e.g. rate limiting, TLS termination, multi-worker scaling) is intentionally excluded at this gate.

---

## 11. Gate 2 PASS / BLOCKED / FAIL Status

| Requirement / Check | Status | Evidence |
|---|---|---|
| 1. Container startup | **PASS** | Uvicorn running on port 8000, mapped to host 8085 |
| 2. GET `/health/live` | **PASS** | HTTP 200 `{"status": "live"}` |
| 3. GET `/health/ready` | **PASS** | HTTP 200 `{"status": "ready", "model_loaded": true}` |
| 4. GET `/v2/models/yolov8n` | **PASS** | HTTP 200 Triton-style metadata schema |
| 5. POST `/v2/models/yolov8n/infer` | **PASS** | HTTP 200 conforming detection response |
| 6. Invalid image rejection | **PASS** | HTTP 400 (bad bytes/empty), HTTP 415 (unsupported media) |
| 7. Confidence threshold behavior | **PASS** | Detections filter cleanly at higher threshold |
| 8. JSON response schema | **PASS** | Matches Pydantic specification with metrics |
| 9. Detection class restriction | **PASS** | Strict filtering to `class_id = 0` (`person`) |
| 10. Model SHA256 integrity | **PASS** | Checksum verified unchanged before and after tests |
| 11. Existing pipeline regression | **PASS** | 5/5 tests passed in `visionstream-ai:sprint-1` container |

### Overall Verdict: **PASS**

---

## 12. Gate 3 Recommendation

The FastAPI serving service is operating cleanly and satisfies all functional, architectural, and safety requirements of Gate 2.

**Recommendations for Gate 3:**
1. Maintain this service as the CPU baseline serving benchmark.
2. If Triton Server evaluation is explored in Gate 3, ensure it runs in a similarly isolated compose configuration without removing this FastAPI baseline.
3. Keep MLOps and monitoring integrations strictly gated behind explicit user approval.
