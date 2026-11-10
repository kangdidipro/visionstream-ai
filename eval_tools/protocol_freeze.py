"""
VisionStream AI - Sprint 2 Task S2.5
Protocol Freeze Specification: Model Evaluation & Head-to-Head Comparison
"""
import json
from pathlib import Path

EVAL_CONFIG = {
    "protocol_version": "1.0.0",
    "task": "S2.5 - Model Evaluation & Head-to-Head Comparison",
    "governing_document": "docs/architecture/MASTER-BLUEPRINT.md",
    "master_blueprint_sha256": "5A8C05D91F1BE08BFE89AE495DAC4553C63CE164655F4C7C98155AFFC0BEE19A",
    "models": {
        "baseline": {
            "name": "yolov8n.pt",
            "path": "/app/data/models/yolov8n.pt",
            "expected_sha256": "f59b3d833e2ff32e194b5bb8e08d211dc7c5bdf144b90d2c8412c47ccfc83b36",
            "filter_classes": [0],
            "description": "Ultralytics pretrained YOLOv8n (80 classes, filtered to class 0 person)"
        },
        "fine_tuned": {
            "name": "best.pt",
            "path": "/app/data/models/best.pt",
            "expected_sha256": "41D74CB7E4288A526D9BF4D092343E12FA61ACC7E4D1DAC76C82593C7BD715EF",
            "filter_classes": [0],
            "description": "Sprint 2 Gate 2 fine-tuned YOLOv8n model (single class person)"
        }
    },
    "dataset": {
        "name": "COCO Person-Only Curated Holdout Test Set",
        "images_dir": "/app/data/datasets/coco-person/images/test",
        "labels_dir": "/app/data/datasets/coco-person/labels/test",
        "image_count": 240,
        "label_count": 240,
        "total_ground_truth_boxes": 972,
        "target_class_id": 0,
        "target_class_name": "person"
    },
    "operational_parameters": {
        "conf_threshold": 0.35,
        "nms_iou_threshold": 0.65,
        "gt_matching_iou_threshold": 0.50,
        "input_imgsz": 640
    },
    "map_evaluation_parameters": {
        "conf_threshold_raw": 0.001,
        "nms_iou_threshold": 0.65,
        "iou_range": [0.50, 0.95, 0.05],
        "input_imgsz": 640
    },
    "benchmark_parameters": {
        "warmup_runs": 10,
        "measured_runs": 240,
        "batch_size": 1,
        "device": "cpu"
    },
    "runtime": {
        "environment": "Docker container visionstream-ai:sprint-1",
        "device": "CPU (AMD Ryzen 7 6800U, 16 logical cores, ~7.38 GB RAM available)",
        "cuda_used": False
    }
}

if __name__ == "__main__":
    out_path = Path("/app/evidence/s2.5-model-evaluation/protocol_freeze_config.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(EVAL_CONFIG, f, indent=2)
    print("Evaluation Protocol successfully frozen and saved to:", out_path)
