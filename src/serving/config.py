"""
Serving configuration for VisionStream AI inference service.
"""
from pathlib import Path
from pydantic import BaseModel, Field


class ServingConfig(BaseModel):
    model_name: str = "yolov8n"
    model_version: str = "1"
    model_path: str = "/app/data/models/yolov8n.pt"
    expected_sha256: str = "f59b3d833e2ff32e194b5bb8e08d211dc7c5bdf144b90d2c8412c47ccfc83b36"
    default_conf: float = 0.35
    default_iou: float = 0.65
    target_class_id: int = 0
    target_class_name: str = "person"
    device: str = "cpu"
    max_image_size_bytes: int = 15 * 1024 * 1024  # 15 MB limit
    allowed_content_types: list[str] = Field(
        default_factory=lambda: [
            "image/jpeg",
            "image/png",
            "image/webp",
            "image/bmp",
        ]
    )


settings = ServingConfig()
