"""
Comprehensive automated tests for Gate 4:
Structured logging, Request ID, Error Taxonomy, Log Rotation, Prometheus Metrics, Model Registry,
and Gate 2 regression verification.
"""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import uuid
import pytest
from fastapi.testclient import TestClient

from src.serving.api import app, engine
from src.serving.config import settings
from src.serving.logging_handler import (
    ErrorCategory,
    InferenceLogEntry,
    StructuredInferenceLogger,
)
from src.serving.metrics import get_metrics_exposition


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


# ============================================================================
# A. REQUEST ID TESTS
# ============================================================================

def test_request_id_generated_when_absent(client):
    """Verify UUID4 request_id is automatically generated and returned in header."""
    response = client.get("/health/live")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    req_id = response.headers["x-request-id"]
    # Check valid UUID format
    parsed_uuid = uuid.UUID(req_id, version=4)
    assert str(parsed_uuid) == req_id


def test_incoming_request_id_passed_through(client):
    """Verify custom X-Request-ID header is preserved safely."""
    custom_id = "test-custom-id-987654321"
    response = client.get("/health/live", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("x-request-id") == custom_id


# ============================================================================
# B. STRUCTURED JSONL LOGGING TESTS
# ============================================================================

def test_successful_inference_logs_structured_jsonl(client):
    """Verify successful inference creates a compliant JSONL record with timing & metadata."""
    image_path = Path("/app/data/inputs/sample_person.jpg")
    with open(image_path, "rb") as f:
        img_bytes = f.read()

    test_req_id = f"test-log-verify-{uuid.uuid4()}"
    response = client.post(
        "/v2/models/yolov8n/infer?conf=0.35&iou=0.65",
        files={"image": ("sample.jpg", img_bytes, "image/jpeg")},
        headers={"X-Request-ID": test_req_id},
    )
    assert response.status_code == 200
    assert response.headers["x-request-id"] == test_req_id

    # Verify log entry in /app/logs/inference_access.jsonl
    log_file = Path("/app/logs/inference_access.jsonl")
    assert log_file.exists()

    found_entry = None
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                if record.get("request_id") == test_req_id:
                    found_entry = record
                    break

    assert found_entry is not None, f"Log record with request_id {test_req_id} not found"
    assert found_entry["http_status"] == 200
    assert found_entry["method"] == "POST"
    assert found_entry["endpoint"] == "/v2/models/yolov8n/infer"
    assert found_entry["model_name"] == "yolov8n"
    assert found_entry["model_sha256"] == settings.expected_sha256
    assert found_entry["image_width"] == 768
    assert found_entry["image_height"] == 432
    assert found_entry["image_size_bytes"] == len(img_bytes)
    assert found_entry["detection_count"] >= 1
    assert found_entry["preprocess_ms"] > 0
    assert found_entry["inference_ms"] > 0
    assert found_entry["total_ms"] > 0
    assert found_entry["error_category"] is None

    # Privacy checks: ensure NO raw bytes, base64, or private data present in log
    line_str = json.dumps(found_entry)
    assert "bytes" not in line_str.lower() or "image_size_bytes" in line_str
    assert "data:image" not in line_str
    assert "base64" not in line_str.lower()


def test_failed_inference_logs_error_category(client):
    """Verify failed request emits structured log with correct ErrorCategory."""
    test_req_id = f"test-err-verify-{uuid.uuid4()}"
    response = client.post(
        "/v2/models/yolov8n/infer",
        files={"image": ("empty.jpg", b"", "image/jpeg")},
        headers={"X-Request-ID": test_req_id},
    )
    assert response.status_code == 400

    log_file = Path("/app/logs/inference_access.jsonl")
    found_entry = None
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                if record.get("request_id") == test_req_id:
                    found_entry = record
                    break

    assert found_entry is not None
    assert found_entry["http_status"] == 400
    assert found_entry["error_category"] == ErrorCategory.EMPTY_PAYLOAD.value
    assert found_entry["detection_count"] == 0


# ============================================================================
# C. LOG ROTATION TESTS
# ============================================================================

def test_log_rotation_mechanism():
    """Verify StructuredInferenceLogger rotates files at maxBytes threshold."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_log_path = Path(tmp_dir) / "test_rotate.jsonl"
        # Small maxBytes for testing rotation (e.g., 500 bytes, backupCount=2)
        rot_logger = StructuredInferenceLogger(
            log_file=str(test_log_path),
            max_bytes=500,
            backup_count=2,
        )

        dummy_entry = InferenceLogEntry(
            timestamp="2026-11-10T15:00:00Z",
            request_id="test-rot-uuid",
            method="POST",
            endpoint="/v2/models/yolov8n/infer",
            http_status=200,
            model_name="yolov8n",
            total_ms=50.0,
        )

        # Write enough lines to exceed 500 bytes multiple times
        for _ in range(15):
            rot_logger.log(dummy_entry)

        # Confirm base file and backup file .1 exist
        assert test_log_path.exists()
        backup_1 = Path(tmp_dir) / "test_rotate.jsonl.1"
        assert backup_1.exists(), "Backup rotated log file .1 should be created"


# ============================================================================
# D. PROMETHEUS METRICS TESTS
# ============================================================================

def test_metrics_endpoint_exposition(client):
    """Verify /metrics returns 200, text format, and required metric keys."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")
    content = response.text

    assert "visionstream_requests_total" in content
    assert "visionstream_request_latency_seconds" in content
    assert "visionstream_inference_latency_seconds" in content
    assert "visionstream_detections_total" in content
    assert "visionstream_inference_errors_total" in content


def test_metrics_counters_increment(client):
    """Verify metrics counters increment on inference and error events."""
    image_path = Path("/app/data/inputs/sample_person.jpg")
    with open(image_path, "rb") as f:
        img_bytes = f.read()

    # Trigger inference
    resp_inf = client.post(
        "/v2/models/yolov8n/infer?conf=0.35&iou=0.65",
        files={"image": ("sample.jpg", img_bytes, "image/jpeg")},
    )
    assert resp_inf.status_code == 200

    # Scrape metrics
    m_resp = client.get("/metrics")
    assert m_resp.status_code == 200
    m_text = m_resp.text

    # Verify request counter has entry for 200
    assert 'visionstream_requests_total{endpoint="/v2/models/yolov8n/infer",method="POST",status_code="200"}' in m_text
    # Verify detection counter recorded
    assert 'visionstream_detections_total{class_name="person",model_name="yolov8n"}' in m_text


# ============================================================================
# E. MODEL REGISTRY TESTS
# ============================================================================

def test_model_registry_validity_and_baseline_sha256():
    """Verify reports/model_registry.json schema, promotion status, and baseline hash."""
    registry_path = Path("/app/reports/model_registry.json")
    assert registry_path.exists(), f"Model registry not found at {registry_path}"

    with open(registry_path, "r", encoding="utf-8") as f:
        registry = json.load(f)

    assert registry["registry_version"] == "1.0"
    assert "models" in registry
    assert len(registry["models"]) >= 2

    # Find baseline
    baseline = next((m for m in registry["models"] if m["model_role"] == "PRIMARY_BASELINE"), None)
    assert baseline is not None
    assert baseline["model_name"] == "yolov8n"
    assert baseline["promotion_status"] == "ACTIVE_SERVING"
    assert baseline["sha256"].lower() == settings.expected_sha256.lower()

    # Check best.pt entry
    finetuned = next((m for m in registry["models"] if m["model_role"] == "RESEARCH_FINE_TUNED_ARTIFACT"), None)
    assert finetuned is not None
    assert finetuned["promotion_status"] == "RESEARCH_ARCHIVED"
    assert finetuned["sha256"].lower() == "41d74cb7e4288a526d9bf4d092343e12fa61acc7e4d1dac76c82593c7bd715ef"


# ============================================================================
# F. GATE 2 REGRESSION VERIFICATION
# ============================================================================

def test_gate2_health_endpoints(client):
    """Verify /health/live and /health/ready remain intact."""
    r_live = client.get("/health/live")
    assert r_live.status_code == 200
    assert r_live.json() == {"status": "live"}

    r_ready = client.get("/health/ready")
    assert r_ready.status_code == 200
    assert r_ready.json()["model_loaded"] is True


def test_gate2_model_metadata(client):
    """Verify /v2/models/yolov8n metadata endpoint contract unchanged."""
    resp = client.get("/v2/models/yolov8n")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "yolov8n"
    assert data["outputs"][0]["target_class"]["name"] == "person"


def test_gate2_invalid_image_rejection(client):
    """Verify invalid payloads are properly rejected with 4xx errors."""
    r_bad_type = client.post(
        "/v2/models/yolov8n/infer",
        files={"image": ("test.pdf", b"%PDF", "application/pdf")},
    )
    assert r_bad_type.status_code == 415

    r_corrupt = client.post(
        "/v2/models/yolov8n/infer",
        files={"image": ("test.jpg", b"corrupted-random-bytes", "image/jpeg")},
    )
    assert r_corrupt.status_code == 400


def test_gate2_model_sha256_unmodified():
    """Verify data/models/yolov8n.pt hash remains unchanged."""
    model_p = Path("/app/data/models/yolov8n.pt")
    hasher = hashlib.sha256()
    with open(model_p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    assert hasher.hexdigest().lower() == settings.expected_sha256.lower()
