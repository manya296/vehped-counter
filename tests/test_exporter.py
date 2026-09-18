import sys
import os
import json
import csv
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.counter import LineCounter
from src.tracker import Track
from src.exporter import CsvLogger, build_summary, write_summary


def test_csv_logger_writes_expected_rows(tmp_path):
    out_path = os.path.join(tmp_path, "log.csv")
    logger = CsvLogger(out_path)

    track = Track(track_id=1, label="car", centroid=(50, 50), box=(40, 40, 60, 60))
    logger.log_frame(0, {1: track})
    logger.close()

    with open(out_path) as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 1
    assert rows[0]["label"] == "car"
    assert rows[0]["frame"] == "0"


def test_build_summary_matches_counter_state():
    counter = LineCounter(frame_width=200, frame_height=200)
    counter.counts["car"] = {"in": 3, "out": 1}
    counter.counts["pedestrian"] = {"in": 0, "out": 2}

    summary = build_summary(counter, frames_processed=100, video_meta={"video_fps": 30})

    assert summary["frames_processed"] == 100
    assert summary["crossings_by_class"]["car"]["total"] == 4
    assert summary["total_crossings"] == 6
    assert summary["video_fps"] == 30


def test_write_summary_creates_valid_json(tmp_path):
    out_path = os.path.join(tmp_path, "summary.json")
    write_summary(out_path, {"a": 1})

    with open(out_path) as f:
        data = json.load(f)
    assert data == {"a": 1}
