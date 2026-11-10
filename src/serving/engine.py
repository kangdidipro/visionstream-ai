"""
Modular inference engine abstraction for VisionStream AI.
Supports single-image CPU inference without stateful tracking.
Designed for thread safety and future ONNX/Triton client extensibility.
"""
import hashlib
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from ultralytics import YOLO

from src.serving.config import ServingConfig, settings
from src.serving.schemas import BoundingBox, Detection, InferenceResponse, Metrics


class BaseInferenceEngine(ABC):
    @abstractmethod
    def load_model(self) -> None:
        """Load and warm up model."""
        pass

    @abstractmethod
    def infer(
        self,
        image_bytes: bytes,
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
    ) -> InferenceResponse:
        """Execute inference on input image bytes."""
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """Check if engine is ready to accept requests."""
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Return model metadata."""
        pass


class YOLOv8InferenceEngine(BaseInferenceEngine):
    def __init__(self, config: Optional[ServingConfig] = None):
        self.config = config or settings
        self.model: Optional[YOLO] = None
        self._lock = threading.Lock()
        self._is_ready: bool = False

    def verify_integrity(self) -> Tuple[bool, str]:
        """Verify model file integrity via SHA256 checksum."""
        model_p = Path(self.config.model_path)
        if not model_p.exists():
            return False, f"Model file not found at: {self.config.model_path}"

        sha256_hash = hashlib.sha256()
        with open(model_p, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        actual_hash = sha256_hash.hexdigest().lower()

        if actual_hash != self.config.expected_sha256.lower():
            return (
                False,
                f"Model hash mismatch! Expected {self.config.expected_sha256}, got {actual_hash}",
            )
        return True, actual_hash

    def load_model(self) -> None:
        """Verify model SHA256, load model onto CPU once, and perform warmup."""
        with self._lock:
            valid, msg = self.verify_integrity()
            if not valid:
                raise RuntimeError(f"Integrity check failed: {msg}")

            # Instantiate model on CPU
            self.model = YOLO(self.config.model_path)

            # Warmup inference with dummy frame (640x640x3 blank)
            dummy = np.zeros((640, 640, 3), dtype=np.uint8)
            _ = self.model.predict(
                source=dummy,
                device=self.config.device,
                classes=[self.config.target_class_id],
                verbose=False,
            )
            self._is_ready = True

    def is_ready(self) -> bool:
        return self._is_ready and self.model is not None

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.config.model_name,
            "versions": [self.config.model_version],
            "platform": "ultralytics_pytorch_cpu",
            "inputs": [
                {
                    "name": "image",
                    "datatype": "BYTES",
                    "shape": [-1, -1, 3],
                    "content_types": self.config.allowed_content_types,
                }
            ],
            "outputs": [
                {
                    "name": "detections",
                    "datatype": "JSON",
                    "shape": [-1, 6],
                    "target_class": {
                        "id": self.config.target_class_id,
                        "name": self.config.target_class_name,
                    },
                }
            ],
        }

    def infer(
        self,
        image_bytes: bytes,
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
    ) -> InferenceResponse:
        """
        Execute single-image stateless person detection.
        Thread-safe: protected by threading.Lock() to prevent corrupting internal state.
        """
        if not self.is_ready():
            raise RuntimeError("Model is not initialized or ready.")

        start_total = time.perf_counter()

        # 1. Preprocess: decode bytes into OpenCV BGR numpy array
        start_pre = time.perf_counter()
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Failed to decode image. Invalid or corrupted image format.")

        img_h, img_w = img.shape[:2]
        end_pre = time.perf_counter()
        preprocess_ms = (end_pre - start_pre) * 1000.0

        conf = conf_threshold if conf_threshold is not None else self.config.default_conf
        iou = iou_threshold if iou_threshold is not None else self.config.default_iou

        # 2. Inference: Run prediction with thread safety
        with self._lock:
            start_infer = time.perf_counter()
            results = self.model.predict(
                source=img,
                conf=conf,
                iou=iou,
                classes=[self.config.target_class_id],
                device=self.config.device,
                verbose=False,
            )
            end_infer = time.perf_counter()

        inference_ms = (end_infer - start_infer) * 1000.0

        # 3. Postprocess: extract and format detections strictly for person class (class_id=0)
        start_post = time.perf_counter()
        detections: List[Detection] = []
        if len(results) > 0 and results[0].boxes is not None:
            res = results[0]
            boxes = res.boxes.xyxy.cpu().numpy()
            confidences = res.boxes.conf.cpu().numpy()
            class_ids = res.boxes.cls.cpu().numpy().astype(int)

            for bbox, score, cls_id in zip(boxes, confidences, class_ids):
                if int(cls_id) == self.config.target_class_id:
                    detections.append(
                        Detection(
                            class_id=int(cls_id),
                            class_name=self.config.target_class_name,
                            confidence=round(float(score), 4),
                            bbox=BoundingBox(
                                x1=round(float(bbox[0]), 2),
                                y1=round(float(bbox[1]), 2),
                                x2=round(float(bbox[2]), 2),
                                y2=round(float(bbox[3]), 2),
                            ),
                        )
                    )

        end_post = time.perf_counter()
        postprocess_ms = (end_post - start_post) * 1000.0

        end_total = time.perf_counter()
        total_ms = (end_total - start_total) * 1000.0

        return InferenceResponse(
            model_name=self.config.model_name,
            model_version=self.config.model_version,
            image_width=img_w,
            image_height=img_h,
            detections=detections,
            metrics=Metrics(
                preprocess_ms=round(preprocess_ms, 2),
                inference_ms=round(inference_ms, 2),
                postprocess_ms=round(postprocess_ms, 2),
                total_ms=round(total_ms, 2),
            ),
        )
