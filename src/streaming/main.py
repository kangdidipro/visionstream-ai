"""
CLI entry point for VisionStream AI GStreamer & RTSP streaming ingestion daemon.
"""
import argparse
import json
import logging
import signal
import sys
import time

from src.streaming.config import settings
from src.streaming.rtsp_client import ResilientRTSPClient

logger = logging.getLogger("visionstream.streaming.main")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    parser = argparse.ArgumentParser(description="VisionStream AI RTSP Ingestion Service")
    parser.add_argument("--duration", type=float, default=None, help="Max run duration in seconds (optional)")
    parser.add_argument("--rtsp-url", type=str, default=None, help="RTSP Stream URL override")
    args = parser.parse_args()

    if args.rtsp_url:
        settings.rtsp_url = args.rtsp_url

    client = ResilientRTSPClient(config=settings)

    def signal_handler(sig, frame):
        logger.info("Signal received, initiating graceful shutdown...")
        client.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("=" * 60)
    logger.info("VISIONSTREAM AI — RTSP INGESTION DAEMON")
    logger.info(f"Stream ID : {settings.stream_id}")
    logger.info(f"RTSP URL  : {settings.rtsp_url}")
    logger.info(f"Model     : {settings.model_path}")
    logger.info(f"Device    : {settings.device}")
    logger.info("=" * 60)

    try:
        client.run_with_reconnect(max_duration_sec=args.duration)
    finally:
        summary = client.metrics.get_summary()
        logger.info("=" * 60)
        logger.info("STREAMING EXECUTION SUMMARY")
        logger.info(json.dumps(summary, indent=2))
        logger.info("=" * 60)


if __name__ == "__main__":
    main()
