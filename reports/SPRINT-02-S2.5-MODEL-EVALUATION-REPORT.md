# VISIONSTREAM AI — SPRINT 2 / TASK S2.5
# LAPORAN EVALUASI MODEL & PERBANDINGAN HEAD-TO-HEAD (BASELINE VS FINE-TUNED)

- **Target Lingkungan:** Development Only (`LAPTOP-62621JIA`)
- **Root Direktori Proyek:** `C:\my-app\visionstream-ai`
- **Canonical Master Blueprint:** `docs/architecture/MASTER-BLUEPRINT.md` (v1.0.1, SHA-256: `5A8C05D91F1BE08BFE89AE495DAC4553C63CE164655F4C7C98155AFFC0BEE19A`)
- **Tanggal Audit & Evaluasi:** 10 November 2026
- **Status Sesi Evaluasi:** **SELESAI (PASS WITH FORMAL MODEL SELECTION)**
- **Rekomendasi Seleksi Model:** **BASELINE MODEL RECOMMENDED (`yolov8n.pt`)**

---

## 1. RINGKASAN EKSEKUTIF

Sesuai otorisasi Proyek VisionStream AI Task S2.5, telah dilakukan pengujian dan evaluasi perbandingan *head-to-head* yang ketat, obyektif, dan terkontrol antara:
1. **Baseline Model:** [`data/models/yolov8n.pt`](file:///c:/my-app/visionstream-ai/data/models/yolov8n.pt) (Ultralytics Pretrained, difilter pada class 0 `person`).
2. **Fine-Tuned Model:** [`data/models/best.pt`](file:///c:/my-app/visionstream-ai/data/models/best.pt) (Hasil fine-tuning 50 epoch dari Sprint 2.4 Gate 2).

Kedua model dievaluasi secara simultan pada **Holdout Test Set yang sama persis (240 citra, 972 anotasi ground-truth person)** dalam container Docker CPU terisolasi (`visionstream-ai:sprint-1`) tanpa melibatkan GPU/CUDA dan tanpa mengubah pipeline produksi.

### Ringkasan Temuan Utama:
- **Baseline Model (`yolov8n.pt`) unggul secara konsisten dan menyeluruh di seluruh metrik deteksi objek**:
  - **mAP@50**: Baseline **0,7532** vs Fine-Tuned **0,6944** (**Baseline lebih unggul +5,88 poin**).
  - **mAP@50-95 (COCO metric)**: Baseline **0,5171** vs Fine-Tuned **0,4425** (**Baseline lebih unggul +7,46 poin**).
  - **Operational Precision (conf=0.35)**: Baseline **0,8609** vs Fine-Tuned **0,8011** (**Baseline lebih unggul +5,98%**).
  - **Operational Recall (conf=0.35)**: Baseline **0,5988** vs Fine-Tuned **0,5885** (**Baseline lebih unggul +1,03%**).
  - **Operational F1-Score**: Baseline **0,7063** vs Fine-Tuned **0,6785** (**Baseline lebih unggul +2,78 poin**).
  - **False Positives (FP)**: Baseline hanya menghasilkan **94 FP**, sedangkan Fine-Tuned menghasilkan **142 FP** (+51% lebih banyak alarm palsu pada model fine-tuned).
- **Efisiensi Inferensi CPU Docker**:
  - Keduanya memiliki performa latensi dan throughput yang setara (Baseline mean inference **58,70 ms** / 17,03 FPS vs Fine-Tuned **56,38 ms** / 17,74 FPS).
- **Rekomendasi Berbasis Bukti Nyata (*Evidence-Driven*):**
  - **BASELINE MODEL RECOMMENDED (`yolov8n.pt`)** sebagai model deteksi utama VisionStream AI. Model fine-tuned mengalami *slight domain/curation bias* dan regresi performa lokalisasi (khususnya pada IoU tinggi 0,70–0,95) akibat subset pelatihan 2.000 citra yang tidak cukup kaya mengungguli generalisasi 80-class COCO pretrained.

---

## 2. VERIFIKASI GERBANG EKSEKUSI (GATE-BY-GATE VERDICTS)

| Gerbang | Deskripsi Evaluasi | Status / Vonis | Catatan Utama |
| :--- | :--- | :---: | :--- |
| **GATE 0** | Read-Only Project Reconnaissance | **PASS** | Lingkungan Docker, Master Blueprint v1.0.1 terverifikasi, status git bersih. |
| **GATE 1** | Holdout & Model Integrity Preflight | **PASS** | 240 citra & 240 label test terverifikasi integritas hash SHA-256 100% cocok dengan manifest. Model baseline & fine-tuned hash cocok. |
| **GATE 2** | Evaluation Protocol Freeze | **PASS** | Protokol dibekukan: conf=0.35, NMS IoU=0.65, matching IoU=0.50, input size 640x640, class 0 person. |
| **GATE 3** | Controlled Model Evaluation | **PASS** | Evaluasi selesai untuk 240 citra, 972 person ground-truth. Perhitungan metrik operasional dan mAP confidence sweep tervalidasi. |
| **GATE 4** | CPU Docker Benchmark | **PASS** | Benchmark CPU container (10 warmup, 240 iterasi terukur). Zero GPU/CUDA utilization. |
| **GATE 5** | Analysis & Model Selection Recommendation | **PASS** | Analisis trade-off selesai; Baseline model direkomendasikan secara definitif. |

---

## 3. AUDIT INTEGRITAS PRA-EVALUASI (GATE 1 PREFLIGHT)

Sebelum evaluasi dimulai, verifikasi integritas kriptografis dan struktur data telah dilakukan secara lengkap:

### A. Verifikasi Master Blueprint
- **Path:** [`docs/architecture/MASTER-BLUEPRINT.md`](file:///c:/my-app/visionstream-ai/docs/architecture/MASTER-BLUEPRINT.md)
- **Ukuran:** 30.022 bytes
- **SHA-256 Terverifikasi:** `5A8C05D91F1BE08BFE89AE495DAC4553C63CE164655F4C7C98155AFFC0BEE19A` (SESUAI 100%)

### B. Verifikasi Checkpoint Model
1. **Baseline Model (`yolov8n.pt`):**
   - **Path:** [`data/models/yolov8n.pt`](file:///c:/my-app/visionstream-ai/data/models/yolov8n.pt)
   - **Ukuran:** 6.549.796 bytes
   - **SHA-256 Terverifikasi:** `F59B3D833E2FF32E194B5BB8E08D211DC7C5BDF144B90D2C8412C47CCFC83B36` (SESUAI 100%)
2. **Fine-Tuned Model (`best.pt`):**
   - **Path:** [`data/models/best.pt`](file:///c:/my-app/visionstream-ai/data/models/best.pt)
   - **Ukuran:** 6.487.978 bytes
   - **SHA-256 Terverifikasi:** `41D74CB7E4288A526D9BF4D092343E12FA61ACC7E4D1DAC76C82593C7BD715EF` (SESUAI 100%)

### C. Verifikasi Holdout Test Set (240 Citra & 240 Label)
- **Direktori Citra:** `data/datasets/coco-person/images/test/` (Tepat 240 berkas `.jpg`)
- **Direktori Label:** `data/datasets/coco-person/labels/test/` (Tepat 240 berkas `.txt`)
- **Total Anotasi Ground-Truth Person:** 972 objek person (seluruhnya berlabel class `0`, koordinat `[0.0, 1.0]`, valid tanpa box OOB).
- **Rekonsiliasi Checksum:** 240/240 citra terverifikasi identik dengan entri manifest kanonikal `metadata/checksums.sha256`. Tidak ada duplikasi ID maupun hash antar split (*train/val/test zero overlap*).
- **Isolasi Data:** Holdout test set 100% tersegel secara lokal di lingkungan Development host/Docker; tidak pernah diunggah ke Colab atau layanan cloud eksternal.

### D. Verifikasi Runtime Eksekusi
- **Platform:** Docker container `visionstream-ai:sprint-1`
- **OS Container:** Linux (Ubuntu 22.04 base)
- **Python:** 3.11.18
- **PyTorch:** 2.15.0+cpu (CUDA Available: `False`)
- **Ultralytics:** 8.4.202
- **OpenCV:** 4.11.0
- **Hardware:** AMD Ryzen 7 6800U (16 logical cores teralokasi), 7,38 GB RAM teralokasi. Tidak ada akselerasi GPU NVIDIA/CUDA.

---

## 4. HASIL EVALUASI KOMPARATIF HEAD-TO-HEAD (GATE 3 & GATE 4)

Pengujian dilakukan dengan menggunakan konfigurasi yang identik secara ketat (*frozen protocol*):
- **Confidence Ambang Batas Operasional:** `0.35`
- **NMS IoU Ambang Batas:** `0.65`
- **Ground-Truth Matching IoU (TP/FP/FN):** `0.50` (One-to-one greedy matching berurutan berdasarkan confidence score tertinggi)
- **Ukuran Citra Input:** `640x640`
- **Kelas Target:** `0` (Person)

### Tabel Perbandingan Metrik Agregat:

| Metrik Evaluasi | Baseline (`yolov8n.pt`) | Fine-Tuned (`best.pt`) | Selisih (Delta) | Model Lebih Unggul |
| :--- | :---: | :---: | :---: | :---: |
| **Total Citra Holdout** | 240 | 240 | 0 | Sama |
| **Total Ground-Truth Objek** | 972 | 972 | 0 | Sama |
| **True Positives (TP)** | **582** | 572 | -10 | **Baseline** (+1,7%) |
| **False Positives (FP)** | **94** | 142 | +48 (+51%) | **Baseline** (FP jauh lebih rendah) |
| **False Negatives (FN)** | **390** | 400 | +10 | **Baseline** (Miss lebih sedikit) |
| **Operational Precision** | **0,8609 (86,09%)** | 0,8011 (80,11%) | -5,98% | **Baseline** |
| **Operational Recall** | **0,5988 (59,88%)** | 0,5885 (58,85%) | -1,03% | **Baseline** |
| **Operational F1-Score** | **0,7063** | 0,6785 | -0,0278 | **Baseline** |
| **mAP@50 (IoU 0.50)** | **0,7532 (75,32%)** | 0,6944 (69,44%) | -5,88% | **Baseline** |
| **mAP@50-95 (COCO mAP)** | **0,5171 (51,71%)** | 0,4425 (44,25%) | -7,46% | **Baseline** |
| **Mean CPU Inference Latency** | 58,70 ms | **56,38 ms** | -2,32 ms | Fine-Tuned (-3,9%) |
| **Median CPU Inference Latency** | 47,99 ms | **47,41 ms** | -0,58 ms | Fine-Tuned |
| **P95 CPU Inference Latency** | **110,19 ms** | 112,27 ms | +2,08 ms | Baseline |
| **Mean Total Latency (Pipeline)** | 62,71 ms | **60,92 ms** | -1,79 ms | Fine-Tuned |
| **Throughput (Inference Only)** | 17,03 FPS | **17,74 FPS** | +0,71 FPS | Fine-Tuned |
| **Throughput (Total Pipeline)** | 15,95 FPS | **16,41 FPS** | +0,46 FPS | Fine-Tuned |

---

### Profil Evaluasi AP pada Berbagai Ambang Batas IoU (COCO Sweep):

| Ambang Batas IoU | Baseline AP (`yolov8n.pt`) | Fine-Tuned AP (`best.pt`) | Selisih Keunggulan Baseline |
| :---: | :---: | :---: | :---: |
| **AP @ 0.50** | **0,7532** | 0,6944 | +0,0588 |
| **AP @ 0.55** | **0,7355** | 0,6736 | +0,0619 |
| **AP @ 0.60** | **0,7106** | 0,6491 | +0,0615 |
| **AP @ 0.65** | **0,6744** | 0,5852 | +0,0892 |
| **AP @ 0.70** | **0,6235** | 0,5311 | +0,0924 |
| **AP @ 0.75** | **0,5505** | 0,4609 | +0,0896 |
| **AP @ 0.80** | **0,4843** | 0,3833 | +0,1010 |
| **AP @ 0.85** | **0,3534** | 0,2594 | +0,0940 |
| **AP @ 0.90** | **0,2212** | 0,1573 | +0,0639 |
| **AP @ 0.95** | **0,0644** | 0,0306 | +0,0338 |
| **Mean (mAP@50-95)** | **0,5171** | **0,4425** | **+0,0746 (+16,9% relative)** |

---

## 5. ANALISIS TEKNIKAL & EVALUASI KEGAGALAN (ERROR ANALYSIS)

### A. Mengapa Baseline Model Lebih Unggul daripada Model Fine-Tuned?
1. **Pretraining Generalization vs Subset Overfitting:**
   - Model baseline `yolov8n.pt` dilatih pada himpunan data COCO penuh (lebih dari 118.000 citra dengan representasi variasi pose, pencahayaan, skala jarak, dan latar belakang yang sangat kaya).
   - Fine-tuning pada Sprint 2 menggunakan subset kurasi person berlisensi CC BY 2.0 sebanyak 2.000 citra train selama 50 epoch. Meskipun loss validasi pada subset val menunjukkan konvergensi baik, model fine-tuned mengalami penyempitan fitur (*representational drift/slight overfitting*) terhadap distribusi subset train, yang menurunkan ketahanan generalisasinya ketika diuji pada 240 citra holdout independen.
2. **Kualitas Lokalisasi Bounding-Box pada IoU Ketat:**
   - Selisih AP tertinggi antara baseline dan fine-tuned terjadi pada IoU ketat (IoU 0,70 hingga 0,85, selisih mencapai ~0,10 poin). Ini membuktikan bahwa *regression head* baseline menghasilkan penempatan koordinat bounding box yang lebih presisi pada tepi objek manusia dibandingkan fine-tuned model.
3. **Peningkatan Drastis False Positives pada Fine-Tuned Model:**
   - Model fine-tuned menghasilkan **142 FP** dibandingkan baseline yang hanya **94 FP** (peningkatan FP sebesar **+51,06%**). Karena fine-tuned model dilatih sebagai single-class detector (hanya kelas person), diskriminasi latar belakang terhadap objek-objek vertikal mirip manusia (seperti tiang, patung, manekin, atau bayangan) menjadi lebih agresif dan memicu false alarm pada conf 0.35.

### B. Karakteristik Kasus Visual (Evidence Visualizations)
Telah dibuat 5 berkas perbandingan visual *side-by-side* di [`evidence/s2.5-model-evaluation/visualizations/`](file:///c:/my-app/visionstream-ai/evidence/s2.5-model-evaluation/visualizations/):
1. **`comparison_000000097679.jpg`**: Kasus perbaikan minor deteksi fine-tuned pada figur siluet tertentu.
2. **`comparison_000000157601.jpg`**: Kasus deteksi orang berjarak sedang dengan peningkatan confidence.
3. **`comparison_000000309391.jpg`**: Kasus kerumunan (*crowded scene*); baseline mendeteksi orang bertumpuk lebih rapi dengan bounding-box yang tidak tumpang-tindih berlebihan.
4. **`comparison_000000341921.jpg`**: Kasus false positive; model fine-tuned mendeteksi objek latar belakang sebagai manusia pada confidence ~0,42.
5. **`comparison_000000415882.jpg`**: Kasus orang berukuran kecil/jauh (*small instance*); baseline mempertahankan recall yang lebih stabil tanpa memicu banyak box palsu.

---

## 6. REKOMENDASI SELEKSI MODEL (FINAL RECOMMENDATION)

### **REKOMENDASI: BASELINE MODEL RECOMMENDED (`yolov8n.pt`)**

Berdasarkan bukti empiris dan audit metrik yang tak terbantahkan:
1. **Akurasi & Deteksi:** Baseline model `yolov8n.pt` mengungguli fine-tuned model di semua metrik kunci: **mAP@50 (+5,88 poin)**, **mAP@50-95 (+7,46 poin)**, **Precision (+5,98%)**, **Recall (+1,03%)**, dan **F1-Score (+2,78 poin)**.
2. **Tingkat Alarm Palsu:** Baseline menghasilkan false positive **33,8% lebih sedikit** (94 vs 142 FP), yang sangat krusial untuk mencegah false trigger pada pipeline inferensi multi-stream VisionStream AI.
3. **Kecepatan Inferensi:** Perbedaan throughput kedua model pada CPU Docker tidak signifikan (17,03 FPS vs 17,74 FPS). Keunggulan 0,7 FPS pada fine-tuned tidak sebanding dengan penurunan drastis pada mAP dan presisi deteksi.
4. **Keputusan Tata Kelola Proyek:**
   - **TIDAK ADA PERUBAHAN** pada model default sistem. Baseline model [`data/models/yolov8n.pt`](file:///c:/my-app/visionstream-ai/data/models/yolov8n.pt) tetap dipertahankan sebagai model produksi kanonikal.
   - Model fine-tuned [`data/models/best.pt`](file:///c:/my-app/visionstream-ai/data/models/best.pt) tetap diarsipkan secara aman di `data/models/` sebagai artefak penelitian Sprint 2 untuk acuan eksperimen lanjutan (misalnya bila di masa mendatang dilakukan transfer learning dengan dataset yang lebih masif atau teknik regularization yang lebih kuat).

---

## 7. INVENTARIS ARTEFAK & BUKTI AUDIT S2.5

Semua artefak evaluasi tersimpan secara terstruktur dan terverifikasi di:
`C:\my-app\visionstream-ai\evidence\s2.5-model-evaluation\`

| Nama Berkas | Relatif Path | Ukuran | Deskripsi | Status |
| :--- | :--- | :---: | :--- | :---: |
| `protocol_freeze_config.json` | `evidence/s2.5-model-evaluation/protocol_freeze_config.json` | 1.928 B | Spesifikasi konfigurasi protokol evaluasi yang dibekukan | Verified |
| `holdout_integrity_check.json` | `evidence/s2.5-model-evaluation/holdout_integrity_check.json` | 169 B | Hasil validasi 240 citra & 240 label test set (Status: PASS) | Verified |
| `holdout_test_manifest_verified.json`| `evidence/s2.5-model-evaluation/holdout_test_manifest_verified.json` | 87.718 B | Manifest lengkap 240 file test berserta hash SHA-256 | Verified |
| `holdout_test_checksums.sha256` | `evidence/s2.5-model-evaluation/holdout_test_checksums.sha256` | 45.600 B | Daftar 480 baris hash SHA-256 (240 citra + 240 label) | Verified |
| `aggregate_metrics_comparison.csv` | `evidence/s2.5-model-evaluation/aggregate_metrics_comparison.csv` | 777 B | Tabel ringkasan perbandingan metrik agregat CSV | Verified |
| `aggregate_metrics_comparison.json`| `evidence/s2.5-model-evaluation/aggregate_metrics_comparison.json` | 5.109 B | Data JSON perbandingan metrik agregat & AP curve | Verified |
| `baseline_evaluation_summary.json` | `evidence/s2.5-model-evaluation/baseline_evaluation_summary.json` | 1.290 B | Ringkasan metrik & benchmark model baseline | Verified |
| `finetuned_evaluation_summary.json`| `evidence/s2.5-model-evaluation/finetuned_evaluation_summary.json` | 1.285 B | Ringkasan metrik & benchmark model fine-tuned | Verified |
| `per_image_evaluation_baseline.csv`| `evidence/s2.5-model-evaluation/per_image_evaluation_baseline.csv` | 34.831 B | Data CSV evaluasi per-citra untuk baseline | Verified |
| `per_image_evaluation_baseline.json`| `evidence/s2.5-model-evaluation/per_image_evaluation_baseline.json` | 260.083 B | Data JSON detail evaluasi per-citra untuk baseline | Verified |
| `per_image_evaluation_finetuned.csv`| `evidence/s2.5-model-evaluation/per_image_evaluation_finetuned.csv` | 35.320 B | Data CSV evaluasi per-citra untuk fine-tuned | Verified |
| `per_image_evaluation_finetuned.json`| `evidence/s2.5-model-evaluation/per_image_evaluation_finetuned.json` | 267.738 B | Data JSON detail evaluasi per-citra untuk fine-tuned | Verified |
| `visualizations/` (5 berkas JPG) | `evidence/s2.5-model-evaluation/visualizations/` | ~1,5 MB | Citra perbandingan visual side-by-side | Verified |

---

## 8. REPRODUSIBILITAS & ISOLASI SISTEM

- **Skrip Evaluasi:** Seluruh skrip evaluasi diisolasi di direktori [`eval_tools/`](file:///c:/my-app/visionstream-ai/eval_tools/) (`protocol_freeze.py` dan `evaluate_engine.py`).
- **Integritas Kode Produksi:** Tidak ada satu pun berkas di [`src/`](file:///c:/my-app/visionstream-ai/src/) yang dimodifikasi. Pipeline inferensi produksi tetap murni dan tidak terpengaruh.
- **Integritas Konfigurasi Docker:** Berkas `docker-compose.yml` dan `docker/Dockerfile` tidak diubah.
- **Integritas Master Blueprint:** Berkas `docs/architecture/MASTER-BLUEPRINT.md` tidak diubah (hash SHA-256 tetap `5A8C05D91F1BE08BFE89AE495DAC4553C63CE164655F4C7C98155AFFC0BEE19A`).
- **Biaya Cloud:** **\$0** (seluruh evaluasi dijalankan 100% lokal di dalam CPU container Docker).
