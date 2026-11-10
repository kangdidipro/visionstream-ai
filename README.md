# VISIONSTREAM AI
### Real-Time Computer Vision & Video Analytics Engineering Portfolio

A practical, production-grade Computer Vision engineering repository demonstrating **YOLOv8 object detection, rigorous model evaluation, TensorRT FP16 acceleration, FastAPI model serving, live RTSP ingestion with GStreamer, ByteTrack multi-object tracking, and lightweight MLOps observability**.

Developed and maintained by **Ahadi Hamijaya**.

---

## 1. Project Overview

VisionStream AI is a full-lifecycle Computer Vision and video analytics project designed to bridge the gap between machine learning models and robust deployment engineering.

Rather than presenting isolated Jupyter notebooks or synthetic benchmarks, this repository documents real-world engineering decisions:
- Conducting controlled holdout evaluations and honestly rejecting regressed fine-tuned models.
- Demonstrating a **2.04x speedup (263 FPS)** with **TensorRT FP16** on NVIDIA Tesla T4 GPU hardware.
- Containerizing low-latency **FastAPI model serving** with SHA256 cryptographic model verification and Prometheus instrumentation.
- Implementing an **RTSP video pipeline** using **MediaMTX**, **GStreamer**, and **ByteTrack** with automated disconnect recovery.
- Benchmarking **ONNX Runtime CPU** optimizations, revealing a **25x improvement in cold-start latency**.

---

## 2. Technology Stack

- **Computer Vision & Tracking:** Ultralytics YOLOv8, OpenCV 4.11, ByteTrack, NumPy
- **Serving & Microservices:** FastAPI, Uvicorn, Pydantic, GStreamer 1.26 (PyGObject), MediaMTX, FFmpeg
- **Optimization & Acceleration:** TensorRT 10.x, ONNX 1.23, ONNX Runtime 1.31, `onnxslim`, CUDA 12.2
- **MLOps & Observability:** Prometheus client (`/metrics`), Python `logging` with structured JSONL, Trace UUIDs
- **Infrastructure & Containerization:** Docker, Docker Compose, WSL2 Linux, Git

---

## 3. End-to-End System Architecture

```mermaid
flowchart TD
    subgraph RTSP Stream Ingestion & Multi-Object Tracking
        SRC["Video Stream Source\n(FFmpeg / RTSP Camera)"] -->|H.264 over TCP| MTX["MediaMTX RTSP Server\n(:8554/live/stream)"]
        MTX -->|TCP RTSP Stream| GST["GStreamer Ingestion\n(rtspsrc ! rtph264depay ! avdec_h264)"]
        GST -->|Decoded RGB Frames| FP["Frame Processor\n(Letterbox 640x640)"]
        FP -->|Batched Frames| DET["YOLOv8 Object Detector\n(yolov8n.pt)"]
        DET -->|Detections| TRACK["ByteTrack Association\n(Track IDs & Trajectories)"]
        TRACK -->|Stream Telemetry| SLOG["Stream Metrics & Drop Logger"]
    end

    subgraph FastAPI Model Serving Gateway
        API_REQ["Client Application / Ingest Service"] -->|POST /v2/models/{model}/infer| API["FastAPI Gateway (:8085)"]
        API -->|Validate SHA256| REG["Model Registry"]
        API -->|Inference Execution| ENG["Inference Engine\n(PyTorch / ONNX)"]
        ENG -->|Boxes & Scores| API
        API -->|Expose Metrics| PROM["Prometheus /metrics"]
        API -->|Structured JSONL| ALOG["logs/serving_access.jsonl"]
    end
```

---

## 4. Key Engineering Achievements

### A. Rigorous Holdout Model Evaluation & Engineering Honesty
- Evaluated YOLOv8 baseline (`yolov8n.pt`) against a fine-tuned candidate (`best.pt`) on an authoritative 240-image holdout set (972 ground-truth annotated persons).
- **Result:** Baseline YOLOv8n outperformed the fine-tuned model (**75.32% vs 69.44% mAP@50**; **51.71% vs 44.25% mAP@50-95**).
- **Engineering Decision:** Reject `best.pt` for production serving; retain it strictly as a research artifact. We transparently report performance regressions rather than claiming unvalidated model improvements.
- *Detailed Evidence:* [Model Evaluation Report](docs/evaluation/model-evaluation.md)

### B. NVIDIA Tesla T4 GPU & TensorRT FP16 Acceleration
- Executed controlled in-memory inference benchmarks on an NVIDIA Tesla T4 GPU in a cloud Linux environment.
- **Speedup:** TensorRT FP16 achieved a **2.04x speedup** over PyTorch FP32 (**3.79 ms vs 7.72 ms** mean latency; **263.27 FPS vs 129.43 FPS**).
- *Engineering Note:* Metrics reflect isolated in-memory model compute passes, distinguishing model throughput from end-to-end network video streaming.
- *Detailed Evidence:* [GPU & TensorRT Benchmark](docs/evaluation/gpu-tensorrt-benchmark.md)

### C. Containerized FastAPI Model Serving Gateway
- Engineered a lightweight, thread-safe FastAPI inference gateway running in Docker (`:8085`).
- Features `/health/live`, `/health/ready`, model metadata inspection, and multipart image inference.
- Cryptographically validates model weights via SHA256 prior to initialization.
- Passed 100% of integration test suites (Gate 2: 9/9 PASS; Gate 4: 12/12 PASS).
- *Detailed Evidence:* [Model Serving Architecture](docs/architecture/model-serving.md)

### D. RTSP Video Streaming with GStreamer & ByteTrack
- Deployed a containerized streaming ecosystem with MediaMTX and GStreamer H.264 decoding.
- **Measured Throughput:** Ingestion verified at **12.02 FPS**; full downstream computer vision analytics (YOLOv8 + ByteTrack) measured at **5.51 FPS** on local CPU.
- Configured real-time frame-dropping backpressure policies (`appsink drop=true max-buffers=2`) to guarantee low latency.
- Verified automatic stream recovery against abrupt RTSP source disconnects.
- *Detailed Evidence:* [Streaming Pipeline Architecture](docs/architecture/streaming-pipeline.md)

### E. ONNX Runtime CPU Benchmark & Multi-Thread Scaling
- Benchmarked `yolov8n.onnx` (Opset 17, 12.26 MB) against PyTorch CPU across 100 measured iterations.
- **Cold-Start Latency:** ONNX Runtime executed its first inference in **144.65 ms** vs PyTorch's **3,616.02 ms** (**25x faster cold start**).
- **Throughput & Tail Latency:** Steady-state throughput remained comparable (PyTorch 11.63 FPS vs ORT 10.84 FPS), while ORT multi-threading yielded lower P95 latency (98.52 ms at 4 threads).
- *Detailed Evidence:* [ONNX Runtime CPU Benchmark](docs/evaluation/onnx-runtime-benchmark.md)

---

## 5. Quantitative Results Summary

<!-- Records-per-page filter: 5, 10, 30, 50, 100, 200, 300, All -->
| Component | Metric | Baseline / PyTorch | Optimized / Accelerated | Delta / Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **Model Accuracy** | Holdout mAP@50 | **75.32%** (Baseline) | 69.44% (Fine-tuned) | Baseline retained; regression documented |
| **GPU Inference** | Mean Latency (T4) | 7.72 ms (PyTorch FP32) | **3.79 ms** (TensorRT FP16) | **2.04x speedup (263.27 FPS)** |
| **CPU Cold Start** | Initial Latency | 3,616.02 ms | **144.65 ms** (ONNX Runtime) | **25x faster cold start** |
| **CPU P95 Latency**| Jitter Tail (4 Thr)| 132.85 ms | **98.52 ms** (ONNX Runtime) | **-25.8% latency jitter** |
| **RTSP Ingestion** | Network Ingest | 12.00 FPS (Target) | **12.02 FPS** (Verified) | Perfect source synchronization |
| **Live Tracking** | CPU End-to-End | N/A | **5.51 FPS** (YOLOv8 + ByteTrack) | CPU-bound ceiling; backpressure drop active |

---

## 6. Architecture Decisions & Trade-Offs

- **PyTorch CPU Default vs. ONNX Runtime:** While ONNX Runtime provides a 25x faster cold start, steady-state throughput is equivalent on AMD Ryzen CPUs (~11 FPS). PyTorch CPU is retained as default for developer ergonomics, keeping ONNX ready for cold-start critical deployments.
- **Local FastAPI vs. Triton Inference Server:** Triton was assessed and deferred for the local AMD CPU environment. Running Triton CPU backend adds ~1.5 GB memory overhead without compute acceleration. Triton is reserved for multi-GPU cloud environments.
- **Real-Time Video Latency vs. Frame Retention:** In surveillance streams, fresh frames take precedence over backlog processing. Older frames are safely dropped when inference falls behind source frame rates.
- *Detailed Evidence:* [Architecture Decision Records (ADRs)](docs/engineering/architecture-decisions.md)

---

## 7. Repository Structure

```text
visionstream-ai/
├── data/
│   └── models/                      # Authoritative model storage (SHA256 verified)
│       └── optimized/onnx/          # Exported ONNX runtime artifacts
├── docker/
│   ├── Dockerfile                   # Base CPU computer vision image
│   ├── Dockerfile.serving           # FastAPI model serving gateway image
│   ├── Dockerfile.streaming         # GStreamer & streaming ingest image
│   └── mediamtx.yml                 # MediaMTX RTSP broker configuration
├── docs/
│   ├── architecture/                # System, serving, and streaming architecture docs
│   ├── evaluation/                  # Model holdout, TensorRT, and ONNX benchmarks
│   ├── engineering/                 # MLOps observability and ADRs
│   └── project/                     # Roadmap and sprint history
├── eval_tools/                      # Isolated evaluation and benchmark engines
├── notebooks/                       # Google Colab & Kaggle GPU experiment notebooks
├── reports/                         # Authoritative audit reports and benchmark data
├── src/
│   ├── serving/                     # FastAPI app, inference engine, schemas, metrics
│   ├── streaming/                   # RTSP client, GStreamer ingest, ByteTrack
│   ├── detector.py                  # Core YOLOv8 inference wrapper
│   └── pipeline.py                  # Offline pipeline coordinator
├── docker-compose.serving.yml       # Model serving service compose file
├── docker-compose.streaming.yml     # MediaMTX + RTSP streaming compose file
├── requirements.txt                 # Project dependencies
└── README.md                        # Portfolio documentation landing page
```

---

## 8. Reproducibility & Quickstart

### Prerequisites
- Docker Desktop with WSL2 (Linux containers)
- Python 3.11+ (for local inspection)

### A. Run Model Serving Gateway
```bash
# Start FastAPI serving container on port 8085
docker compose -f docker-compose.serving.yml up -d

# Verify readiness probe
curl http://localhost:8085/health/ready

# Inspect Prometheus metrics
curl http://localhost:8085/metrics
```

### B. Run RTSP Streaming Pipeline
```bash
# Start MediaMTX, RTSP publisher, and GStreamer ingestion
docker compose -f docker-compose.streaming.yml up -d

# View live streaming ingestion logs
docker compose -f docker-compose.streaming.yml logs -f streaming-ingest
```

---

## 9. Current Limitations & Scope

- **CPU-Bound End-to-End Analytics:** Full analytics (YOLOv8n + ByteTrack) operates at **5.51 FPS** on local CPU. True 30 FPS video analytics requires NVIDIA GPU acceleration (e.g., DeepStream/TensorRT).
- **Single Stream Ingestion:** Multi-camera horizontal scalability has been designed architecturally but not benchmarked across multi-stream hardware.
- **REST Inference Protocol:** The custom API employs Triton-style route conventions but uses multipart image payloads rather than the binary KServe v2 tensor protocol.

---

## 10. Author & Professional Background

**Ahadi Hamijaya**  
*Senior IT Project Manager & Computer Vision Engineer*  
- **Background:** Proven track record in IT project management and telecommunications infrastructure, coupled with hands-on expertise in applied Computer Vision and MLOps.
- **Specializations:** YOLO object detection, inference optimization (TensorRT / ONNX Runtime), video streaming pipelines (GStreamer / RTSP), and production ML model serving.
- **GitHub:** [https://github.com/kangdidipro](https://github.com/kangdidipro)
