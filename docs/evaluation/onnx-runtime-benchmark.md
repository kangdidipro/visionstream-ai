# ONNX Runtime CPU Benchmark & Optimization

## 1. Overview

In Sprint 3 Gate 8, we evaluated whether exporting `yolov8n.pt` to ONNX and serving via **ONNX Runtime (ORT) CPU** yields a measurable performance advantage on an x86-64 mobile CPU (AMD Ryzen 7 6800U, 8C/16T).

## 2. Benchmark Architecture

```mermaid
flowchart LR
    PT["YOLOv8n PyTorch\n(data/models/yolov8n.pt)"] -->|torch.onnx.export (Opset 17)| RAW_ONNX["Raw ONNX Graph"]
    RAW_ONNX -->|onnxslim optimization| OPT_ONNX["Optimized ONNX Artifact\n(data/models/optimized/onnx/yolov8n.onnx)"]
    OPT_ONNX --> ORT_DIRECT["Direct ORT Session\n(CPUExecutionProvider, 4 Threads)"]
```

## 3. Results Summary

<!-- Records-per-page filter: 5, 10, 30, 50, 100, 200, 300, All -->
| Metric | PyTorch CPU (`torch 2.15.0`) | ONNX Runtime CPU Direct (`ort 1.31.1`) | Ultralytics ONNX Wrapper | Delta (ORT Direct vs PyTorch) |
| :--- | :--- | :--- | :--- | :--- |
| **Model Init Time** | 227.70 ms | 171.92 ms | 29.23 ms | -55.78 ms (-24.5%) |
| **Cold Start Latency** | 3,616.02 ms | **144.65 ms** | N/A | **-3,471.37 ms (25x faster)** |
| **Mean Latency (Warm)** | **85.95 ms** | 92.21 ms *(89.78 ms infer core)*| 240.29 ms | +6.26 ms (+7.3%) |
| **P95 Latency** | 132.85 ms | **115.03 ms** *(98.52 ms @ 4 thr)*| 357.54 ms | **-17.82 ms (Lower jitter)** |
| **Throughput** | **11.63 FPS** | 10.84 FPS *(11.86 FPS @ 4 thr)* | 4.16 FPS | -0.79 FPS (-6.8%) |
| **Memory (RSS)** | ~185 MB | **~168 MB** | ~210 MB | **-17 MB (-9.2%)** |

### Output Consistency Verification
Tested on `data/inputs/sample_person.jpg`:
- **Match Rate (IoU >= 0.50):** 100% (1/1)
- **Mean IoU:** **0.9985**
- **Confidence Delta:** 0.0259

*(Note: Consistency was verified on this representative evaluation frame; we do not generalize universal parity across full holdout sets).*

## 4. Key Takeaways & Decision

1. **Throughput Parity:** Both engines achieve ~11–12 FPS steady-state on Zen 3+ CPU.
2. **Cold Start Superiority:** ORT initializes and executes its first inference in **144 ms**, compared to PyTorch's 3.6-second JIT initialization.
3. **Recommendation:** Retain PyTorch CPU as the default FastAPI serving engine for Sprint 3 developer ergonomics; retain the ONNX model as an approved optimization artifact for serverless / edge environments.
