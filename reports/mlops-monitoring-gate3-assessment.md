# VisionStream AI — Sprint 3 Gate 3 Assessment Report
## MLOps & Monitoring Architecture and Environment Assessment

- **Project:** VisionStream AI
- **Sprint:** 3
- **Gate:** Gate 3 — MLOps / Monitoring Architecture & Environment Assessment
- **Date:** 2026-11-10
- **Author:** Senior MLOps Engineer & ML Platform Architect
- **Target Environment:** Development Laptop Only (`LAPTOP-62621JIA`, Windows 11, Docker Desktop WSL2, AMD Ryzen 7 6800U, 16GB RAM)
- **Status:** **PASS** (Assessment completed; zero unauthorized code or environment modifications; baseline verified)

---

## 1. Executive Summary

This report delivers a rigorous, **read-only** architectural and operational assessment of MLOps and monitoring options for VisionStream AI. The system currently consists of:
1. An offline video detection & ByteTrack tracking pipeline (`src/pipeline.py`, `src/detector.py`, `src/logger.py`) running in `visionstream-ai:sprint-1`.
2. A newly implemented stateless FastAPI single-image inference serving service (`src/serving/`) running in an isolated Docker container `visionstream-serving-gateway` on port `8085` (`visionstream-ai:serving-sprint3`).
3. Sprint 2 evaluation artifacts comparing baseline `yolov8n.pt` against fine-tuned `best.pt`, where the baseline was authoritatively selected as primary.

### Key Assessment Findings:
- **Zero Modifications Executed:** As mandated, this evaluation is purely analytical. No files were modified, no containers started or stopped, no Docker images pulled, and no packages installed.
- **Model Integrity Verified:** Primary baseline `data/models/yolov8n.pt` SHA256 was verified as `f59b3d833e2ff32e194b5bb8e08d211dc7c5bdf144b90d2c8412c47ccfc83b36` (100% match).
- **Resource Constraints Verified:** Docker Desktop under WSL2 has a hard memory ceiling of ~7.38 GiB (46% of the 16 GiB host RAM). The existing running serving container consumes 339.4 MiB (4.49% of WSL2 limit). Introducing heavyweight microservices (MLflow, Prometheus, Grafana) would incur an additional 1.2–2.5 GiB footprint, creating unnecessary memory pressure on a development laptop.
- **Strategic Recommendation:** We recommend an ultra-lightweight, zero-daemon MLOps pattern:
  - **Inference Monitoring:** FastAPI middleware logging structured JSONL events with UUID request IDs, timing breakdown, and sanitized metadata with log rotation, supplemented by an in-process `/metrics` endpoint using standard Python counters/gauges.
  - **Experiment & Model Tracking:** Lightweight version-controlled JSON/JSONL manifests mapping model SHA256 to Sprint 2 evaluation metrics and serving contract metadata, avoiding a separate database or MLflow server daemon.
  - **Microservices Verdict:** Heavyweight Prometheus + Grafana and MLflow tracking servers are **NOT recommended** for this development laptop tier; they add operational complexity without enhancing portfolio value beyond structured JSONL and self-contained metrics.

---

## 2. Actual Existing Architecture

Direct static inspection of the codebase reveals the actual state of the architecture:

### A. Serving Layer (`src/serving/`)
- [`src/serving/api.py`](file:///c:/my-app/visionstream-ai/src/serving/api.py):
  - Uses FastAPI with `lifespan` context manager.
  - Exposes `GET /health/live`, `GET /health/ready`, `GET /v2/models/yolov8n`, and `POST /v2/models/yolov8n/infer`.
  - Enforces content type validation (`allowed_content_types`) and maximum payload size (15 MB).
  - Sanitizes client exceptions (returns HTTP 400, 413, 415, 500 without internal tracebacks).
- [`src/serving/engine.py`](file:///c:/my-app/visionstream-ai/src/serving/engine.py):
  - Abstract base class `BaseInferenceEngine` defines standard interface (`load_model`, `infer`, `is_ready`, `get_metadata`).
  - Concrete class `YOLOv8InferenceEngine` implements SHA256 integrity verification before loading.
  - Model loaded once at startup; dummy 640x640 frame warmup performed.
  - Prediction executed with `threading.Lock()` to ensure thread safety across concurrent requests.
  - Restricts detections strictly to `class_id == 0` (`person`).
- [`src/serving/schemas.py`](file:///c:/my-app/visionstream-ai/src/serving/schemas.py):
  - Strictly typed Pydantic v2 schemas: `BoundingBox`, `Detection`, `Metrics`, `InferenceResponse`, `ModelMetadataResponse`, `HealthResponse`.
- [`src/serving/config.py`](file:///c:/my-app/visionstream-ai/src/serving/config.py):
  - Centralized Pydantic `ServingConfig` providing defaults (`conf=0.35`, `iou=0.65`, `device="cpu"`).
- [`docker/Dockerfile.serving`](file:///c:/my-app/visionstream-ai/docker/Dockerfile.serving) & [`docker-compose.serving.yml`](file:///c:/my-app/visionstream-ai/docker-compose.serving.yml):
  - Multi-stage build extending `visionstream-ai:sprint-1`.
  - Dedicated Docker Compose project `visionstream-serving`.
  - Exposes port `8085` -> `8000`.
  - Mounts `./src` as `:ro`, `./data/models` as `:ro`, and `./logs` / `./reports` as writeable.

### B. Offline Video Pipeline Layer (`src/`)
- [`src/detector.py`](file:///c:/my-app/visionstream-ai/src/detector.py): Implements `PersonTracker` with stateful ByteTrack.
- [`src/pipeline.py`](file:///c:/my-app/visionstream-ai/src/pipeline.py): Batch video processing, frame extraction, FPS calculation, annotation rendering.
- [`src/logger.py`](file:///c:/my-app/visionstream-ai/src/logger.py): Synchronous structured logging to JSONL/CSV for video tracking records (`stream_id`, `frame_number`, `track_id`, `bbox`).

---

## 3. Current Logging and Metrics Assessment

### Existing Capabilities (Verified Facts):
1. **Per-Request Response Latency:** The serving API currently calculates and returns granular latency in the JSON response:
   - `preprocess_ms`: Time to decode raw image bytes into OpenCV numpy array.
   - `inference_ms`: Time for PyTorch YOLO forward pass.
   - `postprocess_ms`: Time to filter boxes and populate Pydantic models.
   - `total_ms`: End-to-end wall-clock latency inside the engine.
2. **Standard Console Logging:** `src/serving/api.py` configures Python `logging` to standard output for startup, shutdown, and unexpected 500 exceptions.
3. **Health Checks:** Container has a native Docker health check probing `/health/live` every 10 seconds. Liveness and readiness endpoints exist.
4. **Offline Pipeline Logging:** `src/logger.py` writes structured JSONL detection records for video tracking sessions.

### Gaps and Missing Capabilities (Verified Gaps):
1. **No Unique Request ID:** The serving API currently lacks correlation IDs (e.g. `X-Request-ID` or UUIDv4) for distributed tracing and log attribution.
2. **No Persistent Inference Log File:** Inference requests are processed and returned to the HTTP client, but no structured server-side record is persisted to `/app/logs/` or disk.
3. **No Centralized Error Categorization:** Errors (e.g. bad decode, invalid MIME type, oversized payload, timeout) are logged only to console via FastAPI exception handlers without structured error classification.
4. **No Aggregate Operational Metrics:** There is currently no persistent counter for total requests, status code distribution (2xx, 4xx, 5xx), or rolling latency percentiles (P50, P95, P99).

---

## 4. Experiment Tracking Options

| Criterion | Option A: MLflow Tracking Server | Option B: Lightweight JSONL / Manifest | Option C: Existing Markdown/JSON Reports |
|---|---|---|---|
| **CPU Overhead** | Medium (runs web server + SQLite/Postgres backend + artifact receiver) | **Near Zero** (file appends during execution) | **Zero runtime overhead** (static post-hoc reports) |
| **RAM Overhead** | High (250 MB – 600 MB container resident memory) | **Negligible (< 5 MB)** | **Zero runtime RAM** |
| **Storage & Complexity** | High (separate Docker container, database schema, port mappings, artifact volume) | **Low** (plain text JSON files in `reports/` or `logs/`) | **Low** (Markdown + JSON summaries in `reports/`) |
| **Parameter & Metric Capture** | Full UI, run comparisons, charts, artifact browser | Schema-defined JSON/JSONL with run parameters & metrics | Static tables, diff comparisons in markdown |
| **Reproducibility** | High (packaged model checkpoints, env Conda/pip specs) | **High** (SHA256 manifests, fixed seeds, exact version stamps) | **High** (cryptographic hashes, audited evidence directories) |
| **Portfolio Value** | Recognizable enterprise tool, but overkill for 2 offline model runs | Demonstrates engineering discipline and pragmatic resource awareness | Transparent, easily read directly on GitHub without running servers |
| **Verdict** | **NOT RECOMMENDED** for this laptop phase | **RECOMMENDED TARGET** | **CURRENTLY WORKING & COMPLIANT** |

### Recommendation for Experiment Tracking:
Do not introduce an MLflow tracking server container. For a project with two model checkpoints (`yolov8n.pt` and `best.pt`) and offline evaluation, the overhead of MLflow (port management, database migrations, Python package weight) introduces significant friction without adding analytical capability beyond what exists in `evidence/s2.5-model-evaluation/`.

A lightweight **Model Experiment Registry Manifest** (`reports/model_registry.json`) tracking model hash, training parameters, dataset split hashes, and evaluation metrics is the simplest, most reproducible, and robust solution.

---

## 5. Model Versioning Design

### Current Status:
- Model metadata endpoint (`GET /v2/models/yolov8n`) returns `name: "yolov8n"` and `versions: ["1"]`.
- `config.py` hardcodes `expected_sha256 = "f59b3d833e2ff32e194b5bb8e08d211dc7c5bdf144b90d2c8412c47ccfc83b36"`.
- `data/models/best.pt` exists as a research artifact from Sprint 2.4 Gate 2.

### Proposed Versioning Specification:

```
[Model Artifact] ---> [Cryptographic Fingerprint (SHA256)] ---> [Registry Entry (JSON)]
      |                                                                 |
      +--> yolov8n.pt (f59b3d83...) -----> Version "1.0.0" (Baseline / Production Active)
      +--> best.pt    (f42589d8...) -----> Version "1.1.0-ft" (Research / Rejected Candidate)
```

1. **Semantic Versioning Scheme:**
   - `model_name`: `yolov8n`
   - `model_version`: Major.Minor.Patch (e.g. `1.0.0` for baseline release, `1.1.0-ft` for fine-tuned candidate).
2. **Model Provenance Manifest:**
   Every model registered must have an immutable JSON record containing:
   - `model_id`: Unique identifier (e.g., `yolov8n-baseline-coco80-v1`)
   - `artifact_path`: `data/models/yolov8n.pt`
   - `sha256`: Authoritative SHA256 checksum
   - `provenance`: Origin (e.g., `Ultralytics YOLOv8.3 Pretrained COCO`)
   - `target_class_id`: `0` (`person`)
   - `input_shape`: `[640, 640, 3]`
   - `evaluation_summary`: Key metrics from Sprint 2.5 (mAP@50, mAP@50-95, precision, recall)
   - `promotion_status`: `ACTIVE_SERVING` vs `RESEARCH_ARCHIVED`
3. **Model Promotion Policy:**
   - Any new model checkpoint proposed for serving promotion must:
     1. Pass automated SHA256 integrity check.
     2. Complete evaluation on holdout test set with higher operational F1 and mAP than active model.
     3. Maintain CPU inference latency below SLA threshold (< 60 ms mean).
     4. Pass serving contract regression tests.
     5. Be approved via explicit architecture review.

---

## 6. Inference Logging & Monitoring Design

### A. Logging Contract Specification
Inference logging must capture runtime operational metadata **without ever persisting raw image bytes or sensitive pixel content**.

Each inference request should emit a structured JSONL record to `logs/inference_access.jsonl`:

```json
{
  "timestamp": "2026-11-10T14:06:33.123456Z",
  "request_id": "c4b9319a-9861-42ec-a068-d069b8214150",
  "client_ip": "172.18.0.1",
  "endpoint": "/v2/models/yolov8n/infer",
  "http_status": 200,
  "model_name": "yolov8n",
  "model_version": "1.0.0",
  "model_sha256": "f59b3d833e2ff32e194b5bb8e08d211dc7c5bdf144b90d2c8412c47ccfc83b36",
  "image_width": 768,
  "image_height": 432,
  "image_size_bytes": 104230,
  "conf_threshold": 0.35,
  "iou_threshold": 0.65,
  "detection_count": 1,
  "metrics": {
    "preprocess_ms": 1.37,
    "inference_ms": 56.77,
    "postprocess_ms": 0.24,
    "total_ms": 58.38
  },
  "error_category": null
}
```

### B. Error Taxonomy (Error Categorization)
When a request fails, `error_category` is populated with a standard enum:
- `EMPTY_PAYLOAD` (HTTP 400)
- `DECODE_FAILURE` (HTTP 400)
- `UNSUPPORTED_MEDIA_TYPE` (HTTP 415)
- `PAYLOAD_TOO_LARGE` (HTTP 413)
- `SERVICE_UNREADY` (HTTP 503)
- `INFERENCE_EXCEPTION` (HTTP 500)

### C. Log Rotation & Storage Management
- Target log directory: `/app/logs/` (mounted to `./logs`).
- Rotation strategy: Rotating file handler with max file size of 20 MB and retention of 5 backup files (`maxBytes=20971520, backupCount=5`).
- This guarantees maximum disk consumption under 120 MB.

---

## 7. Evaluation Integration Design

To avoid mixing disparate concerns, metrics must be strictly segregated across three operational domains:

```
+-------------------------------------------------------------------------------+
|                       VISIONSTREAM METRIC TAXONOMY                            |
+-------------------------------------------------------------------------------+
| 1. MODEL ACCURACY EVALUATION (Offline Benchmarks / Sprint 2.5)                |
|    - Dataset: 240 Holdout test images, 972 GT persons                        |
|    - Metrics: mAP@50 (0.7532), mAP@50-95 (0.5171), Precision (0.8609),       |
|               Recall (0.5988), F1 (0.7063), False Positive Count (94)         |
|    - Frequency: Static per model release / training trial                     |
+-------------------------------------------------------------------------------+
| 2. INFERENCE PERFORMANCE BENCHMARKING (Serving Gate 2)                        |
|    - Dataset: Synthetic / Sample frames (768x432)                             |
|    - Metrics: Cold-start latency (63.8 ms), Warm Mean (37.3 ms), Median       |
|               (37.1 ms), P95 (43.1 ms), Throughput (~27 req/s theoretical)    |
|    - Frequency: On deployment / container startup verification                |
+-------------------------------------------------------------------------------+
| 3. RUNTIME OPERATIONAL MONITORING (Gate 3/4 Target)                           |
|    - Input: Live production/client HTTP traffic                               |
|    - Metrics: Request count, HTTP 2xx/4xx/5xx rates, Preprocess/Infer/Post    |
|               latencies, Detections per image distribution, Active memory %   |
|    - Frequency: Continuous streaming / per request                            |
+-------------------------------------------------------------------------------+
```

### Linking Mechanism:
The serving service metadata endpoint `GET /v2/models/yolov8n` can be extended to include a reference to the authoritative evaluation report (`SPRINT-02-S2.5-MODEL-EVALUATION-REPORT.md`) and summary baseline accuracy metrics, creating an explicit audit trail linking runtime serving directly back to holdout evaluation results.

---

## 8. Docker Resource & Environment Assessment

### Host and WSL2 Measurements:
- **Host System:** Windows 11 on AMD Ryzen 7 6800U (8 cores, 16 threads, 16 GB Physical RAM).
- **WSL2 Docker Memory Ceiling:** `7.381 GiB` total available.
- **Current Container Footprint (Verified via `docker stats --no-stream`):**
  - Container: `visionstream-serving-gateway`
  - CPU: `0.23%` (idle)
  - Memory: `339.4 MiB / 7.381 GiB` (`4.49%` of WSL2 allocation)
  - PIDs: `34`

### Resource Impact Analysis of Candidate Tools:

| Candidate Component | Memory Overhead (Est.) | CPU Overhead (Est.) | Network / Port Requirements | Impact on Development Laptop |
|---|---|---|---|---|
| **FastAPI Middleware + JSONL** | < 10 MiB | < 0.5% | None (internal to existing process) | **Optimal (Negligible)** |
| **In-Process `/metrics` (Prometheus Client)** | < 15 MiB | < 1.0% | Same port (8085/8000) | **Very Low** |
| **Prometheus Server (Container)** | 250 – 500 MiB | 1.0 – 3.0% | Port `9090`, scrape network | Moderate overhead |
| **Grafana Server (Container)** | 150 – 300 MiB | 0.5 – 2.0% | Port `3000` | Moderate overhead |
| **MLflow Tracking Server (Container)** | 300 – 600 MiB | 1.0 – 4.0% | Port `5000`, backend store | High overhead |
| **Full Stack (Prom + Graf + MLflow)** | **~1.0 – 1.5 GiB** | **~5 – 10%** | Ports 3000, 5000, 8085, 9090 | **Excessive for 16GB dev host** |

### Network and Port Conflict Review:
- Port `8085`: In use by `visionstream-serving-gateway`.
- Port `8080`: Bound to stopped `potensync_web` container.
- Port `3307`: Bound to stopped `potensync_mariadb` container.
- Port `5173`: Bound to stopped `potensync_node` container.
- Ports `3000`, `5000`, `9090`: Currently free on host, but adding them introduces port sprawl and potential collisions with other local development projects.

---

## 9. Recommended Target Architecture

Based on verified resource measurements and engineering trade-offs, we propose the **Lightweight In-Process MLOps Architecture**:

```
+-----------------------------------------------------------------------------+
|                     FastAPI Serving Container (:8085)                      |
|                                                                             |
|  [HTTP Request]                                                             |
|         |                                                                   |
|         v                                                                   |
|  +-----------------------------------------------------------------------+  |
|  | Logging & Tracing Middleware                                          |  |
|  | - Generates request_id (UUID4)                                        |  |
|  | - Times request lifecycle                                             |  |
|  | - Extracts client & payload metadata                                  |  |
|  +-----------------------------------------------------------------------+  |
|         |                                                                   |
|         v                                                                   |
|  +-------------------------------------+   +-----------------------------+  |
|  | Inference Engine                    |   | Prometheus In-Process Store |  |
|  | - YOLOv8 CPU (Lock-protected)       |   | - request_count_total       |  |
|  | - Metrics (pre/infer/post)          |-->| - request_latency_seconds   |  |
|  +-------------------------------------+   | - detections_total          |  |
|         |                                  +-----------------------------+  |
|         v                                                |                  |
|  +-------------------------------------+                 v                  |
|  | Structured JSONL Rotating Logger    |       GET /metrics                 |
|  | -> logs/inference_access.jsonl      |       (Prometheus text format)     |
|  +-------------------------------------+                                    |
+-----------------------------------------------------------------------------+
```

### Architectural Principles:
1. **Zero Additional Containers:** Keep the deployment footprint strictly to the existing single container (`visionstream-serving-gateway`).
2. **Dual-Channel Observability:**
   - **Audit Channel (JSONL):** Full per-request context for debugging, security audits, and offline data drift analysis.
   - **Metrics Channel (`/metrics`):** Standard OpenMetrics/Prometheus formatted endpoint exposed directly from FastAPI using `prometheus-client` or a lightweight ASGI middleware. Can be scraped by external systems if deployed to production, but operates standalone in dev without running Prometheus/Grafana servers.
3. **Model Versioning Manifest (`reports/model_registry.json`):** Static version-controlled registry linking model weights, SHA256 hashes, and Sprint 2.5 holdout accuracy scores.

---

## 10. Risks and Mitigations

| Risk | Probability | Severity | Mitigation Strategy |
|---|---|---|---|
| **Disk Exhaustion via Inference Logs** | Medium | Medium | Implement rotating file handler (`RotatingFileHandler`) capped at 20 MB x 5 files (100 MB max). |
| **Inference Thread-Lock Contention** | Medium | Low (Dev) | Acceptable for single-user dev testing; keep CPU inference batch size 1; serialize requests safely. |
| **Privacy / Data Leakage in Logs** | Low | High | Strictly forbid logging raw image bytes, base64 strings, or file names with personal data. Log only metadata (dimensions, byte size, hash). |
| **Memory Pressure from Unnecessary Daemons** | High | Medium | Reject standalone MLflow, Prometheus, and Grafana containers on this 16GB host; use in-process telemetry. |
| **Model Desynchronization** | Low | High | Maintain hard failure on model SHA256 mismatch during startup; fail fast if model file is tampered with. |

---

## 11. Gate 4 Implementation Recommendation

### Scope for Gate 4 (When Approved):
1. **Implement FastAPI Structured Logging Middleware:**
   - Attach UUID `request_id` to each request and response headers (`X-Request-ID`).
   - Emit structured JSONL records to `/app/logs/inference_access.jsonl`.
2. **Implement Lightweight `/metrics` Endpoint:**
   - Add in-process counters for request counts (by status code), latency histograms, and detection counts.
3. **Implement Model Registry Metadata File:**
   - Create `data/models/model_registry.json` recording `yolov8n.pt` metadata, SHA256, and Sprint 2 evaluation metrics.
4. **Automate Gate 4 Verification Tests:**
   - Pytest suite verifying request ID propagation, JSONL log format validation, `/metrics` output format, and rotation triggers.

---

## 12. PASS / BLOCKED / NOT VERIFIED Status

| Dimension / Check | Status | Evidence / Verification |
|---|---|---|
| 1. Read-Only Policy Adherence | **PASS** | Zero source code, docker, or config files modified. |
| 2. Authoritative Baseline Integrity | **PASS** | SHA256 `f59b3d833e2ff32e194b5bb8e08d211dc7c5bdf144b90d2c8412c47ccfc83b36` verified. |
| 3. Serving Architecture Assessment | **PASS** | Inspected `api.py`, `engine.py`, `schemas.py`, `config.py`. |
| 4. Experiment Tracking Assessment | **PASS** | Evaluated MLflow vs JSONL; concluded JSONL/manifest optimal for dev. |
| 5. Model Versioning Assessment | **PASS** | Defined SemVer scheme, SHA256 linking, and promotion rules. |
| 6. Inference Logging Assessment | **PASS** | Formulated JSONL schema, error taxonomy, and rotation policy. |
| 7. Performance Monitoring Assessment | **PASS** | Evaluated Prometheus/Grafana; recommended in-process `/metrics`. |
| 8. Evaluation Integration Assessment | **PASS** | Segregated Accuracy, Benchmarking, and Operational monitoring. |
| 9. Docker Resource Assessment | **PASS** | Verified via `docker stats` (339.4 MiB current usage; 7.38 GiB limit). |
| 10. Report File Generation | **PASS** | Non-empty report created at `reports/mlops-monitoring-gate3-assessment.md`. |

### Final Gate 3 Verdict: **PASS**

---
> [!IMPORTANT]
> **Next Step:** As mandated by project rules, NO implementation will be performed. System is waiting for ChatGPT architecture review and explicit user approval before proceeding to Gate 4.
