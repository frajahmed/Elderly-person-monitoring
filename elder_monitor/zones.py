"""Zones (bed, safe areas) and their persistence."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Sequence, Tuple

from .models import Point

logger = logging.getLogger(__name__)


class Zone:
    """A named polygon in image coordinates (e.g. bed, armchair)."""

    def __init__(self, name: str, polygon: Sequence[Point]) -> None:
        if len(polygon) < 3:
            raise ValueError(f"Zone '{name}' needs at least 3 points")
        self.name = name
        self.polygon: List[Point] = [(float(x), float(y)) for x, y in polygon]

    def contains(self, point: Point) -> bool:
        """Ray-casting point-in-polygon test."""
        x, y = point
        inside = False
        n = len(self.polygon)
        for i in range(n):
            x1, y1 = self.polygon[i]
            x2, y2 = self.polygon[(i + 1) % n]
            if (y1 > y) != (y2 > y):
                x_cross = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                if x < x_cross:
                    inside = not inside
        return inside

    def to_dict(self) -> dict:
        return {"name": self.name, "polygon": self.polygon}

    @classmethod
    def from_dict(cls, data: dict) -> "Zone":
        return cls(data["name"], data["polygon"])


class ZoneRepository:
    """Loads/saves the bed zone and optional safe zones as JSON."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def load(self) -> Tuple[Zone, List[Zone]]:
        if not self.path.exists():
            raise FileNotFoundError(
                f"{self.path} not found - run with --calibrate first")
        data = json.loads(self.path.read_text(encoding="utf-8"))
        bed = Zone.from_dict(data["bed"])
        safe = [Zone.from_dict(z) for z in data.get("safe_zones", [])]
        return bed, safe

    def save(self, bed: Zone, safe_zones: List[Zone]) -> None:
        data = {"bed": bed.to_dict(),
                "safe_zones": [z.to_dict() for z in safe_zones]}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info("Zones saved to %s", self.path)
