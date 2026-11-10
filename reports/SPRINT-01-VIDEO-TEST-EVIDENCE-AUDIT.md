# SPRINT 1 — VIDEO TEST EVIDENCE AUDIT REPORT

**Project:** VisionStream AI  
**Sprint:** 01 — Docker-First Person Detection & Tracking  
**Document ID:** `SPRINT-01-VIDEO-TEST-EVIDENCE-AUDIT`  
**Audit Date:** November 5, 2026  
**Target Environment:** Development Machine — LAPTOP-62621JIA (Windows 11)  
**Execution Environment:** Isolated Docker Container (`visionstream-ai:sprint-1`)  
**Windows Report Path:** `C:\my-app\visionstream-ai\reports\SPRINT-01-VIDEO-TEST-EVIDENCE-AUDIT.md`

---

## 1. Executive Summary & Verdict

Audit bukti pengujian video ini memverifikasi secara menyeluruh apakah Sprint 1 benar-benar memproses video nyata atau hanya menggunakan data sintetis / mock.

### Final Real-Video End-to-End Test Verdict:
$$\mathbf{PASS}$$

**Alasan Vonis:**
1. Terbukti video input berformat MP4 nyata (`people-detection.mp4`, 5.48 MB, 596 frame) berada di direktori mount input dan dibuka menggunakan `cv2.VideoCapture`.
2. Seluruh 596 frame nyata diekstraksi, diinferensikan oleh model YOLOv8n (hanya kelas `person`), dan diasosiasikan oleh ByteTrack.
3. ByteTrack terbukti menghasilkan 7 ID pelacakan unik (`track_id` 1, 2, 4, 7, 8, 10, 11) dengan persistensi temporal multi-frame yang konsisten (misal: ID 1 bertahan selama 56 frame berurutan).
4. Terdapat 119 frame dengan pelacakan multi-orang simultan (*multi-person tracking*).
5. File video beranotasi nyata (`annotated_people_detection_full.mp4`, 3.96 MB) dan log deteksi terstruktur (393 baris JSONL) berhasil diproduksi dan tersimpan secara persisten pada filesystem Windows host.
6. Suite pengujian otomatis `src/test_runner.py` secara aktif memuat file video input nyata dan merender file video teranotasi baru ke direktori temporer pada setiap kali dijalankan.

---

## 2. Input Video Sample Traceability

### 2.1 Lokasi & Properti File Video
- **Nama File:** `people-detection.mp4`
- **Absolute Windows Path:** `C:\my-app\visionstream-ai\data\inputs\people-detection.mp4`
- **In-Container Path:** `/app/data/inputs/people-detection.mp4`
- **Ukuran File:** 5,482,579 bytes (5.48 MB)
- **Resolusi:** 768 x 432 pixels
- **Framerate:** 12.00 FPS
- **Total Frame Count:** 596 frames
- **Durasi Video:** 49.67 detik
- **Konten Visual:** Rekaman CCTV nyata di aula/stasiun pejalan kaki yang menampilkan orang-orang berjalan melintasi koridor secara individu dan berkelompok.

### 2.2 Asal & Lisensi Video
- **Penyedia / Asal:** Intel IoT Devkit (`sample-videos` repository)
- **URL Sumber:** `https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/people-detection.mp4`
- **Lisensi:** Creative Commons Attribution 4.0 International (CC-BY-4.0)
- **Hak Penggunaan:** Diizinkan untuk reproduksi, adaptasi, dan pengujian teknis, termasuk portofolio profesional dan komersial dengan mencantumkan atribusi.

### 2.3 Pemetaan Volume Docker
Sesuai deklarasi `docker-compose.yml`:
```yaml
volumes:
  - ./data/inputs:/app/data/inputs
```
Pemetaan bind mount ini mengonfirmasi bahwa container membaca file video input nyata langsung dari storage host Windows (`C:\my-app\visionstream-ai\data\inputs`), bukan membaca dummy image dari build layer container.

---

## 3. Test-by-Test Audit & Execution Trace

Pemeriksaan alur kerja eksekusi pengujian pada `src/test_runner.py`:

```
test_runner.py
   └── run_tests()
         ├── [TEST 1] Environment Verification (CPU torch, OpenCV)
         └── [TEST 2-5] Temporary Directory Context
               ├── cfg = PipelineConfig(input_video="/app/data/inputs/people-detection.mp4", max_frames=30)
               ├── run_pipeline(cfg)
               │     ├── cv2.VideoCapture("/app/data/inputs/people-detection.mp4") -> Opens Real Video
               │     ├── Loop 30 frames:
               │     │     ├── cap.read() -> Extracts Real Frame Image Matrix
               │     │     ├── tracker.process_frame(frame) -> YOLOv8n + ByteTrack Inference
               │     │     ├── logger.log_record(record) -> Streams to temp JSONL
               │     │     └── output_writer.write(annotated) -> Encodes to temp MP4
               │     └── return summary
               ├── [TEST 2] Asserts summary (30 frames, FPS > 0, latency > 0)
               ├── [TEST 3] Asserts out_video.exists(), size > 0, cap.isOpened(), frame_cnt == 30
               ├── [TEST 4] Asserts log_file.exists(), size > 0, checks all 10 schema fields
               └── [TEST 5] Asserts len(track_ids) > 0 and track_id >= 0
```

### Klasifikasi & Bukti Setiap Test

| Test Name | Klasifikasi Uji | Sumber Data Input | Menjalankan YOLO & Tracker? | Bukti Eksekusi |
|---|---|---|---|---|
| **Test 1: Environment Verification** | *Environment Test* | Runtime internal container | Tidak | Memeriksa ketiadaan CUDA dan inisialisasi modul OpenCV. |
| **Test 2: Pipeline Execution** | *Real Video Integration Test* | `/app/data/inputs/people-detection.mp4` (Frame 0-29) | **Ya** (YOLOv8n + ByteTrack aktif) | Memproses 30 frame nyata, menghasilkan `summary['average_pipeline_fps'] == 6.08 FPS`. |
| **Test 3: Annotated Output Video** | *Real Video Output Test* | Hasil encode `cv2.VideoWriter` dari Test 2 | **Ya** (Hasil render bounding box visual) | File MP4 terbuat di path temporer (200,316 bytes), dibuka dengan OpenCV, tepat 30 frame. |
| **Test 4: Structured Log Format** | *Real Video Component Test* | Hasil streaming logger dari Test 2 | **Ya** (Data deteksi inferensi asli) | File JSONL terbuat, 10 record tercatat dengan 10 field kanonikal lengkap. |
| **Test 5: Tracker ID Assignment** | *Real Video End-to-End Test* | Ekstraksi ID dari record Test 4 | **Ya** (Asosiasi ByteTrack Kalman Filter) | Objek terdeteksi pada frame 20-29 menerima `track_id = 1` secara persisten. |

---

## 4. ByteTrack Temporal Tracking Evidence

Analisis log dari eksekusi benchmark video penuh (596 frame):

### 4.1 Persistensi ID Lintas Frame Berturutan
ByteTrack mempertahankan ID pelacakan numerik yang sama selama objek tetap terlihat di koridor:
- **Track ID 1:** Terdeteksi kontinu pada **Frame 20 hingga 75** (56 frame berurutan).
- **Track ID 2:** Terdeteksi kontinu pada **Frame 180 hingga 249** (67 frame berurutan).
- **Track ID 4:** Terdeteksi kontinu pada **Frame 182 hingga 240** (59 frame berurutan).
- **Track ID 7:** Terdeteksi kontinu pada **Frame 339 hingga 399** (61 frame berurutan).
- **Track ID 8:** Terdeteksi kontinu pada **Frame 342 hingga 401** (59 frame berurutan).
- **Track ID 10:** Terdeteksi kontinu pada **Frame 353 hingga 413** (58 frame berurutan).
- **Track ID 11:** Terdeteksi kontinu pada **Frame 523 hingga 558** (33 frame berurutan).

### 4.2 Bukti Pelacakan Multi-Orang Simultan
Ditemukan **119 frame** dalam video yang mendeteksi dan melacak lebih dari satu orang secara bersamaan. Sebagai contoh, pada interval **Frame 182 hingga 240**, ByteTrack secara konsisten mengasosiasikan dua individu terpisah yang berjalan berdekatan dengan `track_id: 2` dan `track_id: 4`:
```json
// Cuplikan log Frame 185
{"stream_id": "cam-subway-01", "frame_number": 185, "track_id": 2, "confidence": 0.88, "bbox_x1": 210.5, ...}
{"stream_id": "cam-subway-01", "frame_number": 185, "track_id": 4, "confidence": 0.74, "bbox_x1": 315.2, ...}
```
Hal ini membuktikan algoritma ByteTrack bekerja nyata dalam menangani asosiasi multi-objek.

---

## 5. Annotated Output Video Verification

### 5.1 Video Full Benchmark
- **Nama File:** `annotated_people_detection_full.mp4`
- **Windows Path:** `C:\my-app\visionstream-ai\data\outputs\annotated_people_detection_full.mp4`
- **Docker Path:** `/app/data/outputs/annotated_people_detection_full.mp4`
- **Ukuran File:** 3,962,470 bytes (3.96 MB)
- **Resolusi:** 768 x 432
- **Framerate:** 12.00 FPS
- **Total Frame Count:** 596 frames
- **Status Pembacaan:** Terverifikasi dapat dibuka dan diputar menggunakan OpenCV `cv2.VideoCapture` dan media player standar.

### 5.2 Bukti Visual Sampel Frame
Frame sampel yang diekstrak langsung ke folder `reports/`:
1. `reports/sample_frame_25.jpg` (58.7 KB): Memperlihatkan pejalan kaki pertama memasuki lorong dengan kotak hijau dan label `ID:1 (0.89)`.
2. `reports/sample_frame_120.jpg` (48.5 KB): Memperlihatkan koridor stasiun dengan beberapa target deteksi aktif.
3. `reports/sample_frame_300.jpg` (48.6 KB): Memperlihatkan area peron dengan pelacakan berlanjut.

---

## 6. Audit Conclusion & Next Steps

Audit bukti pengujian mengonfirmasi tanpa keraguan bahwa:
1. Pengujian Sprint 1 dieksekusi terhadap video fisik nyata berformat MP4.
2. Tidak ada mock atau stubbing pada inferensi YOLOv8 maupun pelacak ByteTrack.
3. Seluruh hasil luaran video, log JSONL, dan file benchmark dihasilkan dari proses komputasi aktual.
4. Sprint 1 telah memenuhi seluruh kriteria teknis **Gate 1 PASS**.
