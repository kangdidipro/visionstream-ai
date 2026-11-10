"""
Integration and functional tests for VisionStream AI FastAPI Serving service.
Tests all Gate 2 requirements inside Docker environment.
"""
import hashlib
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from src.serving.api import app, engine
from src.serving.config import settings


@pytest.fixture(scope="module")
def client():
    # TestClient as context manager triggers app lifespan startup and shutdown
    with TestClient(app) as test_client:
        yield test_client


def test_1_container_startup_and_model_loading(client):
    """Verify that model is loaded and ready at startup (via lifespan)."""
    assert engine.is_ready() is True
    assert engine.model is not None


def test_2_health_live(client):
    """Verify GET /health/live returns 200 and status live."""
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "live"}


def test_3_health_ready(client):
    """Verify GET /health/ready returns 200, status ready and model details."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["model_loaded"] is True
    assert data["model_name"] == "yolov8n"
    assert data["device"] == "cpu"


def test_4_model_metadata_endpoint(client):
    """Verify GET /v2/models/yolov8n returns correct model metadata."""
    response = client.get("/v2/models/yolov8n")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "yolov8n"
    assert "1" in data["versions"]
    assert len(data["inputs"]) > 0
    assert len(data["outputs"]) > 0
    assert data["outputs"][0]["target_class"]["id"] == 0
    assert data["outputs"][0]["target_class"]["name"] == "person"


def test_5_valid_image_inference_and_schema(client):
    """Verify POST /v2/models/yolov8n/infer with valid image conforms to JSON schema."""
    image_path = Path("/app/data/inputs/sample_person.jpg")
    assert image_path.exists(), f"Sample image not found at {image_path}"

    with open(image_path, "rb") as f:
        img_bytes = f.read()

    response = client.post(
        "/v2/models/yolov8n/infer",
        files={"image": ("sample.jpg", img_bytes, "image/jpeg")},
        params={"conf": 0.35, "iou": 0.65},
    )

    assert response.status_code == 200
    data = response.json()

    # Schema checks
    assert data["model_name"] == "yolov8n"
    assert data["model_version"] == "1"
    assert data["image_width"] > 0
    assert data["image_height"] > 0
    assert isinstance(data["detections"], list)
    assert len(data["detections"]) >= 1  # Detects person

    # Metrics checks
    metrics = data["metrics"]
    assert "preprocess_ms" in metrics
    assert "inference_ms" in metrics
    assert "postprocess_ms" in metrics
    assert "total_ms" in metrics
    assert metrics["total_ms"] > 0

    # Detection checks
    det = data["detections"][0]
    assert det["class_id"] == 0
    assert det["class_name"] == "person"
    assert 0.0 <= det["confidence"] <= 1.0
    bbox = det["bbox"]
    assert bbox["x1"] < bbox["x2"]
    assert bbox["y1"] < bbox["y2"]


def test_6_detection_class_restriction(client):
    """Verify that only class_id == 0 (person) is ever returned in detections."""
    image_path = Path("/app/data/inputs/sample_person.jpg")
    with open(image_path, "rb") as f:
        img_bytes = f.read()

    response = client.post(
        "/v2/models/yolov8n/infer",
        files={"image": ("sample.jpg", img_bytes, "image/jpeg")},
        params={"conf": 0.1, "iou": 0.5},  # Low confidence to get more candidates
    )
    assert response.status_code == 200
    data = response.json()
    for det in data["detections"]:
        assert det["class_id"] == 0
        assert det["class_name"] == "person"


def test_7_invalid_image_rejection(client):
    """Verify corrupted, non-image, and empty payloads are properly rejected with HTTP 4xx."""
    # 1. Non-image corrupted content
    response = client.post(
        "/v2/models/yolov8n/infer",
        files={"image": ("bad.jpg", b"not-a-valid-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 400
    assert "detail" in response.json()
    # Confirm no stack trace leaked
    assert "Traceback" not in response.text

    # 2. Unsupported content type
    response = client.post(
        "/v2/models/yolov8n/infer",
        files={"image": ("doc.pdf", b"%PDF-1.4...", "application/pdf")},
    )
    assert response.status_code == 415

    # 3. Empty file
    response = client.post(
        "/v2/models/yolov8n/infer",
        files={"image": ("empty.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400


def test_8_confidence_threshold_behavior(client):
    """Verify that higher confidence threshold filters lower scoring detections."""
    image_path = Path("/app/data/inputs/sample_person.jpg")
    with open(image_path, "rb") as f:
        img_bytes = f.read()

    resp_low = client.post(
        "/v2/models/yolov8n/infer",
        files={"image": ("sample.jpg", img_bytes, "image/jpeg")},
        params={"conf": 0.20},
    )
    resp_high = client.post(
        "/v2/models/yolov8n/infer",
        files={"image": ("sample.jpg", img_bytes, "image/jpeg")},
        params={"conf": 0.95},  # Very high threshold
    )

    assert resp_low.status_code == 200
    assert resp_high.status_code == 200

    dets_low = resp_low.json()["detections"]
    dets_high = resp_high.json()["detections"]

    assert len(dets_high) <= len(dets_low)
    for d in dets_high:
        assert d["confidence"] >= 0.95


def test_9_model_sha256_integrity():
    """Verify authoritative baseline model SHA256 has not been altered or overwritten."""
    model_path = Path("/app/data/models/yolov8n.pt")
    assert model_path.exists()
    hasher = hashlib.sha256()
    with open(model_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    actual_hash = hasher.hexdigest().lower()
    expected_hash = "f59b3d833e2ff32e194b5bb8e08d211dc7c5bdf144b90d2c8412c47ccfc83b36"
    assert actual_hash == expected_hash, f"Model hash changed! Expected {expected_hash}, got {actual_hash}"
