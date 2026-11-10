# VisionStream AI — Sprint 3 Gate 8
# ONNX Runtime CPU Optimization & Benchmark Report

## 1. Executive Summary

- **Gate Status:** COMPLETED / EVALUATION CONCLUDED
- **Evaluation Target:** Assess whether **ONNX Runtime (ORT) CPU** provides a measurable performance advantage over **PyTorch CPU** for the VisionStream AI baseline model (`yolov8n.pt`).
- **Target Environment:** Development Laptop Only (`LAPTOP-62621JIA`, AMD Ryzen 7 6800U @ 2.7–4.7 GHz, 8C/16T, 16GB RAM, WSL2 Docker memory limit ~7.38 GiB, CPU execution only).
- **Core Recommendation:** **SELECTIVE / DEFERRED ADOPTION**.
  - ONNX Runtime direct Python inference exhibits **similar steady-state latency** to PyTorch CPU (92.21 ms vs 85.95 ms end-to-end; 89.78 ms vs 85.95 ms inference core).
  - However, ONNX Runtime demonstrates a **dramatic advantage in cold start latency** (144.65 ms vs 3,616.02 ms — an improvement of **25x**) and lower P95 jitter when multi-threaded (P95 of 98.52 ms at 4 threads vs PyTorch P95 of 132.85 ms).
  - High-level wrappers (`ultralytics` with ONNX backend) suffer substantial Python glue overhead (240.29 ms, 4.16 FPS).
  - **Verdict:** Do NOT replace PyTorch with ONNX Runtime in the main FastAPI serving engine immediately for steady-state throughput alone; maintain PyTorch CPU as default for developer ergonomics while keeping the validated ONNX artifact ready for cold-start critical or standalone C++/embedded deployment tiers.

---

## 2. Environment & Authoritative Baseline Integrity

| Component | Authoritative Expected Value | Verified Execution Value | Status |
| :--- | :--- | :--- | :--- |
| **Host Machine** | `LAPTOP-62621JIA` | `LAPTOP-62621JIA` (AMD Ryzen 7 6800U) | MATCH |
| **OS** | Windows 11 + Docker Desktop / WSL2 | Windows 11 + Docker Desktop / WSL2 | MATCH |
| **WSL2 Memory Ceiling** | ~7.38 GiB | ~7.38 GiB | MATCH |
| **Primary Baseline Model** | `data/models/yolov8n.pt` | SHA256: `f59b3d833e2ff32e194b5bb8e08d211dc7c5bdf144b90d2c8412c47ccfc83b36` | **VERIFIED UNCHANGED** |
| **Research Baseline Model** | `data/models/best.pt` | SHA256: `41d74cb7e4288a526d9bf4d092343e12fa61acc7e4d1dac76c82593c7bd715ef` | **VERIFIED UNTOUCHED** |
| **Exported Artifact** | `data/models/optimized/onnx/yolov8n.onnx` | SHA256: `b59f7372ed3f05934a13241c7965f1e66b40d0ea3f5fff09c89878c491bc8d3d` | **ISOLATED & VERIFIED** |

---

## 3. ONNX Model Export Details

The ONNX artifact was generated strictly in isolation via `eval_tools/export_onnx.py` using a dedicated benchmark container (`visionstream-ai:benchmark-sprint3`):

- **Source File:** `data/models/yolov8n.pt` (6,549,796 bytes)
- **Target File:** `data/models/optimized/onnx/yolov8n.onnx` (12,851,104 bytes, 12.26 MB)
- **Export Framework:** PyTorch 2.15.0+cpu -> ONNX 1.23.2 -> `onnxslim` 0.1.99
- **ONNX Opset:** 17
- **Input Tensor:** `images` — Shape: `[1, 3, 640, 640]` (Float32, BCHW, 0.0–1.0 normalized)
- **Output Tensor:** `output0` — Shape: `[1, 84, 8400]` (Float32, bounding boxes + 80 COCO classes)
- **Model Check:** `onnx.checker.check_model()` passed with 0 errors.

---

## 4. Benchmark Methodology & Results

### 4.1 Test Configuration
- **Input Image:** `data/inputs/sample_person.jpg` (768 x 432 RGB, extracted from project video).
- **Inference Preprocessing:** 640x640 Letterbox with symmetric padding, RGB normalized `[0, 1]`.
- **Detection Parameters:** Confidence threshold = `0.35`, NMS IoU threshold = `0.65`, Class = `0` (`person`).
- **Warmup:** 30 complete inference cycles prior to recording.
- **Sample Size:** 100 consecutive timed iterations.

### 4.2 Comparative Latency & Throughput Benchmark

<!-- Records-per-page filter: 5, 10, 30, 50, 100, 200, 300, All -->
| Metric | PyTorch CPU (`torch 2.15.0`) | ONNX Runtime CPU Direct (`ort 1.31.1`) | Ultralytics ONNX Engine Wrapper | Difference (ORT Direct vs PyTorch) |
| :--- | :--- | :--- | :--- | :--- |
| **Model Init Time** | 227.70 ms | 171.92 ms | 29.23 ms | **-55.78 ms (-24.5%)** |
| **Cold Start Latency (1st call)** | 3,616.02 ms | 144.65 ms | N/A | **-3,471.37 ms (-96.0% / 25x faster)** |
| **Mean Latency (Warm)** | 85.95 ms | 92.21 ms (89.78 ms infer only) | 240.29 ms | +6.26 ms (+7.3%) |
| **Median Latency** | 78.44 ms | 89.63 ms | 227.95 ms | +11.19 ms (+14.3%) |
| **P95 Latency** | 132.85 ms | 115.03 ms (112.73 ms infer only) | 357.54 ms | **-17.82 ms (-13.4% less jitter)** |
| **P99 Latency** | 165.69 ms | 131.85 ms | N/A | **-33.84 ms (-20.4%)** |
| **Throughput (FPS)** | 11.63 FPS | 10.84 FPS (11.14 FPS infer only) | 4.16 FPS | -0.79 FPS (-6.8%) |
| **Memory Footprint (RSS)** | ~185 MB | ~168 MB | ~210 MB | **-17 MB (-9.2%)** |

### 4.3 Multi-Threading Scaling (ONNX Runtime CPU)

Evaluated across varying intra-op thread allocations on the 8-core / 16-thread AMD Ryzen 7 6800U processor:

<!-- Records-per-page filter: 5, 10, 30, 50, 100, 200, 300, All -->
| Thread Count | Mean Latency (ms) | Median Latency (ms) | P95 Latency (ms) | Throughput (FPS) | Scaling Efficiency |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1 Thread** | 198.01 ms | 195.48 ms | 216.78 ms | 5.05 FPS | 1.00x (Baseline) |
| **2 Threads** | 114.93 ms | 112.17 ms | 134.25 ms | 8.70 FPS | 1.72x |
| **4 Threads** | 84.33 ms | 83.25 ms | 98.52 ms | 11.86 FPS | 2.35x (Optimal sweet spot) |
| **8 Threads** | 78.39 ms | 72.60 ms | 118.57 ms | 12.76 FPS | 2.53x (Diminishing return / higher P95) |

---

## 5. Output Consistency & Precision Analysis

To ensure inference fidelity between the PyTorch float32 model and exported ONNX graph:

- **Target Image:** `sample_person.jpg` (ground truth single subject detection).
- **PyTorch Detection:**
  - Class: `0` (`person`)
  - Confidence: `0.5932`
  - Bounding Box `[x1, y1, x2, y2]`: `[471.2, 80.6, 557.6, 260.5]`
- **ONNX Runtime Detection:**
  - Class: `0` (`person`)
  - Confidence: `0.6190`
  - Bounding Box `[x1, y1, x2, y2]`: `[471.2, 80.6, 557.5, 260.5]`
- **Agreement Metrics:**
  - Detection Match Rate (IoU >= 0.50): **100% (1/1)**
  - Intersection-over-Union (IoU): **0.9985** (essentially identical spatial boundary)
  - Absolute Confidence Difference: **0.0258** (attributed to fused conv/batchnorm optimizations in `onnxslim`)
  - False Positives / Negatives: **0**

---

## 6. Architecture & Implementation Assessment

### 6.1 Findings
1. **Steady-State Throughput Equivalence:** PyTorch CPU (with modern oneDNN/MKLDNN bindings) and ONNX Runtime CPU (using MLAS/OpenMP) perform similarly on AMD Zen 3+ (Ryzen 7 6800U) at ~11–12 FPS for YOLOv8n (640x640).
2. **Cold-Start Dominance:** ONNX Runtime eliminates PyTorch's heavy initial JIT graph compilation overhead, dropping first-inference latency from **3.6 seconds to 144 ms**. This is highly beneficial for serverless or autoscaling containerized environments.
3. **Tail-Latency Stability:** ONNX Runtime yields tighter latency distributions (P95 of 98.5 ms at 4 threads vs PyTorch's 132.8 ms), mitigating frame drops in soft real-time video processing.
4. **Integration Trade-offs:** Running ONNX through `ultralytics` wrapper introduces severe overhead (dropping throughput to 4.16 FPS). Direct ORT execution requires maintaining custom letterbox pre-processing and NumPy-based NMS post-processing routines.

### 6.2 Modularity & Safety Audit
- No existing FastAPI endpoints (`src/serving/`) were touched or reconfigured.
- No GStreamer or RTSP pipelines (`src/streaming/`) were altered.
- Hash integrity of both authoritative models (`data/models/yolov8n.pt` and `data/models/best.pt`) remains completely intact.

---

## 7. Modified / Created Files Inventory

| # | File Path | Type | Purpose |
| :--- | :--- | :--- | :--- |
| 1 | `docker/Dockerfile.benchmark` | Created | Isolated Docker definition for Gate 8 benchmark environment containing `onnx`, `onnxruntime`, `onnxslim`, and `psutil`. Preserves production serving Dockerfiles. |
| 2 | `eval_tools/export_onnx.py` | Created | Standalone Python export script that validates input model hashes, exports `yolov8n.pt` to ONNX opset 17, validates the graph, and stores in target path. |
| 3 | `eval_tools/benchmark_onnx_vs_pytorch.py` | Created | Standalone benchmarking engine comparing cold start, warm latency, P95/P99, throughput, and IoU output consistency across 100 runs. |
| 4 | `eval_tools/benchmark_threads.py` | Created | Profiler evaluating CPU thread scaling (1, 2, 4, 8 threads) for ONNX Runtime CPU on AMD Ryzen 6800U. |
| 5 | `data/models/optimized/onnx/yolov8n.onnx` | Created | Exported and verified ONNX model artifact (SHA256: `b59f7372ed3f05934a13241c7965f1e66b40d0ea3f5fff09c89878c491bc8d3d`). |
| 6 | `reports/gate8-onnx-runtime-cpu-benchmark.md` | Created | Authoritative Gate 8 evaluation report and technical recommendation. |

---

## 8. Final Decision & Recommendations

1. **Gate 8 Decision:** **COMPLETE & SATISFIED**.
2. **FastAPI Serving Integration:** **DEFERRED TO SPRINT 4**.
   - Do NOT immediately replace PyTorch CPU in `src/serving/` for Sprint 3. The current PyTorch CPU service meets the baseline requirement at 11.6 FPS with cleaner native maintenance.
   - If cold-start SLA (<500 ms) or serverless scaling is prioritized in future milestones, adopt direct `onnxruntime.InferenceSession` with 4 threads using the pre-compiled artifact created in Gate 8.
