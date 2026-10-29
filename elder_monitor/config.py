"""Central configuration of the monitor."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class MonitorConfig:
    """All tunable parameters in one place."""

    # Input
    camera_source: int | str = 0                # webcam index or RTSP/file path
    zones_file: Path = Path("zones.json")       # saved by the calibrator

    # Detection
    model_path: str = "yolo11n-pose.pt"         # Ultralytics pose model
    min_confidence: float = 0.5                 # minimum person confidence
    process_fps: float = 2.0                    # analysed frames per second

    # Alerting
    alert_after_seconds: float = 15 * 60        # floor time before alert
    reminder_interval_seconds: float = 10 * 60  # repeat alert while unresolved
    grace_seconds: float = 30.0                 # tolerate short detection gaps

    # Debugging
    show_preview: bool = False                  # debug window with overlay
