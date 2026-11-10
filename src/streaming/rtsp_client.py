"""
Resilient RTSP streaming client managing automatic reconnection, exponential backoff,
health state tracking, and pipeline lifecycle.
"""
import logging
import threading
import time
from typing import Optional

import numpy as np

from src.streaming.config import StreamingConfig, settings
from src.streaming.frame_processor import StreamFrameProcessor
from src.streaming.gstreamer_ingest import GStreamerRTSPIngest
from src.streaming.stream_metrics import (
    StreamErrorCategory,
    StreamingLogEntry,
    StreamingMetricsCollector,
    StructuredStreamingLogger,
    StreamStatus,
    get_utc_timestamp,
)

logger = logging.getLogger("visionstream.rtsp_client")


class ResilientRTSPClient:
    """
    High-level streaming coordinator.
    Handles continuous ingestion, frame dispatch, disconnects, and exponential backoff retry.
    """
    def __init__(
        self,
        config: Optional[StreamingConfig] = None,
        processor: Optional[StreamFrameProcessor] = None,
        metrics: Optional[StreamingMetricsCollector] = None,
        logger_instance: Optional[StructuredStreamingLogger] = None,
    ):
        self.config = config or settings
        self.metrics = metrics or StreamingMetricsCollector(stream_id=self.config.stream_id)
        self.logger = logger_instance or StructuredStreamingLogger(log_file=self.config.log_file)
        self.processor = processor or StreamFrameProcessor(
            config=self.config,
            metrics_collector=self.metrics,
            logger=self.logger,
        )

        self.ingest: Optional[GStreamerRTSPIngest] = None
        self.status = StreamStatus.INITIALIZING
        self._stop_requested = False
        self._last_error: Optional[str] = None
        self._disconnect_time: Optional[float] = None
        self._reconnect_lock = threading.Lock()

    def _on_frame_received(self, frame: np.ndarray, seq: int) -> None:
        """Callback from GStreamer ingest when a decoded frame arrives."""
        if self._stop_requested:
            return

        self.status = StreamStatus.STREAMING
        self._disconnect_time = None

        try:
            # Process frame through YOLOv8 + ByteTrack
            self.processor.process_frame(frame, seq)
        except Exception as e:
            logger.error(f"Error processing frame {seq}: {e}")

    def _on_stream_error(self, error_msg: str) -> None:
        """Callback from GStreamer bus on fatal error."""
        logger.warning(f"Stream error observed: {error_msg}")
        self._last_error = error_msg
        self.status = StreamStatus.DISCONNECTED
        self._disconnect_time = time.time()

    def start(self) -> None:
        """Initialize frame processor and launch GStreamer ingestion."""
        logger.info(f"Initializing Resilient RTSP Client for stream: {self.config.stream_id}")
        self.processor.initialize()

        self.ingest = GStreamerRTSPIngest(
            config=self.config,
            metrics=self.metrics,
            on_frame_callback=self._on_frame_received,
            on_error_callback=self._on_stream_error,
        )

        self.status = StreamStatus.CONNECTED
        self.ingest.start()

    def stop(self) -> None:
        """Stop ingestion and cleanly release pipeline resources."""
        self._stop_requested = True
        self.status = StreamStatus.STOPPED
        if self.ingest:
            self.ingest.stop()
            self.ingest = None
        logger.info("Resilient RTSP Client stopped.")

    def run_with_reconnect(self, max_duration_sec: Optional[float] = None) -> None:
        """
        Run streaming loop with automated reconnection and exponential backoff.
        """
        self.start()
        start_time = time.time()
        retry_delay = self.config.initial_retry_delay_sec
        reconnect_attempts = 0

        try:
            while not self._stop_requested:
                if max_duration_sec and (time.time() - start_time) >= max_duration_sec:
                    logger.info(f"Max test duration {max_duration_sec}s reached.")
                    break

                # Check if stream disconnected
                if self.status == StreamStatus.DISCONNECTED or (self.ingest and not self.ingest.is_running):
                    if not self._stop_requested:
                        with self._reconnect_lock:
                            reconnect_attempts += 1
                            self.metrics.record_reconnect()
                            self.status = StreamStatus.RECONNECTING

                            logger.warning(
                                f"Stream disconnected. Attempting reconnect {reconnect_attempts}/"
                                f"{self.config.max_reconnect_attempts} in {retry_delay:.1f}s..."
                            )

                            self.logger.log(
                                StreamingLogEntry(
                                    timestamp=get_utc_timestamp(),
                                    stream_id=self.config.stream_id,
                                    connection_status=StreamStatus.RECONNECTING.value,
                                    reconnect_count=self.metrics.reconnect_count,
                                    error_category=StreamErrorCategory.CONNECTION_REFUSED.value,
                                )
                            )

                            # If stream was down for longer than threshold, reset tracker
                            if self._disconnect_time and (time.time() - self._disconnect_time) > self.config.tracker_reset_outage_sec:
                                logger.info("Prolonged stream outage detected. Resetting ByteTrack tracker state.")
                                self.processor.reset_tracker()

                            time.sleep(retry_delay)

                            # Clean up old ingest
                            if self.ingest:
                                self.ingest.stop()
                                self.ingest = None

                            try:
                                # Re-create and start ingest
                                self.ingest = GStreamerRTSPIngest(
                                    config=self.config,
                                    metrics=self.metrics,
                                    on_frame_callback=self._on_frame_received,
                                    on_error_callback=self._on_stream_error,
                                )
                                self.ingest.start()
                                self.status = StreamStatus.CONNECTED
                                retry_delay = self.config.initial_retry_delay_sec
                                logger.info("Successfully reconnected to RTSP stream.")
                            except Exception as re_err:
                                logger.error(f"Reconnection attempt {reconnect_attempts} failed: {re_err}")
                                retry_delay = min(
                                    retry_delay * self.config.reconnect_backoff_factor,
                                    self.config.max_retry_delay_sec,
                                )

                            if reconnect_attempts >= self.config.max_reconnect_attempts:
                                logger.critical("Max reconnection attempts exceeded. Stopping stream.")
                                self.status = StreamStatus.ERROR
                                break

                time.sleep(0.5)

        finally:
            self.stop()
