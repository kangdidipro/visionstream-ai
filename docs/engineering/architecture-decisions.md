# Architecture Decisions & Trade-Offs

This document records the foundational Architectural Decision Records (ADRs) that guided VisionStream AI.

---

### ADR-001: Rejection of Fine-Tuned Model for Production Serving
- **Context:** Sprint 2 evaluated fine-tuning YOLOv8n on a domain-specific dataset.
- **Decision:** Reject `best.pt` for serving default and retain pre-trained `yolov8n.pt`.
- **Reasoning:** Rigorous holdout evaluation revealed mAP@50 dropped from 75.32% to 69.44% (-5.88%). Generalization capability deteriorated. Engineering integrity dictates serving the superior baseline.

---

### ADR-002: In-Process FastAPI Serving vs. Dedicated Triton Inference Server
- **Context:** Evaluated deploying NVIDIA Triton Inference Server for model serving.
- **Decision:** Retain lightweight in-process FastAPI serving for local CPU development; defer Triton to multi-GPU enterprise infrastructure.
- **Reasoning:** Local AMD Radeon 680M hardware lack NVIDIA Tensor Cores; running Triton CPU backend in Docker yields no performance gain over PyTorch/ORT while introducing substantial container memory overhead (~1.5 GB).

---

### ADR-003: GStreamer Drop Policy for Real-Time Streaming
- **Context:** Full analytics (YOLOv8 + ByteTrack) runs at 5.51 FPS on CPU, while RTSP streams arrive at 12 FPS.
- **Decision:** Configure GStreamer `appsink` with `drop=true` and `max-buffers=2`.
- **Reasoning:** In real-time video surveillance, low-latency timeliness is prioritized over processing every historic frame. Dropping outdated frames prevents memory buffering exhaustion.

---

### ADR-004: ONNX Runtime CPU Adoption Strategy
- **Context:** Benchmark evaluated ONNX Runtime CPU vs. PyTorch CPU.
- **Decision:** Retain PyTorch CPU as default development engine; maintain ONNX artifact as validated optimization target.
- **Reasoning:** Warm inference latency is virtually identical (86 ms vs 92 ms). PyTorch provides simpler developer ergonomics, while ONNX is preserved for cold-start and C++ deployment scenarios.
