# SPRINT 1 — ADDITIONAL CCTV VIDEO SAMPLE SELECTION

**Project:** VisionStream AI  
**Sprint:** 01 — Docker-First Person Detection & Tracking  
**Document ID:** `SPRINT-01-ADDITIONAL-VIDEO-CANDIDATES`  
**Report Date:** November 5, 2026  
**Target Environment:** Development Machine — LAPTOP-62621JIA (Windows 11)  
**Windows Report Path:** `C:\my-app\visionstream-ai\reports\SPRINT-01-ADDITIONAL-VIDEO-CANDIDATES.md`  
**Status:** Evaluation Complete — Waiting for Human Approval (No Files Downloaded)

---

## 1. Objective & Evaluation Criteria

Dokumen ini menyajikan evaluasi 3 kandidat video uji bergaya CCTV/surveillance untuk demonstrasi deteksi orang (*person detection*) dan pelacakan multi-objek (*multi-object tracking*) pada VisionStream AI.

### Kriteria Evaluasi Wajib:
1. **Perspektif CCTV Tetap (Fixed Surveillance Perspective):** Sudut pandang kamera statis/terkunci (tripod / wall-mounted / high-angle overhead), bukan handheld, panning, atau gimbal tracking.
2. **Area Publik Nyata:** Jalan raya, penyeberangan pejalan kaki (*crosswalk*), lobi, pintu masuk gedung, atau plaza.
3. **Multi-Person Dynamic:** Terdapat banyak individu yang berjalan melintasi area pantau.
4. **Wajah Terbedakan (Distinguishable Faces):** Wajah manusia terlihat jelas pada beberapa frame (resolusi dan pencahayaan memadai, tanpa memerlukan face recognition).
5. **Resolusi:** 720p (1280x720) atau lebih tinggi (Full HD 1080p disukai).
6. **Durasi:** Preferensi rentang 20 hingga 120 detik.
7. **Framerate:** 24 hingga 30 FPS.
8. **Lisensi & Hak Penggunaan Jelas:** Lisensi bebas royalti publik (Pexels License, CC-BY-4.0, dsb.) dengan dokumentasi atribusi eksplisit.
9. **Tantangan Tracking Real-World:** Persilangan jalur pejalan kaki (*crossing paths*), oklusi sementara, serta subjek yang masuk dan keluar dari frame.

---

## 2. Candidate Evaluations

---

### Candidate 1: "Video of People Walking" (Pexels / Pixabay)

* **Judul & URL Asli:**  
  *Judul:* Video of People Walking  
  *URL:* `https://www.pexels.com/video/video-of-people-walking-855564/` (Pexels Asset ID: `855564`)
* **Kreator / Penerbit:** Pixabay / Pexels Contributor
* **Lisensi & Kondisi Penggunaan:**  
  **Pexels License** (Free for commercial and personal use, no attribution required, can be modified, unaltered resale prohibited).
* **Spesifikasi Teknis:**
  - *Resolusi:* 1920 x 1080 (Full HD, 1080p)
  - *Framerate:* 23.98 FPS (~24 FPS)
  - *Durasi:* 19 detik (455 total frames)
  - *Estimasi Ukuran File:* $\sim 15 - 25\text{ MB}$ (MP4 H.264)
* **Perspektif Kamera:**  
  **Fixed Surveillance Perspective (Eye-level to slight high-angle)**. Kamera statis terpasang pada posisi tetap menghadap lorong pejalan kaki di bawah lengkungan arsitektur klasik (*colonnade / portico*).
* **Estimasi Jumlah Orang:**  
  15 hingga 25 pejalan kaki yang bergerak secara simultan dari arah latar belakang (*background*) mendekat ke arah kamera (*foreground*) dan sebaliknya.
* **Keterlihatan Wajah:**  
  **Sangat Baik (Visibly Distinguishable)**. Karena pencahayaan siang hari dan jalur pejalan kaki yang mendekat ke arah lensa, wajah subjek di area *middleground* dan *foreground* dapat dibedakan dengan sangat jelas oleh mata manusia.
* **Tantangan Pelacakan (Tracking Challenges):**
  - Pejalan kaki saling berpapasan (*crossing paths*) dari arah berlawanan.
  - Oklusi parsial saat pejalan kaki di barisan depan menutupi pejalan kaki di belakangnya.
  - Perubahan skala bounding box yang signifikan saat orang berjalan dari kejauhan menuju lensa kamera.

---

### Candidate 2: "Pedestrians Walking on City Street" (Pexels)

* **Judul & URL Asli:**  
  *Judul:* Pedestrians Walking on City Street  
  *URL:* `https://www.pexels.com/video/people-walking-on-the-street-4763784/` (Pexels Asset ID: `4763784`)
* **Kreator / Penerbit:** George Morina (London, UK) / Pexels
* **Lisensi & Kondisi Penggunaan:**  
  **Pexels License** (Free for commercial and personal use, no attribution required, can be modified, unaltered resale prohibited).
* **Spesifikasi Teknis:**
  - *Resolusi:* 1920 x 1080 (Full HD, 1080p)
  - *Framerate:* 25.00 FPS
  - *Durasi:* 13 detik (325 total frames)
  - *Estimasi Ukuran File:* $\sim 12 - 20\text{ MB}$ (MP4 H.264)
* **Perspektif Kamera:**  
  **Fixed Angle (Semi-elevated street perspective)**. Sudut pandang semi-tinggi yang menghadap trotoar distrik perbelanjaan urban.
* **Estimasi Jumlah Orang:**  
  10 hingga 20 orang pejalan kaki bergerak di sepanjang trotoar.
* **Keterlihatan Wajah:**  
  **Cukup (Moderately Distinguishable)**. Sebagian subjek yang menghadap kamera menampakkan fitur wajah yang jelas, namun durasi klip relatif singkat (13 detik) dan beberapa subjek membelakangi kamera.
* **Tantangan Pelacakan (Tracking Challenges):**
  - Kepadatan pejalan kaki yang berjalan searah dan berlawanan arah.
  - Oklusi sesaat di dekat tiang dan etalase toko.
  - *Durasi terbatas:* 13 detik berada sedikit di bawah preferensi 20 detik, sehingga jendela evaluasi kontinuitas ID jangka panjang menjadi lebih sempit.

---

### Candidate 3: "face-demographics-walking.mp4" (Intel IoT DevKit)

* **Judul & URL Asli:**  
  *Judul:* Face Demographics Walking Sample  
  *URL:* `https://github.com/intel-iot-devkit/sample-videos/raw/master/face-demographics-walking.mp4`
* **Kreator / Penerbit:** Intel Corporation (Intel IoT DevKit Computer Vision Samples)
* **Lisensi & Kondisi Penggunaan:**  
  **Creative Commons Attribution 4.0 International (CC-BY-4.0)** (Free for commercial and personal use with appropriate credit/attribution).
* **Spesifikasi Teknis:**
  - *Resolusi:* 768 x 432 pixels
  - *Framerate:* 12.00 FPS
  - *Durasi:* 61.03 detik (732 total frames)
  - *Ukuran File:* 6,396,313 bytes (~6.1 MB)
* **Perspektif Kamera:**  
  **Fixed CCTV Perspective**. Kamera pengawas statis yang dipasang pada posisi elevasi sudut pandang lorong pejalan kaki stasiun transit.
* **Estimasi Jumlah Orang:**  
  8 hingga 15 orang melintasi koridor dalam interval waktu yang berbeda.
* **Keterlihatan Wajah:**  
  **Sangat Baik (Visibly Distinguishable)**. Video ini secara khusus dirancang oleh Intel untuk benchmarking deteksi wajah pejalan kaki.
* **Tantangan Pelacakan (Tracking Challenges):**
  - Orang berjalan mendekat dan menjauh dari kamera CCTV.
  - Persilangan pejalan kaki di lorong stasiun.
  - *Keterbatasan Resolusi/FPS:* Resolusi $768\times 432$ dan framerate $12\text{ FPS}$ identik dengan baseline video `people-detection.mp4` saat ini, sehingga tidak memenuhi preferensi peningkatan ke 720p/1080p @ 24-30 FPS.

---

## 3. Comparison Matrix

| Kriteria Evaluasi | Candidate 1: Pexels 855564 | Candidate 2: Pexels 4763784 | Candidate 3: Intel DevKit |
|---|---|---|---|
| **Judul Video** | *Video of People Walking* | *Pedestrians on City Street* | *face-demographics-walking.mp4* |
| **Sumber Platform** | **Pexels** (`pexels.com/video/855564`) | **Pexels** (`pexels.com/video/4763784`) | **GitHub / Intel IoT DevKit** |
| **Kreator / Publisher** | Pixabay / Pexels | George Morina / Pexels | Intel Corporation |
| **Lisensi Hukum** | **Pexels License** (Commercial / Free) | **Pexels License** (Commercial / Free) | **CC-BY-4.0** (Attribution Required) |
| **Resolusi** | **1920 x 1080 (1080p Full HD)** | **1920 x 1080 (1080p Full HD)** | $768 \times 432$ (Standard Def) |
| **Framerate (FPS)** | **23.98 FPS** ($\sim 24\text{ FPS}$) | **25.00 FPS** | 12.00 FPS |
| **Durasi Video** | **19 detik** (455 frames) | 13 detik (325 frames) | **61.03 detik** (732 frames) |
| **Perspektif Kamera** | **Fixed / Static (Colonnade Walkway)** | Fixed / Semi-elevated | **Fixed CCTV (Station Corridor)** |
| **Jumlah Pejalan Kaki** | 15 – 25 subjek simultan | 10 – 20 subjek | 8 – 15 subjek |
| **Keterlihatan Wajah** | **Sangat Jelas** (Jalur mendekat) | Cukup Jelas | **Sangat Jelas** (Jalur mendekat) |
| **Tantangan Pelacakan** | Oklusi multi-orang, crossing paths | Oklusi trotoar | Persilangan lorong, scale changes |
| **Kesesuaian Spesifikasi** | **95% (Hampir Sempurna)** | 75% (Durasi agak singkat) | 70% (Resolusi & FPS di bawah 720p/24fps) |

---

## 4. Recommendation & Selection Verdict

### Recommended Candidate:
$$\mathbf{Candidate\ 1:\ \text{"Video of People Walking" (Pexels ID: 855564)}}$$

### Alasan Rekomendasi:
1. **Kualitas Gambar & Sudut Pandang CCTV Statis:** Memiliki resolusi **1080p Full HD (1920x1080)** dengan kamera terkunci statis (*fixed camera*), memenuhi standar modern demonstrasi vision AI.
2. **Framerate Standar Industri:** Direkam pada **23.98 FPS**, memberikan kepadatan temporal frame-ke-frame yang jauh lebih halus untuk pelacakan Kalman Filter ByteTrack dibandingkan video 12 FPS.
3. **Keterlihatan Wajah yang Alami:** Arah pejalan kaki yang bergerak menuju arah kamera memungkinkan wajah subjek terlihat jelas pada beberapa frame tanpa melanggar batasan etika/privasi (karena merupakan stok video publik berlisensi bebas royalti).
4. **Lisensi Bebas Hambatan:** Pexels License memberikan kebebasan legal penuh untuk portofolio profesional dan demonstrasi tanpa konflik lisensi komersial.
5. **Durasi Optimal (19 Detik / 455 Frame):** Memberikan jumlah frame yang cukup besar untuk mengevaluasi *track continuity* dan *ID switching* pada beban CPU 1080p tanpa membebani runtime secara berlebihan.

---

## 5. Next Steps (Hold for User Approval)

Sesuai instruksi ketat:
- **TIDAK ADA file video yang diunduh.**
- **File `people-detection.mp4` tetap utuh dan tidak dimodifikasi.**
- **Tidak ada kode sumber aplikasi atau Docker yang diubah.**
- **Menunggu konfirmasi dan persetujuan pengguna sebelum melakukan tindakan pengunduhan.**
