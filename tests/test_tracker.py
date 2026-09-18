import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.detector import Detection
from src.tracker import CentroidTracker


def make_det(cx, cy, label="car", size=20):
    half = size // 2
    return Detection(box=(cx - half, cy - half, cx + half, cy + half), label=label, confidence=0.9)


def test_new_detection_creates_new_track():
    tracker = CentroidTracker()
    tracks = tracker.update([make_det(100, 100)])
    assert len(tracks) == 1


def test_small_movement_keeps_same_track_id():
    tracker = CentroidTracker(max_distance=50)
    tracks = tracker.update([make_det(100, 100)])
    first_id = list(tracks.keys())[0]

    tracks = tracker.update([make_det(108, 102)])  # small move
    second_id = list(tracks.keys())[0]

    assert first_id == second_id


def test_large_jump_creates_new_track_not_reuse():
    tracker = CentroidTracker(max_distance=30)
    tracks = tracker.update([make_det(100, 100)])
    first_id = list(tracks.keys())[0]

    # Object far away appears; should NOT be matched to the first track
    tracks = tracker.update([make_det(500, 500)])
    assert first_id not in tracks
    assert len(tracks) == 1


def test_track_removed_after_max_disappeared_frames():
    tracker = CentroidTracker(max_distance=50, max_disappeared=2)
    tracker.update([make_det(100, 100)])

    tracker.update([])  # missed frame 1
    tracker.update([])  # missed frame 2
    tracks = tracker.update([])  # missed frame 3 -> should be dropped

    assert len(tracker.tracks) == 0
    assert len(tracks) == 0


def test_different_labels_do_not_match_each_other():
    tracker = CentroidTracker(max_distance=100)
    tracker.update([make_det(100, 100, label="car")])
    tracks = tracker.update([make_det(105, 105, label="pedestrian")])

    # Should be a new track, not matched to the "car" track
    labels = {t.label for t in tracks.values()}
    assert "pedestrian" in labels
    assert len(tracker.tracks) == 2
