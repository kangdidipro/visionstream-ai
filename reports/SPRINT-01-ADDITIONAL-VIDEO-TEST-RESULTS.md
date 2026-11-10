# SPRINT 1 — ADDITIONAL VIDEO DETECTION & TRACKING VALIDATION REPORT

**Project:** VisionStream AI  
**Task:** Additional CCTV Video Detection & ByteTrack Validation  
**Document ID:** `SPRINT-01-ADDITIONAL-VIDEO-TEST-RESULTS`  
**Execution Date:** November 5, 2026  
**Target Environment:** Development Machine — LAPTOP-62621JIA (Windows 11)  
**Execution Environment:** Isolated Docker Container (`visionstream-ai:sprint-1`)  
**Input Video:** `data/inputs/people-detection-faces.mp4` (Pexels Asset 855564, 1080p Full HD)  
**Original Baseline Video:** `data/inputs/people-detection.mp4` (Preserved & Unchanged)  
**Windows Report Path:** `C:\my-app\visionstream-ai\reports\SPRINT-01-ADDITIONAL-VIDEO-TEST-RESULTS.md`  
**Overall Verdict:** **PASS** (Robust Multi-Object Tracking across 1080p High-Density Scene)

---

## 1. Executive Summary & Verdict

Validasi inferensi dan pelacakan terhadap sampel video CCTV tambahan (`people-detection-faces.mp4`, 1920x1080, 23.98 FPS, 460 frame) telah diselesaikan 100% menggunakan arsitektur pipeline Sprint 1 di dalam Docker container tanpa memodifikasi kode sumber aplikasi, tanpa mengubah dependensi, dan tanpa memperkenalkan modul pengenalan wajah (*face recognition*).

### Ringkasan Hasil Validasi:
- **Total Frames Processed:** 460 / 460 frame (100% video selesai diproses).
- **Total Person Detections Logged:** **4,667 event deteksi** dicatat ke dalam log terstruktur JSONL.
- **Unique Tracking IDs:** **99 ID pelacakan unik** dialokasikan oleh algoritma ByteTrack sepanjang video.
- **Multi-Person Tracking:** **460 / 460 frame (100.0%)** berisi lebih dari satu orang secara simultan, dengan rata-rata **10.15 orang per frame** (rentang: 5 hingga 15 orang per frame).
- **Track Continuity Terlama:** Track ID 6 bertahan selama **367 frame** (dari frame 0 hingga frame 397), Track ID 1 bertahan selama **258 frame**, dan Track ID 57 bertahan selama **241 frame**.
- **CPU Throughput (1080p):** Rata-rata **8.08 FPS** dengan latensi inferensi rata-rata **71.86 ms/frame** pada CPU host AMD Ryzen 7 6800U.
- **Output Artifacts:** File video beranotasi MP4 Full HD (31.78 MB), log JSONL (1.13 MB), dan 4 gambar representatif beresolusi 1080p berhasil dibuat dan diverifikasi di filesystem host Windows.

---

## 2. Pre-Execution Verification (Integrity & Baselines)

Sebelum inferensi dijalankan, seluruh prasyarat integritas sistem telah divalidasi:
1. **Verifikasi Hash Video Input Baru:**  
   - Path: `data/inputs/people-detection-faces.mp4`  
   - SHA-256: `e32f2150b98488e7f1063f1fe15917e334caf510060c3ce96f131a0c89dce87b` (Cocok 100% dengan laporan akuisisi).
2. **Preservasi Video Baseline Asli:**  
   - Path: `data/inputs/people-detection.mp4`  
   - SHA-256: `18ffe8672d741e3e29c9d891d22c59d453720b086c25b35c88b393d55f92f693` (Tetap utuh, tidak tersentuh).
3. **Mount Docker:** Kedua video terekspos secara transparan di `/app/data/inputs/`.
4. **Bobot Model YOLO:** Bobot model resmi `/app/data/models/yolov8n.pt` siap digunakan di cache model volume.

---

## 3. Pipeline Execution Parameters

Eksekusi dijalankan via antarmuka pipeline resmi:
```bash
docker compose run --rm visionstream python3 src/pipeline.py \
  --input /app/data/inputs/people-detection-faces.mp4 \
  --output /app/data/outputs/annotated_people_detection_faces_1080p.mp4 \
  --stream-id cam-colonnade-02 \
  --session-id sprint1-additional-faces \
  --conf 0.35 \
  --iou 0.5 \
  --log-format jsonl
```

---

## 4. Detection & Tracking Analysis

### 4.1 Statistik Deteksi Orang
- **Total Deteksi Terdaftar:** 4,667 record.
- **Confidence Score Range:** Min $0.3503$, Max $0.9470$.
- **Rata-rata Confidence (Mean):** $0.6821$ (Median: $0.7008$).
- **Distribusi Confidence:**
  - $0.35 - 0.50$: 764 deteksi (16.4%) — mayoritas subjek kecil di latar belakang kejauhan.
  - $0.50 - 0.70$: 1,559 deteksi (33.4%) — subjek di area jarak menengah.
  - $0.70 - 0.85$: 1,494 deteksi (32.0%) — subjek di area tengah dan depan.
  - $0.85 - 1.00$: 850 deteksi (18.2%) — subjek yang terlihat utuh di area latar depan.

### 4.2 Dinamika Pelacakan ByteTrack & Kontinuitas ID
- **Kepadatan Adegan (Scene Density):** 100% frame mengandung multi-person secara bersamaan, dengan rata-rata 10.15 orang per frame.
- **Kontinuitas Pelacakan Jangka Panjang:**
  - *Track ID 6:* Bertahan selama **367 frame** (Frame 0 s.d. 397).
  - *Track ID 1:* Bertahan selama **258 frame** (Frame 0 s.d. 257).
  - *Track ID 57:* Bertahan selama **241 frame** (Frame 123 s.d. 385).
  - *Track ID 11:* Bertahan selama **236 frame** (Frame 0 s.d. 262).
  - *Track ID 111:* Bertahan selama **183 frame** (Frame 275 s.d. 459).
  - *Track ID 104:* Bertahan selama **181 frame** (Frame 253 s.d. 435).
  - *Track ID 94:* Bertahan selama **174 frame** (Frame 227 s.d. 419).
  - *Track ID 103:* Bertahan selama **170 frame** (Frame 252 s.d. 456).
- **Perubahan Skala (Scale Magnification) Saat Mendekati Kamera:**  
  Sebagai contoh, subjek pada **Track ID 57** yang mulai terdeteksi di latar belakang pada Frame 123 memiliki area bounding box $51,098.8\text{ px}^2$ ($161.2 \times 317.0\text{ px}$). Ketika subjek berjalan mendekat ke arah kamera pada Frame 385, area kotak membesar menjadi $109,000.3\text{ px}^2$ ($209.3 \times 520.8\text{ px}$), menunjukkan faktor pembesaran skala **2.13x** yang berhasil diakomodasi oleh Kalman Filter ByteTrack tanpa kehilangan asosiasi ID.
- **Fragmentasi & ID Switching:**  
  Terjadi 99 ID yang teralokasi sepanjang 19 detik klip. Tingginya jumlah alokasi ID disebabkan oleh:
  1. Pejalan kaki yang baru masuk dan keluar dari tepi bingkai kamera (*entering/exiting frame boundaries*).
  2. Oklusi total sesaat ketika subjek di latar belakang tertutup sepenuhnya oleh pejalan kaki di baris depan yang lebih besar. Ketika subjek muncul kembali beberapa frame kemudian, ByteTrack mengalokasikan ID baru secara aman sesuai sifat pelacak non-ReID (tanpa Re-ID fitur visual permanen).

---

## 5. Benchmark & Resource Utilization

### 5.1 Perbandingan Metrik: Baseline vs. Video Tambahan

> [!IMPORTANT]
> **Catatan Analisis:** Perbedaan throughput di bawah ini murni mencerminkan perbedaan resolusi spasial ($768\times 432$ vs. $1920\times 1080$), framerate native ($12\text{ FPS}$ vs. $24\text{ FPS}$), serta kepadatan deteksi rata-rata per frame ($0.66$ orang vs. $10.15$ orang per frame). Ini **bukan perbandingan degradasi model**, melainkan tolok ukur beban komputasi resolusi tinggi.

| Parameter Pengukuran | Baseline: `people-detection.mp4` | Video Baru: `people-detection-faces.mp4` |
|---|---|---|
| **Resolusi Input** | $768 \times 432$ (SD) | **$1920 \times 1080$ (Full HD 1080p)** |
| **Native Video FPS** | 12.00 FPS | **23.98 FPS** |
| **Durasi Video** | 49.67 detik | **19.19 detik** |
| **Total Frame Diproses** | 596 frame | **460 frame** |
| **Total Deteksi Terdaftar** | 393 deteksi | **4,667 deteksi (11.8x lebih padat)** |
| **Rata-rata Orang / Frame** | ~0.66 orang / frame | **~10.15 orang / frame** |
| **Total Waktu Pemrosesan** | 48.517 detik | **56.902 detik** |
| **Rata-rata Throughput Pipeline** | **12.28 FPS** | **8.08 FPS** |
| **Rata-rata Latensi Inferensi YOLO** | **62.23 ms / frame** | **71.86 ms / frame** |
| **Rata-rata Latensi End-to-End Pipeline** | **77.88 ms / frame** | **102.90 ms / frame** |
| **Hardware Host** | AMD Ryzen 7 6800U (CPU-only) | AMD Ryzen 7 6800U (CPU-only) |

### 5.2 Analisis Latensi
- Waktu inferensi forward-pass YOLOv8n pada resolusi 1080p hanya meningkat sedikit ($62.23\text{ ms} \rightarrow 71.86\text{ ms}$) karena input tensor YOLO di-resize secara otomatis ke dimensi $640\times 640$ oleh Ultralytics pre-processing.
- Waktu siklus frame end-to-end meningkat dari $77.88\text{ ms}$ menjadi $102.90\text{ ms}$ terutama akibat beban decoding frame 1080p yang jauh lebih besar ($1920\times 1080$ piksel vs $768\times 432$), asosiasi matriks Kalman Filter untuk 10–15 orang simultan per frame, rendering On-Screen Display pada kanvas 1080p, dan encoding H.264/MP4 pada resolusi Full HD.

---

## 6. Output Artifacts & Representative Frames

Seluruh artefak hasil eksekusi telah diverifikasi di sistem host Windows:

### 6.1 Video & Log Files
- **Annotated Video:**  
  `C:\my-app\visionstream-ai\data\outputs\annotated_people_detection_faces_1080p.mp4` (31,783,509 bytes / 31.78 MB, 460 frame, valid MP4).
- **Structured Log File:**  
  `C:\my-app\visionstream-ai\logs\detections_cam-colonnade-02_sprint1-additional-faces.jsonl` (1,128,705 bytes / 1.13 MB, 4,667 baris JSON).
- **Benchmark JSON Summary:**  
  `C:\my-app\visionstream-ai\reports\benchmark_cam-colonnade-02_sprint1-additional-faces.json` (783 bytes).

### 6.2 Representative Output Frames
Empat frame sampel beranotasi diekstrak langsung ke direktori `reports/` untuk inspeksi visual manusia:
1. [`reports/annotated_faces_frame_50.jpg`](file:///c:/my-app/visionstream-ai/reports/annotated_faces_frame_50.jpg) (Frame 50, 372.8 KB): Memperlihatkan kerumunan pejalan kaki di lorong dengan pelacakan simultan `ID:1`, `ID:5`, `ID:6`, `ID:11`, `ID:13`, `ID:16`, `ID:18`.
2. [`reports/annotated_faces_frame_150.jpg`](file:///c:/my-app/visionstream-ai/reports/annotated_faces_frame_150.jpg) (Frame 150, 395.5 KB): Memperlihatkan persilangan pejalan kaki dari dua arah dengan bounding box multi-warna dan label confidence.
3. [`reports/annotated_faces_frame_250.jpg`](file:///c:/my-app/visionstream-ai/reports/annotated_faces_frame_250.jpg) (Frame 250, 295.6 KB): Memperlihatkan subjek yang mendekat ke latar depan dengan pembesaran skala dan pelacak tetap terkunci.
4. [`reports/annotated_faces_frame_350.jpg`](file:///c:/my-app/visionstream-ai/reports/annotated_faces_frame_350.jpg) (Frame 350, 337.1 KB): Memperlihatkan pejalan kaki yang keluar dari area pantau di bagian bawah dan subjek baru yang masuk dari latar belakang.

---

## 7. Known Issues & Operational Observations

1. **Throughput Scaling pada Resolusi 1080p:** Pipeline menghasilkan throughput 8.08 FPS pada video Full HD 1080p ketika dijalankan murni pada CPU host tanpa akselerator hardware. Untuk mencapai framerate real-time 24 FPS pada video 1080p, diperlukan optimasi kompilasi model (OpenVINO / ONNX Runtime AVX2) dan pemisahan thread decoding video.
2. **Oklusi di Area Padat:** Pada kepadatan 15 orang, pejalan kaki yang melintas persis di belakang pejalan kaki berbadan besar di latar depan mengalami kehilangan deteksi sementara selama 2–4 frame, yang memicu pembuatan ID baru saat muncul kembali. Hal ini sesuai dengan batas kapabilitas tracker spasial murni tanpa Re-ID deep appearance feature.
3. **Deteksi Kelas Manusia Terisolasi:** Model secara konsisten hanya mendeteksi kelas `person` (COCO ID 0). Tiang, lentera, dan lantai kolonnade tidak memicu false positive.

---

## 8. Final Verdict & Next Steps

$$\mathbf{FINAL\ VERDICT:\ PASS}$$

Pengujian terhadap sampel video CCTV 1080p berdensitas tinggi berhasil memvalidasi ketahanan (*robustness*) pipeline deteksi orang dan pelacakan ByteTrack Sprint 1 dalam skenario nyata yang jauh lebih kompleks daripada video baseline. Seluruh batasan ketat dipatuhi sepenuhnya.
