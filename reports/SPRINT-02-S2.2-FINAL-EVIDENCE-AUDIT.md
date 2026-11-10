# SPRINT 2 — FINAL TECHNICAL EVIDENCE AUDIT
## TASK S2.2: DATASET ACQUISITION & PREPROCESSING VERIFICATION

**Project:** VisionStream AI  
**Audit Identifier:** `S2.2 — Final Technical Evidence Audit`  
**Governing Phase:** Phase 3 (Operational Sprint 2 — Model Training & Evaluation)  
**Execution Environment:** Development Machine `LAPTOP-62621JIA` (Docker Container Isolation)  
**Audit Mode:** Read-Only Verification — Zero Code / Data / Docker Modification  
**Document Date:** November 5, 2026  
**Canonical File Location:** `C:\my-app\visionstream-ai\reports\SPRINT-02-S2.2-FINAL-EVIDENCE-AUDIT.md`  
**Audit Verdict:** **PASS WITH LIMITATIONS** (Dataset Validated — Methodological & License Verification Distinctions Formally Established)

---

## 1. Executive Summary

Audit teknis independen dan *read-only* telah dilakukan terhadap seluruh artefak yang dihasilkan pada **Task S2.2 (Dataset Acquisition & Preprocessing)**. Audit ini mencakup inspeksi perubahan konfigurasi Docker Compose, integritas struktur dan isi dataset `coco-person`, penelaahan bukti lisensi dan atribusi citra, analisis keterbatasan metodologis domain COCO, serta konfirmasi kepatuhan terhadap batasan eksekusi (*execution boundary*).

Hasil audit memverifikasi:
1. **Modifikasi Konfigurasi:** Penambahan mount volume `./data/datasets:/app/data/datasets` pada `docker-compose.yml` telah diverifikasi secara tepat sasaran, terisolasi penuh, dan tidak mengganggu fungsionalitas pipeline Sprint 1 maupun container eksternal lainnya.
2. **Integritas Dataset:** Sebanyak **2,479 citra** (2,000 Train, 239 Val, 240 Test) dan **2,479 file label YOLO** yang berisi **9,969 bounding box person** terverifikasi 100% utuh, saling lepas (*strictly disjoint* tanpa tumpang tindih ID maupun hash SHA-256), dengan koordinat ternormalisasi yang valid. Seluruh 2,479 file lulus verifikasi checksum SHA-256 (0 *mismatch*).
3. **Status Lisensi:** Seluruh 2,479 citra memiliki **License ID 4 (CC BY 2.0)** berdasarkan metadata resmi anotasi COCO Consortium. Audit menetapkan perbedaan tegas bahwa verifikasi lisensi ini didasarkan pada metadata COCO resmi (bukan verifikasi API langsung secara independen ke Flickr).
4. **Keterbatasan Metodologis:** Eksperimen mendatang diklasifikasikan secara formal sebagai *continued fine-tuning within the COCO domain*, bukan sebagai pengujian generalisasi pada dataset independen baru, mengingat bobot awal `yolov8n.pt` telah melihat distribusi COCO Train2017 dan arsitektur Ultralytics berpotensi divalidasi terhadap COCO Val2017.

Vonis resmi audit ini adalah **PASS WITH LIMITATIONS**.

---

## 2. Audit 1 — Docker Compose & Git Ignore Change Investigation

### 2.1 Git Status & Riwayat Perubahan
Repositori Git lokal saat ini berada pada cabang `master` dalam status repositori baru tanpa riwayat komit sebelumnya (*initial state, no commits yet*). Oleh karena itu, *diff* historis komit Git tidak dapat ditarik secara otomatis dari riwayat commit. Namun, perbandingan langsung terhadap struktur dasar konfigurasi Sprint 1 dan log eksekusi menghasilkan rekonstruksi yang pasti:

#### A. Rekonstruksi Diff `docker-compose.yml`
```diff
     volumes:
       - ./src:/app/src
       - ./data/inputs:/app/data/inputs
       - ./data/outputs:/app/data/outputs
       - ./data/models:/app/data/models
+      - ./data/datasets:/app/data/datasets
       - ./logs:/app/logs
       - ./reports:/app/reports
```

#### B. Rekonstruksi Diff `.gitignore`
```diff
 # Data and models
 data/inputs/*
 !data/inputs/.gitkeep
 data/outputs/*
 !data/outputs/.gitkeep
 data/models/*
 !data/models/.gitkeep
+data/datasets/*
+!data/datasets/.gitkeep
```

### 2.2 Penilaian Teknis Modifikasi
1. **Alasan Modifikasi:** Task S2.2 mengamanatkan pembuatan direktori dataset terkurasi pada `data/datasets/coco-person` di host Windows dan mewajibkan seluruh pemrosesan Python berjalan di dalam container Docker. Penambahan mount volume `- ./data/datasets:/app/data/datasets` diperlukan secara teknis agar container Docker dapat membaca dan menulis file dataset di host.
2. **Dampak terhadap Layanan / Container Lain:** Tidak ada layanan atau container lain yang terpengaruh. Proyek VisionStream AI hanya mendefinisikan satu service (`visionstream`) pada satu container runner (`visionstream-ai-runner`).
3. **Dampak terhadap Konfigurasi Runtime Sprint 1:** Tidak ada variabel lingkungan, port, atau dependensi arsitektur Sprint 1 yang diubah. Mount volume `./data/inputs`, `./data/outputs`, `./data/models`, `./src`, dan `./reports` tetap identik dan tidak terganggu.
4. **Verifikasi Jalur Mount di Dalam Container:** Pengujian read-only mengonfirmasi bahwa jalur `/app/data/datasets/coco-person` ter-mount dengan sempurna di dalam container dan dapat diakses dengan permission penuh (2,000 file train terbaca langsung).
5. **Kepatuhan Kebijakan Isolasi:** Tidak ada direktori sistem Windows (`C:\`) yang di-mount. Hanya subfolder proyek eksplisit `./data/datasets` yang di-mount. Penambahan aturan pada `.gitignore` berhasil mencegah commit file citra mentah (~392 MB) ke repositori publik.

---

## 3. Audit 2 — Dataset Integrity Verification

Audit verifikasi *read-only* dijalankan langsung terhadap dataset di `data/datasets/coco-person/` tanpa regenerasi atau modifikasi data.

### 3.1 Kuantitas File dan Anotasi
- **Train Split:** 2,000 file citra JPG (`images/train/`) $\leftrightarrow$ 2,000 file label TXT (`labels/train/`).
- **Validation Split:** 239 file citra JPG (`images/val/`) $\leftrightarrow$ 239 file label TXT (`labels/val/`).
- **Holdout Test Split:** 240 file citra JPG (`images/test/`) $\leftrightarrow$ 240 file label TXT (`labels/test/`).
- **Total Citra & Label:** Tepat **2,479 citra** dan **2,479 file label**.
- **Total Bounding Box Person:** Tepat **9,969 kotak** (Train: 8,024, Val: 983, Test: 962). Rata-rata: 4.02 kotak per citra.

### 3.2 Integritas Format & Koordinat YOLO
- Seluruh 2,479 file label berisi sintaks YOLO valid: `0 <x_center> <y_center> <width> <height>`.
- Seluruh koordinat berada dalam batas ternormalisasi: $0.0 \le x_c, y_c \le 1.0$ dan $0.0 < w, h \le 1.0$.
- Tidak ditemukan baris rusak (*malformed line*), zero-area box, atau file label kosong dalam kumpulan person terkurasi.
- Seluruh anotasi dengan flag `iscrowd == 1` telah dikecualikan.

### 3.3 Pemisahan Split (*Disjointness*) & Uji Duplikasi
Audit independen memeriksa Image ID dan hash SHA-256 konten citra:
- $\text{Train ID} \cap \text{Val ID} = \emptyset$ (0 overlap).
- $\text{Train ID} \cap \text{Test ID} = \emptyset$ (0 overlap).
- $\text{Val ID} \cap \text{Test ID} = \emptyset$ (0 overlap).
- $\text{Train SHA-256} \cap \text{Val SHA-256} = \emptyset$ (0 overlap).
- $\text{Train SHA-256} \cap \text{Test SHA-256} = \emptyset$ (0 overlap).
- $\text{Val SHA-256} \cap \text{Test SHA-256} = \emptyset$ (0 overlap).
- **Hasil:** Independensi data terjamin 100% tanpa kebocoran data (*zero data leakage*).

### 3.4 Verifikasi Checksum SHA-256
File [`metadata/checksums.sha256`](file:///c:/my-app/visionstream-ai/data/datasets/coco-person/metadata/checksums.sha256) memuat 2,479 hash SHA-256. Verifikasi audit penuh terhadap seluruh 2,479 file biner citra di disk menghasilkan:
- **Jumlah file diperiksa:** 2,479 file.
- **Mismatch:** **0**.
- **Status:** **100% PASS**.

### 3.5 Verifikasi `dataset.yaml`
File konfigurasi Ultralytics memuat konfigurasi yang valid dan dapat di-resolve di dalam container:
```yaml
path: /app/data/datasets/coco-person
train: images/train
val: images/val
test: images/test

names:
  0: person
```

---

## 4. Audit 3 — License and Attribution Evidence Assessment

### 4.1 Bukti Lisensi pada Metadata Manifest
Pemeriksaan menyeluruh terhadap [`metadata/image-manifest.json`](file:///c:/my-app/visionstream-ai/data/datasets/coco-person/metadata/image-manifest.json) (2,479 entri) mengonfirmasi:
- **Distribusi License ID:** 100% License ID `4`.
- **Nama Lisensi:** `Attribution License (CC BY 2.0)`.
- **URL Lisensi Resmi:** `http://creativecommons.org/licenses/by/2.0/`.
- **Kelengkapan Atribusi:** Seluruh 2,479 entri memiliki URL Flickr asli (`flickr_url`), URL COCO CDN (`coco_url`), tanggal pengambilan (`date_captured`), dimensi citra, dan ID citra.
- **Pengecualian Lisensi Lain:** Tidak ditemukan License ID 1, 2, 3 (Non-commercial), License 5 (CC BY-SA), License 6 (No-derivatives), atau License 7.

### 4.2 Perbedaan Penting: Metadata Resmi COCO vs Verifikasi Sumber Langsung Flickr
Audit ini secara eksplisit membedakan derajat verifikasi hukum:
1. **Verifikasi Berdasarkan Metadata Anotasi COCO Resmi:**  
   Status lisensi CC BY 2.0 (License ID 4) diverifikasi secara sah dari file metadata resmi COCO Consortium (`instances_train2017.json` dan `instances_val2017.json`).
2. **Keterbatasan Verifikasi Langsung Flickr API:**  
   Proyek ini **tidak melakukan permintaan API independen langsung ke server Flickr** untuk mengonfirmasi status lisensi real-time terkini dari setiap tautan foto fotografer (banyak tautan Flickr berumur lebih dari satu dekade). Oleh karena itu, klaim kelayakan hukum didasarkan pada catatan metadata kurasi resmi COCO Consortium, bukan audit langsung ke pemilik akun Flickr.

---

## 5. Audit 4 — Methodology Limitations & Generalization Scope

Untuk menjaga integritas ilmiah dan standar portofolio profesional, batasan metodologis berikut didokumentasikan secara transparan:

1. **Tumpang Tindih Data Pelatihan Pretrained YOLOv8n:**
   Checkpoint awal `yolov8n.pt` resmi dari Ultralytics dilatih pada keseluruhan dataset COCO Train2017 (118,287 citra, mencakup ~64,115 citra berlabel orang). Sebanyak 2,000 citra train yang diakuisisi pada pilot ini merupakan bagian dari domain pelatihan asli model tersebut.
2. **Potensi Pemaparan COCO Val2017 pada Model Baseline:**
   Dalam literatur deep learning dan rilis Ultralytics YOLOv8, metrik performa model pretrained (`yolov8n.pt`) diukur dan dituning hyperparameternya berdasarkan kumpulan data COCO Val2017. Akibatnya, citra validasi (239 citra) dan holdout test (240 citra) yang bersumber dari Val2017 memiliki kemungkinan pernah terpapar pada proses evaluasi arsitektur dasar YOLOv8.
3. **Keterbatasan Uji Holdout Test untuk Generalisasi Independen:**
   Holdout test set (240 citra) dalam eksperimen ini **tidak dapat diklaim sebagai benchmark generalisasi out-of-domain yang independen**. Holdout test ini berfungsi murni untuk mengukur dampak adaptasi parameter bobot pada subset spesifik kelas `person` di dalam domain distribusi data COCO.
4. **Definisi Formal Eksperimen:**
   Eksperimen fine-tuning mendatang (Task S2.3) wajib didefinisikan secara jujur sebagai:  
   **"Continued domain fine-tuning / single-class focus within the existing COCO distribution"**,  
   bukan sebagai adaptasi domain baru atau pelatihan dari awal (*from scratch*).

---

## 6. Audit 5 — Strict Execution Boundary Verification

Audit memverifikasi kepatuhan terhadap batasan eksekusi yang diamanatkan:

| Batasan / Kriteria Audit | Status Kepatuhan | Bukti Verifikasi |
|:---|:---:|:---|
| **Pelatihan Model / Fine-Tuning** | **TIDAK DIJALANKAN (PASS)** | Tidak ada bobot baru (`best.pt`, `last.pt`) atau direktori runs training dibuat. |
| **Inferensi Model / Benchmarking** | **TIDAK DIJALANKAN (PASS)** | Tidak ada pengujian inferensi baru dijalankan pada dataset. |
| **Alokasi Sumber Daya Cloud / GPU** | **TIDAK DIJALANKAN (PASS)** | Tidak ada koneksi, alokasi Colab, atau cloud berbayar yang digunakan. |
| **Pembelian Lisensi / Layanan Berbayar**| **TIDAK DIJALANKAN (PASS)** | Nol biaya finansial ($0). |
| **Integritas Artefak Sprint 0 & 1** | **TERJAGA 100% (PASS)** | Seluruh laporan, bobot `yolov8n.pt`, dan video input/output Sprint 1 utuh. |
| **Isolasi Host Windows** | **TERJAGA 100% (PASS)** | Nol paket Python diinstal di host; tidak ada `.venv` dibuat di host. |
| **Status Gerbang S2.3** | **BELUM DIMULAI (HOLD)** | S2.3 tetap berada dalam status HOLD menunggu otorisasi terpisah. |

---

## 7. Final Recommendation & Verdict

Berdasarkan hasil audit teknis:
- Seluruh 2,479 citra dan label dataset COCO person-only pilot telah terverifikasi utuh, valid, dan saling lepas.
- Konfigurasi Docker Compose dan Git ignore terbukti aman dan mempertahankan kebijakan isolasi.
- Seluruh batasan eksekusi dipatuhi secara ketat.

**VONIS RESMI:** **PASS WITH LIMITATIONS**

*Catatan Limitasi:*
1. Status lisensi CC BY 2.0 diverifikasi berdasarkan metadata resmi anotasi COCO, bukan audit langsung ke Flickr API individual.
2. Eksperimen fine-tuning di masa mendatang didefinisikan sebagai *continued COCO-domain fine-tuning*, bukan evaluasi generalisasi independen.

**Langkah Selanjutnya:**  
Task S2.2 secara formal ditutup. Sistem saat ini berhenti (**STOP**) dan menunggu otorisasi terpisah dari pemilik proyek sebelum melangkah ke **Task S2.3 (Training Experiment Setup & Fine-Tuning Execution Plan)**.
