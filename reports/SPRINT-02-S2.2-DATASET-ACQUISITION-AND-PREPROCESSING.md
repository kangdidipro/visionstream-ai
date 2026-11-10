# SPRINT 2 — TASK S2.2 REPORT
## DATASET ACQUISITION & PREPROCESSING (COCO PERSON-ONLY PILOT)

**Project:** VisionStream AI  
**Task Identifier:** `S2.2 — Dataset Acquisition & Preprocessing`  
**Governing Phase:** Phase 3 (Operational Sprint 2 — Model Training & Evaluation)  
**Execution Environment:** Isolated Docker Container (`visionstream-ai:sprint-1`) on Windows 11 (`LAPTOP-62621JIA`)  
**Document Date:** November 5, 2026  
**Canonical File Location:** `C:\my-app\visionstream-ai\reports\SPRINT-02-S2.2-DATASET-ACQUISITION-AND-PREPROCESSING.md`  
**Task Verdict:** **PASS** (100% Verified CC BY 2.0 Dataset Acquired & Tested — Zero Model Training/Inference Executed)

---

## 1. Executive Summary

Task S2.2 telah berhasil diselesaikan secara penuh di dalam lingkungan Docker terisolasi tanpa instalasi dependensi host Windows maupun modifikasi pada pipeline Sprint 1.

Mengikuti otorisasi resmi pemilik proyek (*Approved Scope Option 1*), alur akuisisi menerapkan pemfilteran lisensi yang ketat (*Strict License Gate*). Karena hanya terdapat 484 citra berlabel `person` di dalam COCO Val2017 yang memenuhi lisensi murni CC BY 2.0 (License ID 4), alokasi split disesuaikan secara berimbang menjadi:
- **Train Set:** **2,000 citra** (dari COCO Train2017).
- **Validation Set:** **239 citra** (dari COCO Val2017).
- **Holdout Test Set:** **240 citra** (dari COCO Val2017).
- **Total Citra Terakuisisi:** **2,479 citra** (seluruhnya 100% berlisensi CC BY 2.0).

Seluruh anotasi bounding box `person` (Class ID `0`) telah dikonversi ke format standar YOLO TXT ternormalisasi. Suite pengujian integritas otomatis (`test_dataset_integrity.py`) mengonfirmasi kelengkapan file, keabsahan sintaks YOLO, independensi split (*100% disjoint* tanpa kebocoran data spasial atau hash), dan kelayakan lisensi dengan hasil **ALL INTEGRITY TESTS PASSED**.

---

## 2. Acquisition Method & Provenance Screening

### 2.1 Sumber Resmi & Arsip Anotasi
1. **Official Annotation Archive:** `http://images.cocodataset.org/annotations/annotations_trainval2017.zip`
   - SHA-256: `113a836d90195ee1f884e704da6304dfaaecff1f023f49b6ca93c4aaae470268` (241.2 MB).
2. **Official Annotations JSON:**
   - `instances_train2017.json` (SHA-256: `610fce4944abdeb15354cc765333805529359d12d88f2f711393ca586901d01d`).
   - `instances_val2017.json` (SHA-256: `e8c7f7908f1d7278341fae127d0da654f102f11bd7b21d8aeefa635b8c810b6f`).
3. **Seleksi Selektif Citra Mandiri:** Citra diunduh satu per satu secara paralel (16 worker threads) langsung dari server CDN resmi COCO (`http://images.cocodataset.org/{train2017,val2017}/<file_name>`). **Tidak ada pengunduhan arsip gambar penuh (~20 GB) yang dilakukan**, menjaga penggunaan bandwidth dan disk host.

### 2.2 License and Provenance Audit

Berdasarkan metadata resmi COCO, terdapat 8 kategori lisensi gambar Flickr:

| License ID | Nama Lisensi Metadata COCO | URL Lisensi | Keputusan S2.2 Gate | Jumlah Person Images (Val2017) | Jumlah Person Images (Train2017) |
|:---:|:---|:---|:---:|:---:|:---:|
| **1** | Attribution-NonCommercial-ShareAlike | `creativecommons.org/licenses/by-nc-sa/2.0/` | **REJECT** (Non-commercial) | 808 | 17,913 |
| **2** | Attribution-NonCommercial | `creativecommons.org/licenses/by-nc/2.0/` | **REJECT** (Non-commercial) | 331 | 8,950 |
| **3** | Attribution-NonCommercial-NoDerivs | `creativecommons.org/licenses/by-nc-nd/2.0/` | **REJECT** (Non-commercial, No-derivs) | 716 | 17,506 |
| **4** | **Attribution License (CC BY 2.0)** | `creativecommons.org/licenses/by/2.0/` | **ACCEPT (APPROVED SCOPE)** | **479** | **10,322** |
| **5** | Attribution-ShareAlike (CC BY-SA 2.0) | `creativecommons.org/licenses/by-sa/2.0/` | **REJECT** (Per S2.2 Update) | 212 | 5,809 |
| **6** | Attribution-NoDerivs (CC BY-ND 2.0) | `creativecommons.org/licenses/by-nd/2.0/` | **REJECT** (No-derivatives) | 142 | 3,233 |
| **7** | No known copyright restrictions | `flickr.com/commons/usage/` | **REJECT** (Per S2.2 Update) | 5 | 382 |
| **8** | United States Government Work | `usa.gov/copyright.shtml` | N/A (0 citra) | 0 | 0 |

**Status Audit Lisensi:** **100% Lolos.** Sebanyak 2,479 citra yang diakuisisi seluruhnya terverifikasi berlisensi **CC BY 2.0 (License ID 4)**. Seluruh URL Flickr asli, tanggal pengambilan, lisensi, dan ID citra tersimpan rapi pada manifest metadata.

---

## 3. Actual Dataset Counts & Split Manifest

### 3.1 Ringkasan Jumlah Dataset

| Split | Sumber Resmi | Target Awal | Target Disetujui (Opsi 1) | Citra Terakuisisi | Label File Valid | Total Bounding Box Person |
|:---|:---|---:|---:|---:|---:|---:|
| **Train** | COCO Train2017 | 2,000 | 2,000 | **2,000** | 2,000 | 8,024 |
| **Validation** | COCO Val2017 | 500 | 239 | **239** | 239 | 983 |
| **Holdout Test** | COCO Val2017 | 500 | 240 | **240** | 240 | 962 |
| **TOTAL** | | 3,000 | 2,479 | **2,479** | **2,479** | **9,969** |

### 3.2 Integritas dan Pemisahan Split (*Disjointness*)
- **Random Seed:** `42` (menggunakan generator acak deterministik `random.Random(42)`).
- **Uji Tumpang Tindih ID Citra (*Image ID Overlap*):**
  - $\text{Train} \cap \text{Val} = \emptyset$ (0 overlap).
  - $\text{Train} \cap \text{Test} = \emptyset$ (0 overlap).
  - $\text{Val} \cap \text{Test} = \emptyset$ (0 overlap).
- **Uji Tumpang Tindih Konten Citra (*SHA-256 Hash Overlap*):**
  - $\text{Hash}(\text{Train}) \cap \text{Hash}(\text{Val}) = \emptyset$ (0 overlap).
  - $\text{Hash}(\text{Train}) \cap \text{Hash}(\text{Test}) = \emptyset$ (0 overlap).
  - $\text{Hash}(\text{Val}) \cap \text{Hash}(\text{Test}) = \emptyset$ (0 overlap).
- Seluruh 2,479 citra memiliki hash SHA-256 yang unik tanpa duplikasi konten lintas subset.

---

## 4. Annotation Conversion Method

### 4.1 Format Konversi COCO ke YOLO
Setiap bounding box dikonversi dari format piksel absolut COCO `[x_min, y_min, width, height]` ke format koordinat relatif ternormalisasi YOLO:
$$\text{x\_center} = \frac{x_1 + x_2}{2 \cdot W}, \quad \text{y\_center} = \frac{y_1 + y_2}{2 \cdot H}, \quad \text{norm\_w} = \frac{x_2 - x_1}{W}, \quad \text{norm\_h} = \frac{y_2 - y_1}{H}$$

Format teks YOLO TXT per baris:
```text
0 <x_center> <y_center> <norm_w> <norm_h>
```
di mana `0` merepresentasikan kelas `person`.

### 4.2 Kebijakan Penanganan Bounding Box & Crowd
1. **Anomali Koordinat / Clipping:** Bounding box yang sedikit melebihi dimensi batas citra ($W, H$) dipotong (*clipped*) secara aman ke interval $[0.0, W]$ dan $[0.0, H]$.
2. **Zero-Area Box:** Kotak dengan lebar atau tinggi $\le 0$ diabaikan.
3. **Pengecualian `iscrowd`:** Anotasi yang memiliki flag `iscrowd == 1` (wilayah kerumunan yang tidak memiliki kotak individual yang tegas) **dikecualikan** dari bounding box pelatihan/evaluasi reguler, menjamin bahwa model hanya dilatih dan diuji pada instans individu yang terisolasi dengan baik.

---

## 5. Dataset Directory Structure & Deliverables

Struktur direktori dataset telah dibuat pada `data/datasets/coco-person/`:

```text
data/datasets/coco-person/
├── dataset.yaml
├── README.md
├── images/
│   ├── train/     [2,000 JPG images, 316.47 MB]
│   ├── val/       [  239 JPG images,  37.46 MB]
│   └── test/      [  240 JPG images,  38.07 MB]
├── labels/
│   ├── train/     [2,000 TXT label files]
│   ├── val/       [  239 TXT label files]
│   └── test/      [  240 TXT label files]
└── metadata/
    ├── image-manifest.json        [Manifest lengkap 2,479 entri metadata citra & Flickr URL]
    ├── annotation-manifest.json   [Ringkasan 9,969 bounding box terkonversi]
    ├── license-manifest.json      [Metadata audit lisensi CC BY 2.0]
    ├── split-manifest.json        [Daftar deterministik Image ID per split]
    └── checksums.sha256           [Daftar SHA-256 untuk 2,479 citra]
```

### 5.1 Konfigurasi Ultralytics `dataset.yaml`
```yaml
# Ultralytics YOLOv8 Dataset Configuration
# VisionStream AI - Sprint 2 Person Detection Dataset
# License: CC BY 2.0 (COCO 2017 Curated Person-Only Pilot Subset)

path: /app/data/datasets/coco-person
train: images/train
val: images/val
test: images/test

names:
  0: person
```

### 5.2 Perlindungan Repositori (`.gitignore`)
Aturan `data/datasets/*` telah ditambahkan ke dalam `.gitignore`, dengan pengecualian `.gitkeep`. File citra mentah (~392 MB) **tidak akan terlacak atau ter-commit ke dalam repositori Git publik**, mematuhi kebijakan portofolio dan pedoman lisensi redistribusi citra.

---

## 6. Storage Footprint

| Komponen | Ukuran Aktual | Keterangan |
|:---|---:|:---|
| `images/train` (2,000 citra) | 316.47 MB | File JPEG resolusi asli COCO |
| `images/val` (239 citra) | 37.46 MB | File JPEG resolusi asli COCO |
| `images/test` (240 citra) | 38.07 MB | File JPEG resolusi asli COCO |
| `labels/` (2,479 file TXT) | 0.36 MB | Koordinat bounding-box format YOLO |
| `metadata/` (Manifest & Checksums) | 1.69 MB | Metadata JSON & SHA-256 |
| **Total Dataset Footprint** | **394.06 MB (0.38 GB)** | Sangat ringkas dan efisien untuk host laptop |

---

## 7. Automated Integrity Test Results

Suite pengujian otomatis dijalankan melalui script [`src/test_dataset_integrity.py`](file:///c:/my-app/visionstream-ai/src/test_dataset_integrity.py) di dalam container Docker:

```json
{
  "image_counts": {
    "train": 2000,
    "val": 239,
    "test": 240
  },
  "label_counts": {
    "train": 2000,
    "val": 239,
    "test": 240
  },
  "manifest_entries": 2479,
  "split_id_counts": {
    "train": 2000,
    "val": 239,
    "test": 240
  },
  "all_licenses": [
    4
  ],
  "total_person_annotations": 9969,
  "total_parsed_boxes": 9969,
  "invalid_label_files": 0,
  "checksum_file_exists": true,
  "dataset_yaml_exists": true,
  "readme_exists": true,
  "status": "PASS"
}
```
**Status Hasil:** **ALL INTEGRITY TESTS PASSED.**

---

## 8. Important Methodology Notice

Sesuai metodologi yang disetujui:
- Model baseline `yolov8n.pt` sebelumnya telah dilatih oleh Ultralytics pada keseluruhan dataset COCO 2017 (80 kelas).
- Oleh karena itu, eksperimen fine-tuning mendatang (Task S2.3) didefinisikan secara jujur dan ilmiah sebagai:  
  **"Continued domain fine-tuning / class-focused specialization within the COCO domain"**,  
  bukan sebagai pelatihan pada dataset yang sepenuhnya belum pernah dilihat model (*unseen dataset*).
- Generalisasi independen (*out-of-domain generalization*) tidak diklaim hanya berdasarkan eksperimen COCO subset ini.

---

## 9. Strict Non-Execution & Audit Confirmation

Sesuai batasan otorisasi Task S2.2:
- [x] **TIDAK ADA pelatihan model atau fine-tuning yang dijalankan.**
- [x] **TIDAK ADA inferensi baru atau evaluasi model yang dijalankan.**
- [x] **TIDAK ADA sumber daya Google Colab atau Cloud GPU yang dialokasikan.**
- [x] **TIDAK ADA lisensi berbayar atau layanan komersial yang dibeli.**
- [x] Seluruh eksekusi Python berjalan 100% di dalam Docker container.
- [x] Tidak ada perubahan dependensi atau Python `.venv` pada Windows host.
- [x] Seluruh kode dan artefak Sprint 0 dan Sprint 1 tetap utuh dan terlindungi.
- [x] Task S2.3 **BELUM DIMULAI**.

---

## 10. Recommended Next Gate

Task S2.2 telah selesai dengan vonis **PASS**.  
Tahap selanjutnya adalah **Task S2.3 — Training Experiment Setup & Fine-Tuning Execution Plan**.

Saat ini proses berada dalam status **STOP & HOLD** menunggu tinjauan dan otorisasi tertulis terpisah dari pemilik proyek.
