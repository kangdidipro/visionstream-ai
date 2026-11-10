"""
GStreamer RTSP ingestion pipeline using PyGObject and appsink.
Extracts decoded BGR frames into NumPy arrays with backpressure and leaky buffer management.
"""
import logging
import threading
import time
from typing import Callable, Optional, Tuple

import gi
gi.require_version("Gst", "1.0")
gi.require_version("GstApp", "1.0")
from gi.repository import GLib, Gst, GstApp
import numpy as np

from src.streaming.config import StreamingConfig, settings
from src.streaming.stream_metrics import StreamingMetricsCollector

logger = logging.getLogger("visionstream.gstreamer")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Initialize GStreamer once
Gst.init(None)


class GStreamerRTSPIngest:
    """
    Manages GStreamer pipeline lifecycle:
    rtspsrc -> rtph264depay -> h264parse -> avdec_h264 -> videoconvert -> queue (leaky) -> appsink
    """
    def __init__(
        self,
        config: Optional[StreamingConfig] = None,
        metrics: Optional[StreamingMetricsCollector] = None,
        on_frame_callback: Optional[Callable[[np.ndarray, int], None]] = None,
        on_error_callback: Optional[Callable[[str], None]] = None,
    ):
        self.config = config or settings
        self.metrics = metrics
        self.on_frame_callback = on_frame_callback
        self.on_error_callback = on_error_callback

        self.pipeline: Optional[Gst.Pipeline] = None
        self.loop: Optional[GLib.MainLoop] = None
        self.loop_thread: Optional[threading.Thread] = None
        self.appsink: Optional[GstApp.AppSink] = None

        self._frame_sequence = 0
        self._is_running = False
        self._eos_received = False
        self._last_error_msg: Optional[str] = None

    def build_pipeline_string(self) -> str:
        """
        Construct GStreamer pipeline string with bounded queues and leaky backpressure.
        """
        # Leaky mode: 2 = downstream (drop oldest)
        leaky_val = "downstream" if self.config.queue_leaky_mode == "downstream" else "no"

        pipeline_str = (
            f"rtspsrc location={self.config.rtsp_url} protocols={self.config.rtsp_transport} "
            f"latency={self.config.jitter_buffer_ms} drop-on-latency=true ! "
            f"rtph264depay ! "
            f"h264parse ! "
            f"avdec_h264 ! "
            f"videoconvert ! "
            f"video/x-raw,format={self.config.target_format} ! "
            f"queue max-size-buffers={self.config.queue_max_buffers} leaky={leaky_val} ! "
            f"appsink name=sink emit-signals=true max-buffers={self.config.appsink_max_buffers} "
            f"drop={str(self.config.appsink_drop).lower()} sync=false"
        )
        return pipeline_str

    def _on_new_sample(self, sink: GstApp.AppSink) -> Gst.FlowReturn:
        """Appsink callback when a new decoded frame is available."""
        sample = sink.emit("pull-sample")
        if not sample:
            return Gst.FlowReturn.ERROR

        buf = sample.get_buffer()
        caps = sample.get_caps()
        if not buf or not caps:
            return Gst.FlowReturn.OK

        struct = caps.get_structure(0)
        width = struct.get_value("width")
        height = struct.get_value("height")

        success, map_info = buf.map(Gst.MapFlags.READ)
        if not success:
            return Gst.FlowReturn.ERROR

        try:
            # Map memory directly to numpy BGR array
            frame = np.ndarray(
                shape=(height, width, 3),
                dtype=np.uint8,
                buffer=map_info.data,
            ).copy()  # Make safe independent copy

            self._frame_sequence += 1
            if self.metrics:
                self.metrics.record_frame_received()
                self.metrics.record_frame_decoded()

            if self.on_frame_callback:
                self.on_frame_callback(frame, self._frame_sequence)

        finally:
            buf.unmap(map_info)

        return Gst.FlowReturn.OK

    def _on_bus_message(self, bus: Gst.Bus, message: Gst.Message) -> bool:
        """Process out-of-band GStreamer bus messages."""
        msg_type = message.type
        if msg_type == Gst.MessageType.EOS:
            logger.info("GStreamer bus: End-Of-Stream received.")
            self._eos_received = True
            self.stop()
        elif msg_type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            self._last_error_msg = f"{err.message} (debug: {debug})"
            logger.error(f"GStreamer bus error: {self._last_error_msg}")
            if self.on_error_callback:
                self.on_error_callback(self._last_error_msg)
            self.stop()
        elif msg_type == Gst.MessageType.WARNING:
            warn, debug = message.parse_warning()
            logger.warning(f"GStreamer bus warning: {warn.message}")
        return True

    def start(self) -> None:
        """Parse pipeline, attach callbacks, and transition to PLAYING state."""
        if self._is_running:
            return

        pipeline_str = self.build_pipeline_string()
        logger.info(f"Launching GStreamer pipeline:\n  {pipeline_str}")

        try:
            self.pipeline = Gst.parse_launch(pipeline_str)
        except Exception as e:
            logger.critical(f"Failed to parse GStreamer pipeline: {e}")
            raise e

        # Connect appsink signal
        self.appsink = self.pipeline.get_by_name("sink")
        if not self.appsink:
            raise RuntimeError("Could not find 'sink' element in GStreamer pipeline.")

        self.appsink.connect("new-sample", self._on_new_sample)

        # Connect bus watch
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._on_bus_message)

        # Start GLib main loop in background thread
        self.loop = GLib.MainLoop()
        self.loop_thread = threading.Thread(target=self.loop.run, daemon=True)
        self.loop_thread.start()

        # Set pipeline state to PLAYING
        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            self.stop()
            raise RuntimeError("GStreamer pipeline failed to transition to PLAYING.")

        self._is_running = True
        logger.info("GStreamer pipeline is now PLAYING.")

    def stop(self) -> None:
        """Orderly pipeline teardown: PLAYING -> READY -> NULL and free loop."""
        if not self._is_running and not self.pipeline:
            return

        logger.info("Stopping GStreamer pipeline...")
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline = None

        if self.loop and self.loop.is_running():
            self.loop.quit()

        self._is_running = False
        logger.info("GStreamer pipeline stopped cleanly.")

    @property
    def is_running(self) -> bool:
        return self._is_running
