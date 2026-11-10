import time
import os
import psutil
import cv2
import numpy as np
import onnxruntime as ort
import json
from eval_tools.benchmark_onnx_vs_pytorch import letterbox, postprocess_onnx

def benchmark_threads():
    img_path = "/app/data/inputs/sample_person.jpg"
    orig_img = cv2.imread(img_path)
    orig_h, orig_w = orig_img.shape[:2]
    lb_img, ratio, (dw, dh) = letterbox(orig_img, new_shape=(640, 640), auto=False)
    input_tensor = lb_img[:, :, ::-1].transpose(2, 0, 1).astype(np.float32) / 255.0
    input_tensor = np.expand_dims(input_tensor, axis=0)
    
    thread_counts = [1, 2, 4, 8]
    thread_results = {}
    
    for threads in thread_counts:
        session_options = ort.SessionOptions()
        session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        session_options.intra_op_num_threads = threads
        session_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        
        session = ort.InferenceSession(
            "/app/data/models/optimized/onnx/yolov8n.onnx",
            sess_options=session_options,
            providers=["CPUExecutionProvider"]
        )
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name
        
        # Warmup
        for _ in range(15):
            _ = session.run([output_name], {input_name: input_tensor})
            
        latencies = []
        for _ in range(50):
            t0 = time.time()
            _ = session.run([output_name], {input_name: input_tensor})
            latencies.append((time.time() - t0) * 1000)
            
        thread_results[f"threads_{threads}"] = {
            "mean_ms": np.mean(latencies),
            "median_ms": np.median(latencies),
            "p95_ms": np.percentile(latencies, 95),
            "fps": 1000.0 / np.mean(latencies)
        }
        print(f"Threads={threads}: Mean={np.mean(latencies):.2f} ms, P95={np.percentile(latencies, 95):.2f} ms, FPS={1000.0/np.mean(latencies):.2f}")
        
    with open("/app/reports/gate8_thread_bench.json", "w") as f:
        json.dump(thread_results, f, indent=2)

if __name__ == "__main__":
    benchmark_threads()
