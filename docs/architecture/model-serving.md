# FastAPI Model Serving Gateway

## 1. Overview

The VisionStream AI serving layer exposes a production-ready, low-latency HTTP REST API developed with FastAPI. It handles synchronous computer vision inference requests, health checks, readiness probes, and telemetry.

## 2. Serving Architecture

```mermaid
flowchart LR
    Client["Client / Upstream Ingest"] -->|POST /v2/models/{model_name}/infer| API["FastAPI App (src/serving/api.py)"]
    API -->|1. Validate Schema & Extract Image| RequestHandler["Request Handler"]
    RequestHandler -->|2. Route to Engine| Engine["InferenceEngine (src/serving/engine.py)"]
    Engine -->|3. Forward Pass| Model["YOLOv8 Model (data/models/yolov8n.pt)"]
    Model -->|4. Raw Detections| Engine
    Engine -->|5. Format Output| RequestHandler
    RequestHandler -->|6. Record In-Process Metrics| Metrics["Prometheus Registry (/metrics)"]
    RequestHandler -->|7. Emit Structured Event| Logger["Structured Logger (JSONL)"]
    RequestHandler -->|8. HTTP 200 JSON| Client
```

## 3. Endpoints & Protocol

| Endpoint | Method | Purpose | Protocol / Return Type |
| :--- | :--- | :--- | :--- |
| `/health/live` | `GET` | Kubernetes Liveness Probe | `{"status": "alive"}` |
| `/health/ready` | `GET` | Kubernetes Readiness Probe | `{"status": "ready", "models_loaded": [...]}` |
| `/v2/models/{model_name}` | `GET` | Model Metadata | `{"name": "yolov8n", "version": "1.0.0", "framework": "pytorch", ...}` |
| `/v2/models/{model_name}/infer` | `POST` | Inference Request | Multipart form-data image upload -> JSON response |
| `/metrics` | `GET` | Prometheus Scrape Endpoint | Prometheus text format |

> [!NOTE]
> The inference endpoint uses Triton/KServe v2 route naming patterns (`/v2/models/...`) for forward compatibility, but operates over a streamlined multipart form payload rather than raw KServe v2 binary tensor buffers.

## 4. Verification & Testing

The serving implementation has completed full automated test suites:
- **Gate 2 Functional Tests:** 9/9 PASS (health, inference, invalid model handling, invalid image handling).
- **Gate 4 MLOps & Observability Tests:** 12/12 PASS (Prometheus counters, histograms, structured JSONL access logs, trace UUID propagation).
