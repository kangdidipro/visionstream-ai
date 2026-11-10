# VISIONSTREAM AI — SPRINT 3: TRITON / MODEL SERVING
# GATE 1 — ARCHITECTURE & ENVIRONMENT ASSESSMENT REPORT

- **Lingkungan Target:** DEVELOPMENT LAPTOP ONLY (`LAPTOP-62621JIA`)
- **Root Direktori Proyek:** `C:\my-app\visionstream-ai`
- **Sistem Operasi:** Microsoft Windows 11 Home Single Language (Build 10.0.26300)
- **Container Runtime:** Docker Desktop 4.93.0 (Engine v29.8.1, WSL2 Kernel 6.6.87.2)
- **Model Baseline Otoritatif:** `data/models/yolov8n.pt`
- **Tanggal Asesmen:** 10 November 2026
- **Status Evaluasi Gerbang:** **PASS (READY FOR GATE 2 DESIGN & IMPLEMENTATION)**

---

## 1. RINGKASAN EKSEKUTIF (EXECUTIVE SUMMARY)

Laporan ini menyajikan hasil asesmen teknis mendalam secara *read-only* terhadap arsitektur perangkat lunak, infrastruktur Docker, model machine learning, serta kelayakan teknologi model serving (**NVIDIA Triton Inference Server** vs **FastAPI Inference Service**) untuk proyek VisionStream AI pada Sprint 3.

### Temuan Kunci Asesmen:
1. **Integritas Model Baseline:** Berkas model baseline kanonikal [`data/models/yolov8n.pt`](file:///c:/my-app/visionstream-ai/data/models/yolov8n.pt) berukuran **6.549.796 bytes** terverifikasi memiliki hash SHA-256 yang **100% cocok** dengan acuan kanonikal (`F59B3D833E2FF32E194B5BB8E08D211DC7C5BDF144B90D2C8412C47CCFC83B36`).
2. **Kondisi Komputasi Host:** Host development ditenagai oleh prosesor **AMD Ryzen 7 6800U (8 Cores, 16 Threads)** dengan grafis terintegrasi AMD Radeon 680M tanpa dGPU NVIDIA. Oleh karena itu, seluruh inferensi serving lokal wajib beroperasi di atas **backend CPU**.
3. **Status Komponen Serving Saat Ini:** Sistem saat ini merupakan pipeline batch/file video pemrosesan offline berbasis CLI (`src/pipeline.py` & `src/detector.py`). **Belum ada HTTP/REST atau gRPC inference API service (seperti FastAPI atau Triton)** yang terpasang.
4. **Analisis Kelayakan Model Serving:**
   - **Triton Inference Server CPU:** Layak secara teknis melalui image resmi `nvcr.io/nvidia/tritonserver:xx.yy-py3`, namun memiliki overhead image yang sangat besar (~10–15 GB), startup lambat, dan konfigurasi *model repository* yang rigid untuk lingkungan development laptop lokal.
   - **Standalone FastAPI Service:** Sangat ringan, modular, cepat dibangun, mendukung Pydantic schema kanonikal, namun kurang memamerkan kompetensi enterprise model serving standar industri.
   - **Rekomendasi Arsitektur Target:** **Modular Hybrid Architecture (FastAPI Gateway + ONNX Runtime / Triton-Ready Client Interface)**. Pada Gate 2, diusulkan membangun layanan **FastAPI Inference Service modular** yang membungkus inferensi model baseline (via PyTorch/ONNX Runtime CPU) dengan kontrak antarmuka API yang kompatibel dengan standar *KServe v2 / Triton Data Plane*. Hal ini memungkinkan transisi tanpa hambatan ke Triton Server saat dideploy ke cluster GPU/remote server di masa depan.
5. **Vonis Gate 1:** **PASS**. Tidak ada blocker kritis yang menghalangi perancangan arsitektur serving.

---

## 2. STRUKTUR NYATA REPOSITORI (ACTUAL REPOSITORY STRUCTURE)

Berdasarkan inspeksi fisik sistem berkas pada direktori `C:\my-app\visionstream-ai`, berikut adalah struktur direktori nyata yang terdeteksi:

```
C:\my-app\visionstream-ai\
├── .dockerignore
├── .gitignore
├── docker-compose.yml
├── README.md
├── requirements.txt
├── data\
│   ├── datasets\
│   │   ├── .cache\
│   │   ├── coco-person\ (images/, labels/, metadata/)
│   │   └── coco-person-sprint2.zip
│   ├── inputs\ (video pengujian MP4)
│   ├── models\
│   │   ├── best.pt (fine-tuned artifact, 6.487.978 bytes)
│   │   └── yolov8n.pt (authoritative baseline, 6.549.796 bytes)
│   └── outputs\ (video hasil anotasi MP4)
├── docker\
│   └── Dockerfile (Python 3.11-slim, CPU PyTorch, FFmpeg)
├── docs\
│   ├── architecture\
│   │   └── MASTER-BLUEPRINT.md (v1.0.1)
│   └── benchmark CPU vs GPU CONTROLLED BENCHMARK.md
├── eval_tools\ (perkakas evaluasi S2.5: protocol_freeze.py, evaluate_engine.py)
├── evidence\ (artefak audit S2.4 Colab dan S2.5 evaluasi)
├── images\ (tangkapan layar dokumentasi)
├── logs\ (log deteksi JSONL hasil eksekusi Sprint 1)
├── notebooks\
│   ├── sprint2_colab_gate1_trial.ipynb
│   ├── sprint2_colab_gate2_training.ipynb
│   └── remote_gpu\ (4 template notebook portabel Sprint 3 Gate 2)
├── reports\ (laporan audit resmi seluruh sprint)
└── src\
    ├── __init__.py
    ├── config.py (Pydantic schema PipelineConfig)
    ├── dataset_pipeline.py (kurasi COCO)
    ├── detector.py (PersonTracker: YOLO + ByteTrack)
    ├── inspect_coco_licenses.py
    ├── logger.py (DetectionLogger: JSONL/CSV writer)
    ├── pipeline.py (Orkestrator inferensi video batch)
    ├── test_dataset_integrity.py
    ├── test_pipeline.py
    ├── test_runner.py
    └── visualizer.py (Anotasi OpenCV)
```

---

## 3. ASESMEN ARSITEKTUR DOCKER EKSISTING (DOCKER ENVIRONMENT ASSESSMENT)

Hasil inspeksi langsung terhadap daemon Docker Desktop di Windows 11 host:

- **Versi Docker Desktop:** `4.93.0 (Engine 29.8.1, API 1.56)`
- **Kernel WSL2:** `6.6.87.2-microsoft-standard-WSL2 (x86_64)`
- **Alokasi Sumber Daya Docker:** 16 logical CPUs, ~7,38 GB RAM teralokasi ke WSL2 VM.
- **Image Proyek Eksisting:** `visionstream-ai:sprint-1` (ID: `cbac8965808e`, Virtual Size: 3,69 GB, Python 3.11.18, PyTorch 2.15.0+cpu, OpenCV 4.11.0, Ultralytics 8.4.202).
- **Kontainer Aktif:** Tidak ada kontainer proyek yang sedang berjalan saat ini (`CONTAINER ID` kosong). Kontainer pihak ketiga lainnya (`potensync_web`, `potensync_mariadb`, `potensync_node`) berstatus `Exited (255)`.
- **Jaringan Docker Proyek:** `visionstream-ai_default` (Bridge driver).
- **Konfigurasi `docker-compose.yml` Saat Ini:**
  - Menentukan satu service tunggal: `visionstream`.
  - Berorientasi pada eksekusi perintah ad-hoc/batch (`command: ["python3", "-c", "print(...)"]`).
  - Me-mount direktori host: `./src`, `./data/inputs`, `./data/outputs`, `./data/models`, `./data/datasets`, `./logs`, `./reports`.
  - **Belum ada konfigurasi port forwarding** (misal `- "8000:8000"` untuk REST API atau `- "8001:8001"` untuk gRPC).

---

## 4. VERIFIKASI MODEL BASELINE (MODEL BASELINE VERIFICATION)

Pemeriksaan integritas kriptografis dan metadata terhadap berkas model baseline:

| Parameter | Nilai Terverifikasi | Status Kesesuaian |
| :--- | :--- | :---: |
| **Path Berkas** | `C:\my-app\visionstream-ai\data\models\yolov8n.pt` | **TERVERIFIKASI** |
| **Ukuran Berkas** | `6.549.796 bytes` | **TERVERIFIKASI** |
| **Format Model** | PyTorch Checkpoint (`.pt` - Ultralytics YOLOv8 nano) | **TERVERIFIKASI** |
| **SHA-256 Terhitung** | `F59B3D833E2FF32E194B5BB8E08D211DC7C5BDF144B90D2C8412C47CCFC83B36` | **100% IDENTIK** |
| **SHA-256 Ekspektasi**| `f59b3d833e2ff32e194b5bb8e08d211dc7c5bdf144b90d2c8412c47ccfc83b36` | **MATCH** |
| **Kompatibilitas Runtime**| Dapat dimuat langsung oleh `ultralytics.YOLO` di CPU container Docker | **VERIFIED** |

*Catatan Tata Kelola:* Model fine-tuned [`data/models/best.pt`](file:///c:/my-app/visionstream-ai/data/models/best.pt) tetap dipertahankan terpisah sebagai artefak riset Sprint 2. Baseline `yolov8n.pt` tidak digantikan dan tetap menjadi model utama untuk serving.

---

## 5. ARSITEKTUR INFERENSI SAAT INI (CURRENT INFERENCE ARCHITECTURE)

Alur kerja inferensi eksisting diimplementasikan dalam [`src/detector.py`](file:///c:/my-app/visionstream-ai/src/detector.py) dan [`src/pipeline.py`](file:///c:/my-app/visionstream-ai/src/pipeline.py):
1. **Preprocessing:** Video lokal dibaca menggunakan `cv2.VideoCapture`. Frame dilewatkan ke `PersonTracker.process_frame()`, di mana Ultralytics internal melakukan resizing letterbox ke `640x640`, normalisasi piksel, dan konversi ke tensor.
2. **Inference Execution:** Model dipanggil secara in-process melalui `self.model.track(source=frame, conf=0.35, iou=0.5, classes=[0])`.
3. **Postprocessing & Tracking:** Filter deteksi khusus `class_id == 0` (person), diikuti algoritma ByteTrack untuk asosiasi ID jejak objek (*track ID*).
4. **Output Serialization:** Hasil disimpan sebagai log baris JSONL/CSV di direktori `logs/` dan video dianotasi dengan bounding-box OpenCV di `data/outputs/`.

*Keterbatasan Arsitektural:*
- Model terikat erat dengan eksekusi file video lokal.
- Tidak tersedia endpoint jaringan (network-accessible endpoint) yang dapat menerima input gambar/frame secara realtime melalui protokol HTTP/REST atau gRPC.
- Tidak ada mekanisme antrean permintaan (*request queuing*) atau batching dinamis.

---

## 6. ASESMEN KELAYAKAN TRITON MODEL SERVING (PADA HOST CPU)

Evaluasi terhadap 3 varian NVIDIA Triton Inference Server pada host CPU:

### A. Varian 1: Triton Inference Server dengan CPU / Python Backend
- **Kebutuhan Hardware & Docker:** Memerlukan image resmi `nvcr.io/nvidia/tritonserver:<tag>` (ukuran ~12–15 GB). Docker Desktop WSL2 dapat menjalankannya dalam mode CPU tanpa flag `--gpus`.
- **Kompatibilitas Model:** Python backend Triton dapat mengeksekusi script Python yang memuat model PyTorch atau Ultralytics.
- **Kompleksitas & Kendala:** Overhead memori sangat tinggi untuk laptop 16 GB RAM (WSL2 hanya memiliki ~7,38 GB limit). Python backend pada Triton memiliki IPC overhead (Inter-Process Communication via shared memory) yang memperlambat inferensi CPU.
- **Kelayakan:** **CONDITIONALLY FEASIBLE (HIGH RESOURCE OVERHEAD)**.

### B. Varian 2: Triton ONNX Runtime Backend (CPU)
- **Kebutuhan Hardware & Docker:** Model `yolov8n.pt` diekspor terlebih dahulu ke format `yolov8n.onnx`. Triton menggunakan built-in C++ ONNX Runtime CPU backend.
- **Kompatibilitas Model:** Sangat tinggi. Format ONNX adalah standar terbuka industri.
- **Kompleksitas & Kendala:** Struktur *Model Repository* Triton sangat ketat (`model_repository/yolov8n/1/model.onnx` dan `config.pbtxt`). Preprocessing (letterbox 640x640, BGR->RGB, HWC->CHW) dan postprocessing (NMS, decoding output tensor `[1, 84, 8400]`) harus ditulis secara manual menggunakan *ensemble model* Triton (Python/DALI/custom backend) atau dipindahkan ke client-side.
- **Kelayakan:** **FEASIBLE BUT HIGH EFFORT FOR PRE/POST-PROCESSING ENSEMBLE**.

### C. Varian 3: Triton PyTorch (TorchScript) Backend (CPU)
- **Kompatibilitas Model:** YOLOv8 Ultralytics tidak selalu mengekspor dengan mulus ke TorchScript murni tanpa kehilangan beberapa operator NMS dinamis.
- **Kelayakan:** **NOT RECOMMENDED** (Format ONNX jauh lebih stabil dan portabel dibandingkan TorchScript untuk YOLOv8).

---

## 7. ASESMEN KELAYAKAN FASTAPI INFERENCE SERVICE

Evaluasi opsi pembangunan microservice mandiri berbasis **FastAPI**:

- **Kebutuhan Hardware & Docker:** Sangat ringan. Image Docker berbasis `python:3.11-slim` yang sudah ada dapat diperluas dengan menambahkan paket `fastapi` dan `uvicorn[standard]` (hanya menambah ~50 MB).
- **Model & Runtime:** Model `yolov8n.pt` dapat dimuat langsung menggunakan PyTorch CPU eksisting atau model diekspor ke ONNX Runtime CPU.
- **Preprocessing & Postprocessing:** Pre/post-processing Python native yang sudah tervalidasi di Sprint 1 dan Sprint 2 (`src/detector.py`) dapat langsung digunakan kembali tanpa perlu menulis ulang operator C++ atau ensemble config yang rumit.
- **Kemudahan Pengembangan & Pengujian:** Menyediakan dokumentasi interaktif Swagger UI (`/docs`), validasi schema input otomatis via Pydantic v2, endpoint health check (`/health`), konfigurasi threshold dinamis melalui parameter query/JSON body, dan metrik latensi per permintaan.
- **Kelayakan:** **HIGHLY FEASIBLE, LIGHTWEIGHT, AND IMMEDIATE PRODUCTION READY**.

---

## 8. REKOMENDASI TARGET ARSITEKTUR SPRINT 3 (RECOMMENDED TARGET ARCHITECTURE)

Untuk menyeimbangkan kepraktisan performa CPU lokal, stabilitas memori laptop, serta nilai portofolio rekayasa machine learning tingkat lanjut, direkomendasikan pendekatan:

### **"Modular Dual-Tier Architecture: FastAPI Serving Gateway + KServe v2 Protocol Alignment"**

```
                     ┌────────────────────────────────────────────────────────┐
                     │                 CLIENT REQUEST                         │
                     │  (HTTP POST /v1/models/yolov8n:predict / multipart)    │
                     └───────────────────────────┬────────────────────────────┘
                                                 │
                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                           DOCKER CONTAINER: visionstream-serving                            │
│                                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                  FASTAPI GATEWAY                                      │  │
│  │   • Endpoints: /v1/models/yolov8n (Metadata), /health (Liveness/Readiness)            │  │
│  │   • Endpoint:  /v1/models/yolov8n:predict (Inference with configurable conf/iou)      │  │
│  │   • Validasi Skema: Pydantic v2 (Input image validation & response serialization)     │  │
│  │   • Latensi & Metrik: Request timer (preprocess_ms, inference_ms, postprocess_ms)     │  │
│  └───────────────────────────────────────────┬───────────────────────────────────────────┘  │
│                                              │                                              │
│                                              ▼                                              │
│  ┌───────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                            MODULAR INFERENCE ENGINE (CORE)                            │  │
│  │                                                                                       │  │
│  │   • Default Provider: PyTorch CPU Engine (yolov8n.pt kanonikal)                       │  │
│  │   • Accelerated Option: ONNX Runtime CPU Provider (yolov8n.onnx)                      │  │
│  │   • Interface Abstraction: BaseInferenceEngine (Dapat di-swap ke Triton Client)       │  │
│  └───────────────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Keunggulan Arsitektur yang Direkomendasikan:
1. **Ringan & Hemat Memori:** Bekerja optimal dalam batasan RAM 16 GB laptop tanpa risiko kehabisan memori (*Out Of Memory*).
2. **Kesesuaian Standar Industri (KServe v2 / Triton Compliant):** Rute API dirancang mengikuti konvensi standar KServe/Triton (`/v1/models/{model_name}/infer` dan `/v1/models/{model_name}`), sehingga antarmuka klien kompatibel dengan ekosistem Triton.
3. **Modularitas Migrasi GPU Masa Depan:** Menggunakan *abstract base class* inferensi. Ketika GPU remote (Google Colab atau server Triton cloud) aktif, backend engine dapat diubah menjadi `TritonGRPCInferenceClient` tanpa mengubah kontrak API FastAPI yang dikonsumsi klien.

---

## 9. MATRIKS RISIKO TEKNIS & MITIGASI (TECHNICAL RISKS)

| No | Risiko Teknis | Dampak | Probabilitas | Rencana Mitigasi |
| :-: | :--- | :---: | :---: | :--- |
| 1 | **Keterbatasan CPU Throughput:** Inferensi gambar tunggal pada CPU laptop memakan waktu ~50–60 ms (~16–20 FPS). | Sedang | Tinggi | Gunakan single-image inference policy pada Gate 2; sediakan opsi ekspor ONNX Runtime CPU untuk optimasi throughput. |
| 2 | **Docker Overhead & Memory Pressure:** Penggunaan image berat seperti Triton Server (~15 GB) dapat membekukan WSL2. | Tinggi | Tinggi | Prioritaskan FastAPI lightweight service di dalam container `visionstream-ai:sprint-1` atau varian ringkasnya. |
| 3 | **Konflik Port Jaringan Host:** Port default `8000` mungkin bertabrakan dengan layanan web lain. | Rendah | Sedang | Parameterkan pemetaan port di `docker-compose.yml` (misal `8085:8000` atau periksa ketersediaan port sebelum binding). |
| 4 | **Perubahan Format Bounding-Box:** Format output deteksi tidak konsisten antara model serving dan pipeline Sprint 1. | Sedang | Rendah | Gunakan skema Pydantic standar dengan atribut `[x1, y1, x2, y2]`, `confidence`, dan `class_id == 0`. |

---

## 10. REKOMENDASI TAHAP IMPLEMENTASI (IMPLEMENTATION GATE 2 RECOMMENDATION)

Berdasarkan asesmen ini, Gate 1 dinyatakan **PASS**. Langkah-langkah teknis yang direkomendasikan untuk **Sprint 3 Gate 2** adalah:
1. **Desain Skema Kontrak API:** Mendefinisikan schema input/output inferensi Pydantic yang selaras dengan KServe v2 Data Plane.
2. **Implementasi Layanan FastAPI:** Mengembangkan file serving modular (misal `src/serving/api.py` dan `src/serving/engine.py`) tanpa mengubah pipeline offline video eksisting di `src/pipeline.py`.
3. **Penyelarasan Docker Compose:** Menambahkan deklarasi service serving pada `docker-compose.yml` dengan konfigurasi port HTTP terisolasi.
4. **Pengujian Fungsionalitas Serving:** Menguji endpoint health check dan pengiriman gambar pengujian untuk memverifikasi akurasi person detection, latensi, dan format respons JSON.

---

## 11. BUKTI EKSEKUSI & AUDIT KEBERADAAN BERKAS

Laporan ini telah disimpan di path kanonikal:
`C:\my-app\visionstream-ai\reports\triton-model-serving-gate1-assessment.md`

- **Verifikasi Fisik Berkas:** Ada dan non-empty.
- **Konfirmasi Integritas:** Tidak ada berkas kode sumber (`src/`), berkas model (`data/models/`), berkas dataset (`data/datasets/`), maupun konfigurasi Docker (`docker-compose.yml`, Dockerfile) yang diubah selama asesmen ini berlangsung.
