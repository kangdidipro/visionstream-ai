# MASTER BLUEPRINT REVIEW CHANGELOG

**Document ID:** `MASTER-BLUEPRINT-REVIEW-CHANGELOG`  
**Governing Document:** `docs/architecture/MASTER-BLUEPRINT.md`  
**Target Version:** 1.0.1 (Corrected from Version 1.0)  
**Date:** November 5, 2026  
**Review Type:** Architecture and Governance Review  
**Status:** All Required Corrections Applied

---

## 1. Summary of Changes

Dokumen Master Blueprint (`docs/architecture/MASTER-BLUEPRINT.md`) telah diperbarui ke **Versi 1.0.1** untuk mengakomodasi seluruh masukan review arsitektur tanpa mengubah implementasi kode sumber, tanpa mengubah konfigurasi Docker, dan tanpa memulai sprint baru.

---

## 2. Itemized Corrections

### Correction 1: Phase and Sprint Mapping
- **Bagian yang Diperbaiki:** Section 7 (*Project Development Roadmap & Sprint Mapping*).
- **Alasan Koreksi:** Menghilangkan kebingungan antara penomoran Fase Master (Phase 0–8) dan penomoran Sprint operasional (Sprint 0–6 & Final Release).
- **Klasifikasi Perubahan:** *Architectural & Governance Clarification*.
- **Rincian Perubahan:**
  - Phase 0 $\rightarrow$ Sprint 0 (Environment Assessment).
  - Phase 1 $\rightarrow$ Sprint 0A / Architecture Gate (Architecture & Repository).
  - Phase 2 $\rightarrow$ Sprint 1 (Person Detection & Tracking).
  - Phase 3 $\rightarrow$ Sprint 2 (Model Training & Evaluation).
  - Phase 4 $\rightarrow$ Sprint 3 (NVIDIA TensorRT Optimization).
  - Phase 5 $\rightarrow$ Sprint 4 (DeepStream & Multi-Stream Processing).
  - Phase 6 $\rightarrow$ Sprint 5 (Triton & Inference Serving).
  - Phase 7 $\rightarrow$ Sprint 6 (Database, Dashboard & Deployment).
  - Phase 8 $\rightarrow$ Final Release (Portfolio Release).

---

### Correction 2: Sprint 1 Status Reconciliation
- **Bagian yang Diperbaiki:** Section 7 (Phase 2 Detail) dan Section 13 (*Current Acceptance State Table*).
- **Alasan Koreksi:** Membedakan secara eksplisit antara kelulusan teknis fungsional (*functional pass*), audit video empiris, dan persetujuan formal (*formal gate approval*) oleh pemilik proyek.
- **Klasifikasi Perubahan:** *Governance & Evidence Alignment*.
- **Rincian Perubahan:**
  - Status implementasi fungsional: **PASS**.
  - Pengujian video baseline (`people-detection.mp4`): **PASS** (merujuk pada `reports/SPRINT-01-VIDEO-TEST-EVIDENCE-AUDIT.md`).
  - Pengujian video CCTV tambahan (`people-detection-faces.mp4`): **PASS** (merujuk secara eksplisit pada `reports/SPRINT-01-ADDITIONAL-VIDEO-TEST-RESULTS.md`, 460 frame, 4,667 deteksi, 99 track).
  - Status Persetujuan Formal Sprint 1: **PENDING** hingga pemilik proyek memberikan persetujuan eksplisit.

---

### Correction 3: DeepStream and Triton Architectural Patterns
- **Bagian yang Diperbaiki:** Section 4.2 (*Logical Processing Flow & Architectural Patterns*) dan Section 4.3 (*Target Architecture Diagram*).
- **Alasan Koreksi:** Mencegah kesalahpahaman bahwa DeepStream dan Triton harus selalu digabungkan secara monolitik.
- **Klasifikasi Perubahan:** *Architectural Design Clarification*.
- **Rincian Perubahan:** Mendefinisikan 3 pola arsitektur yang didukung secara modular:
  - **Pattern A:** NVIDIA DeepStream + TensorRT Engine (pipeline analitik video terintegrasi penuh).
  - **Pattern B:** Application / Video Pipeline + Triton Inference Server (arsitektur microservice decoupled).
  - **Pattern C:** DeepStream + Triton Server Backend Integration (DeepStream menggunakan plugin `nvinferserver` untuk routing ke Triton).

---

### Correction 4: Model Evaluation Ground-Truth Requirements
- **Bagian yang Diperbaiki:** Section 8.1 (*Ground-Truth Evaluation Requirements*) dan Section 8.3 (*Tracking Metrics: Operational vs. Benchmark*).
- **Alasan Koreksi:** Menjaga kredibilitas teknis agar metrik akurasi formal (mAP, IDF1, HOTA, MOTA) tidak diklaim secara keliru pada video tanpa anotasi ground truth.
- **Klasifikasi Perubahan:** *Methodological Rigor & Evaluation Governance*.
- **Rincian Perubahan:**
  - Menetapkan bahwa evaluasi deteksi (mAP50, mAP50-95, PR-curves) **wajib** menggunakan dataset beranotasi bounding box ground truth manusia.
  - Menetapkan bahwa evaluasi tracking formal (IDF1, HOTA, ID switches) **wajib** menggunakan dataset ground truth identitas temporal lintas frame.
  - Menegaskan bahwa metrik pada video CCTV tanpa anotasi diklasifikasikan sebagai *Operational Tracking Statistics* (bukan formal benchmark accuracy).

---

### Correction 5: Docker Isolation Policy
- **Bagian yang Diperbaiki:** Section 6.1 (*Docker Isolation Policy*).
- **Alasan Koreksi:** Mempertegas aturan isolasi sistem host Windows, container runtime lokal, Google Colab, dan NVIDIA Cloud GPU.
- **Klasifikasi Perubahan:** *Operational Policy Clarification*.
- **Rincian Perubahan:**
  - Menegaskan kembali: tidak ada instalasi Python global di Windows, tidak ada `.venv` lokal Windows, dan tidak ada perubahan konfigurasi Windows yang tidak disetujui.
  - Menetapkan bahwa beban kerja NVIDIA Cloud GPU wajib menggunakan container NVIDIA Container Toolkit.
  - Menetapkan bahwa eksperimen Colab wajib dijalankan pada runtime terisolasi mandiri.

---

### Correction 6: GitHub Asset Management Rules
- **Bagian yang Diperbaiki:** Section 10 (*GitHub & Asset Management Rules*).
- **Alasan Koreksi:** Mencegah kebocoran kredensial, pelanggaran lisensi, dan commit file biner besar ke dalam repositori Git publik.
- **Klasifikasi Perubahan:** *Security & Repository Hygiene Governance*.
- **Rincian Perubahan:**
  - Larangan mutlak melakukan commit secrets, API keys, dan file `.env`.
  - Larangan melakukan commit file video mentah (`data/inputs/*`), video teranotasi (`data/outputs/*`), dan model weights (`data/models/*`).
  - Kewajiban mencantumkan atribusi, lisensi, dan dokumentasi asal aset pihak ketiga.

---

### Correction 7: Document Consistency Review
- **Bagian yang Diperbaiki:** Seluruh dokumen (`docs/architecture/MASTER-BLUEPRINT.md`).
- **Alasan Koreksi:** Menghilangkan duplikasi, menghapus pernyataan yang bertentangan, dan memastikan penomoran versi 1.0.1 sinkron.
- **Klasifikasi Perubahan:** *Editorial Refinement*.

---

## 3. Unresolved Issues

Tidak ada isu teknis atau tata kelola arsitektur yang belum terselesaikan. Seluruh butir masukan telah diakomodasi secara tuntas dan konsisten.
