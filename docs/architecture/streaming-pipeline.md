# RTSP Video Ingestion, GStreamer, and ByteTrack Pipeline

## 1. Overview

VisionStream AI integrates a containerized video streaming pipeline engineered for real-time video surveillance and analytics. The pipeline consumes H.264 video streams over RTSP, decodes frames via GStreamer, executes YOLOv8 object detection, and tracks targets across frames using ByteTrack.

## 2. Ingestion & Tracking Pipeline Flow

```mermaid
flowchart TD
    subgraph Video Source & Proxy
        FILE["Source MP4 (people-detection.mp4)"] -->|Loop Publish| FFMPEG["FFmpeg Publisher Container"]
        FFMPEG -->|RTSP TCP :8554| MTX["MediaMTX Server (:8554/live/stream)"]
    end

    subgraph Streaming Ingestion Worker
        MTX -->|TCP Stream| Rtspsrc["rtspsrc latency=100 protocols=tcp"]
        Rtspsrc --> Depay["rtph264depay"]
        Depay --> Parse["h264parse"]
        Parse --> Decoder["avdec_h264"]
        Decoder --> Convert["videoconvert"]
        Convert --> Sink["appsink emit-signals=true max-buffers=2 drop=true"]
    end

    subgraph Analytics & Tracking
        Sink -->|NumPy ndarray (RGB)| Pre["Letterbox Preprocessing (640x640)"]
        Pre --> YOLO["YOLOv8 Baseline Inference"]
        YOLO --> Post["Postprocess (conf=0.35, iou=0.65, class=0)"]
        Post --> Tracker["ByteTrack Multi-Object Tracker"]
        Tracker --> Visualizer["Bounding Box & Track ID Renderer"]
    end
```

## 3. Benchmarked Metrics & Realities

During Gate 6 and Gate 6A verifications on host hardware (`LAPTOP-62621JIA`, AMD Ryzen 7 6800U, CPU inference):

- **Source RTSP Ingestion Rate:** **12.02 FPS** (matching publisher source).
- **Standalone Ingestion Pipeline:** **12.00 FPS** (zero frame drops at network level).
- **Full End-to-End Analytics (Ingestion + YOLOv8 + ByteTrack):** **5.51 FPS** (CPU bound).
- **Backpressure & Drop Policy:** When downstream processing falls below source FPS, GStreamer's `appsink (max-buffers=2, drop=true)` safely drops older frames to maintain real-time low latency without memory starvation.
- **Resilience:** Disconnect and reconnect handling verified against abrupt RTSP publisher restarts.
