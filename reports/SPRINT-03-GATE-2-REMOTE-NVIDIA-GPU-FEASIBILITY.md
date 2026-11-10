# VISIONSTREAM AI — SPRINT 3 / GATE 2
# REMOTE NVIDIA GPU LAB FEASIBILITY STUDY REPORT

- **Target Lingkungan:** DEVELOPMENT ONLY (`LAPTOP-62621JIA`)
- **Root Direktori Proyek:** `C:\my-app\visionstream-ai`
- **Canonical Master Blueprint:** `docs/architecture/MASTER-BLUEPRINT.md` (v1.0.1, SHA-256: `5A8C05D91F1BE08BFE89AE495DAC4553C63CE164655F4C7C98155AFFC0BEE19A`)
- **Kandidat Platform Remote:** Google Colab Free vs Kaggle Notebooks Free
- **Tanggal Asesmen:** 10 November 2026
- **Status Gate 2:** **PASS WITH LIMITATIONS**

---

## 1. RINGKASAN EKSEKUTIF (EXECUTIVE SUMMARY)

Berdasarkan temuan Gate 1 bahwa mesin lokal development (`LAPTOP-62621JIA`) tidak memiliki perangkat keras NVIDIA discrete GPU, Gate 2 melaksanakan studi kelayakan teknis secara komprehensif terhadap pemanfaatan lab remote berbasis cloud notebook gratis (**Google Colab Free** dan **Kaggle Notebooks Free**) untuk memenuhi target kompetensi NVIDIA GPU pada Sprint 3 VisionStream AI.

### Temuan & Keputusan Utama:
1. **Platform Rekomendasi:** **Google Colab Free** adalah kandidat utama yang paling fleksibel dan kompatibel.
   - Mengalokasikan GPU **NVIDIA Tesla T4 (16 GB GDDR6, Turing Architecture, Compute Capability 7.5)**.
   - Kompatibel penuh dengan PyTorch CUDA, ONNX Runtime GPU (CUDAExecutionProvider), dan TensorRT modern (10.x / 11.x).
   - Terbukti sukses dan stabil pada uji coba Sprint 2.4 (pelatihan 50 epoch YOLOv8n tanpa interupsi).
2. **Kaggle Notebooks Free sebagai Sekunder:**
   - Menyediakan kuota 30 jam GPU/minggu, sering kali mengalokasikan **Tesla P100 (Pascal SM 6.0)** atau **Tesla T4**.
   - *Catatan Kritis:* Tesla P100 **TIDAK MENDUKUNG** TensorRT 10+/11+ modern karena arsitektur Pascal (SM 6.0) telah dihentikan dukungannya (*deprecated/dropped*) oleh NVIDIA TensorRT modern.
3. **Keterbatasan Teknologi Lanjutan (DeepStream & Triton):**
   - **NVIDIA DeepStream SDK:** **BLOCKED / NOT REALISTIC** pada lingkungan Colab/Kaggle standar (DeepStream membutuhkan kernel display/GStreamer plugin sistem dan driver video hardware encoder/decoder NVDEC tingkat host yang tidak didukung dalam container sandbox Jupyter).
   - **NVIDIA Triton Inference Server:** **CONDITIONALLY FEASIBLE FOR CLIENT-ONLY / DOCKER IN DOCKER BLOCKED** (Colab tidak mengizinkan daemon Docker di dalam VM free tier; pengujian Triton terbatas pada Python client gRPC/HTTP atau mock server).
4. **Artefak yang Disiapkan:**
   - Telah dibuat 4 template notebook portabel di direktori kanonikal [`notebooks/remote_gpu/`](file:///c:/my-app/visionstream-ai/notebooks/remote_gpu/):
     1. `01_gpu_environment_check.ipynb`
     2. `02_yolov8_cuda_inference.ipynb`
     3. `03_onnx_gpu_benchmark.ipynb`
     4. `04_tensorrt_feasibility.ipynb`
5. **Kepatuhan Tata Kelola:**
   - \$0 Cloud Spend (100% Free Tier).
   - Tidak ada pengunggahan dataset privat atau kredensial.
   - Tidak ada modifikasi pada kode produksi `src/` maupun host laptop.

---

## 2. KAJIAN KEBUTUHAN PROYEK (TASK 1 — PROJECT REQUIREMENTS REVIEW)

- **Model Kanonikal:** Baseline [`data/models/yolov8n.pt`](file:///c:/my-app/visionstream-ai/data/models/yolov8n.pt) (Ukuran: 6.549.796 bytes, SHA-256: `F59B3D833E2FF32E194B5BB8E08D211DC7C5BDF144B90D2C8412C47CCFC83B36`).
- **Dimensi Input:** `640x640x3` (RGB normalized float32 atau BGR uint8 untuk inference).
- **Format Output:** Bounding boxes `[x1, y1, x2, y2]`, confidence score, class ID (difilter khusus person, class ID 0).
- **Parameter Operasional Kanonikal:**
  - Confidence threshold: `0.35`
  - NMS IoU threshold: `0.65`
  - Ground-truth matching IoU: `0.50`
- **Dependensi Utama:** Python 3.10+, PyTorch 2.x dengan CUDA, Ultralytics 8.x, OpenCV 4.x, ONNX 1.16+, ONNX Runtime GPU 1.17+, TensorRT 10.x/11.x.

---

## 3. ASESMEN KELAYAKAN PLATFORM (TASK 2 — PLATFORM FEASIBILITY)

| Parameter Teknis | Google Colab (Free Tier) | Kaggle Notebooks (Free Tier) | Status Komparasi |
| :--- | :--- | :--- | :---: |
| **GPU yang Umum Dialokasikan** | **NVIDIA Tesla T4 (15–16 GB)** (Sangat umum). Jarang: L4/A100 (hanya berbayar). | **NVIDIA Tesla T4 (x2)** atau **NVIDIA Tesla P100 (16 GB)**. | Colab lebih konsisten T4 |
| **Batasan Penggunaan / Sesi** | Kuota komputasi harian dinamis; sesi maks 12 jam (idle timeout ~30–90 menit). | Kuota 30 jam GPU / minggu; sesi maks 9–12 jam (idle timeout 60 menit). | Kaggle kuota terhitung per jam |
| **Kompatibilitas CUDA / PyTorch** | CUDA 12.2 / 12.4 pre-installed, PyTorch GPU built-in. | CUDA 11.8 / 12.1 pre-installed, PyTorch GPU built-in. | Keduanya Sangat Baik |
| **Instalasi Paket (`pip`/`apt`)** | Akses `sudo apt-get` dan `pip` penuh di VM container Ubuntu. | Akses `pip` dan `apt-get` tersedia (beberapa repositori dibatasi). | Colab lebih fleksibel |
| **Ekspor Artefak / Hasil** | Google Drive mounting (`google.colab.drive`), download langsung via browser. | Ekspor via Kaggle Output Dataset, download zip via browser. | Keduanya Memadai |
| **Dukungan TensorRT** | **FEASIBLE via `pip install tensorrt`** pada Tesla T4 (SM 7.5). | **T4: FEASIBLE**, **P100: FAILED** (Pascal SM 6.0 ditolak oleh TRT 10+). | Colab lebih aman untuk TRT |
| **Dukungan NVIDIA DeepStream** | **NOT REALISTIC** (Membutuhkan X11/EGL display driver, GStreamer plugin tingkat kernel, dan hardware codec NVDEC/NVENC host passthrough). | **NOT REALISTIC** (Keterbatasan sandbox container yang sama dengan Colab). | Keduanya Tidak Layak |
| **Dukungan Triton Inference Server** | **CLIENT ONLY** (Triton Server daemon memerlukan Docker-in-Docker atau background service privilege yang dilarang/dibatasi di free tier). | **CLIENT ONLY** (Tidak ada hak akses daemon Docker). | Keduanya Terbatas Client |

---

## 4. MATRIKS KOMPATIBILITAS GPU (TASK 3 — GPU COMPATIBILITY MATRIX)

| Arsitektur & Model GPU | Compute Capability (SM) | Dukungan CUDA Driver / PyTorch | Kompatibilitas TensorRT 10.x / 11.x | Kelayakan DeepStream | Kelayakan Triton Server |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **NVIDIA Tesla T4** *(Turing)* | **7.5** | **PENUH** (CUDA 11.x – 12.x, PyTorch cu121/cu124) | **PENUH** (Didukung resmi hingga TensorRT 11.4+; FP32, FP16, INT8 Tensor Cores) | **TERBATAS (Headless pipeline only, no display)** | **CLIENT / MOCK ONLY** (Server daemon dibatasi sandbox) |
| **NVIDIA Tesla P100** *(Pascal)* | **6.0** | **PENUH** (CUDA 11.x – 12.x, PyTorch GPU) | **TIDAK DIDUKUNG / DEPRECATED** (NVIDIA TensorRT 10+ dan 11+ telah menghentikan dukungan arsitektur Pascal SM 6.0) | **BLOCKED** | **CLIENT / MOCK ONLY** |
| **NVIDIA L4 / A100** *(Ada / Ampere)* | **8.9 / 8.0** | **PENUH** (CUDA 12.x+) | **PENUH** (Generasi modern; performa optimal FP16/BF16/INT8) | **TERBATAS** | **CLIENT / MOCK ONLY** |

> [!IMPORTANT]
> **Catatan Kritis TensorRT:** Jika platform (seperti Kaggle) mengalokasikan Tesla P100, pengujian TensorRT modern akan gagal saat tahap *engine builder* karena arsitektur Pascal SM 6.0 tidak lagi memiliki operator dan layer kernel yang didukung oleh TensorRT 10.x/11.x. Oleh karena itu, **Tesla T4 adalah prasyarat minimum** untuk pengujian TensorRT.

---

## 5. ANALISIS KELAYAKAN TEKNOLOGI LANJUTAN (DEEPSTREAM & TRITON)

### A. Kelayakan NVIDIA DeepStream SDK
- **Analisis:** DeepStream SDK adalah platform analitik video tingkat lanjut yang bergantung kuat pada arsitektur GStreamer dengan akselerasi perangkat keras khusus NVIDIA: NVDEC (Hardware Video Decoding), NVENC (Hardware Video Encoding), dan EGL/X11 rendering display.
- **Kendala di Colab / Kaggle:**
  - Lingkungan remote notebook adalah kontainer virtual headless tanpa driver display X11/Wayland terakreditasi.
  - Akses kernel ke modul NVDEC tingkat host tidak diizinkan di free tier, sehingga pipeline GStreamer `nvv4l2decoder` dan `nvvideoconvert` kerap mengalami segfault atau *device node permission denied*.
- **Vonis:** **BLOCKED / NOT REALISTIC FOR SPRINT 3 NOTEBOOK LAB**. DeepStream direkomendasikan untuk dievaluasi melalui kajian arsitektural atau pengujian di workstation lokal ber-GPU fisik di masa mendatang.

### B. Kelayakan NVIDIA Triton Inference Server
- **Analisis:** Triton Inference Server dirancang sebagai daemon service enterprise mandiri (biasanya dijalankan dalam container Docker resmi `nvcr.io/nvidia/tritonserver`).
- **Kendala di Colab / Kaggle:**
  - Colab Free tidak mengizinkan Docker daemon (`dockerd` / Docker-in-Docker) berjalan secara native.
  - Membuka port listening HTTP/gRPC (port 8000/8001) di dalam notebook Colab terbatas pada koneksi `localhost` sesi itu sendiri.
- **Vonis:** **CONDITIONALLY FEASIBLE (MOCK / IN-PROCESS / PYTHON CLIENT ONLY)**. Dapat diuji menggunakan Triton C++ in-process backend atau via Python gRPC client yang memanggil mock endpoint, tetapi bukan sebagai production cluster deployment.

---

## 6. RANCANGAN SEKUENS EKSPERIMEN REMOTE GPU (TASK 4 — EXPERIMENT DESIGN)

Eksperimen portabel dirancang dalam 4 modul pengujian berurutan:

```
[01. GPU Diagnostics] ──► [02. YOLOv8 CUDA] ──► [03. ONNX GPU] ──► [04. TensorRT Engine]
   (nvidia-smi / T4)        (PyTorch FP32/FP16)     (CUDAProvider)        (FP16 Engine)
```

1. **Modul 1: GPU Diagnostics & Hardware Verification (`01_gpu_environment_check.ipynb`)**
   - *Prasyarat:* Runtime GPU dialokasikan.
   - *Bukti yang Dihasilkan:* `gpu_environment_diagnostic.json` (Nama GPU, VRAM, Compute Capability, PyTorch CUDA build).
   - *Kriteria Lolos:* GPU terdeteksi, Compute Capability $\ge 7.0$ (Tesla T4).
2. **Modul 2: YOLOv8 CUDA Inference & Baseline Benchmarking (`02_yolov8_cuda_inference.ipynb`)**
   - *Prasyarat:* Modul 1 PASS; berkas `yolov8n.pt` diunduh dan hash SHA-256 diverifikasi.
   - *Bukti yang Dihasilkan:* `cuda_inference_benchmark.json` (Mean latency, median, P95, FPS pada 200 iterasi terukur).
   - *Kriteria Lolos:* Latensi inferensi GPU jauh lebih cepat daripada CPU (>100 FPS).
3. **Modul 3: ONNX Export & ONNX Runtime CUDA Benchmark (`03_onnx_gpu_benchmark.ipynb`)**
   - *Prasyarat:* Modul 2 PASS; model diekspor ke `yolov8n.onnx`.
   - *Bukti yang Dihasilkan:* `onnx_cuda_benchmark.json` (Perbandingan latensi ONNX CUDAExecutionProvider vs PyTorch).
   - *Kriteria Lolos:* ONNX session berhasil dialokasikan pada provider CUDA tanpa fallback ke CPU.
4. **Modul 4: TensorRT Feasibility & Engine Export Probe (`04_tensorrt_feasibility.ipynb`)**
   - *Prasyarat:* Modul 1 mengonfirmasi Compute Capability $\ge 7.0$; paket `tensorrt` terpasang.
   - *Bukti yang Dihasilkan:* `tensorrt_feasibility_results.json` dan berkas engine `yolov8n.engine`.
   - *Kriteria Lolos:* Engine TensorRT FP16 berhasil di-build dan dievaluasi latensinya.

---

## 7. TEMPLATE NOTEBOOK PORTABEL (TASK 5 — PORTABLE NOTEBOOKS)

Seluruh template notebook telah dibuat dan diverifikasi di direktori [`notebooks/remote_gpu/`](file:///c:/my-app/visionstream-ai/notebooks/remote_gpu/):

1. [`notebooks/remote_gpu/01_gpu_environment_check.ipynb`](file:///c:/my-app/visionstream-ai/notebooks/remote_gpu/01_gpu_environment_check.ipynb) (4.224 bytes)
2. [`notebooks/remote_gpu/02_yolov8_cuda_inference.ipynb`](file:///c:/my-app/visionstream-ai/notebooks/remote_gpu/02_yolov8_cuda_inference.ipynb) (4.885 bytes)
3. [`notebooks/remote_gpu/03_onnx_gpu_benchmark.ipynb`](file:///c:/my-app/visionstream-ai/notebooks/remote_gpu/03_onnx_gpu_benchmark.ipynb) (4.425 bytes)
4. [`notebooks/remote_gpu/04_tensorrt_feasibility.ipynb`](file:///c:/my-app/visionstream-ai/notebooks/remote_gpu/04_tensorrt_feasibility.ipynb) (5.079 bytes)

Semua notebook dibuat tanpa data kredensial, tanpa dataset privat, menggunakan bobot resmi YOLOv8n dengan verifikasi hash SHA-256 kanonikal, serta dependensi yang terisolasi di dalam sesi notebook.

---

## 8. RISIKO, BATASAN, & KEPUTUSAN TATA KELOLA

### A. Risiko & Keterbatasan:
1. **Ketidakpastian Alokasi GPU Free Tier:** Google Colab Free dapat sewaktu-waktu mengalokasikan CPU jika kuota harian tercapai. Kaggle dapat sewaktu-waktu mengalokasikan Tesla P100 yang tidak kompatibel dengan TensorRT modern.
2. **Session Disconnection:** Sesi cloud notebook dapat terputus secara mendadak jika tab browser ditutup atau idle lebih dari 60 menit. Seluruh hasil benchmark harus segera diekspor sebagai berkas JSON sebelum sesi berakhir.

### B. Keputusan Tata Kelola yang Diperlukan dari Project Owner:
1. **Otorisasi Eksekusi Remote Lab:** Menyetujui pelaksanaan eksekusi notebook portabel di Google Colab Free (Gate 3).
2. **Pilihan Platform Utama:** Menetapkan **Google Colab Free (NVIDIA Tesla T4)** sebagai lingkungan remote resmi untuk Sprint 3.
3. **Penyelarasan Ruang Lingkup Teknologi:** Mengonfirmasi bahwa Sprint 3 berfokus pada **CUDA Inference, ONNX Runtime GPU, dan TensorRT Feasibility**, sementara **DeepStream dan Triton Server Production Daemon** diakui sebagai keterbatasan (*scope exclusion*) yang tidak layak diuji pada free-tier remote notebook.

---

## 9. REKOMENDASI TAHAP BERIKUTNYA

### **VONIS: PASS WITH LIMITATIONS**

- **Rekomendasi:** Mengajukan persetujuan Project Owner untuk melanjutkan ke **Sprint 3 Gate 3 — Remote GPU Trial Execution (Google Colab Free)**.
- **Kondisi:** Menunggu otorisasi resmi sebelum notebook diunggah atau dijalankan di Google Colab.
