# System Architecture Overview

VisionStream AI is designed as a modular, decoupled computer vision platform capable of handling real-time video stream ingestion, scalable model serving, and telemetry observability.

## 1. High-Level Architecture

The system decouples edge/stream processing from model serving and analytics:

```mermaid
flowchart TD
    subgraph Stream Ingestion & Tracking
        RTSP_SRC["RTSP Source\n(FFmpeg / IP Cam)"] -->|RTSP H.264| MTX["MediaMTX Server\n(:8554/live/stream)"]
        MTX -->|TCP RTSP| GST["GStreamer Ingestion\n(rtspsrc ! rtph264depay ! avdec_h264)"]
        GST -->|RGB Frames| FP["Frame Processor"]
        FP -->|Inference Batches| YOLOV8["YOLOv8 Detector\n(Local or Gateway)"]
        YOLOV8 -->|Detections| BT["ByteTrack\nAssociation & Tracking"]
        BT -->|Stream Metrics| STREAM_LOG["JSONL Stream Telemetry\n(FPS, Jitter, Drops)"]
    end

    subgraph FastAPI Model Serving Gateway
        CLIENT["Inference Client\n(App / Webhook)"] -->|HTTP POST Multipart| FASTAPI["FastAPI Serving Gateway\n(:8085)"]
        FASTAPI -->|Validate SHA256| REGISTRY["Model Registry\n(/app/data/models)"]
        FASTAPI -->|In-Process Engine| INFER["YOLOv8 PyTorch / ONNX Engine"]
        INFER -->|Boxes & Scores| FASTAPI
        FASTAPI -->|Prometheus Counter/Hist| PROM["/metrics Endpoint"]
        FASTAPI -->|Structured JSONL| LOGS["logs/serving_access.jsonl"]
    end
```

## 2. Key Architectural Tenets

1. **Decoupled Video Pipeline vs. Inference Serving:**  
   Streaming ingestion operates autonomously with resilient reconnect mechanics and backpressure drop policies. The model serving layer can run standalone or edge-colocated.
2. **Defensive Model Validation:**  
   Model weights are cryptographically verified via SHA256 hashes prior to runtime initialization to prevent silent drift or corrupted weight substitution.
3. **Hardware Agnostic Design:**  
   The system provides optimized inference paths across:
   - **Local CPU:** Multi-threaded PyTorch CPU & ONNX Runtime (Ryzen 7 6800U).
   - **Accelerated Cloud GPU:** NVIDIA Tesla T4 with TensorRT FP16 execution.
4. **Structured Telemetry First:**  
   Every transaction carries a trace UUID, measured latency breakdown (preprocess, inference, postprocess), and outputs to structured JSONL and Prometheus gauges.
