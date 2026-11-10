"""
Person detector and tracker wrapper using Ultralytics YOLO and ByteTrack.
"""
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
from ultralytics import YOLO


class PersonTracker:
    def __init__(
        self,
        model_path: str = "/app/data/models/yolov8n.pt",
        conf_threshold: float = 0.35,
        iou_threshold: float = 0.5,
        tracker_type: str = "bytetrack.yaml",
        target_class_id: int = 0
    ):
        """
        Initialize YOLO person detector and ByteTrack.
        COCO class 0 is person.
        """
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.tracker_type = tracker_type
        self.target_class_id = target_class_id

        # Load YOLO model
        self.model = YOLO(self.model_path)

    def process_frame(self, frame: np.ndarray, persist: bool = True) -> Tuple[List[Dict[str, Any]], float]:
        """
        Run person detection and ByteTrack tracking on a single frame.
        
        Returns:
            tracks: List of dicts with keys:
                - track_id: int
                - bbox: [x1, y1, x2, y2]
                - confidence: float
                - class_id: int
            inference_ms: inference time in milliseconds
        """
        # Run tracking using Ultralytics track interface
        # persist=True maintains tracker state across consecutive frames
        results = self.model.track(
            source=frame,
            persist=persist,
            tracker=self.tracker_type,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            classes=[self.target_class_id],
            verbose=False
        )

        res = results[0]
        inference_ms = float(res.speed.get("inference", 0.0))

        tracks = []
        if res.boxes is not None and len(res.boxes) > 0:
            boxes = res.boxes.xyxy.cpu().numpy()
            confidences = res.boxes.conf.cpu().numpy()
            class_ids = res.boxes.cls.cpu().numpy().astype(int)
            track_ids = res.boxes.id.cpu().numpy().astype(int) if res.boxes.id is not None else [None] * len(boxes)

            for bbox, conf, cls_id, trk_id in zip(boxes, confidences, class_ids, track_ids):
                # Ensure only target class is included
                if cls_id == self.target_class_id:
                    tracks.append({
                        "track_id": int(trk_id) if trk_id is not None else -1,
                        "bbox": [float(b) for b in bbox],
                        "confidence": float(conf),
                        "class_id": int(cls_id)
                    })

        return tracks, inference_ms
