# Model Evaluation & Holdout Benchmark

## 1. Evaluation Methodology

A rigorous holdout evaluation was conducted during Sprint 2 (Gate 2.5) to assess whether custom fine-tuning improved person detection performance over the official YOLOv8n baseline.

- **Holdout Test Set:** 240 unseen images from COCO 2017 val with verified license integrity.
- **Ground Truth:** 972 annotated person bounding boxes.
- **Protocol Freeze:** Fixed image resolution (640x640), confidence threshold (0.25), and IoU threshold (0.60) across both models.
- **Hardware:** Isolated CPU evaluation environment.

## 2. Quantitative Results

<!-- Records-per-page filter: 5, 10, 30, 50, 100, 200, 300, All -->
| Metric | YOLOv8n Baseline (`yolov8n.pt`) | Fine-Tuned Model (`best.pt`) | Delta | Result |
| :--- | :--- | :--- | :--- | :--- |
| **mAP@50** | **75.32%** | 69.44% | -5.88% | Baseline Wins |
| **mAP@50-95** | **51.71%** | 44.25% | -7.46% | Baseline Wins |
| **Precision** | **78.40%** | 72.10% | -6.30% | Baseline Wins |
| **Recall** | **71.20%** | 66.80% | -4.40% | Baseline Wins |
| **Model Size** | 6.55 MB | 6.49 MB | -0.06 MB | Comparable |
| **Authoritative SHA256** | `f59b3d833e2ff32e...` | `41d74cb7e4288a52...` | N/A | Verified |

## 3. Engineering Analysis & Honest Conclusion

Contrary to naive expectations, fine-tuning on a restricted subset resulted in **performance regression** across all primary detection metrics.

### Root Cause Analysis:
1. **Domain Over-Specialization:** The fine-tuning dataset caused catastrophic forgetting of edge cases (occluded persons, varying scales) well-captured in the general COCO pre-training.
2. **Dataset Size Disparity:** The original YOLOv8n was trained on extensive, diverse data; fine-tuning on limited samples without heavy augmentation degraded generalized feature representations.

### Architectural Decision:
The fine-tuned model (`best.pt`) was designated strictly as a **research artifact**. The production serving baseline remains authoritative on `yolov8n.pt`. We explicitly do **not** claim fine-tuning improvements.
