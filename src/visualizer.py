"""
Visualization utilities for annotating detections and tracking IDs on frames.
"""
from typing import List, Dict, Any
import cv2
import numpy as np


# High-contrast color palette for persistent track IDs
COLOR_PALETTE = [
    (0, 255, 0),     # Bright Green
    (255, 128, 0),   # Orange / Sky Blue
    (0, 165, 255),   # Bright Orange
    (255, 0, 255),   # Magenta
    (0, 255, 255),   # Yellow
    (255, 0, 0),     # Blue
    (147, 20, 255),  # Deep Pink
    (0, 215, 255),   # Gold
    (128, 255, 0),   # Lime
    (255, 191, 0)    # Deep Sky
]


def get_color_for_id(track_id: int):
    if track_id < 0:
        return (180, 180, 180)  # Gray for unassigned
    return COLOR_PALETTE[track_id % len(COLOR_PALETTE)]


def annotate_frame(
    frame: np.ndarray,
    tracks: List[Dict[str, Any]],
    frame_number: int,
    fps: float,
    active_count: int
) -> np.ndarray:
    annotated = frame.copy()
    h, w = annotated.shape[:2]

    # Draw detections and tracking labels
    for track in tracks:
        bbox = track["bbox"]
        track_id = track["track_id"]
        conf = track["confidence"]

        x1, y1, x2, y2 = [int(v) for v in bbox]
        color = get_color_for_id(track_id)

        # Draw bounding box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

        # Label text
        if track_id >= 0:
            label = f"ID:{track_id} ({conf:.2f})"
        else:
            label = f"Person ({conf:.2f})"

        # Label background
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1
        (txt_w, txt_h), baseline = cv2.getTextSize(label, font, font_scale, thickness)

        label_y1 = max(0, y1 - txt_h - 6)
        label_y2 = y1
        label_x2 = min(w, x1 + txt_w + 6)

        cv2.rectangle(annotated, (x1, label_y1), (label_x2, label_y2), color, -1)
        cv2.putText(
            annotated,
            label,
            (x1 + 3, label_y2 - 3),
            font,
            font_scale,
            (255, 255, 255) if color != (0, 255, 255) else (0, 0, 0),
            thickness,
            cv2.LINE_AA
        )

    # Draw OSD (On-Screen Display) header
    header_text = f"Frame: {frame_number} | Tracking Active: {active_count} | Processing FPS: {fps:.1f}"
    cv2.rectangle(annotated, (10, 10), (w - 10, 42), (20, 20, 20), -1)
    cv2.putText(
        annotated,
        header_text,
        (20, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 255, 200),
        1,
        cv2.LINE_AA
    )

    return annotated
