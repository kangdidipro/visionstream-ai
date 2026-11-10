"""
Sprint 2 Dataset Inspector Script
Inspects COCO 2017 annotation licenses and screens for eligible person images.
"""
import json
import zipfile
import urllib.request
import os
import hashlib
from pathlib import Path

ANNOTATIONS_URL = "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
DOWNLOAD_DIR = Path("/app/data/datasets/.cache")
ZIP_PATH = DOWNLOAD_DIR / "annotations_trainval2017.zip"

def download_file(url: str, dest_path: Path):
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists():
        print(f"File already exists: {dest_path} ({dest_path.stat().st_size} bytes)")
        return
    print(f"Downloading {url} to {dest_path}...")
    def report_hook(block_num, block_size, total_size):
        if block_num % 1000 == 0:
            downloaded = block_num * block_size
            pct = downloaded / total_size * 100 if total_size > 0 else 0
            print(f"Downloaded {downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB ({pct:.1f}%)")
    urllib.request.urlretrieve(url, str(dest_path), reporthook=report_hook)
    print(f"Download complete: {dest_path} ({dest_path.stat().st_size} bytes)")

def inspect_licenses():
    download_file(ANNOTATIONS_URL, ZIP_PATH)
    
    with zipfile.ZipFile(str(ZIP_PATH), 'r') as z:
        print("Zip contents:", z.namelist())
        
        # Read val2017 annotations
        print("\nLoading instances_val2017.json...")
        with z.open("annotations/instances_val2017.json") as f:
            val_data = json.load(f)
            
        print("Val2017 Licenses:")
        for lic in val_data.get("licenses", []):
            print(f"  ID {lic['id']}: name='{lic['name']}', url='{lic['url']}'")
            
        # Find person category ID
        categories = {cat['id']: cat['name'] for cat in val_data.get('categories', [])}
        person_cat_ids = [cid for cid, name in categories.items() if name == 'person']
        print(f"Person category IDs: {person_cat_ids}")
        person_cat_id = person_cat_ids[0]
        
        # Check images with person annotations in val2017
        person_img_ids_val = set(
            ann['image_id'] for ann in val_data.get('annotations', [])
            if ann['category_id'] == person_cat_id
        )
        print(f"Val2017 total images: {len(val_data['images'])}")
        print(f"Val2017 images with person: {len(person_img_ids_val)}")
        
        # Count per license for person images in val2017
        license_counts_val = {}
        for img in val_data['images']:
            if img['id'] in person_img_ids_val:
                lid = img.get('license')
                license_counts_val[lid] = license_counts_val.get(lid, 0) + 1
        print("Val2017 person images by license ID:")
        for lid, count in sorted(license_counts_val.items()):
            lic_info = next((l for l in val_data['licenses'] if l['id'] == lid), {'name': 'Unknown'})
            print(f"  License {lid} ({lic_info['name']}): {count} images")

        # Now inspect train2017
        print("\nLoading instances_train2017.json...")
        with z.open("annotations/instances_train2017.json") as f:
            train_data = json.load(f)
            
        person_img_ids_train = set(
            ann['image_id'] for ann in train_data.get('annotations', [])
            if ann['category_id'] == person_cat_id
        )
        print(f"Train2017 total images: {len(train_data['images'])}")
        print(f"Train2017 images with person: {len(person_img_ids_train)}")
        
        license_counts_train = {}
        for img in train_data['images']:
            if img['id'] in person_img_ids_train:
                lid = img.get('license')
                license_counts_train[lid] = license_counts_train.get(lid, 0) + 1
        print("Train2017 person images by license ID:")
        for lid, count in sorted(license_counts_train.items()):
            lic_info = next((l for l in train_data['licenses'] if l['id'] == lid), {'name': 'Unknown'})
            print(f"  License {lid} ({lic_info['name']}): {count} images")

if __name__ == "__main__":
    inspect_licenses()
