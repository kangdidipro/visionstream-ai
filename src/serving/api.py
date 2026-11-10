"""
FastAPI application gateway for VisionStream AI inference service.
Provides health endpoints, model metadata, Prometheus metrics, and multipart image inference
with structured JSONL logging, request ID tracing, and error classification.
"""
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, File, HTTPException, Query, Request, Response, UploadFile, status
from fastapi.responses import JSONResponse, Response as RawResponse

from src.serving.config import settings
from src.serving.engine import YOLOv8InferenceEngine
from src.serving.logging_handler import (
    ErrorCategory,
    InferenceLogEntry,
    StructuredInferenceLogger,
    get_utc_iso_timestamp,
)
from src.serving.metrics import (
    DETECTIONS_TOTAL,
    INFERENCE_ERRORS_TOTAL,
    INFERENCE_LATENCY_SECONDS,
    REQUEST_LATENCY_SECONDS,
    REQUESTS_TOTAL,
    get_metrics_exposition,
)
from src.serving.schemas import HealthResponse, InferenceResponse, ModelMetadataResponse

logger = logging.getLogger("visionstream.serving")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

engine = YOLOv8InferenceEngine(config=settings)
access_logger = StructuredInferenceLogger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager: load model at startup."""
    logger.info("Initializing VisionStream AI Inference Engine...")
    try:
        engine.load_model()
        logger.info(f"Model {settings.model_name} loaded successfully on {settings.device}.")
    except Exception as e:
        logger.critical(f"Failed to load model on startup: {e}")
        raise e
    yield
    logger.info("Shutting down VisionStream AI Inference Engine...")


app = FastAPI(
    title="VisionStream AI Inference Service",
    description="Lightweight modular FastAPI serving gateway for YOLOv8n CPU person detection with MLOps observability",
    version="1.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def request_tracing_middleware(request: Request, call_next):
    """
    Middleware for:
    1. Managing X-Request-ID (UUID4 generation or safe passthrough).
    2. Measuring request duration.
    3. Updating Prometheus request and latency metrics (bounded labels only).
    """
    start_time = time.perf_counter()

    # 1. Extract or generate request ID
    req_id_header = request.headers.get("X-Request-ID")
    if req_id_header and len(req_id_header) <= 64:
        request_id = req_id_header.strip()
    else:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # 2. Call next handler
    response = await call_next(request)

    # 3. Attach X-Request-ID response header
    response.headers["X-Request-ID"] = request_id

    duration_seconds = time.perf_counter() - start_time

    # 4. Update Prometheus metrics (excluding high cardinality labels)
    endpoint_path = request.url.path
    # Group endpoint paths to prevent metric explosion
    if endpoint_path.startswith("/v2/models/yolov8n/infer"):
        normalized_endpoint = "/v2/models/yolov8n/infer"
    elif endpoint_path.startswith("/v2/models/yolov8n"):
        normalized_endpoint = "/v2/models/yolov8n"
    elif endpoint_path in ("/health/live", "/health/ready", "/metrics"):
        normalized_endpoint = endpoint_path
    else:
        normalized_endpoint = "other"

    REQUESTS_TOTAL.labels(
        method=request.method,
        endpoint=normalized_endpoint,
        status_code=str(response.status_code),
    ).inc()

    REQUEST_LATENCY_SECONDS.labels(
        method=request.method,
        endpoint=normalized_endpoint,
    ).observe(duration_seconds)

    return response


@app.get("/health/live", summary="Liveness Probe")
async def health_live():
    """Returns 200 if the service process is alive."""
    return {"status": "live"}


@app.get("/health/ready", response_model=HealthResponse, summary="Readiness Probe")
async def health_ready():
    """Returns 200 if model is loaded and ready to serve, otherwise 503."""
    if not engine.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not ready or failed to load",
        )
    return HealthResponse(
        status="ready",
        model_loaded=True,
        model_name=settings.model_name,
        device=settings.device,
    )


@app.get(
    "/v2/models/yolov8n",
    response_model=ModelMetadataResponse,
    summary="Model Metadata (Triton-style route)",
)
async def get_model_metadata():
    """Return model metadata and input/output contracts."""
    if not engine.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not ready",
        )
    return engine.get_metadata()


@app.get("/metrics", summary="Prometheus Metrics Scrape Endpoint")
async def metrics():
    """
    Exposes in-process Prometheus metrics in standard exposition format.
    Does not increment inference request counters.
    """
    data, content_type = get_metrics_exposition()
    return RawResponse(content=data, media_type=content_type)


@app.post(
    "/v2/models/yolov8n/infer",
    response_model=InferenceResponse,
    summary="Stateless Person Detection Inference",
)
async def infer(
    request: Request,
    image: UploadFile = File(..., description="Image file (JPEG/PNG/WEBP/BMP)"),
    conf: Optional[float] = Query(
        default=0.35, ge=0.01, le=1.0, description="Confidence threshold"
    ),
    iou: Optional[float] = Query(
        default=0.65, ge=0.01, le=1.0, description="IoU threshold for NMS"
    ),
):
    """
    Perform single-image person detection using yolov8n CPU baseline.
    Logs structured audit records and updates Prometheus metrics.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    timestamp_str = get_utc_iso_timestamp()
    image_bytes = None
    image_size_bytes = 0

    # Helper function to log failure before raising
    def log_and_raise_error(
        status_code: int,
        detail: str,
        error_cat: ErrorCategory,
        img_w: Optional[int] = None,
        img_h: Optional[int] = None,
        size_bytes: Optional[int] = None,
    ):
        INFERENCE_ERRORS_TOTAL.labels(error_category=error_cat.value).inc()
        access_logger.log(
            InferenceLogEntry(
                timestamp=timestamp_str,
                request_id=request_id,
                method="POST",
                endpoint="/v2/models/yolov8n/infer",
                http_status=status_code,
                model_name=settings.model_name,
                model_version=settings.model_version,
                model_sha256=settings.expected_sha256,
                image_width=img_w,
                image_height=img_h,
                image_size_bytes=size_bytes,
                conf_threshold=conf,
                iou_threshold=iou,
                detection_count=0,
                preprocess_ms=0.0,
                inference_ms=0.0,
                postprocess_ms=0.0,
                total_ms=0.0,
                error_category=error_cat.value,
            )
        )
        raise HTTPException(status_code=status_code, detail=detail)

    # 1. Validate engine readiness
    if not engine.is_ready():
        log_and_raise_error(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Inference engine is not ready",
            ErrorCategory.SERVICE_UNREADY,
        )

    # 2. Validate content type
    if image.content_type and image.content_type not in settings.allowed_content_types:
        log_and_raise_error(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Unsupported media type '{image.content_type}'. Allowed types: {', '.join(settings.allowed_content_types)}",
            ErrorCategory.UNSUPPORTED_MEDIA_TYPE,
        )

    # 3. Read image bytes and validate size
    try:
        image_bytes = await image.read()
        image_size_bytes = len(image_bytes) if image_bytes else 0
    except Exception:
        log_and_raise_error(
            status.HTTP_400_BAD_REQUEST,
            "Could not read uploaded image data.",
            ErrorCategory.DECODE_FAILURE,
        )

    if not image_bytes or image_size_bytes == 0:
        log_and_raise_error(
            status.HTTP_400_BAD_REQUEST,
            "Uploaded image file is empty.",
            ErrorCategory.EMPTY_PAYLOAD,
            size_bytes=0,
        )

    if image_size_bytes > settings.max_image_size_bytes:
        log_and_raise_error(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"Image size exceeds limit of {settings.max_image_size_bytes // (1024 * 1024)} MB.",
            ErrorCategory.PAYLOAD_TOO_LARGE,
            size_bytes=image_size_bytes,
        )

    # 4. Execute inference
    try:
        response = engine.infer(
            image_bytes=image_bytes,
            conf_threshold=conf,
            iou_threshold=iou,
        )
    except ValueError as ve:
        log_and_raise_error(
            status.HTTP_400_BAD_REQUEST,
            str(ve),
            ErrorCategory.DECODE_FAILURE,
            size_bytes=image_size_bytes,
        )
    except Exception as e:
        logger.error(f"Inference error encountered: {type(e).__name__}: {e}")
        log_and_raise_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Internal inference error occurred while processing image.",
            ErrorCategory.INFERENCE_EXCEPTION,
            size_bytes=image_size_bytes,
        )

    # 5. On success: record metrics and emit structured log
    det_count = len(response.detections)
    DETECTIONS_TOTAL.labels(
        model_name=settings.model_name,
        class_name=settings.target_class_name,
    ).inc(det_count)

    INFERENCE_LATENCY_SECONDS.labels(
        model_name=settings.model_name,
        model_version=settings.model_version,
    ).observe(response.metrics.inference_ms / 1000.0)

    access_logger.log(
        InferenceLogEntry(
            timestamp=timestamp_str,
            request_id=request_id,
            method="POST",
            endpoint="/v2/models/yolov8n/infer",
            http_status=status.HTTP_200_OK,
            model_name=response.model_name,
            model_version=response.model_version,
            model_sha256=settings.expected_sha256,
            image_width=response.image_width,
            image_height=response.image_height,
            image_size_bytes=image_size_bytes,
            conf_threshold=conf,
            iou_threshold=iou,
            detection_count=det_count,
            preprocess_ms=response.metrics.preprocess_ms,
            inference_ms=response.metrics.inference_ms,
            postprocess_ms=response.metrics.postprocess_ms,
            total_ms=response.metrics.total_ms,
            error_category=None,
        )
    )

    return response
