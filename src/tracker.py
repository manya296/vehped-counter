"""
tracker.py
----------
A lightweight centroid-distance tracker.

Each detection in a new frame is matched to the closest existing track
(by Euclidean distance between centroids) as long as that distance is
under `max_distance` and the label matches. Tracks that go unmatched for
more than `max_disappeared` consecutive frames are dropped. This is
intentionally simple (no Kalman filter, no IoU term) so it stays fast
on CPU and easy to reason about and test — appropriate for a counting
task, where we only need a stable ID and recent trajectory per object,
not sub-pixel motion prediction.
"""

from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from src.detector import Detection


def _distance(a: Tuple[int, int], b: Tuple[int, int]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


@dataclass
class Track:
    track_id: int
    label: str
    centroid: Tuple[int, int]
    box: Tuple[int, int, int, int]
    disappeared: int = 0
    history: List[Tuple[int, int]] = field(default_factory=list)

    def update_position(self, centroid, box):
        self.history.append(self.centroid)
        if len(self.history) > 30:
            self.history.pop(0)
        self.centroid = centroid
        self.box = box
        self.disappeared = 0


class CentroidTracker:
    def __init__(self, max_distance: float = 80.0, max_disappeared: int = 15):
        self.max_distance = max_distance
        self.max_disappeared = max_disappeared
        self._next_id = 1
        self.tracks: "OrderedDict[int, Track]" = OrderedDict()

    def update(self, detections: List[Detection]) -> Dict[int, Track]:
        """
        Reconcile the current tracks with a new frame's detections and
        return the updated set of active tracks (keyed by track_id).
        """
        if not detections:
            self._age_out_unmatched(matched_ids=set())
            return self._active_tracks()

        unmatched_detection_indices = list(range(len(detections)))
        matched_ids = set()

        # Greedy nearest-neighbour matching: for each existing track, find
        # the closest still-unmatched detection of the same label.
        for track_id, track in list(self.tracks.items()):
            best_index = None
            best_dist = self.max_distance
            for i in unmatched_detection_indices:
                det = detections[i]
                if det.label != track.label:
                    continue
                dist = _distance(track.centroid, det.centroid)
                if dist < best_dist:
                    best_dist = dist
                    best_index = i

            if best_index is not None:
                det = detections[best_index]
                track.update_position(det.centroid, det.box)
                matched_ids.add(track_id)
                unmatched_detection_indices.remove(best_index)

        # Any detection left over becomes a brand-new track.
        for i in unmatched_detection_indices:
            det = detections[i]
            new_track = Track(
                track_id=self._next_id,
                label=det.label,
                centroid=det.centroid,
                box=det.box,
            )
            self.tracks[self._next_id] = new_track
            matched_ids.add(self._next_id)
            self._next_id += 1

        self._age_out_unmatched(matched_ids)
        return self._active_tracks()

    def _age_out_unmatched(self, matched_ids: set):
        to_remove = []
        for track_id, track in self.tracks.items():
            if track_id not in matched_ids:
                track.disappeared += 1
                if track.disappeared > self.max_disappeared:
                    to_remove.append(track_id)
        for track_id in to_remove:
            del self.tracks[track_id]

    def _active_tracks(self) -> Dict[int, Track]:
        return {
            tid: t for tid, t in self.tracks.items() if t.disappeared == 0
        }
