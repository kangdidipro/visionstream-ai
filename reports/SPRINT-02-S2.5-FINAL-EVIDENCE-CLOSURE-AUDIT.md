# VISIONSTREAM AI — SPRINT 2 / TASK S2.5
# S2.5 — FINAL EVIDENCE CLOSURE AUDIT REPORT

- **Lingkungan Target:** DEVELOPMENT ONLY (`LAPTOP-62621JIA`)
- **Root Direktori Proyek:** `C:\my-app\visionstream-ai`
- **Canonical Master Blueprint:** `docs/architecture/MASTER-BLUEPRINT.md` (v1.0.1, SHA-256: `5A8C05D91F1BE08BFE89AE495DAC4553C63CE164655F4C7C98155AFFC0BEE19A`)
- **Laporan Evaluasi Objek Audit:** `reports/SPRINT-02-S2.5-MODEL-EVALUATION-REPORT.md` (SHA-256: `A9AD52FE16195BBCDBCDB9A361AB34FA87F3F67F990BA75039BDF4AA8E482CB0`)
- **Model Checkpoint Baseline:** `data/models/yolov8n.pt` (SHA-256: `F59B3D833E2FF32E194B5BB8E08D211DC7C5BDF144B90D2C8412C47CCFC83B36`)
- **Model Checkpoint Fine-Tuned:** `data/models/best.pt` (SHA-256: `41D74CB7E4288A526D9BF4D092343E12FA61ACC7E4D1DAC76C82593C7BD715EF`)
- **Tanggal Audit Penutupan:** 10 November 2026
- **Status Audit Penutupan:** **VERIFIED & CLOSED (S2.5 — CLOSED / PASS)**
- **Rekomendasi Model Definitif:** **BASELINE MODEL (`yolov8n.pt`)**

---

## 1. RINGKASAN EKSEKUTIF AUDIT PENUTUPAN (EVIDENCE CLOSURE SUMMARY)

Audit penutupan bukti (*evidence closure audit*) ini dilakukan secara *read-only* untuk memeriksa, memvalidasi integritas, serta memastikan keterlacakan (*traceability*) dan reprodusibilitas (*reproducibility*) menyeluruh terhadap seluruh bukti artefak yang dihasilkan pada evaluasi model **Sprint 2 Task S2.5**.

### Vonis Komponen Audit:
1. **Evidence Inventory:** **VERIFIED** (Seluruh 17 berkas artefak S2.5 di `evidence/s2.5-model-evaluation/` ada secara fisik, non-empty, dan tervalidasi hash SHA-256).
2. **Benchmark Traceability:** **VERIFIED** (Parameter benchmark 10 warmup, 240 measured, latensi mean baseline 58,70 ms, fine-tuned 56,38 ms, throughput 17,03 vs 17,74 FPS terlacak persis pada log eksekusi tugas dan file JSON/CSV per-citra).
3. **Metric Traceability & Reconciliation:** **VERIFIED** (Rekonsiliasi 100% sempurna: $TP + FN = 972$ cocok persis dengan total ground-truth person; precision, recall, F1, dan mAP terlacak tanpa diskrepansi antara file agregat dan data baris per-citra).
4. **Evaluator Reproducibility:** **VERIFIED** (Skrip `eval_tools/protocol_freeze.py` dan `eval_tools/evaluate_engine.py` terekam hash SHA-256, perintah pemanggilan Docker tercatat, runtime Docker terkonfirmasi CPU-only tanpa CUDA).
5. **Daftar Bukti Hilang (*Missing Evidence*):** **NONE (NIHIL)**.
6. **Vonis Akhir Penutupan:** **S2.5 — CLOSED / PASS**.

---

## 2. INVENTARIS BUKTI LENGKAP (TASK 1 — EVIDENCE INVENTORY)

Seluruh berkas bukti S2.5 telah diinspeksi secara fisik pada direktori `evidence/s2.5-model-evaluation/`, `eval_tools/`, dan `reports/`.

| No | Path Relatif | Ukuran (Bytes) | SHA-256 Checksum | Tipe Berkas | Deskripsi Singkat | Status Fisik | Status Audit |
| :-: | :--- | :-: | :--- | :---: | :--- | :-: | :-: |
| 1 | `evidence/s2.5-model-evaluation/protocol_freeze_config.json` | 1.928 | `9ECB62B3E64B7E42275D555D39A5D794A056C20C7C32264F501C5D1BFB88D987` | JSON | Konfigurasi parameter protokol beku (ambang batas operasional, input size, kelas target) | Ada / Non-empty | **VERIFIED** |
| 2 | `evidence/s2.5-model-evaluation/holdout_integrity_check.json` | 169 | `BD6AE431758D251D66FFB7BB13CD2BF2B3494EDAC4072DA91393471BA6659BF5` | JSON | Hasil verifikasi integritas 240 citra & label test set (Status: PASS) | Ada / Non-empty | **VERIFIED** |
| 3 | `evidence/s2.5-model-evaluation/holdout_test_manifest_verified.json` | 87.718 | `014D56B3FD44F627AF78117588D6D5C8463A78A11A49A1BF11E41F747753CD4C` | JSON | Manifest lengkap 240 citra dan label test beserta SHA-256 masing-masing berkas | Ada / Non-empty | **VERIFIED** |
| 4 | `evidence/s2.5-model-evaluation/holdout_test_checksums.sha256` | 45.600 | `1D77D8395300B116F77790088EC74A4E28F72463B845447AC8B9B4A4CB240FDE` | TXT / Hash | 480 baris hash SHA-256 kanonikal (240 citra test + 240 file label test) | Ada / Non-empty | **VERIFIED** |
| 5 | `evidence/s2.5-model-evaluation/aggregate_metrics_comparison.csv` | 777 | `054408778CFCD6103E3EB62D6BD9371CA3C6198EE670681F44FA584F2D069847` | CSV | Ringkasan metrik agregat perbandingan komparatif Baseline vs Fine-Tuned | Ada / Non-empty | **VERIFIED** |
| 6 | `evidence/s2.5-model-evaluation/aggregate_metrics_comparison.json` | 5.109 | `84689EAE44E82A08BBE4C169A105EC1CCC2A5C69A9EA4E1559EDDF28BEA252FF` | JSON | Data detail JSON perbandingan metrik agregat beserta 10 titik AP kurva IoU 0.50–0.95 | Ada / Non-empty | **VERIFIED** |
| 7 | `evidence/s2.5-model-evaluation/baseline_evaluation_summary.json` | 1.290 | `D87AE6E6BF86CE056B0CAA14EDA60113DD182BA4C715DC03AEF08E6A3C7CDD06` | JSON | Ringkasan metrik akurasi & benchmark latensi CPU untuk model baseline | Ada / Non-empty | **VERIFIED** |
| 8 | `evidence/s2.5-model-evaluation/finetuned_evaluation_summary.json` | 1.285 | `704A03C1143066706CC169D4EEE78B5D566A5DB0BBB9B9C7E1A00B7DAF18C940` | JSON | Ringkasan metrik akurasi & benchmark latensi CPU untuk model fine-tuned | Ada / Non-empty | **VERIFIED** |
| 9 | `evidence/s2.5-model-evaluation/per_image_evaluation_baseline.csv` | 34.831 | `E3D11C75A0B564F1EF80678D15CE89D2386EFCA4B4BF011F2949DAFC19C85988` | CSV | Baris metrik operasional dan waktu eksekusi baseline per citra (240 baris data) | Ada / Non-empty | **VERIFIED** |
| 10 | `evidence/s2.5-model-evaluation/per_image_evaluation_baseline.json` | 260.083 | `B1852E2B578B4DDE70A2DB73BABCB55DF2F135DFE5D472991239C9F3A3FBE986` | JSON | Detail komprehensif baseline per citra (bounding boxes, koordinat, conf, matching) | Ada / Non-empty | **VERIFIED** |
| 11 | `evidence/s2.5-model-evaluation/per_image_evaluation_finetuned.csv` | 35.320 | `B8D0C7FC0948936DAAB84A1BD7BC601DACD76E1486B017DF3563B1CBDAB8F319` | CSV | Baris metrik operasional dan waktu eksekusi fine-tuned per citra (240 baris data) | Ada / Non-empty | **VERIFIED** |
| 12 | `evidence/s2.5-model-evaluation/per_image_evaluation_finetuned.json` | 267.738 | `5E0B5FBC5429B5F98090C40CBFFFFCC2588D8E9595B853B489A34A1EB519BC54` | JSON | Detail komprehensif fine-tuned per citra (bounding boxes, koordinat, conf, matching) | Ada / Non-empty | **VERIFIED** |
| 13 | `evidence/s2.5-model-evaluation/visualizations/comparison_000000097679.jpg` | 272.596 | `536A25C16A2FAF815EF76E1478033F2E871A0456A862C29B88A50EDDE604AC5B` | JPEG | Visualisasi komparasi side-by-side: deteksi siluet figur | Ada / Non-empty | **VERIFIED** |
| 14 | `evidence/s2.5-model-evaluation/visualizations/comparison_000000157601.jpg` | 234.361 | `A1C5D3BC94A091394C19BCEF339288F465FDE314C204FD593A11E3F1E61C63C2` | JPEG | Visualisasi komparasi side-by-side: orang jarak sedang | Ada / Non-empty | **VERIFIED** |
| 15 | `evidence/s2.5-model-evaluation/visualizations/comparison_000000309391.jpg` | 357.559 | `3E5CFA8B4942DD6AE551181ABF05C6F53EF3B74ABF9CEA4E5417FA256DBFD7F6` | JPEG | Visualisasi komparasi side-by-side: skenario kerumunan (*crowded scene*) | Ada / Non-empty | **VERIFIED** |
| 16 | `evidence/s2.5-model-evaluation/visualizations/comparison_000000341921.jpg` | 342.101 | `BC85E15C7E719CF6911317F388C296583767CE287A4779D78BC4FDC31CD3421C` | JPEG | Visualisasi komparasi side-by-side: analisis false positive fine-tuned | Ada / Non-empty | **VERIFIED** |
| 17 | `evidence/s2.5-model-evaluation/visualizations/comparison_000000415882.jpg` | 319.257 | `E55A7E982D70D3B6B6AFA59B6690678E648CC317A30C56D89EFAFB3C2F637C67` | JPEG | Visualisasi komparasi side-by-side: orang skala kecil/jauh (*small instance*) | Ada / Non-empty | **VERIFIED** |
| 18 | `eval_tools/protocol_freeze.py` | 2.572 | `629C670D3725CE806929D15B319CF76F016F843B8F67E896B3D07C1648939EC1` | Python | Skrip pembekuan spesifikasi protokol evaluasi | Ada / Non-empty | **VERIFIED** |
| 19 | `eval_tools/evaluate_engine.py` | 24.424 | `AFFBCFDD6A51A7282476A0920B54816BB447CE760DE39ED513C4E93BDEE33C87` | Python | Mesin evaluasi inferensi komparatif, mAP COCO sweep, dan visualisasi | Ada / Non-empty | **VERIFIED** |
| 20 | `reports/SPRINT-02-S2.5-MODEL-EVALUATION-REPORT.md` | 16.422 | `A9AD52FE16195BBCDBCDB9A361AB34FA87F3F67F990BA75039BDF4AA8E482CB0` | Markdown | Laporan komprehensif evaluasi model & perbandingan head-to-head S2.5 | Ada / Non-empty | **VERIFIED** |

---

## 3. KETERLACAKAN BENCHMARK (TASK 2 — BENCHMARK TRACEABILITY)

Pemeriksaan log mentah (*raw execution logs*) dan data latensi per citra:

1. **Log Eksekusi Asli:**
   - Log sesi eksekusi tugas background terekam pada berkas task runner kanonikal:  
     `file:///C:/Users/Ahadi/.gemini/antigravity/brain/3f180c5f-627e-4c2e-bf91-8ec8cc0e1720/.system_generated/tasks/task-977.log` (986 bytes).
   - Log mengonfirmasi secara berurutan:
     - Pemuatan 240 citra holdout test set.
     - Eksekusi model `baseline` dengan 10 iterasi *warm-up* pada CPU dilanjutkan evaluasi 240 citra.
     - Eksekusi model `fine_tuned` dengan 10 iterasi *warm-up* pada CPU dilanjutkan evaluasi 240 citra.
     - Pembuatan 5 citra perbandingan visual side-by-side.
     - Penyimpanan seluruh hasil ke `/app/evidence/s2.5-model-evaluation`.
2. **Keterlacakan Metrik Benchmark Latensi & Throughput:**
   - **Baseline Inference Latency:** Mean $58,7028\text{ ms}$, Median $47,9897\text{ ms}$, P95 $110,1890\text{ ms}$. Terlacak langsung dari akumulasi 240 baris data `inference_ms` pada [`per_image_evaluation_baseline.csv`](file:///c:/my-app/visionstream-ai/evidence/s2.5-model-evaluation/per_image_evaluation_baseline.csv).
   - **Fine-Tuned Inference Latency:** Mean $56,3820\text{ ms}$, Median $47,4074\text{ ms}$, P95 $112,2723\text{ ms}$. Terlacak langsung dari akumulasi 240 baris data `inference_ms` pada [`per_image_evaluation_finetuned.csv`](file:///c:/my-app/visionstream-ai/evidence/s2.5-model-evaluation/per_image_evaluation_finetuned.csv).
   - **Baseline Throughput:** $1000 / 58,7028 = 17,0349\text{ FPS}$ (Inference only) dan $1000 / 62,7055 = 15,9475\text{ FPS}$ (Total pipeline).
   - **Fine-Tuned Throughput:** $1000 / 56,3820 = 17,7361\text{ FPS}$ (Inference only) dan $1000 / 60,9210 = 16,4147\text{ FPS}$ (Total pipeline).
3. **Konfirmasi Lingkungan CPU-Only:**
   - Parameter `device="cpu"` pada `evaluate_engine.py` baris 204 dan 227.
   - Diagnostik container (`Torch 2.15.0+cpu`, `CUDA available: False`) memastikan tidak ada GPU/CUDA yang digunakan.

**Vonis Benchmark Traceability: VERIFIED**

---

## 4. KETERLACAKAN & REKONSILIASI METRIK (TASK 3 — METRIC TRACEABILITY)

Rekonsiliasi matematis independen telah dilakukan antara berkas ringkasan agregat (`aggregate_metrics_comparison.json`, `aggregate_metrics_comparison.csv`, `baseline_evaluation_summary.json`, `finetuned_evaluation_summary.json`) dengan data per-citra (`per_image_evaluation_baseline.json`, `per_image_evaluation_finetuned.json`):

### A. Rekonsiliasi Model Baseline (`yolov8n.pt`):
- **Jumlah Citra Teruji:** 240 citra.
- **Total Ground-Truth Objek:** $\sum \text{GT} = 972$ objek person.
- **True Positives (TP):** $\sum \text{TP} = 582$. Cocok 100% dengan nilai agregat (582).
- **False Positives (FP):** $\sum \text{FP} = 94$. Cocok 100% dengan nilai agregat (94).
- **False Negatives (FN):** $\sum \text{FN} = 390$. Cocok 100% dengan nilai agregat (390).
- **Integritas Konservasi Objek:** $TP + FN = 582 + 390 = 972 \equiv \text{Total GT}$ (**Lolos Persis**).
- **Operational Precision:** $\frac{582}{582 + 94} = \frac{582}{676} = 0,8609467...$ (Agregat: $0,8609$, Delta: $0,00000000$).
- **Operational Recall:** $\frac{582}{582 + 390} = \frac{582}{972} = 0,5987654...$ (Agregat: $0,5988$, Delta: $0,00000000$).
- **Operational F1-Score:** $\frac{2 \times 0,8609467 \times 0,5987654}{0,8609467 + 0,5987654} = 0,7063106...$ (Agregat: $0,7063$, Delta: $0,00000000$).
- **mAP@50 (IoU 0.50):** $0,753211...$ (Agregat: $0,7532$).
- **mAP@50-95 (COCO 10-point IoU mean):** $0,517096...$ (Agregat: $0,5171$).

### B. Rekonsiliasi Model Fine-Tuned (`best.pt`):
- **Jumlah Citra Teruji:** 240 citra.
- **Total Ground-Truth Objek:** $\sum \text{GT} = 972$ objek person.
- **True Positives (TP):** $\sum \text{TP} = 572$. Cocok 100% dengan nilai agregat (572).
- **False Positives (FP):** $\sum \text{FP} = 142$. Cocok 100% dengan nilai agregat (142).
- **False Negatives (FN):** $\sum \text{FN} = 400$. Cocok 100% dengan nilai agregat (400).
- **Integritas Konservasi Objek:** $TP + FN = 572 + 400 = 972 \equiv \text{Total GT}$ (**Lolos Persis**).
- **Operational Precision:** $\frac{572}{572 + 142} = \frac{572}{714} = 0,8011204...$ (Agregat: $0,8011$, Delta: $0,00000000$).
- **Operational Recall:** $\frac{572}{572 + 400} = \frac{572}{972} = 0,5884773...$ (Agregat: $0,5885$, Delta: $0,00000000$).
- **Operational F1-Score:** $\frac{2 \times 0,8011204 \times 0,5884773}{0,8011204 + 0,5884773} = 0,6785290...$ (Agregat: $0,6785$, Delta: $0,00000000$).
- **mAP@50 (IoU 0.50):** $0,694398...$ (Agregat: $0,6944$).
- **mAP@50-95 (COCO 10-point IoU mean):** $0,442483...$ (Agregat: $0,4425$).

### C. Metodologi Perhitungan mAP (Confidence Sweep):
- Evaluasi operasional menggunakan titik kerja tetap ($conf = 0,35$, $NMS = 0,65$, $matching = 0,50$).
- Perhitungan mAP dieksekusi secara terpisah menggunakan raw prediction ($conf \ge 0,001$) dengan interpolasi 101-titik standar COCO pada 10 ambang batas IoU ($0,50, 0,55, \dots, 0,95$), sehingga perhitungan mAP valid secara metodologi visi komputer dan tidak dibatasi secara artifisial oleh threshold operasional 0.35.

**Vonis Metric Traceability: VERIFIED**

---

## 5. REPRODUSIBILITAS EVALUATOR (TASK 4 — EVALUATOR REPRODUCIBILITY)

1. **Skrip Eksekusi:**
   - `eval_tools/protocol_freeze.py` (SHA-256: `629C670D3725CE806929D15B319CF76F016F843B8F67E896B3D07C1648939EC1`)
   - `eval_tools/evaluate_engine.py` (SHA-256: `AFFBCFDD6A51A7282476A0920B54816BB447CE760DE39ED513C4E93BDEE33C87`)
2. **Perintah Docker yang Digunakan:**
   - Pembekuan protokol:
     `docker run --rm -v "C:\my-app\visionstream-ai:/app" -w /app visionstream-ai:sprint-1 python3 eval_tools/protocol_freeze.py`
   - Eksekusi evaluasi & benchmark:
     `docker run --rm -v "C:\my-app\visionstream-ai:/app" -w /app visionstream-ai:sprint-1 python3 eval_tools/evaluate_engine.py`
3. **Versi Dependensi Runtime Terkonfirmasi:**
   - Docker Image: `visionstream-ai:sprint-1` (Image ID: `cbac8965808e`)
   - Python: `3.11.18`
   - PyTorch: `2.15.0+cpu`
   - OpenCV: `4.11.0`
   - Ultralytics: `8.4.202`
   - NumPY: `1.26.4`
4. **Isolasi Kode & Lingkungan:**
   - Seluruh perkakas evaluasi berada di direktori mandiri `eval_tools/`.
   - Direktori kode sumber produksi `src/` tidak dimodifikasi sama sekali (*zero touch*).

**Vonis Evaluator Reproducibility: VERIFIED**

---

## 6. DAFTAR BUKTI YANG HILANG ATAU TIDAK DAPAT DIVERIFIKASI

- **Bukti Hilang (*Missing Evidence*):** **TIDAK ADA (NONE)**.
- **Bukti Tidak Dapat Diverifikasi (*Not Verifiable*):** **TIDAK ADA (NONE)**.
- **Inkonsistensi Data (*Inconsistent Evidence*):** **TIDAK ADA (NONE)**.

Semua klaim numerik pada laporan utama S2.5 memiliki relasi korespondensi 1-ke-1 langsung dengan berkas data mentah CSV, JSON, hash, dan log eksekusi.

---

## 7. REKOMENDASI PENUTUPAN AKHIR (FINAL S2.5 CLOSURE RECOMMENDATION)

### **VONIS: S2.5 — CLOSED / PASS**

Berdasarkan seluruh kriteria audit kepatuhan, keutuhan artefak, dan keterlacakan numerik:
1. **Bukti Lengkap & Sah:** Seluruh 17 berkas artefak S2.5 terbukti valid, berintegritas tinggi, dan tersimpan aman di `evidence/s2.5-model-evaluation/`.
2. **Seleksi Model Definitif:** Rekomendasi model baseline [`data/models/yolov8n.pt`](file:///c:/my-app/visionstream-ai/data/models/yolov8n.pt) diterima secara definitif berbasis bukti obyektif bahwa model baseline unggul pada seluruh metrik deteksi (mAP@50 0,7532 vs 0,6944; mAP@50-95 0,5171 vs 0,4425; Precision 86,09% vs 80,11%; False Positives 94 vs 142).
3. **Konfirmasi Tata Kelola:**
   - Model baseline [`data/models/yolov8n.pt`](file:///c:/my-app/visionstream-ai/data/models/yolov8n.pt) tetap dipertahankan sebagai model inferensi kanonikal VisionStream AI.
   - Tidak ada modifikasi pada konfigurasi produksi, arsitektur Docker Compose, maupun Master Blueprint.
   - Sprint 2 (S2.1, S2.2, S2.3, S2.4, dan S2.5) secara resmi dinyatakan **SELESAI dan DITUTUP PENUH (FORMALLY CLOSED)**.
