"""
exporter.py
-----------
Handles all structured output: a per-frame CSV observation log and a
consolidated JSON summary written once processing finishes. Kept
separate from the main loop so the output schema can change without
touching detection, tracking, or counting logic.
"""

import csv
import json
import os


class CsvLogger:
    """Writes one row per tracked object per frame to a CSV file."""

    FIELDNAMES = ["frame", "track_id", "label", "x", "y", "width", "height"]

    def __init__(self, output_path: str):
        self.output_path = output_path
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self._file = open(output_path, "w", newline="")
        self._writer = csv.DictWriter(self._file, fieldnames=self.FIELDNAMES)
        self._writer.writeheader()

    def log_frame(self, frame_index, tracks):
        for track_id, track in tracks.items():
            x1, y1, x2, y2 = track.box
            self._writer.writerow({
                "frame": frame_index,
                "track_id": track_id,
                "label": track.label,
                "x": x1,
                "y": y1,
                "width": x2 - x1,
                "height": y2 - y1,
            })

    def close(self):
        self._file.close()


def write_summary(output_path: str, summary: dict):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)


def build_summary(counter, frames_processed: int, video_meta: dict) -> dict:
    by_label = {
        label: {"in": c["in"], "out": c["out"], "total": c["in"] + c["out"]}
        for label, c in counter.counts.items()
    }
    return {
        "frames_processed": frames_processed,
        "total_crossings": counter.grand_total(),
        "crossings_by_class": by_label,
        "line_orientation": counter.orientation,
        "line_position_fraction": counter.position_fraction,
        **video_meta,
    }
