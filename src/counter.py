"""
counter.py
----------
Implements directional line-crossing counting.

A single virtual line is drawn across the frame (horizontal or vertical).
For every tracked object, we compare its previous centroid position to
its current one. If the object's position relative to the line flips
sign between the two frames, it has "crossed," and we record one count
in the appropriate direction for that object's label. Each track is only
allowed to register a crossing once (tracked via `counted_track_ids`) so
a vehicle that lingers near the line does not get counted repeatedly.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Tuple

from src.tracker import Track


@dataclass
class LineCounter:
    orientation: str = "horizontal"   # "horizontal" or "vertical"
    position_fraction: float = 0.5    # where the line sits, 0.0-1.0 of frame dim
    frame_width: int = 0
    frame_height: int = 0

    counted_track_ids: set = field(default_factory=set)
    counts: Dict[str, Dict[str, int]] = field(
        default_factory=lambda: defaultdict(lambda: {"in": 0, "out": 0})
    )

    def line_pixel_position(self) -> int:
        if self.orientation == "horizontal":
            return int(self.frame_height * self.position_fraction)
        return int(self.frame_width * self.position_fraction)

    def _side(self, centroid: Tuple[int, int]) -> int:
        """Returns -1 or +1 depending on which side of the line a point is on."""
        line_pos = self.line_pixel_position()
        value = centroid[1] if self.orientation == "horizontal" else centroid[0]
        return -1 if value < line_pos else 1

    def update(self, tracks: Dict[int, Track]):
        """
        Check every active track for a line crossing since its previous
        recorded position and update counts accordingly.
        """
        for track_id, track in tracks.items():
            if track_id in self.counted_track_ids:
                continue
            if not track.history:
                continue  # need at least one prior position to detect a crossing

            previous_centroid = track.history[-1]
            previous_side = self._side(previous_centroid)
            current_side = self._side(track.centroid)

            if previous_side != current_side:
                direction = "in" if current_side == 1 else "out"
                self.counts[track.label][direction] += 1
                self.counted_track_ids.add(track_id)

    def total_by_label(self, label: str) -> int:
        c = self.counts.get(label, {"in": 0, "out": 0})
        return c["in"] + c["out"]

    def grand_total(self) -> int:
        return sum(self.total_by_label(label) for label in self.counts)
