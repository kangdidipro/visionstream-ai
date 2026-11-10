"""
Pydantic schemas for VisionStream AI inference service.
"""
from typing import List
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class Detection(BaseModel):
    class_id: int = Field(default=0, description="Target class ID (0 = person)")
    class_name: str = Field(default="person", description="Target class name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    bbox: BoundingBox


class Metrics(BaseModel):
    preprocess_ms: float = Field(..., ge=0.0, description="Preprocessing latency in milliseconds")
    inference_ms: float = Field(..., ge=0.0, description="Inference latency in milliseconds")
    postprocess_ms: float = Field(..., ge=0.0, description="Postprocessing latency in milliseconds")
    total_ms: float = Field(..., ge=0.0, description="Total end-to-end latency in milliseconds")


class InferenceResponse(BaseModel):
    model_name: str = "yolov8n"
    model_version: str = "1"
    image_width: int
    image_height: int
    detections: List[Detection]
    metrics: Metrics


class ModelMetadataResponse(BaseModel):
    name: str
    versions: List[str]
    platform: str
    inputs: List[dict]
    outputs: List[dict]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_name: str
    device: str
