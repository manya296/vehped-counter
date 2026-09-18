import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.counter import LineCounter
from src.tracker import Track


def make_track(track_id, label, centroid, history):
    t = Track(track_id=track_id, label=label, centroid=centroid, box=(0, 0, 10, 10))
    t.history = history
    return t


def test_crossing_downward_counts_as_in():
    counter = LineCounter(orientation="horizontal", position_fraction=0.5,
                           frame_width=200, frame_height=200)
    # line is at y=100; object moves from y=90 (above) to y=110 (below)
    track = make_track(1, "car", centroid=(50, 110), history=[(50, 90)])
    counter.update({1: track})

    assert counter.counts["car"]["in"] == 1
    assert counter.counts["car"]["out"] == 0


def test_crossing_upward_counts_as_out():
    counter = LineCounter(orientation="horizontal", position_fraction=0.5,
                           frame_width=200, frame_height=200)
    track = make_track(1, "car", centroid=(50, 90), history=[(50, 110)])
    counter.update({1: track})

    assert counter.counts["car"]["out"] == 1


def test_no_crossing_does_not_count():
    counter = LineCounter(orientation="horizontal", position_fraction=0.5,
                           frame_width=200, frame_height=200)
    # both points on the same side of the line (y=100)
    track = make_track(1, "car", centroid=(50, 60), history=[(50, 40)])
    counter.update({1: track})

    assert counter.grand_total() == 0


def test_same_track_not_counted_twice():
    counter = LineCounter(orientation="horizontal", position_fraction=0.5,
                           frame_width=200, frame_height=200)
    track = make_track(1, "pedestrian", centroid=(50, 110), history=[(50, 90)])
    counter.update({1: track})
    # simulate the same track lingering near/past the line on subsequent frames
    track.history = [(50, 110)]
    track.centroid = (50, 115)
    counter.update({1: track})

    assert counter.total_by_label("pedestrian") == 1


def test_vertical_line_orientation():
    counter = LineCounter(orientation="vertical", position_fraction=0.5,
                           frame_width=200, frame_height=200)
    # line at x=100; object moves left-to-right
    track = make_track(1, "bicycle", centroid=(110, 50), history=[(90, 50)])
    counter.update({1: track})

    assert counter.counts["bicycle"]["in"] == 1
