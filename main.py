"""
Entry point of the Elder Monitor.

Usage
-----
    # 1) Draw the bed zone (and optional safe zones) once:
    python main.py --calibrate

    # 2) Run the monitor:
    python main.py
    python main.py --source rtsp://user:pass@192.168.1.50:554/stream1 --preview

    # Optional: Telegram alerts via environment variables
    TELEGRAM_BOT_TOKEN=...   TELEGRAM_CHAT_ID=...
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from elder_monitor.calibrator import ZoneCalibrator
from elder_monitor.config import MonitorConfig
from elder_monitor.monitor import ElderMonitor
from elder_monitor.notifiers import build_notifier_from_env


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Elder floor-time monitor")
    parser.add_argument("--calibrate", action="store_true",
                        help="draw bed/safe zones and exit")
    parser.add_argument("--source", default="0",
                        help="camera index, stream URL or video file")
    parser.add_argument("--minutes", type=float, default=15,
                        help="minutes on the floor before the alert")
    parser.add_argument("--zones", default="data/zones.json",
                        help="path to the zones file")
    parser.add_argument("--preview", action="store_true",
                        help="show debug window")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> MonitorConfig:
    source: int | str = int(args.source) if args.source.isdigit() else args.source
    return MonitorConfig(
        camera_source=source,
        zones_file=Path(args.zones),
        alert_after_seconds=args.minutes * 60,
        show_preview=args.preview,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    args = parse_args()
    config = build_config(args)

    if args.calibrate:
        ZoneCalibrator(config).run()
        return

    try:
        monitor = ElderMonitor(config, build_notifier_from_env())
    except FileNotFoundError as exc:
        logging.error("%s", exc)
        sys.exit(1)
    monitor.run()


if __name__ == "__main__":
    main()
