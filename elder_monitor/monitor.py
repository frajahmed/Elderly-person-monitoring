"""Main processing loop: capture -> detect -> classify -> analyze -> alert."""

from __future__ import annotations

import logging
import time
from typing import Optional

from .alert_manager import AlertManager
from .analyzer import SituationAnalyzer
from .config import MonitorConfig
from .detection import PersonDetector
from .models import Detection, Posture, SafetyState
from .notifiers import Notifier
from .posture import PostureClassifier
from .video import VideoSource
from .zones import ZoneRepository

logger = logging.getLogger(__name__)


class ElderMonitor:
    """Wires all components together and runs the monitoring loop."""

    def __init__(self, config: MonitorConfig, notifier: Notifier) -> None:
        self.cfg = config
        bed, safe_zones = ZoneRepository(config.zones_file).load()
        self.detector = PersonDetector(config.model_path, config.min_confidence)
        self.classifier = PostureClassifier()
        self.analyzer = SituationAnalyzer(bed, safe_zones)
        self.alerts = AlertManager(config, notifier)
        self.video = VideoSource(config.camera_source)
        self._last_seen: float = 0.0
        self._last_state = SafetyState.NO_PERSON

    def run(self) -> None:
        logger.info("Monitoring started")
        interval = 1.0 / self.cfg.process_fps
        try:
            while True:
                started = time.monotonic()
                frame = self.video.read()
                if frame is not None:
                    self._process(frame)
                time.sleep(max(0.0, interval - (time.monotonic() - started)))
        except KeyboardInterrupt:
            logger.info("Stopped by user")
        finally:
            self.video.release()

    def _process(self, frame) -> None:
        det = self.detector.detect(frame)
        posture = self.classifier.classify(det) if det else Posture.UNKNOWN
        state = self._smooth(self.analyzer.analyze(det, posture))

        self.alerts.update(state)
        if self.cfg.show_preview:
            self._draw(frame, det, posture, state)

    def _smooth(self, state: SafetyState) -> SafetyState:
        """Bridge short detection gaps by keeping the last known state."""
        now = time.monotonic()
        if state is SafetyState.NO_PERSON:
            if now - self._last_seen < self.cfg.grace_seconds:
                return self._last_state
            return state
        self._last_seen, self._last_state = now, state
        return state

    def _draw(self, frame, det: Optional[Detection],
              posture: Posture, state: SafetyState) -> None:
        """Debug overlay: zones, person box and current status."""
        import cv2
        import numpy as np

        zones = [(self.analyzer.bed, (255, 0, 0))] + \
                [(z, (0, 200, 0)) for z in self.analyzer.safe_zones]
        for zone, color in zones:
            pts = np.array(zone.polygon, dtype=np.int32)
            cv2.polylines(frame, [pts], True, color, 2)
        if det:
            x1, y1, x2, y2 = map(int, det.bbox)
            color = (0, 0, 255) if state is SafetyState.AT_RISK else (0, 255, 0)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        text = f"{posture.name} | {state.name} | risk {int(self.alerts.risk_duration)}s"
        cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.imshow("Elder Monitor", frame)
        cv2.waitKey(1)
