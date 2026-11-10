# SPRINT 2 PLANNING — TASK S2.1
## DATASET STRATEGY & LICENSING ASSESSMENT REPORT (REVISED)

**Project:** VisionStream AI  
**Task Identifier:** `S2.1 — Dataset Strategy & Licensing Assessment`  
**Governing Phase:** Phase 3 (Operational Sprint 2 — Model Training & Evaluation)  
**Execution Environment:** Isolated Read-Only Planning on Windows 11 (`LAPTOP-62621JIA`)  
**Document Date:** November 5, 2026 (Revised: November 5, 2026)  
**Canonical File Location:** `C:\my-app\visionstream-ai\reports\SPRINT-02-S2.1-DATASET-STRATEGY.md`  
**Task Status:** **PASS (Planning & Research Complete — Zero Implementation Executed)**

---

## Revision History

| Version | Date | Author / Agent | Changes Summary |
|---|---|---|---|
| 1.0.0 | 2026-11-05 | Antigravity Engine | Initial draft of Sprint 2 Dataset Strategy and Licensing Assessment. |
| 1.1.0 | 2026-11-05 | Antigravity Engine | Formal revision addressing review corrections: (1) Disjoint COCO split definition (Train2017 vs Val2017 subsets) and Test2017 annotation clarification; (2) Pretrained `yolov8n.pt` provenance verification; (3) Separate COCO image vs annotation licensing with portfolio verification recommendation; (4) Dedicated Ultralytics AGPL-3.0 and Enterprise licensing implications; (5) Decoupled detection metric calculation (mAP low confidence floor, IoU separation) from operational benchmark (conf 0.35); (6) Formal restrictions on CrowdHuman and primary-source requirement for WiderPerson; (7) Reclassified unmeasured metrics as `Planning Estimate — Subject to Pilot Verification` and noted non-guaranteed free Colab GPU availability. |

---

## 1. Executive Summary

Sprint 1 telah diselesaikan secara formal dengan vonis **PASS WITH LIMITATIONS** (tervalidasi pada video baseline `people-detection.mp4` dan video CCTV Full HD `people-detection-faces.mp4`). Saat ini, platform mengandalkan checkpoint bobot model pretrained `yolov8n.pt` yang dilatih pada 80 kelas COCO (dengan filter inferensi murni untuk kelas `person` [ID: 0]).

Tujuan dari Sprint 2 adalah merancang alur kerja pelatihan dan evaluasi model (*model training & evaluation*) yang dapat direproduksi (*reproducible*), membandingkan performa model baseline pretrained terhadap model hasil fine-tuning khusus person detection.

Berdasarkan investigasi mendalam terhadap aspek metodologis, komputasi, dan lisensi hukum:
1. **Rekomendasi Dataset Primer:** **COCO 2017 (Person-only subset)** direkomendasikan sebagai dataset utama untuk fase pilot fine-tuning dan evaluasi.
2. **Skema Pembagian Data Terisolasi (Disjoint Pilot Split):**
   - **Train Set:** 2,000 citra beranotasi `person` diambil dari **COCO Train2017**.
   - **Validation Set:** 500 citra beranotasi `person` diambil dari **COCO Val2017**.
   - **Holdout Test Set:** 500 citra beranotasi `person` yang berbeda (*disjoint*) diambil dari **COCO Val2017**.
   - Seluruh Image ID dijamin saling lepas (*mutually disjoint*). Ground-truth anotasi COCO Test2017 tidak dirilis secara publik sehingga tidak dapat dipakai untuk evaluasi mandiri lokal. Holdout test set yang sama wajib dipakai untuk evaluasi komparatif kedua model (*head-to-head*).
3. **Kepatuhan Lisensi Citra & Model:**
   - Anotasi COCO berlisensi CC BY 4.0, tetapi hak cipta citra dimiliki oleh masing-masing fotografer di Flickr; verifikasi lisensi citra direkomendasikan sebelum redistribusi portofolio.
   - Pustaka dan model Ultralytics diatur di bawah lisensi **AGPL-3.0** (atau Enterprise License komersial).
4. **Kandidat Dataset Tambahan (CrowdHuman / WiderPerson):** Ditunda (*deferred*). CrowdHuman terikat klausul non-komersial dan larangan redistribusi citra; WiderPerson memerlukan bukti lisensi sumber primer resmi sebelum dapat dipertimbangkan. Keduanya tidak diunduh atau digunakan pada tahap ini.
5. **Strategi Komputasi:** Pelatihan model dialokasikan ke Google Colab (bergantung pada ketersediaan GPU gratis yang tidak dijamin), sedangkan evaluasi inferensi dilakukan secara deterministik di dalam container Docker lokal CPU. Seluruh estimasi komputasi diklasifikasikan sebagai `Planning Estimate — Subject to Pilot Verification`.

---

## 2. Existing Project Baseline & Inherited Constraints

Inspeksi terhadap `docs/architecture/MASTER-BLUEPRINT.md` dan laporan verifikasi teknis Sprint 1 menetapkan baseline arsitektur berikut:

### 2.1 Model Checkpoint & Provenance
- **Model Checkpoint:** `data/models/yolov8n.pt` (FP32, 6.55 MB, arsitektur Ultralytics YOLOv8 nano).
- **Model Provenance & Training Assumptions:** Checkpoint resmi didistribusikan oleh Ultralytics Ltd., dilatih pada full dataset COCO Train2017 (118,287 citra, 80 kelas) dengan augmentasi Mosaic, MixUp, dan fliplr pada resolusi $640 \times 640$. Kelas `person` merepresentasikan Class ID `0`.
- **Target Kelas Operasional:** COCO Class ID `0` (`person`).
- **Pelacak:** ByteTrack (`bytetrack.yaml`, Kalman Filter + IoU association).

### 2.2 Aset Video & Evaluasi Saat Ini
- `data/inputs/people-detection.mp4` (768x432, 12 FPS, 596 frame, Intel IoT sample, lisensi CC-BY-4.0).
- `data/inputs/people-detection-faces.mp4` (1920x1080, 23.98 FPS, 460 frame, Pexels asset 855564, Pexels License).
- **Status Ground-Truth:** Kedua video tersebut adalah video uji inferensi visual tanpa anotasi bounding-box ground-truth frame-by-frame, sehingga metrik pada Sprint 1 merupakan statistik operasional inferensi.

### 2.3 Batasan Komputasi & Isolasi Docker
- **Host Machine:** AMD Ryzen 7 6800U (8 core / 16 thread), 16 GB RAM, GPU terintegrasi AMD Radeon 680M. **Tidak ada GPU discrete NVIDIA lokal.**
- **Docker Isolation Policy:** Seluruh eksekusi dan dependensi runtime wajib diisolasi di dalam container Docker. Tidak ada instalasi dependensi Python atau perubahan PATH pada host Windows.

---

## 3. Dataset Candidate Comparison

| Parameter Evaluasi | Kandidat 1: COCO 2017 (Person Subset) | Kandidat 2: CrowdHuman | Kandidat 3: WiderPerson |
|---|---|---|---|
| **Karakteristik Utama** | Deteksi objek umum berskala besar; kelas `person` merupakan kategori terbanyak. | Deteksi manusia dalam skenario kerumunan ekstrem (*dense crowds*) dan oklusi parah. | Deteksi pejalan kaki di alam bebas (*pedestrian in the wild*) dengan beragam pose dan kondisi cuaca. |
| **Jumlah Citra & Anotasi** | **Total Citra:** ~118,287 (Train), ~5,000 (Val).<br/>**Person Subset:** ~64,115 citra train mengandung orang; >260,000 bounding box person. | **Total Citra:** 15,000 (Train), 4,370 (Val), 5,000 (Test).<br/>**Total Anotasi:** >470,000 bounding box manusia (~22.6 orang/citra). | **Total Citra:** 8,000 (Train), 1,000 (Val), 4,382 (Test).<br/>**Total Anotasi:** ~399,786 bounding box (~29.8 orang/citra). |
| **Format Anotasi Bounding Box** | COCO JSON format: `[x_min, y_min, width, height]` dalam piksel absolut; standar industri untuk konversi ke format YOLO (`class x_center y_center w h` ternormalisasi). | Format kustom ODGT JSONL: Menyediakan 3 kotak per individu: `vbox` (visible), `fbox` (full body), dan `head`. Memerlukan parser kustom. | Format teks kustom: `[class x1 y1 x2 y2]` dengan 5 kategori (Pedestrians, Riders, Partially-visible, Ignore, Crowd). |
| **Relevansi CCTV** | **Sedang – Tinggi.** Menjangkau variasi jarak dan sudut pandang normal. | **Sangat Tinggi.** Karakteristik kerumunan sangat mirip dengan situasi CCTV stasiun dan plaza pejalan kaki. | **Sangat Tinggi.** Fokus pada pejalan kaki di jalanan dengan oklusi dan skala dinamis. |
| **Ukuran Dataset Penuh** | - Train2017 images: ~19 GB<br/>- Val2017 images: ~1 GB<br/>- Annotations JSON: ~241 MB | - Gambar Train + Val: ~110+ GB<br/>- Ukuran masif untuk diunduh pada penyimpanan lokal. | - Gambar Train + Val: ~5–7 GB (arsip tar/zip). |
| **Sumber Resmi** | Official COCO Consortium: [cocodataset.org](https://cocodataset.org/#download) | Megvii Technology Official Source: [crowdhuman.org](https://www.crowdhuman.org/) | Official WiderPerson Project: [wider-challenge.org](https://wider-challenge.org/) |
| **Ketentuan Lisensi** | **Anotasi:** CC BY 4.0.<br/>**Citra:** Flickr Terms of Use / lisensi individual fotografer. | **Strict Non-Commercial Research & Educational Use Only.** Redistribusi dilarang. | **Academic Research License.** Bukti lisensi sumber primer belum diverifikasi penuh. |
| **Rekomendasi Portofolio** | **PRIMARY DATASET** (Pilot terfilter). | **DEFERRED** (Risiko lisensi komersial dan larangan redistribusi). | **DEFERRED** (Perlu verifikasi lisensi sumber primer resmi). |

---

## 4. Legal, Provenance, and Licensing Assessment

### 4.1 COCO 2017 Dataset: Pemisahan Lisensi Anotasi vs Citra
Evaluasi kepatuhan hukum untuk dataset COCO 2017:
- **Anotasi COCO:** Dilisensikan oleh COCO Consortium di bawah **Creative Commons Attribution 4.0 International (CC BY 4.0)**. Pengguna bebas membagikan dan mengadaptasi metadata anotasi untuk tujuan apa pun, termasuk komersial, dengan atribusi yang sesuai.
- **Citra COCO:** COCO Consortium **tidak memiliki hak cipta atas citra**. Citra dikumpulkan dari platform Flickr dan tunduk pada **Flickr Terms of Use** serta lisensi individual masing-masing pemilik akun/fotografer (sebagian besar Creative Commons, sebagian hak cipta penuh).
- **Koreksi Asumsi Hukum:** Klaim bahwa seluruh citra COCO bebas dari batasan komersial adalah **tidak berdasar**. Penggunaan citra untuk tujuan komersial atau redistribusi dataset publik harus menghormati lisensi asli Flickr setiap citra.
- **Rekomendasi Provenance untuk Portofolio Publik:** Sebelum mempublikasikan dataset subset atau artefak citra dalam repositori portofolio publik, disarankan melakukan proses verifikasi lisensi (*image provenance / license check*) melalui metadata Flickr API untuk menyaring hanya citra dengan lisensi CC0, CC-BY, atau Public Domain.

### 4.2 Ultralytics YOLOv8 Licensing Assessment
Kerangka kerja YOLOv8 dikembangkan dan dimiliki oleh Ultralytics Ltd.:
- **Model Lisensi Ganda (Dual-Licensing):**
  1. **AGPL-3.0 (GNU Affero General Public License v3.0):** Lisensi open-source *strong copyleft*. Berlaku secara default untuk pustaka Ultralytics, kode inferensi/pelatihan yang mengimpor pustaka tersebut, serta bobot turunan langsung.
  2. **Ultralytics Enterprise License:** Lisensi komersial berbayar yang membebaskan pengguna dari kewajiban membuka kode sumber (tidak diotorisasi untuk dibeli dalam proyek ini).
- **Implikasi terhadap VisionStream AI:**
  - **Bobot Pretrained (`yolov8n.pt`):** Diterbitkan di bawah AGPL-3.0.
  - **Bobot Hasil Fine-Tuning (`best.pt`):** Merupakan karya turunan (*derivative work*) dari arsitektur dan bobot Ultralytics, sehingga terikat oleh ketentuan AGPL-3.0 bila didistribusikan.
  - **Kode Aplikasi & Pelatihan:** Selama VisionStream AI dirilis sebagai portofolio open-source publik di GitHub di bawah lisensi yang kompatibel dengan AGPL-3.0 dan kode sumber terbuka penuh, penggunaan ini sepenuhnya mematuhi ketentuan AGPL-3.0.
  - **Penyedia Layanan Jaringan / Commercial Deployment:** Jika sistem diterapkan sebagai layanan jaringan tertutup (SaaS/commercial backend) tanpa membuka kode sumber modifikasi, lisensi AGPL-3.0 mewajibkan pembukaan kode sumber atau pembelian Enterprise License.
- **Batasan Hukum:** Catatan ini bukan nasihat hukum formal (*not definitive legal advice*). Tinjauan kepatuhan lisensi formal (*compliance review*) direkomendasikan sebelum deployment komersial. Tidak ada lisensi berbayar yang diotorisasi untuk dibeli.

### 4.3 Evaluasi Lisensi Dataset Suplemen (CrowdHuman & WiderPerson)
- **CrowdHuman (Megvii Technology):**
  - Lisensi secara tegas menyatakan: *"You will use the data only for non-commercial research and educational purposes. You will NOT distribute the above images."*
  - **Dampak:** Melarang keras redistribusi citra dan melarang penggunaan untuk keperluan komersial. Model yang dilatih pada CrowdHuman tidak dapat diposisikan sebagai produk komersial. Status: **Ditunda / Tidak Digunakan.**
- **WiderPerson Benchmark:**
  - Diperkenalkan oleh peneliti akademis untuk riset pejalan kaki.
  - **Dampak:** Persyaratan lisensi resmi sumber primer belum terverifikasi secara lengkap dari situs resminya. Sesuai prinsip kehati-hatian, bukti lisensi primer resmi wajib diperoleh dan diaudit sebelum merekomendasikan penggunaan apa pun. Status: **Ditunda / Tidak Digunakan.**

---

## 5. Recommended Dataset Strategy & Data Split Definition

### 5.1 Rekomendasi Utama: COCO 2017 Person-Only Curated Subset
Dipilih sebagai dataset primer tunggal untuk Sprint 2 karena:
1. Relevan secara langsung dengan kelas target `person`.
2. Menghindari risiko pelanggaran redistribusi gambar CrowdHuman.
3. Memungkinkan perbandingan performa terstandarisasi terhadap arsitektur YOLOv8 baseline.

### 5.2 Skema Pembagian Data Terisolasi (Disjoint Pilot Split)
Untuk menjamin integritas saintifik dan mencegah kebocoran data (*data leakage*):
- **Train Set (Pelatihan):** **2,000 citra** berlabel person, diekstrak secara eksklusif dari **COCO Train2017** (`train2017.zip`).
- **Validation Set (Validasi Hyperparameter):** **500 citra** berlabel person, diekstrak dari **COCO Val2017** (`val2017.zip`). Digunakan untuk monitoring loss dan checkpoint selection (`patience`, `save_best`).
- **Holdout Test Set (Evaluasi Akhir):** **500 citra** berlabel person yang berbeda (*disjoint*) yang diekstrak dari sisa citra **COCO Val2017** (`val2017.zip`).
- **Pencegahan Data Leakage (Strict Disjointness):**
  $$\mathcal{D}_{\text{train}} \cap \mathcal{D}_{\text{val}} = \emptyset, \quad \mathcal{D}_{\text{train}} \cap \mathcal{D}_{\text{test}} = \emptyset, \quad \mathcal{D}_{\text{val}} \cap \mathcal{D}_{\text{test}} = \emptyset$$
  Semua Image ID pada set validasi dan holdout test dipisahkan secara deterministik menggunakan *fixed seed* (`seed=42`) dari kumpulan ~2,693 citra beranotasi orang pada Val2017, memastikan tidak ada citra yang tumpang tindih.
- **Klarifikasi COCO Test2017:** Kumpulan data resmi COCO Test2017 (~41,000 citra) **tidak menyediakan anotasi ground-truth untuk publik** (evaluasi resmi COCO Test dilakukan melalui server kompetisi C-Eval). Oleh karena itu, evaluasi mandiri lokal wajib menggunakan Holdout Test Set yang diambil dari Val2017.
- **Evaluasi Komparatif Identik:** Holdout Test Set (500 citra) yang persis sama wajib digunakan untuk mengevaluasi kedua model: baseline `yolov8n.pt` dan model fine-tuned `best.pt`.

---

## 6. Model Evaluation Methodology

Evaluasi model pada Sprint 2 dipisahkan secara tegas ke dalam dua tujuan yang berbeda: **Akurasi Deteksi** dan **Kinerja Inferensi Operasional**.

### 6.1 Evaluasi Akurasi Deteksi (Ground-Truth Evaluation)
Tujuan: Mengukur kemampuan lokalisasi spasial dan klasifikasi model terhadap anotasi ground-truth bounding-box pada Holdout Test Set (500 citra).

1. **Metrik Utama:**
   - **mAP@50:** Mean Average Precision pada ambang batas IoU evaluasi $0.50$.
   - **mAP@50-95:** Metrik resmi COCO (rata-rata AP pada 10 ambang batas IoU evaluasi dari $0.50$ hingga $0.95$ dengan step $0.05$).
   - **Precision ($P$) & Recall ($R$):** Dihitung pada kurva PR optimal.
2. **Karakteristik Parameter Evaluasi Akurasi:**
   - **Confidence Floor:** Menggunakan batas confidence dasar yang sangat rendah (`conf=0.001` standar pycocotools / Ultralytics val) untuk memungkinkan kalkulasi kurva PR (Precision-Recall) dan integrasi AUC mAP yang akurat secara matematis. Nilai ambang batas operasional $0.25$ atau $0.35$ **tidak digunakan** sebagai filter awal pada evaluasi mAP.
   - **Pemisahan Ambang Batas IoU (NMS IoU vs Metric IoU):**
     - **NMS IoU Threshold:** Ambang batas IoU untuk proses penekanan non-maksimum post-processing (default: $0.60 - 0.70$), berfungsi mengeliminasi bounding-box duplikat pada objek yang sama.
     - **Evaluation Metric IoU Threshold:** Ambang batas kecocokan spasial antara bounding-box prediksi dengan bounding-box ground-truth (misal: $0.50$ untuk mAP@50, dan $[0.50:0.95]$ untuk mAP@50-95).
   - **Evaluator Tooling:** Menggunakan modul validasi resmi Ultralytics/pycocotools yang terdokumentasi versinya di dalam Docker.

### 6.2 Evaluasi Kinerja Inferensi Operasional (Operational Benchmark)
Tujuan: Mengukur kesiapan model untuk integrasi streaming CCTV real-time pada arsitektur VisionStream AI.

1. **Metrik Utama:**
   - **Latency (ms):** Preprocessing time, Inference time, dan Postprocessing (NMS) time per frame.
   - **Throughput (FPS):** Frame per second rata-rata yang diproses pipeline.
2. **Karakteristik Parameter Operasional:**
   - **Confidence Threshold:** Ditetapkan pada $0.35$ (konsisten persis dengan konfigurasi operasional Sprint 1).
   - **IoU Threshold (NMS):** Ditetapkan pada $0.50$.
   - **Lingkungan Eksekusi:** Diuji pada CPU container Docker lokal (`LAPTOP-62621JIA`) dengan resolusi input $640 \times 640$ dan batch size 1, menggunakan protokol benchmark yang identik dengan Sprint 1.

### 6.3 Batasan Metrik Pelacakan (Tracking Metrics Limitation)
Dataset citra statis (seperti COCO) hanya memiliki anotasi bounding-box spasial per citra, tanpa ID pelacakan temporal lintas-frame. Metrik pelacakan multi-objek formal (**IDF1**, **HOTA**, **MOTA**, **ID Switches**) **tidak dapat** dihitung pada dataset citra statis. Kinerja pelacakan ByteTrack tetap dievaluasi pada video CCTV uji (`people-detection.mp4` dan `people-detection-faces.mp4`) untuk kesinambungan operasional.

---

## 7. Compute Strategy & Resource Estimates

### 7.1 Klasifikasi Estimasi Sumber Daya

> [!NOTE]
> Seluruh estimasi kebutuhan penyimpanan, durasi komputasi, dan throughput yang belum diukur secara empiris di bawah ini diberi label eksplisit:  
> **`Planning Estimate — Subject to Pilot Verification`**

| Komponen & Tugas | Lingkungan Komputasi | Kebutuhan Storage | Estimasi Compute / Waktu | Status Kepastian |
|---|---|---|---|---|
| **Pilot Dataset Storage (3,000 citra + label)** | Host Windows Mount (`data/datasets/`) | $\sim 1.5 - 2.5\text{ GB}$ | I/O transfer rate lokal | **Planning Estimate — Subject to Pilot Verification** |
| **Pelatihan Model YOLOv8n (30–50 epoch)** | **Google Colab (NVIDIA T4 GPU)** | $\sim 10\text{ GB}$ (Ephemeral disk VM) | $\sim 20 - 45\text{ menit}$ | **Planning Estimate — Subject to Pilot Verification** |
| **Ketersediaan GPU Cloud Gratis** | Google Colab Free Tier | $0\text{ MB}$ | Bergantung alokasi dinamis Google | **Tidak Dijamin (Best-Effort Availability)** |
| **Benchmark Inferensi CPU (500 citra test)** | **Local Docker Container (AMD Ryzen 7 6800U)** | $\sim 25\text{ MB}$ (Model & logs) | $\sim 35 - 45\text{ detik}$ ($\sim 11 - 14\text{ FPS}$) | **Planning Estimate — Subject to Pilot Verification** (Merujuk baseline Sprint 1: 12.28 FPS) |

### 7.2 Strategi Mitigasi Keterbatasan Hardware
1. **Host AMD CPU Tanpa NVIDIA GPU:** Pelatihan deep learning pada CPU lokal tidak praktis. Pelatihan model dialokasikan ke Google Colab hanya setelah otorisasi terpisah.
2. **Ketiadaan Jaminan GPU Colab Gratis:** Free-tier Google Colab menerapkan alokasi dinamis (*preemptible*). Jika alokasi GPU T4 tidak tersedia, proses pelatihan dapat ditunda atau dijalankan dengan batch size kecil pada alokasi berikutnya tanpa mengeluarkan biaya cloud berbayar.
3. **Isolasi Penuh Hasil Evaluasi:** Model hasil pelatihan (`best.pt`) diekspor dan dibawa kembali ke container Docker lokal untuk memastikan evaluasi benchmark operasional tetap 100% konsisten dengan runtime produksi.

---

## 8. Risks and Limitations

1. **Storage Footprint:** Mengunduh arsip utuh Train2017 (~19 GB) dapat membebani kuota laptop. Diperlukan skrip selektif atau pengunduhan terfilter berbasis API/URL langsung.
2. **Domain Adaptation Gap:** Citra COCO sebagian besar diambil pada sudut pandang horizontal (kamera saku/smartphone). Kamera pengawas CCTV biasanya terpasang pada sudut tinggi (*high-angle perspective*). Penurunan performa pada sudut CCTV tertentu dapat dimitigasi dengan augmentasi skala dan perspektif selama fine-tuning.
3. **Keterbatasan Akurasi vs Latensi:** Mengingat arsitektur target adalah `yolov8n` (nano), prioritas utama adalah mempertahankan throughput *real-time* (>12 FPS pada CPU) dengan peningkatan mAP khusus kelas person yang terukur.

---

## 9. Final Recommendations & Proposed Next Gate

### 9.1 Ringkasan Rekomendasi
- **Primary Dataset:** COCO 2017 Person-Only Curated Subset.
- **Pilot Dataset Scope:** 2,000 train (COCO Train2017), 500 validation (COCO Val2017), dan 500 holdout test (COCO Val2017) yang saling lepas (*mutually disjoint*).
- **Supplementary Datasets:** CrowdHuman dan WiderPerson ditunda (*deferred*).
- **Training Runtime:** Google Colab (setelah otorisasi terpisah).
- **Evaluation Runtime:** Container Docker terisolasi lokal pada CPU host.

### 9.2 Status Gerbang Sprint 2 (Next Gate)
- Dokumen strategi Task S2.1 ini telah direvisi secara komprehensif.
- **Task S2.2 (Dataset Acquisition & Preprocessing)** saat ini berada dalam status **HOLD**.
- Tidak ada implementasi kode, pengunduhan data, atau pelatihan model yang dimulai sebelum otorisasi resmi diberikan oleh pemilik proyek.

---

## 10. References and Official Sources

1. **COCO Consortium:** Lin, T.-Y., et al. *"Microsoft COCO: Common Objects in Context."* ECCV 2014. [cocodataset.org](https://cocodataset.org/)
2. **COCO Download & Terms:** Official Data Download Page: [cocodataset.org/#download](https://cocodataset.org/#download)
3. **CrowdHuman Benchmark:** Shao, S., et al. *"CrowdHuman: A Benchmark for Detecting Human in a Crowd."* arXiv:1805.00123 (2018). Terms of Use: [crowdhuman.org](https://www.crowdhuman.org/)
4. **WiderPerson Benchmark:** Zhang, S., et al. *"WiderPerson: A Diverse Dataset for Dense Pedestrian Detection in the Wild."* IEEE Transactions on Multimedia (2019). [wider-challenge.org](https://wider-challenge.org/)
5. **Ultralytics Documentation & License:** Ultralytics AGPL-3.0 and Enterprise Licensing Guide: [docs.ultralytics.com/license](https://docs.ultralytics.com/license/)
6. **Ultralytics YOLOv8 Dataset Format:** Ultralytics Dataset Guide: [docs.ultralytics.com/datasets/detect/](https://docs.ultralytics.com/datasets/detect/)

---

## 11. Explicit Verification & Non-Execution Confirmation

Penyusunan dan revisi dokumen ini mematuhi batasan ketat:
- [x] Tidak ada dataset yang diunduh.
- [x] Tidak ada model yang dilatih atau di-fine-tune.
- [x] Tidak ada inferensi atau benchmark baru dijalankan.
- [x] Tidak ada kode sumber aplikasi atau konfigurasi Docker yang dimodifikasi.
- [x] Tidak ada dependensi yang diinstal pada Windows host.
- [x] Tidak ada sumber daya cloud yang dialokasikan.
- [x] Seluruh artefak Sprint 0 dan Sprint 1 tetap utuh dan tidak dimodifikasi.
- [x] Implementasi Task S2.2 tetap berada dalam status **HOLD**.
