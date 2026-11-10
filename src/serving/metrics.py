"""
Prometheus metrics registry and instrumentation for VisionStream AI inference service.
"""
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# 1. Total requests counter by method, endpoint, and HTTP status code
REQUESTS_TOTAL = Counter(
    "visionstream_requests_total",
    "Total HTTP requests received by the service",
    ["method", "endpoint", "status_code"],
)

# 2. Total request latency histogram (seconds)
REQUEST_LATENCY_SECONDS = Histogram(
    "visionstream_request_latency_seconds",
    "Total HTTP request end-to-end latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

# 3. Model inference latency histogram (seconds)
INFERENCE_LATENCY_SECONDS = Histogram(
    "visionstream_inference_latency_seconds",
    "Model inference forward pass execution latency in seconds",
    ["model_name", "model_version"],
    buckets=[0.01, 0.02, 0.035, 0.05, 0.075, 0.1, 0.2, 0.5],
)

# 4. Total detections counter
DETECTIONS_TOTAL = Counter(
    "visionstream_detections_total",
    "Total target class person detections predicted",
    ["model_name", "class_name"],
)

# 5. Total inference errors counter by error category
INFERENCE_ERRORS_TOTAL = Counter(
    "visionstream_inference_errors_total",
    "Total inference errors classified by taxonomy",
    ["error_category"],
)


def get_metrics_exposition() -> tuple[bytes, str]:
    """Return raw Prometheus text representation and content type."""
    return generate_latest(), CONTENT_TYPE_LATEST
