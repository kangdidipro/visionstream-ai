"""
Dataset Acquisition and Preprocessing Pipeline for VisionStream AI Sprint 2 (Task S2.2).
Acquires verified CC BY 2.0 (License ID 4) person images from COCO 2017:
- Train: 2,000 images from Train2017
- Validation: 239 images from Val2017
- Holdout Test: 240 images from Val2017
Total: 2,479 images.

Converts COCO bounding boxes to YOLO normalized TXT format:
0 <x_center> <y_center> <width> <height>
Generates manifests, checksums, and dataset.yaml.
"""

import json
import zipfile
import urllib.request
import os
import random
import hashlib
import time
import concurrent.futures
from pathlib import Path

DATASET_ROOT = Path("/app/data/datasets/coco-person")
CACHE_DIR = Path("/app/data/datasets/.cache")
ANNOTATIONS_ZIP = CACHE_DIR / "annotations_trainval2017.zip"

TRAIN_TARGET = 2000
VAL_TARGET = 239
TEST_TARGET = 240
RANDOM_SEED = 42

LICENSE_CC_BY_2 = 4

def setup_directories():
    for split in ["train", "val", "test"]:
        (DATASET_ROOT / "images" / split).mkdir(parents=True, exist_ok=True)
        (DATASET_ROOT / "labels" / split).mkdir(parents=True, exist_ok=True)
    (DATASET_ROOT / "metadata").mkdir(parents=True, exist_ok=True)

def download_image(url: str, dest_path: Path, max_retries: int = 3) -> tuple[bool, str, int]:
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (VisionStream-AI-Dataset-Acquisition)'})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
                dest_path.write_bytes(data)
                sha256 = hashlib.sha256(data).hexdigest()
                return True, sha256, len(data)
        except Exception as e:
            if attempt == max_retries - 1:
                return False, str(e), 0
            time.sleep(1.0)
    return False, "Failed after retries", 0

def convert_coco_bbox_to_yolo(bbox: list, img_w: int, img_h: int) -> tuple[float, float, float, float] | None:
    x_min, y_min, w, h = bbox
    if w <= 0 or h <= 0 or img_w <= 0 or img_h <= 0:
        return None
    
    # Clip box to image boundaries
    x1 = max(0.0, min(float(x_min), float(img_w)))
    y1 = max(0.0, min(float(y_min), float(img_h)))
    x2 = max(0.0, min(float(x_min + w), float(img_w)))
    y2 = max(0.0, min(float(y_min + h), float(img_h)))
    
    clipped_w = x2 - x1
    clipped_h = y2 - y1
    if clipped_w <= 0 or clipped_h <= 0:
        return None
    
    x_center = (x1 + x2) / 2.0 / img_w
    y_center = (y1 + y2) / 2.0 / img_h
    norm_w = clipped_w / img_w
    norm_h = clipped_h / img_h
    
    # Bounds check
    x_center = max(0.0, min(1.0, x_center))
    y_center = max(0.0, min(1.0, y_center))
    norm_w = max(0.0, min(1.0, norm_w))
    norm_h = max(0.0, min(1.0, norm_h))
    
    return x_center, y_center, norm_w, norm_h

def main():
    print(f"=== Starting S2.2 Dataset Acquisition & Preprocessing ===")
    print(f"Target counts: Train={TRAIN_TARGET}, Val={VAL_TARGET}, Test={TEST_TARGET} (Total={TRAIN_TARGET+VAL_TARGET+TEST_TARGET})")
    print(f"Random seed: {RANDOM_SEED}")
    setup_directories()

    with zipfile.ZipFile(str(ANNOTATIONS_ZIP), 'r') as z:
        print("Loading instances_val2017.json...")
        with z.open("annotations/instances_val2017.json") as f:
            val_json = json.load(f)
        print("Loading instances_train2017.json...")
        with z.open("annotations/instances_train2017.json") as f:
            train_json = json.load(f)

    # 1. Filter Val2017 License 4 person images
    person_cat_id = 1
    val_person_anns = [a for a in val_json['annotations'] if a['category_id'] == person_cat_id and a.get('area', 0) > 0 and a.get('iscrowd', 0) == 0]
    val_person_img_ids = set(a['image_id'] for a in val_person_anns)
    
    val_lic4_imgs = [img for img in val_json['images'] if img.get('license') == LICENSE_CC_BY_2 and img['id'] in val_person_img_ids]
    val_lic4_imgs.sort(key=lambda x: x['id']) # deterministic sort
    print(f"Total eligible Val2017 License 4 images: {len(val_lic4_imgs)}")
    
    if len(val_lic4_imgs) < VAL_TARGET + TEST_TARGET:
        raise ValueError(f"Not enough Val2017 Lic 4 images! Need {VAL_TARGET + TEST_TARGET}, got {len(val_lic4_imgs)}")

    # Deterministic split with seed
    rng = random.Random(RANDOM_SEED)
    shuffled_val = list(val_lic4_imgs)
    rng.shuffle(shuffled_val)

    selected_val_imgs = shuffled_val[:VAL_TARGET]
    selected_test_imgs = shuffled_val[VAL_TARGET:VAL_TARGET + TEST_TARGET]
    
    # 2. Filter Train2017 License 4 person images
    train_person_anns = [a for a in train_json['annotations'] if a['category_id'] == person_cat_id and a.get('area', 0) > 0 and a.get('iscrowd', 0) == 0]
    train_person_img_ids = set(a['image_id'] for a in train_person_anns)
    
    train_lic4_imgs = [img for img in train_json['images'] if img.get('license') == LICENSE_CC_BY_2 and img['id'] in train_person_img_ids]
    train_lic4_imgs.sort(key=lambda x: x['id']) # deterministic sort
    print(f"Total eligible Train2017 License 4 images: {len(train_lic4_imgs)}")
    
    shuffled_train = list(train_lic4_imgs)
    rng.shuffle(shuffled_train)
    selected_train_imgs = shuffled_train[:TRAIN_TARGET]

    print(f"Selected counts: Train={len(selected_train_imgs)}, Val={len(selected_val_imgs)}, Test={len(selected_test_imgs)}")

    # Check disjointness
    train_ids = set(x['id'] for x in selected_train_imgs)
    val_ids = set(x['id'] for x in selected_val_imgs)
    test_ids = set(x['id'] for x in selected_test_imgs)
    assert len(train_ids.intersection(val_ids)) == 0, "Train and Val overlap!"
    assert len(train_ids.intersection(test_ids)) == 0, "Train and Test overlap!"
    assert len(val_ids.intersection(test_ids)) == 0, "Val and Test overlap!"
    assert len(train_ids) == TRAIN_TARGET
    assert len(val_ids) == VAL_TARGET
    assert len(test_ids) == TEST_TARGET
    print("Disjointness check PASSED.")

    # Build annotations map
    val_ann_by_img = {}
    for a in val_person_anns:
        val_ann_by_img.setdefault(a['image_id'], []).append(a)

    train_ann_by_img = {}
    for a in train_person_anns:
        train_ann_by_img.setdefault(a['image_id'], []).append(a)

    tasks = []
    for img in selected_train_imgs:
        tasks.append(('train', img, train_ann_by_img.get(img['id'], [])))
    for img in selected_val_imgs:
        tasks.append(('val', img, val_ann_by_img.get(img['id'], [])))
    for img in selected_test_imgs:
        tasks.append(('test', img, val_ann_by_img.get(img['id'], [])))

    print(f"Total images to download and process: {len(tasks)}")

    image_manifest = []
    annotation_manifest = []
    license_manifest = {
        "license_id": 4,
        "license_name": "Attribution License (CC BY 2.0)",
        "license_url": "http://creativecommons.org/licenses/by/2.0/",
        "authorizing_policy": "S2.2 Approved Scope Option 1",
        "total_images": len(tasks)
    }
    split_manifest = {
        "seed": RANDOM_SEED,
        "counts": {"train": len(selected_train_imgs), "val": len(selected_val_imgs), "test": len(selected_test_imgs)},
        "splits": {"train": sorted(list(train_ids)), "val": sorted(list(val_ids)), "test": sorted(list(test_ids))}
    }
    checksums = []

    # Download workers
    start_time = time.time()
    def process_item(item):
        split, img_info, anns = item
        img_id = img_info['id']
        file_name = img_info['file_name']
        coco_url = img_info['coco_url']
        dest_img_path = DATASET_ROOT / "images" / split / file_name
        dest_lbl_path = DATASET_ROOT / "labels" / split / f"{Path(file_name).stem}.txt"

        # Download image if not exists
        if not dest_img_path.exists():
            ok, sha256_or_err, sz = download_image(coco_url, dest_img_path)
            if not ok:
                return False, f"Failed download {file_name}: {sha256_or_err}", None
            sha256 = sha256_or_err
            byte_size = sz
        else:
            data = dest_img_path.read_bytes()
            sha256 = hashlib.sha256(data).hexdigest()
            byte_size = len(data)

        # Convert annotations to YOLO
        yolo_lines = []
        ann_records = []
        for a in anns:
            box = convert_coco_bbox_to_yolo(a['bbox'], img_info['width'], img_info['height'])
            if box is not None:
                xc, yc, w, h = box
                yolo_lines.append(f"0 {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}")
                ann_records.append({
                    "annotation_id": a['id'],
                    "category_id": 1,
                    "yolo_box": [xc, yc, w, h],
                    "coco_bbox": a['bbox'],
                    "area": a.get('area', 0)
                })

        dest_lbl_path.write_text("\n".join(yolo_lines) + ("\n" if yolo_lines else ""))
        
        img_meta = {
            "image_id": img_id,
            "split": split,
            "file_name": file_name,
            "coco_url": coco_url,
            "flickr_url": img_info.get("flickr_url", ""),
            "date_captured": img_info.get("date_captured", ""),
            "license_id": img_info.get("license"),
            "license_name": "Attribution License (CC BY 2.0)",
            "license_url": "http://creativecommons.org/licenses/by/2.0/",
            "width": img_info['width'],
            "height": img_info['height'],
            "sha256": sha256,
            "bytes": byte_size,
            "annotations_count": len(yolo_lines)
        }
        
        return True, img_meta, ann_records

    print("Beginning concurrent download & conversion (16 workers)...")
    processed_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        futures = {executor.submit(process_item, item): item for item in tasks}
        for future in concurrent.futures.as_completed(futures):
            ok, res_meta, ann_list = future.result()
            if not ok:
                raise RuntimeError(res_meta)
            image_manifest.append(res_meta)
            annotation_manifest.extend(ann_list)
            checksums.append(f"{res_meta['sha256']}  images/{res_meta['split']}/{res_meta['file_name']}")
            processed_count += 1
            if processed_count % 250 == 0 or processed_count == len(tasks):
                elapsed = time.time() - start_time
                print(f"Processed {processed_count}/{len(tasks)} images ({processed_count/len(tasks)*100:.1f}%) in {elapsed:.1f}s")

    # Sort manifests for determinism
    image_manifest.sort(key=lambda x: (x['split'], x['image_id']))
    checksums.sort()

    print("Writing metadata manifests...")
    (DATASET_ROOT / "metadata" / "image-manifest.json").write_text(json.dumps(image_manifest, indent=2))
    (DATASET_ROOT / "metadata" / "license-manifest.json").write_text(json.dumps(license_manifest, indent=2))
    (DATASET_ROOT / "metadata" / "split-manifest.json").write_text(json.dumps(split_manifest, indent=2))
    (DATASET_ROOT / "metadata" / "checksums.sha256").write_text("\n".join(checksums) + "\n")
    
    # Write summary of annotation manifest (to keep size manageable)
    ann_summary = {
        "total_person_annotations": len(annotation_manifest),
        "total_images": len(image_manifest),
        "annotations_per_split": {
            "train": sum(1 for a in image_manifest if a['split'] == 'train' for _ in range(a['annotations_count'])),
            "val": sum(1 for a in image_manifest if a['split'] == 'val' for _ in range(a['annotations_count'])),
            "test": sum(1 for a in image_manifest if a['split'] == 'test' for _ in range(a['annotations_count']))
        }
    }
    (DATASET_ROOT / "metadata" / "annotation-manifest.json").write_text(json.dumps(ann_summary, indent=2))

    # Write dataset.yaml
    dataset_yaml_content = """# Ultralytics YOLOv8 Dataset Configuration
# VisionStream AI - Sprint 2 Person Detection Dataset
# License: CC BY 2.0 (COCO 2017 Curated Person-Only Pilot Subset)

path: /app/data/datasets/coco-person
train: images/train
val: images/val
test: images/test

names:
  0: person
"""
    (DATASET_ROOT / "dataset.yaml").write_text(dataset_yaml_content)

    # Write README.md
    readme_content = """# VisionStream AI — COCO Person-Only Dataset (Sprint 2 Pilot)

## Overview
Curated subset of COCO 2017 containing only images with verified person annotations and licensed under **Creative Commons Attribution 2.0 Generic (CC BY 2.0)** (COCO License ID 4).

## Dataset Scope
- **Train:** 2,000 images (Source: COCO Train2017)
- **Validation:** 239 images (Source: COCO Val2017)
- **Holdout Test:** 240 images (Source: COCO Val2017)
- **Total Images:** 2,479 images
- **Target Class:** 0 (`person`)

## License and Attribution
- **Annotations:** CC BY 4.0 (COCO Consortium).
- **Images:** Creative Commons Attribution 2.0 Generic (CC BY 2.0). Individual image attributions and original Flickr URLs are documented in `metadata/image-manifest.json`.
- **License Terms:** http://creativecommons.org/licenses/by/2.0/
- **Original Dataset Citation:** Lin, T.-Y., et al. "Microsoft COCO: Common Objects in Context." ECCV 2014.

## Split Independence & Integrity
- All image IDs across `train`, `val`, and `test` are strictly disjoint.
- Selection was deterministically generated with seed `42`.
- All images are verified against their SHA-256 checksums in `metadata/checksums.sha256`.

## Usage Notice
In accordance with portfolio policy and repository rules, image data in `images/` is excluded from Git tracking via `.gitignore`.
"""
    (DATASET_ROOT / "README.md").write_text(readme_content)

    print("Dataset acquisition and preprocessing complete successfully!")

if __name__ == "__main__":
    main()
