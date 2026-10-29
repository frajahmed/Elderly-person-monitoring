"""Interactive tool to draw the bed zone and safe zones."""

from __future__ import annotations

from typing import List

from .config import MonitorConfig
from .models import Point
from .video import VideoSource
from .zones import Zone, ZoneRepository


class ZoneCalibrator:
    """Click polygon points on a camera snapshot.

    The first zone is the bed, every further zone is a safe zone
    (armchair, sofa, ...).
    """

    WINDOW = "Calibrate"
    HELP = "Left click: add point | ENTER: finish zone | ESC: save & exit"
    KEY_ENTER, KEY_ESC = 13, 27

    def __init__(self, config: MonitorConfig) -> None:
        self.cfg = config
        self._zones: List[Zone] = []
        self._points: List[Point] = []

    def run(self) -> None:
        import cv2

        frame = self._grab_frame()
        cv2.namedWindow(self.WINDOW)
        cv2.setMouseCallback(self.WINDOW, self._on_click)
        print("First zone = BED, further zones = safe zones (chair, sofa ...)")
        print(self.HELP)

        while True:
            cv2.imshow(self.WINDOW, self._render(frame))
            key = cv2.waitKey(30) & 0xFF
            if key == self.KEY_ENTER and len(self._points) >= 3:
                self._finish_zone()
            elif key == self.KEY_ESC:
                break
        cv2.destroyAllWindows()
        self._save()

    def _grab_frame(self):
        video = VideoSource(self.cfg.camera_source)
        frame = None
        while frame is None:
            frame = video.read()
        video.release()
        return frame

    def _on_click(self, event, x, y, *_) -> None:
        import cv2

        if event == cv2.EVENT_LBUTTONDOWN:
            self._points.append((x, y))

    def _finish_zone(self) -> None:
        name = "bed" if not self._zones else f"safe_{len(self._zones)}"
        self._zones.append(Zone(name, list(self._points)))
        self._points.clear()

    def _render(self, frame):
        import cv2
        import numpy as np

        view = frame.copy()
        for zone in self._zones:
            cv2.polylines(view, [np.array(zone.polygon, np.int32)], True, (0, 255, 0), 2)
        for p in self._points:
            cv2.circle(view, (int(p[0]), int(p[1])), 4, (0, 0, 255), -1)
        label = "BED" if not self._zones else f"SAFE ZONE {len(self._zones)}"
        cv2.putText(view, f"Drawing: {label}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        return view

    def _save(self) -> None:
        if not self._zones:
            print("No bed zone drawn - nothing saved.")
            return
        ZoneRepository(self.cfg.zones_file).save(self._zones[0], self._zones[1:])
        print(f"Saved to {self.cfg.zones_file}")
