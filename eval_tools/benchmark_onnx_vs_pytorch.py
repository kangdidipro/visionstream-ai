import time
import os
import psutil
import cv2
import numpy as np
import torch
from ultralytics import YOLO
import onnxruntime as ort
import json
from pathlib import Path

def letterbox(im, new_shape=(640, 640), color=(114, 114, 114), auto=True, scaleFill=False, scaleup=True, stride=32):
    # Standard YOLO letterbox resize
    shape = im.shape[:2] # current shape [height, width]
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)

    # Scale ratio (new / old)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    if not scaleup:
        r = min(r, 1.0)

    # Compute padding
    ratio = r, r # width, height ratios
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1] # wh padding
    if auto:
        dw, dh = np.mod(dw, stride), np.mod(dh, stride)
    elif scaleFill:
        dw, dh = 0.0, 0.0
        new_unpad = (new_shape[1], new_shape[0])
        ratio = new_shape[1] / shape[1], new_shape[0] / shape[0]

    dw /= 2 # divide padding into 2 sides
    dh /= 2

    if shape[::-1] != new_unpad: # resize
        im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    im = cv2.copyMakeBorder(im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    return im, ratio, (dw, dh)

def postprocess_onnx(output, orig_shape, input_shape=(640, 640), conf_thresh=0.35, iou_thresh=0.65):
    # output: [1, 84, 8400]
    predictions = np.squeeze(output[0]).T # [8400, 84]
    
    # Filter class 0 (person)
    scores = predictions[:, 4:] # 80 classes
    class_ids = np.argmax(scores, axis=1)
    confidences = np.max(scores, axis=1)
    
    mask = (class_ids == 0) & (confidences >= conf_thresh)
    boxes = predictions[mask, :4]
    confs = confidences[mask]
    
    if len(boxes) == 0:
        return []
        
    # Scale boxes back to original image
    gain = min(input_shape[0] / orig_shape[0], input_shape[1] / orig_shape[1])
    pad_x = (input_shape[1] - orig_shape[1] * gain) / 2
    pad_y = (input_shape[0] - orig_shape[0] * gain) / 2
    
    # xc, yc, w, h -> x1, y1, x2, y2
    x1 = (boxes[:, 0] - boxes[:, 2] / 2 - pad_x) / gain
    y1 = (boxes[:, 1] - boxes[:, 3] / 2 - pad_y) / gain
    x2 = (boxes[:, 0] + boxes[:, 2] / 2 - pad_x) / gain
    y2 = (boxes[:, 1] + boxes[:, 3] / 2 - pad_y) / gain
    
    boxes_xyxy = np.stack([x1, y1, x2, y2], axis=1)
    
    # Apply NMS
    # OpenCV NMSBoxes expects [x, y, w, h]
    boxes_xywh = np.stack([x1, y1, x2 - x1, y2 - y1], axis=1)
    indices = cv2.dnn.NMSBoxes(boxes_xywh.tolist(), confs.tolist(), conf_thresh, iou_thresh)
    
    results = []
    if len(indices) > 0:
        for idx in indices.flatten():
            results.append({
                "class_id": 0,
                "confidence": float(confs[idx]),
                "bbox": [float(c) for c in boxes_xyxy[idx]]
            })
    return results

def compute_iou(box1, box2):
    # box: [x1, y1, x2, y2]
    xA = max(box1[0], box2[0])
    yA = max(box1[1], box2[1])
    xB = min(box1[2], box2[2])
    yB = min(box1[3], box2[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (box1[2] - box1[0]) * (box1[3] - box1[1])
    boxBArea = (box2[2] - box2[0]) * (box2[3] - box2[1])
    iou = interArea / float(boxAArea + boxBArea - interArea + 1e-6)
    return iou

def main():
    img_path = "/app/data/inputs/sample_person.jpg"
    orig_img = cv2.imread(img_path)
    assert orig_img is not None, f"Could not read {img_path}"
    orig_h, orig_w = orig_img.shape[:2]
    print(f"Sample image loaded: {orig_w}x{orig_h}")
    
    # Preprocess for ONNX
    lb_img, ratio, (dw, dh) = letterbox(orig_img, new_shape=(640, 640), auto=False)
    input_tensor = lb_img[:, :, ::-1].transpose(2, 0, 1).astype(np.float32) / 255.0
    input_tensor = np.expand_dims(input_tensor, axis=0) # [1, 3, 640, 640]
    
    # ----------------------------------------------------
    # Benchmark 1: PyTorch CPU (Ultralytics YOLO)
    # ----------------------------------------------------
    print("\n" + "="*50)
    print("Benchmarking PyTorch CPU...")
    print("="*50)
    
    t0 = time.time()
    pt_model = YOLO("/app/data/models/yolov8n.pt")
    pt_init_time = (time.time() - t0) * 1000
    print(f"PyTorch Initialization time: {pt_init_time:.2f} ms")
    
    # First inference (Cold)
    t0 = time.time()
    _ = pt_model.predict(source=orig_img, conf=0.35, iou=0.65, classes=[0], imgsz=640, verbose=False)
    pt_cold_latency = (time.time() - t0) * 1000
    print(f"PyTorch First Inference Latency (Cold): {pt_cold_latency:.2f} ms")
    
    # Warm-up 30 runs
    print("Running 30 warm-up runs for PyTorch...")
    for _ in range(30):
        _ = pt_model.predict(source=orig_img, conf=0.35, iou=0.65, classes=[0], imgsz=640, verbose=False)
        
    # Measured 100 runs
    print("Running 100 measured iterations for PyTorch...")
    pt_latencies = []
    proc = psutil.Process()
    mem_before = proc.memory_info().rss / (1024 * 1024)
    cpu_samples = []
    
    start_total = time.time()
    for _ in range(100):
        t_start = time.time()
        res = pt_model.predict(source=orig_img, conf=0.35, iou=0.65, classes=[0], imgsz=640, verbose=False)
        pt_latencies.append((time.time() - t_start) * 1000)
    total_pt_time = time.time() - start_total
    mem_after = proc.memory_info().rss / (1024 * 1024)
    
    pt_mean = np.mean(pt_latencies)
    pt_median = np.median(pt_latencies)
    pt_p95 = np.percentile(pt_latencies, 95)
    pt_p99 = np.percentile(pt_latencies, 99)
    pt_fps = 100.0 / total_pt_time
    
    # Detections from last run
    pt_detections = []
    for r in res:
        for b in r.boxes:
            pt_detections.append({
                "class_id": int(b.cls.item()),
                "confidence": float(b.conf.item()),
                "bbox": [float(x) for x in b.xyxy[0].tolist()]
            })
    print(f"PyTorch Detections count: {len(pt_detections)}")
    
    # ----------------------------------------------------
    # Benchmark 2: ONNX Runtime CPU
    # ----------------------------------------------------
    print("\n" + "="*50)
    print("Benchmarking ONNX Runtime CPU...")
    print("="*50)
    
    t0 = time.time()
    session_options = ort.SessionOptions()
    session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    session_options.intra_op_num_threads = 4  # Standard multi-thread
    ort_session = ort.InferenceSession(
        "/app/data/models/optimized/onnx/yolov8n.onnx",
        sess_options=session_options,
        providers=["CPUExecutionProvider"]
    )
    ort_init_time = (time.time() - t0) * 1000
    print(f"ONNX Runtime Initialization time: {ort_init_time:.2f} ms")
    
    input_name = ort_session.get_inputs()[0].name
    output_name = ort_session.get_outputs()[0].name
    
    # First inference (Cold)
    t0 = time.time()
    out = ort_session.run([output_name], {input_name: input_tensor})
    _ = postprocess_onnx(out[0], (orig_h, orig_w), conf_thresh=0.35, iou_thresh=0.65)
    ort_cold_latency = (time.time() - t0) * 1000
    print(f"ONNX Runtime First Inference Latency (Cold): {ort_cold_latency:.2f} ms")
    
    # Warm-up 30 runs
    print("Running 30 warm-up runs for ONNX Runtime...")
    for _ in range(30):
        out = ort_session.run([output_name], {input_name: input_tensor})
        _ = postprocess_onnx(out[0], (orig_h, orig_w), conf_thresh=0.35, iou_thresh=0.65)
        
    # Measured 100 runs
    print("Running 100 measured iterations for ONNX Runtime...")
    ort_latencies_inference_only = []
    ort_latencies_end_to_end = []
    
    start_total_ort = time.time()
    for _ in range(100):
        t_start = time.time()
        # End to end includes run + postprocess
        out = ort_session.run([output_name], {input_name: input_tensor})
        t_infer = time.time()
        ort_dets = postprocess_onnx(out[0], (orig_h, orig_w), conf_thresh=0.35, iou_thresh=0.65)
        t_end = time.time()
        
        ort_latencies_inference_only.append((t_infer - t_start) * 1000)
        ort_latencies_end_to_end.append((t_end - t_start) * 1000)
    total_ort_time = time.time() - start_total_ort
    
    ort_mean = np.mean(ort_latencies_end_to_end)
    ort_median = np.median(ort_latencies_end_to_end)
    ort_p95 = np.percentile(ort_latencies_end_to_end, 95)
    ort_p99 = np.percentile(ort_latencies_end_to_end, 99)
    ort_fps = 100.0 / total_ort_time
    
    ort_raw_mean = np.mean(ort_latencies_inference_only)
    ort_raw_p95 = np.percentile(ort_latencies_inference_only, 95)
    
    print(f"ONNX Runtime Detections count: {len(ort_dets)}")
    
    # ----------------------------------------------------
    # Benchmark 3: Ultralytics ONNX Engine (Ultralytics wrapper over ORT)
    # ----------------------------------------------------
    print("\n" + "="*50)
    print("Benchmarking Ultralytics YOLO ONNX Engine wrapper...")
    print("="*50)
    t0 = time.time()
    yolo_onnx = YOLO("/app/data/models/optimized/onnx/yolov8n.onnx", task="detect")
    yolo_onnx_init = (time.time() - t0) * 1000
    
    # Warmup
    for _ in range(30):
        _ = yolo_onnx.predict(source=orig_img, conf=0.35, iou=0.65, classes=[0], imgsz=640, verbose=False)
        
    yolo_onnx_latencies = []
    start_yolo_onnx = time.time()
    for _ in range(100):
        t_start = time.time()
        res_yo = yolo_onnx.predict(source=orig_img, conf=0.35, iou=0.65, classes=[0], imgsz=640, verbose=False)
        yolo_onnx_latencies.append((time.time() - t_start) * 1000)
    total_yolo_onnx_time = time.time() - start_yolo_onnx
    
    yo_mean = np.mean(yolo_onnx_latencies)
    yo_median = np.median(yolo_onnx_latencies)
    yo_p95 = np.percentile(yolo_onnx_latencies, 95)
    yo_fps = 100.0 / total_yolo_onnx_time
    
    # ----------------------------------------------------
    # Compare Output Consistency
    # ----------------------------------------------------
    print("\n" + "="*50)
    print("Output Consistency Analysis...")
    print("="*50)
    
    print(f"PyTorch detections found: {len(pt_detections)}")
    for i, d in enumerate(pt_detections):
        print(f"  PT #{i+1}: conf={d['confidence']:.4f}, box={[round(x, 1) for x in d['bbox']]}")
        
    print(f"ORT Direct detections found: {len(ort_dets)}")
    for i, d in enumerate(ort_dets):
        print(f"  ORT #{i+1}: conf={d['confidence']:.4f}, box={[round(x, 1) for x in d['bbox']]}")
        
    # Match detections
    matched = 0
    iou_scores = []
    conf_diffs = []
    for pd in pt_detections:
        best_iou = 0.0
        best_od = None
        for od in ort_dets:
            iou = compute_iou(pd["bbox"], od["bbox"])
            if iou > best_iou:
                best_iou = iou
                best_od = od
        if best_iou >= 0.50:
            matched += 1
            iou_scores.append(best_iou)
            conf_diffs.append(abs(pd["confidence"] - best_od["confidence"]))
            
    print(f"Matched detections (IoU >= 0.50): {matched}/{len(pt_detections)}")
    mean_iou = np.mean(iou_scores) if iou_scores else 0.0
    mean_conf_diff = np.mean(conf_diffs) if conf_diffs else 0.0
    print(f"Mean IoU: {mean_iou:.4f}, Mean Conf Diff: {mean_conf_diff:.4f}")
    
    # Summary results dict
    benchmark_results = {
        "pytorch_cpu": {
            "init_time_ms": pt_init_time,
            "cold_latency_ms": pt_cold_latency,
            "mean_latency_ms": pt_mean,
            "median_latency_ms": pt_median,
            "p95_latency_ms": pt_p95,
            "p99_latency_ms": pt_p99,
            "throughput_fps": pt_fps,
            "detections_count": len(pt_detections)
        },
        "onnxruntime_cpu_direct": {
            "init_time_ms": ort_init_time,
            "cold_latency_ms": ort_cold_latency,
            "raw_inference_mean_ms": ort_raw_mean,
            "raw_inference_p95_ms": ort_raw_p95,
            "mean_latency_ms": ort_mean,
            "median_latency_ms": ort_median,
            "p95_latency_ms": ort_p95,
            "p99_latency_ms": ort_p99,
            "throughput_fps": ort_fps,
            "detections_count": len(ort_dets)
        },
        "ultralytics_onnx_wrapper": {
            "init_time_ms": yolo_onnx_init,
            "mean_latency_ms": yo_mean,
            "median_latency_ms": yo_median,
            "p95_latency_ms": yo_p95,
            "throughput_fps": yo_fps
        },
        "consistency": {
            "pt_count": len(pt_detections),
            "ort_count": len(ort_dets),
            "matched_count": matched,
            "mean_iou": float(mean_iou),
            "mean_conf_diff": float(mean_conf_diff)
        }
    }
    
    with open("/app/reports/gate8_benchmark_data.json", "w") as f:
        json.dump(benchmark_results, f, indent=2)
    print("\nBenchmark raw results written to /app/reports/gate8_benchmark_data.json")

if __name__ == "__main__":
    main()
