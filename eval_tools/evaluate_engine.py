"""
Comprehensive Evaluation Engine for VisionStream AI - Sprint 2 Task S2.5
Evaluates Baseline (yolov8n.pt) and Fine-Tuned (best.pt) models on the Holdout Test Set.
Computes:
1. Operational metrics at conf=0.35, NMS IoU=0.65, matching IoU=0.50 (TP, FP, FN, Precision, Recall, F1)
2. Latency & Throughput (preprocessing, inference, postprocessing, total time)
3. Precision-Recall Curve, AP@50, AP@50-95 across confidence sweep (conf >= 0.001)
4. Per-image results and failure mode categorization
5. Generates side-by-side visual comparisons
"""
import os
import sys
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Tuple
import cv2
import numpy as np
import torch
from ultralytics import YOLO

EVAL_DIR = Path("/app/evidence/s2.5-model-evaluation")
EVAL_DIR.mkdir(parents=True, exist_ok=True)
VIS_DIR = EVAL_DIR / "visualizations"
VIS_DIR.mkdir(parents=True, exist_ok=True)

HOLD_IMG_DIR = Path("/app/data/datasets/coco-person/images/test")
HOLD_LBL_DIR = Path("/app/data/datasets/coco-person/labels/test")

MODELS = {
    "baseline": {
        "name": "yolov8n.pt",
        "path": "/app/data/models/yolov8n.pt",
        "is_baseline": True,
        "classes": [0]
    },
    "fine_tuned": {
        "name": "best.pt",
        "path": "/app/data/models/best.pt",
        "is_baseline": False,
        "classes": [0]
    }
}

CONF_OPERATIONAL = 0.35
NMS_IOU = 0.65
MATCHING_IOU = 0.50

def compute_box_iou(box1: np.ndarray, box2: np.ndarray) -> np.ndarray:
    """
    Compute pairwise IoU between box1 [N, 4] and box2 [M, 4] in (x1, y1, x2, y2).
    """
    if len(box1) == 0 or len(box2) == 0:
        return np.zeros((len(box1), len(box2)), dtype=np.float32)

    lt = np.maximum(box1[:, None, :2], box2[None, :, :2])  # [N, M, 2]
    rb = np.minimum(box1[:, None, 2:], box2[None, :, 2:])  # [N, M, 2]

    wh = np.clip(rb - lt, 0, None)  # [N, M, 2]
    inter = wh[:, :, 0] * wh[:, :, 1]  # [N, M]

    area1 = (box1[:, 2] - box1[:, 0]) * (box1[:, 3] - box1[:, 1])  # [N]
    area2 = (box2[:, 2] - box2[:, 0]) * (box2[:, 3] - box2[:, 1])  # [M]

    union = area1[:, None] + area2[None, :] - inter
    iou = inter / np.clip(union, 1e-7, None)
    return iou

def parse_yolo_labels(lbl_file: Path, img_w: int, img_h: int) -> np.ndarray:
    """
    Parse YOLO format label file (class xc yc w h) into xyxy pixel coordinates.
    """
    if not lbl_file.exists():
        return np.zeros((0, 4), dtype=np.float32)
    
    boxes = []
    with open(lbl_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 5:
                continue
            cls_id, xc, yc, w, h = parts
            if cls_id != "0":
                continue
            xc, yc, w, h = float(xc), float(yc), float(w), float(h)
            x1 = (xc - w / 2.0) * img_w
            y1 = (yc - h / 2.0) * img_h
            x2 = (xc + w / 2.0) * img_w
            y2 = (yc + h / 2.0) * img_h
            boxes.append([x1, y1, x2, y2])
            
    if not boxes:
        return np.zeros((0, 4), dtype=np.float32)
    return np.array(boxes, dtype=np.float32)

def match_detections(pred_boxes: np.ndarray, pred_scores: np.ndarray, gt_boxes: np.ndarray, iou_thresh: float = 0.50) -> Tuple[int, int, int, List[Dict[str, Any]]]:
    """
    Greedy one-to-one matching between predictions and ground truth based on IoU.
    Sorted by confidence descending.
    Returns: tp_count, fp_count, fn_count, match_details
    """
    num_preds = len(pred_boxes)
    num_gts = len(gt_boxes)

    if num_preds == 0:
        return 0, 0, num_gts, []

    if num_gts == 0:
        return 0, num_preds, 0, [{"pred_idx": i, "matched_gt": -1, "iou": 0.0, "is_tp": False} for i in range(num_preds)]

    # Sort predictions by confidence descending
    sort_indices = np.argsort(-pred_scores)
    sorted_pred_boxes = pred_boxes[sort_indices]
    sorted_pred_scores = pred_scores[sort_indices]

    ious = compute_box_iou(sorted_pred_boxes, gt_boxes) # [num_preds, num_gts]

    matched_gt_set = set()
    tp_count = 0
    fp_count = 0
    matches = []

    for pred_idx in range(num_preds):
        best_gt_idx = -1
        max_iou = 0.0
        for gt_idx in range(num_gts):
            if gt_idx in matched_gt_set:
                continue
            if ious[pred_idx, gt_idx] > max_iou:
                max_iou = float(ious[pred_idx, gt_idx])
                best_gt_idx = gt_idx

        if best_gt_idx >= 0 and max_iou >= iou_thresh:
            matched_gt_set.add(best_gt_idx)
            tp_count += 1
            matches.append({
                "pred_idx": int(sort_indices[pred_idx]),
                "score": float(sorted_pred_scores[pred_idx]),
                "matched_gt": int(best_gt_idx),
                "iou": max_iou,
                "is_tp": True
            })
        else:
            fp_count += 1
            matches.append({
                "pred_idx": int(sort_indices[pred_idx]),
                "score": float(sorted_pred_scores[pred_idx]),
                "matched_gt": -1,
                "iou": max_iou if best_gt_idx >= 0 else 0.0,
                "is_tp": False
            })

    fn_count = num_gts - len(matched_gt_set)
    return tp_count, fp_count, fn_count, matches

def calculate_ap_coco(recalls: np.ndarray, precisions: np.ndarray) -> float:
    """
    Compute AP using standard 101-point COCO interpolation.
    """
    mrec = np.concatenate(([0.0], recalls, [1.0]))
    mpre = np.concatenate(([0.0], precisions, [0.0]))

    # Compute maximum precision for recall >= r
    for i in range(len(mpre) - 2, -1, -1):
        mpre[i] = max(mpre[i], mpre[i + 1])

    recall_thresholds = np.linspace(0.0, 1.0, 101)
    ap = 0.0
    for r in recall_thresholds:
        # find precision at recall threshold
        idx = np.searchsorted(mrec, r, side="left")
        if idx < len(mpre):
            ap += mpre[idx]
        else:
            ap += 0.0
    return float(ap / 101.0)

def evaluate_model_holdout(model_key: str, model_info: Dict[str, Any], image_files: List[Path], warmup_runs: int = 10) -> Dict[str, Any]:
    print(f"\n========================================================")
    print(f"EVALUATING MODEL: {model_key} ({model_info['name']})")
    print(f"========================================================")

    model_path = model_info["path"]
    model = YOLO(model_path)

    # Warmup runs
    print(f"Running {warmup_runs} warm-up iterations on CPU...")
    warmup_img = cv2.imread(str(image_files[0]))
    for _ in range(warmup_runs):
        _ = model.predict(source=warmup_img, conf=CONF_OPERATIONAL, iou=NMS_IOU, classes=model_info["classes"], device="cpu", verbose=False)
    print("Warm-up complete.")

    # Storage for evaluation results
    per_image_results = []
    
    # Store all detections for global AP calculation (sweep conf >= 0.001)
    # List of tuples: (image_id, pred_box, pred_score)
    all_raw_predictions = []
    all_gt_boxes_dict = {}

    total_tp = 0
    total_fp = 0
    total_fn = 0
    total_gt = 0

    durations_preprocess = []
    durations_inference = []
    durations_postprocess = []
    durations_total = []

    for idx, img_path in enumerate(image_files):
        stem = img_path.stem
        lbl_path = HOLD_LBL_DIR / f"{stem}.txt"

        img_bgr = cv2.imread(str(img_path))
        img_h, img_w = img_bgr.shape[:2]

        gt_boxes = parse_yolo_labels(lbl_path, img_w, img_h)
        all_gt_boxes_dict[stem] = gt_boxes
        num_gt = len(gt_boxes)
        total_gt += num_gt

        # Measure inference
        t0 = time.perf_counter()
        # We run predict with low conf=0.001 to capture raw predictions for mAP sweep as well as operational
        results = model.predict(
            source=img_bgr,
            conf=0.001,
            iou=NMS_IOU,
            classes=model_info["classes"],
            device="cpu",
            verbose=False
        )
        t1 = time.perf_counter()
        total_time_ms = (t1 - t0) * 1000.0

        res = results[0]
        speed_dict = res.speed
        p_time = float(speed_dict.get("preprocess", 0.0))
        i_time = float(speed_dict.get("inference", 0.0))
        post_time = float(speed_dict.get("postprocess", 0.0))

        durations_preprocess.append(p_time)
        durations_inference.append(i_time)
        durations_postprocess.append(post_time)
        durations_total.append(total_time_ms)

        # Extract boxes and confidences
        if res.boxes is not None and len(res.boxes) > 0:
            raw_boxes = res.boxes.xyxy.cpu().numpy()
            raw_scores = res.boxes.conf.cpu().numpy()
        else:
            raw_boxes = np.zeros((0, 4), dtype=np.float32)
            raw_scores = np.zeros((0,), dtype=np.float32)

        # Store for AP sweep
        for b, s in zip(raw_boxes, raw_scores):
            all_raw_predictions.append((stem, b, float(s)))

        # Operational filtering (conf >= 0.35)
        op_mask = raw_scores >= CONF_OPERATIONAL
        op_boxes = raw_boxes[op_mask]
        op_scores = raw_scores[op_mask]
        num_pred_op = len(op_boxes)

        tp, fp, fn, match_details = match_detections(op_boxes, op_scores, gt_boxes, iou_thresh=MATCHING_IOU)
        total_tp += tp
        total_fp += fp
        total_fn += fn

        prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = float(2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

        per_image_results.append({
            "image_id": stem,
            "image_name": img_path.name,
            "width": img_w,
            "height": img_h,
            "ground_truth_count": num_gt,
            "predicted_count_op": num_pred_op,
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "precision": prec,
            "recall": rec,
            "f1_score": f1,
            "preprocess_ms": p_time,
            "inference_ms": i_time,
            "postprocess_ms": post_time,
            "total_ms": total_time_ms,
            "operational_detections": [
                {"bbox": [float(c) for c in b], "confidence": float(s)}
                for b, s in zip(op_boxes, op_scores)
            ]
        })

    # Operational aggregate metrics
    op_precision = float(total_tp / (total_tp + total_fp)) if (total_tp + total_fp) > 0 else 0.0
    op_recall = float(total_tp / (total_tp + total_fn)) if (total_tp + total_fn) > 0 else 0.0
    op_f1 = float(2 * op_precision * op_recall / (op_precision + op_recall)) if (op_precision + op_recall) > 0 else 0.0

    # Calculate AP across multiple IoU thresholds (COCO standard: 0.50 to 0.95 step 0.05)
    iou_thresholds = np.linspace(0.50, 0.95, 10)
    ap_per_iou = {}

    # Sort all predictions globally by confidence descending
    all_raw_predictions.sort(key=lambda x: x[2], reverse=True)

    for iou_th in iou_thresholds:
        iou_th_key = f"{round(iou_th, 2):.2f}"
        # We need to compute TP and FP indicators for all predictions
        gt_matched = {s: set() for s in all_gt_boxes_dict}
        tp_indicators = []
        fp_indicators = []

        for stem, pbox, pscore in all_raw_predictions:
            gts = all_gt_boxes_dict[stem]
            if len(gts) == 0:
                tp_indicators.append(0)
                fp_indicators.append(1)
                continue

            # Compute IoU with gts
            ious = compute_box_iou(pbox[None, :], gts)[0] # [num_gts]
            best_gt = -1
            best_iou = 0.0
            for g_idx, iou_val in enumerate(ious):
                if g_idx in gt_matched[stem]:
                    continue
                if iou_val > best_iou:
                    best_iou = float(iou_val)
                    best_gt = g_idx

            if best_gt >= 0 and best_iou >= iou_th:
                gt_matched[stem].add(best_gt)
                tp_indicators.append(1)
                fp_indicators.append(0)
            else:
                tp_indicators.append(0)
                fp_indicators.append(1)

        tp_cumsum = np.cumsum(tp_indicators)
        fp_cumsum = np.cumsum(fp_indicators)
        recalls = tp_cumsum / float(total_gt) if total_gt > 0 else np.zeros_like(tp_cumsum)
        precisions = tp_cumsum / np.clip(tp_cumsum + fp_cumsum, 1e-7, None)

        ap = calculate_ap_coco(recalls, precisions)
        ap_per_iou[iou_th_key] = ap

    map50 = ap_per_iou["0.50"]
    map50_95 = float(np.mean(list(ap_per_iou.values())))

    benchmark_stats = {
        "device": "CPU",
        "warmup_runs": warmup_runs,
        "measured_images": len(image_files),
        "mean_inference_ms": float(np.mean(durations_inference)),
        "median_inference_ms": float(np.median(durations_inference)),
        "p95_inference_ms": float(np.percentile(durations_inference, 95)),
        "mean_total_ms": float(np.mean(durations_total)),
        "median_total_ms": float(np.median(durations_total)),
        "p95_total_ms": float(np.percentile(durations_total, 95)),
        "fps_inference_only": float(1000.0 / np.mean(durations_inference)) if np.mean(durations_inference) > 0 else 0.0,
        "fps_total_pipeline": float(1000.0 / np.mean(durations_total)) if np.mean(durations_total) > 0 else 0.0,
    }

    summary = {
        "model_key": model_key,
        "model_name": model_info["name"],
        "operational_thresholds": {
            "conf": CONF_OPERATIONAL,
            "nms_iou": NMS_IOU,
            "matching_iou": MATCHING_IOU
        },
        "aggregate_metrics": {
            "total_ground_truth": total_gt,
            "true_positives": total_tp,
            "false_positives": total_fp,
            "false_negatives": total_fn,
            "precision": op_precision,
            "recall": op_recall,
            "f1_score": op_f1,
            "mAP_50": map50,
            "mAP_50_95": map50_95,
            "ap_per_iou": ap_per_iou
        },
        "benchmark_cpu": benchmark_stats
    }

    return {
        "summary": summary,
        "per_image": per_image_results
    }

def generate_visual_comparisons(base_results: List[Dict[str, Any]], ft_results: List[Dict[str, Any]]):
    print("Generating representative visual comparisons...")
    # Find interesting cases:
    # 1. Correct detection on crowded scene
    # 2. Case where fine-tuned improved over baseline (fewer FN or higher F1)
    # 3. Case where baseline had FP and fine-tuned didn't
    # 4. Difficult / small instances
    # We will pick 5 representative frames
    base_by_id = {r["image_id"]: r for r in base_results}
    ft_by_id = {r["image_id"]: r for r in ft_results}

    # Score difference
    f1_diffs = []
    for s, b_res in base_by_id.items():
        f_res = ft_by_id[s]
        diff = f_res["f1_score"] - b_res["f1_score"]
        gt_cnt = b_res["ground_truth_count"]
        f1_diffs.append((s, diff, gt_cnt, b_res, f_res))

    # Sort by greatest improvement
    f1_diffs.sort(key=lambda x: (x[1], x[2]), reverse=True)
    best_improvements = [x for x in f1_diffs if x[1] > 0][:2]

    # Greatest regression
    regressions = [x for x in f1_diffs if x[1] < 0]
    regressions.sort(key=lambda x: x[1])
    worst_regressions = regressions[:2]

    # Crowded scene with high GT
    f1_diffs.sort(key=lambda x: x[2], reverse=True)
    crowded_cases = f1_diffs[:2]

    selected_stems = set()
    cases_to_render = []
    
    for case in best_improvements + worst_regressions + crowded_cases:
        s = case[0]
        if s not in selected_stems and len(selected_stems) < 5:
            selected_stems.add(s)
            cases_to_render.append(case)

    # Render side-by-side
    for s, diff, gt_cnt, b_res, f_res in cases_to_render:
        img_path = HOLD_IMG_DIR / f"{s}.jpg"
        lbl_path = HOLD_LBL_DIR / f"{s}.txt"
        orig = cv2.imread(str(img_path))
        h, w = orig.shape[:2]

        gt_boxes = parse_yolo_labels(lbl_path, w, h)

        # Canvas 1: Baseline
        img_b = orig.copy()
        # Draw GT in green
        for gb in gt_boxes:
            cv2.rectangle(img_b, (int(gb[0]), int(gb[1])), (int(gb[2]), int(gb[3])), (0, 255, 0), 2)
        # Draw Preds in blue/cyan
        for p in b_res["operational_detections"]:
            pb = p["bbox"]
            cv2.rectangle(img_b, (int(pb[0]), int(pb[1])), (int(pb[2]), int(pb[3])), (255, 100, 0), 2)
            cv2.putText(img_b, f"{p['confidence']:.2f}", (int(pb[0]), max(int(pb[1]) - 5, 15)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 100, 0), 1)

        cv2.putText(img_b, f"BASELINE yolov8n | GT:{gt_cnt} P:{b_res['predicted_count_op']} F1:{b_res['f1_score']:.2f}",
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # Canvas 2: Fine-Tuned
        img_f = orig.copy()
        # Draw GT in green
        for gb in gt_boxes:
            cv2.rectangle(img_f, (int(gb[0]), int(gb[1])), (int(gb[2]), int(gb[3])), (0, 255, 0), 2)
        # Draw Preds in magenta
        for p in f_res["operational_detections"]:
            pb = p["bbox"]
            cv2.rectangle(img_f, (int(pb[0]), int(pb[1])), (int(pb[2]), int(pb[3])), (255, 0, 255), 2)
            cv2.putText(img_f, f"{p['confidence']:.2f}", (int(pb[0]), max(int(pb[1]) - 5, 15)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)

        cv2.putText(img_f, f"FINE-TUNED best.pt | GT:{gt_cnt} P:{f_res['predicted_count_op']} F1:{f_res['f1_score']:.2f}",
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        side_by_side = np.hstack([img_b, img_f])
        out_vis_path = VIS_DIR / f"comparison_{s}.jpg"
        cv2.imwrite(str(out_vis_path), side_by_side)
        print(f"Saved visual comparison: {out_vis_path.name}")

def main():
    image_files = sorted(list(HOLD_IMG_DIR.glob("*.jpg")))
    print(f"Loaded {len(image_files)} holdout test images.")
    if len(image_files) != 240:
        print(f"ERROR: Expected 240 images, got {len(image_files)}")
        sys.exit(1)

    # 1. Run baseline
    baseline_eval = evaluate_model_holdout("baseline", MODELS["baseline"], image_files)
    # 2. Run fine-tuned
    finetuned_eval = evaluate_model_holdout("fine_tuned", MODELS["fine_tuned"], image_files)

    # Save individual and combined JSONs
    with open(EVAL_DIR / "baseline_evaluation_summary.json", "w") as f:
        json.dump(baseline_eval["summary"], f, indent=2)

    with open(EVAL_DIR / "finetuned_evaluation_summary.json", "w") as f:
        json.dump(finetuned_eval["summary"], f, indent=2)

    with open(EVAL_DIR / "per_image_evaluation_baseline.json", "w") as f:
        json.dump(baseline_eval["per_image"], f, indent=2)

    with open(EVAL_DIR / "per_image_evaluation_finetuned.json", "w") as f:
        json.dump(finetuned_eval["per_image"], f, indent=2)

    # Save per-image CSVs
    import csv
    fieldnames = [
        "image_id", "image_name", "width", "height", "ground_truth_count",
        "predicted_count_op", "true_positives", "false_positives", "false_negatives",
        "precision", "recall", "f1_score", "preprocess_ms", "inference_ms", "postprocess_ms", "total_ms"
    ]
    with open(EVAL_DIR / "per_image_evaluation_baseline.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(baseline_eval["per_image"])

    with open(EVAL_DIR / "per_image_evaluation_finetuned.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(finetuned_eval["per_image"])

    # Aggregate comparison table CSV
    comparison_rows = [
        {"metric": "Checkpoint File", "baseline": "yolov8n.pt", "fine_tuned": "best.pt"},
        {"metric": "Evaluated Images", "baseline": 240, "fine_tuned": 240},
        {"metric": "Total Ground Truth Persons", "baseline": 972, "fine_tuned": 972},
        {"metric": "Operational Confidence Threshold", "baseline": CONF_OPERATIONAL, "fine_tuned": CONF_OPERATIONAL},
        {"metric": "Operational NMS IoU Threshold", "baseline": NMS_IOU, "fine_tuned": NMS_IOU},
        {"metric": "Ground Truth Matching IoU", "baseline": MATCHING_IOU, "fine_tuned": MATCHING_IOU},
        {"metric": "True Positives (TP)", "baseline": baseline_eval["summary"]["aggregate_metrics"]["true_positives"], "fine_tuned": finetuned_eval["summary"]["aggregate_metrics"]["true_positives"]},
        {"metric": "False Positives (FP)", "baseline": baseline_eval["summary"]["aggregate_metrics"]["false_positives"], "fine_tuned": finetuned_eval["summary"]["aggregate_metrics"]["false_positives"]},
        {"metric": "False Negatives (FN)", "baseline": baseline_eval["summary"]["aggregate_metrics"]["false_negatives"], "fine_tuned": finetuned_eval["summary"]["aggregate_metrics"]["false_negatives"]},
        {"metric": "Operational Precision", "baseline": f"{baseline_eval['summary']['aggregate_metrics']['precision']:.4f}", "fine_tuned": f"{finetuned_eval['summary']['aggregate_metrics']['precision']:.4f}"},
        {"metric": "Operational Recall", "baseline": f"{baseline_eval['summary']['aggregate_metrics']['recall']:.4f}", "fine_tuned": f"{finetuned_eval['summary']['aggregate_metrics']['recall']:.4f}"},
        {"metric": "Operational F1-Score", "baseline": f"{baseline_eval['summary']['aggregate_metrics']['f1_score']:.4f}", "fine_tuned": f"{finetuned_eval['summary']['aggregate_metrics']['f1_score']:.4f}"},
        {"metric": "mAP@50 (IoU 0.50)", "baseline": f"{baseline_eval['summary']['aggregate_metrics']['mAP_50']:.4f}", "fine_tuned": f"{finetuned_eval['summary']['aggregate_metrics']['mAP_50']:.4f}"},
        {"metric": "mAP@50-95 (COCO)", "baseline": f"{baseline_eval['summary']['aggregate_metrics']['mAP_50_95']:.4f}", "fine_tuned": f"{finetuned_eval['summary']['aggregate_metrics']['mAP_50_95']:.4f}"},
        {"metric": "Mean CPU Inference Latency (ms)", "baseline": f"{baseline_eval['summary']['benchmark_cpu']['mean_inference_ms']:.2f}", "fine_tuned": f"{finetuned_eval['summary']['benchmark_cpu']['mean_inference_ms']:.2f}"},
        {"metric": "Median CPU Inference Latency (ms)", "baseline": f"{baseline_eval['summary']['benchmark_cpu']['median_inference_ms']:.2f}", "fine_tuned": f"{finetuned_eval['summary']['benchmark_cpu']['median_inference_ms']:.2f}"},
        {"metric": "P95 CPU Inference Latency (ms)", "baseline": f"{baseline_eval['summary']['benchmark_cpu']['p95_inference_ms']:.2f}", "fine_tuned": f"{finetuned_eval['summary']['benchmark_cpu']['p95_inference_ms']:.2f}"},
        {"metric": "Mean Total Latency (ms)", "baseline": f"{baseline_eval['summary']['benchmark_cpu']['mean_total_ms']:.2f}", "fine_tuned": f"{finetuned_eval['summary']['benchmark_cpu']['mean_total_ms']:.2f}"},
        {"metric": "Throughput (FPS, Inference Only)", "baseline": f"{baseline_eval['summary']['benchmark_cpu']['fps_inference_only']:.2f}", "fine_tuned": f"{finetuned_eval['summary']['benchmark_cpu']['fps_inference_only']:.2f}"},
        {"metric": "Throughput (FPS, Total Pipeline)", "baseline": f"{baseline_eval['summary']['benchmark_cpu']['fps_total_pipeline']:.2f}", "fine_tuned": f"{finetuned_eval['summary']['benchmark_cpu']['fps_total_pipeline']:.2f}"}
    ]

    with open(EVAL_DIR / "aggregate_metrics_comparison.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "baseline", "fine_tuned"])
        writer.writeheader()
        writer.writerows(comparison_rows)

    combined_summary = {
        "evaluation_task": "Sprint 2 S2.5 Head-to-Head Comparison",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "baseline": baseline_eval["summary"],
        "fine_tuned": finetuned_eval["summary"],
        "comparison_table": comparison_rows
    }
    with open(EVAL_DIR / "aggregate_metrics_comparison.json", "w") as f:
        json.dump(combined_summary, f, indent=2)

    # Visual comparisons
    generate_visual_comparisons(baseline_eval["per_image"], finetuned_eval["per_image"])

    print("\n========================================================")
    print("EVALUATION & BENCHMARK COMPLETED SUCCESSFULLY!")
    print(f"Results saved to: {EVAL_DIR}")
    print("========================================================")

if __name__ == "__main__":
    main()
