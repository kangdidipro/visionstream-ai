# SPRINT 1 — ADDITIONAL CCTV VIDEO ACQUISITION REPORT

**Project:** VisionStream AI  
**Task:** Additional CCTV Video Sample Validation & Acquisition  
**Document ID:** `SPRINT-01-ADDITIONAL-VIDEO-ACQUISITION`  
**Execution Date:** November 5, 2026  
**Target Environment:** Development Machine — LAPTOP-62621JIA (Windows 11)  
**Execution Environment:** Isolated Docker Container (`visionstream-ai:sprint-1`)  
**Windows Report Path:** `C:\my-app\visionstream-ai\reports\SPRINT-01-ADDITIONAL-VIDEO-ACQUISITION.md`  
**Status:** **ACQUISITION & INTEGRITY VERIFIED (PASS)**

---

## 1. Executive Summary

Sesuai otorisasi pengguna pada tahap seleksi kandidat, **Candidate 1** telah divalidasi secara visual, diunduh, dan diverifikasi integritasnya secara menyeluruh tanpa mengorbankan atau mengubah aset baseline asli (`people-detection.mp4`).

Video tambahan ini disimpan pada lokasi:
`C:\my-app\visionstream-ai\data\inputs\people-detection-faces.mp4`

Pengujian decoding dan ekstraksi metadata dilakukan langsung di dalam container Docker menggunakan `OpenCV` dan `FFmpeg/ffprobe`. Tidak ada modifikasi kode aplikasi, tidak ada perubahan arsitektur Docker Compose, dan tidak ada inferensi deteksi yang dijalankan pada task ini sesuai aturan *Strict Restrictions*.

---

## 2. Source Information & License Audit

| Parameter | Detail Sumber Resmi |
|---|---|
| **Platform** | Pexels (`https://www.pexels.com`) |
| **Asset ID** | `855564` |
| **Judul Asli** | *Video of People Walking* |
| **Halaman Resmi** | `https://www.pexels.com/video/video-of-people-walking-855564/` |
| **Direct CDN URL** | `https://videos.pexels.com/video-files/855564/855564-hd_1920_1080_24fps.mp4` |
| **Kreator / Uploader** | Pixabay / Pexels Contributor |
| **Lisensi Hukum** | **Pexels License** |
| **Ketentuan Penggunaan** | - Bebas digunakan untuk keperluan personal dan komersial.<br/>- Atribusi tidak diwajibkan secara hukum (tetap didokumentasikan untuk integritas portofolio).<br/>- Diizinkan untuk modifikasi dan pengolahan computer vision.<br/>- Dilarang menjual kembali salinan video mentah tanpa perubahan. |

---

## 3. Step 1 — Final Visual Validation Findings

Validasi visual dilakukan dengan menginspeksi preview video aktual dan mengekstrak frame representatif di berbagai titik waktu klip:
- `reports/preview_candidate1_frame_46.jpg` (Frame 46 — 10% durasi)
- `reports/preview_candidate1_frame_138.jpg` (Frame 138 — 30% durasi)
- `reports/preview_candidate1_frame_230.jpg` (Frame 230 — 50% durasi)
- `reports/preview_candidate1_frame_322.jpg` (Frame 322 — 70% durasi)
- `reports/preview_candidate1_frame_414.jpg` (Frame 414 — 90% durasi)

### Hasil Pemeriksaan Kriteria Wajib:
1. **Kamera Statis (Fixed Surveillance Perspective):**  
   **CONFIRMED (PASS).** Kamera terkunci diam pada posisi elevasi tetap menghadap koridor beratap lengkungan arsitektur klasik (*colonnade*). Analisis metrik perbedaan absolut piksel (*absolute difference*) pada area arsitektur latar belakang statis antar frame menghasilkan nilai $\Delta = 1.78$, membuktikan tidak ada pergerakan kamera (no panning, no handheld wobble).
2. **Keberadaan Multi-Person:**  
   **CONFIRMED (PASS).** Terlihat antara 15 hingga 25 individu berjalan melintasi koridor secara kontinu sepanjang 19 detik klip.
3. **Keterlihatan Wajah Manusia (Distinguishable Faces):**  
   **CONFIRMED (PASS).** Karena sebagian pejalan kaki bergerak dari latar belakang menuju arah kamera di bawah pencahayaan siang hari yang terang, fitur wajah terlihat jelas dan dapat dibedakan oleh mata manusia pada frame jarak menengah dan dekat.
4. **Persilangan Jalur & Dinamika Pelacakan (Tracking Suitability):**  
   **CONFIRMED (PASS).** Pejalan kaki berjalan dalam dua arah berlawanan, menciptakan skenario saling berpapasan (*crossing paths*), oklusi parsial sesaat, dan perubahan skala deteksi yang representatif untuk pengujian multi-object tracking.
5. **Kesesuaian Lisensi:**  
   **CONFIRMED (PASS).** Berlisensi Pexels License resmi untuk demonstrasi portofolio profesional.

---

## 4. Step 2 & 3 — File Acquisition, Integrity & Metadata

Video diunduh langsung dari CDN resmi Pexels ke volume input proyek di dalam container.

### 4.1 Spesifikasi Metadata Aktual (Inspeksi Docker ffprobe & OpenCV)

| Atribut Metadata | Nilai Aktual Terverifikasi | Nilai Ekspektasi Pexels | Status Kesesuaian |
|---|---|---|---|
| **Nama File** | `people-detection-faces.mp4` | `people-detection-faces.mp4` | **Identik** |
| **Ukuran File** | 8,284,362 bytes (8.28 MB) | $\sim 8.28\text{ MB}$ | **Valid (Bukan HTML stub)** |
| **SHA-256 Checksum** | `e32f2150b98488e7f1063f1fe15917e334caf510060c3ce96f131a0c89dce87b` | - | **Tervalidasi & Tercatat** |
| **Resolusi Spasial** | **1920 x 1080** (Full HD) | 1920 x 1080 | **Sesuai Ekspektasi (1080p)** |
| **Framerate (FPS)** | **23.9760 FPS** (24000/1001) | ~23.98 FPS | **Sesuai Standar 24p** |
| **Total Frame Count** | **460 frames** | ~455-460 frames | **Lengkap (100%)** |
| **Durasi Waktu** | **19.19 detik** | 19 detik | **Sesuai Ekspektasi** |
| **Video Codec** | `h264` (High Profile) | H.264 / AVC | **Valid** |
| **Pixel Format** | `yuv420p` | yuv420p | **Kompatibel OpenCV** |
| **Audio Stream** | Tidak ada (*No audio stream*) | N/A | **Optimal untuk CV** |
| **Container Format** | ISO Media MP4 (`isom/iso2/avc1/mp41`) | MP4 | **Valid** |
| **OpenCV Decoding** | `cv2.VideoCapture.isOpened() == True` | True | **PASS** |

---

## 5. Step 4 — Docker Input Mount Verification

Pemetaan bind mount pada `docker-compose.yml`:
```yaml
volumes:
  - ./data/inputs:/app/data/inputs
```

Inspeksi direktori `/app/data/inputs` di dalam container `visionstream-ai:sprint-1` mengonfirmasi:
```
-rw-r--r-- 1 root root 8284362 Nov  5 11:25 people-detection-faces.mp4
-rw-r--r-- 1 root root 5482579 Nov  5 09:50 people-detection.mp4
```
File baru langsung terekspos di `/app/data/inputs/people-detection-faces.mp4` tanpa perlu mengubah konfigurasi Docker Compose.

---

## 6. Baseline Preservation Confirmation

Integritas video baseline awal `people-detection.mp4` telah diverifikasi secara ketat:
- **Lokasi Host:** `C:\my-app\visionstream-ai\data\inputs\people-detection.mp4`
- **Ukuran File:** `5,482,579 bytes` (Tidak berubah)
- **SHA-256 Checksum:** `18ffe8672d741e3e29c9d891d22c59d453720b086c25b35c88b393d55f92f693` (Identik dengan hasil audit Sprint 1)
- **Status:** **PRESERVED & UNCHANGED**.

---

## 7. Strict Restrictions Compliance Check

| Batasan Ketat | Status Kepatuhan | Keterangan |
|---|---|---|
| **No Face Detection / Recognition** | **COMPLIANT** | Tidak ada library atau modul pengenalan wajah yang diinstal atau dipanggil. |
| **No Re-ID Implementation** | **COMPLIANT** | Tidak ada Re-ID lintas kamera. |
| **No Source Code Changes** | **COMPLIANT** | File `src/pipeline.py`, `src/detector.py`, dll. tidak diubah. |
| **No Dependency / Docker Changes** | **COMPLIANT** | `Dockerfile`, `docker-compose.yml`, dan `requirements.txt` tidak dimodifikasi. |
| **Preserve Original Baseline** | **COMPLIANT** | File `people-detection.mp4` tetap utuh. |
| **No Inference in this Task** | **COMPLIANT** | Pipeline deteksi tidak dieksekusi pada task akuisisi ini. |
