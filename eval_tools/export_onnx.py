import time
import shutil
from pathlib import Path
import hashlib
from ultralytics import YOLO
import onnx

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def main():
    src_pt = Path("/app/data/models/yolov8n.pt")
    target_onnx = Path("/app/data/models/optimized/onnx/yolov8n.onnx")
    
    print(f"Loading {src_pt}...")
    pt_hash_before = compute_sha256(src_pt)
    print(f"yolov8n.pt SHA256 before export: {pt_hash_before}")
    assert pt_hash_before.lower() == "f59b3d833e2ff32e194b5bb8e08d211dc7c5bdf144b90d2c8412c47ccfc83b36"
    
    start_time = time.time()
    # Ultralytics exports to same directory as model by default: /app/data/models/yolov8n.onnx
    model = YOLO(str(src_pt))
    exported_file = model.export(format="onnx", imgsz=640, dynamic=False, opset=17)
    duration = time.time() - start_time
    print(f"Export completed in {duration:.2f}s. Exported path: {exported_file}")
    
    # Move to target path: data/models/optimized/onnx/yolov8n.onnx
    shutil.move(exported_file, str(target_onnx))
    print(f"Moved to {target_onnx}")
    
    onnx_hash = compute_sha256(target_onnx)
    onnx_size = target_onnx.stat().st_size
    print(f"ONNX Size: {onnx_size} bytes ({onnx_size / 1024 / 1024:.2f} MB)")
    print(f"ONNX SHA256: {onnx_hash}")
    
    # Verify ONNX model structure
    onnx_model = onnx.load(str(target_onnx))
    onnx.checker.check_model(onnx_model)
    print("ONNX checker passed successfully!")
    
    for inp in onnx_model.graph.input:
        shape = [d.dim_value for d in inp.type.tensor_type.shape.dim]
        print(f"Input: {inp.name}, Shape: {shape}")
    for out in onnx_model.graph.output:
        shape = [d.dim_value for d in out.type.tensor_type.shape.dim]
        print(f"Output: {out.name}, Shape: {shape}")
        
    pt_hash_after = compute_sha256(src_pt)
    print(f"yolov8n.pt SHA256 after export: {pt_hash_after}")
    assert pt_hash_after == pt_hash_before, "CRITICAL: yolov8n.pt was altered!"

if __name__ == "__main__":
    main()
