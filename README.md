# Vehicle & Pedestrian Line-Crossing Counter

A headless, command-line-only computer vision pipeline that detects, tracks,
and counts vehicles and pedestrians as they cross a virtual line drawn
across a video (e.g. a footpath, a road lane, or an entrance/exit point).

Built for **CSE3010 — Computer Vision** as an original flipped-course project.

---

## Overview

The system reads a video file, detects people and road vehicles frame by
frame using a YOLO object detector, tracks each object across frames using
a lightweight centroid tracker, and increments a directional counter every
time a tracked object crosses a configurable virtual line. It produces:

- An annotated MP4 video with bounding boxes, track IDs, motion trails,
  the counting line, and a live counts overlay.
- A CSV log of every tracked object's position in every frame.
- A JSON summary of total and per-class crossing counts.

## Features

- Multi-class detection: `pedestrian`, `car`, `bus`, `truck`, `motorcycle`, `bicycle`
- Centroid-distance multi-object tracking with configurable matching distance
  and track-loss tolerance
- Configurable counting line (horizontal or vertical, positioned anywhere
  in the frame) with per-class **in/out** directional counts
- Fully headless execution — no GUI window is required or opened by default
- Frame-skipping support for faster processing on CPU
- 13 automated unit tests covering tracking, counting, and export logic

## Technologies / Tools Used

- Python 3.10+
- [Ultralytics YOLO](https://docs.ultralytics.com/) (YOLOv8n) for object detection
- OpenCV (headless build) for video I/O and drawing
- pytest for automated testing

## Repository Structure

```
vehped-counter/
├── main.py                    # CLI entry point
├── requirements.txt
├── README.md
├── statement.md
├── src/
│   ├── detector.py            # YOLO wrapper, class filtering
│   ├── tracker.py             # Centroid-distance multi-object tracker
│   ├── counter.py             # Line-crossing directional counter
│   ├── visualizer.py          # Drawing / HUD overlay
│   ├── video_processor.py     # Pipeline orchestrator
│   └── exporter.py            # CSV/JSON export
├── tests/
│   ├── test_tracker.py
│   ├── test_counter.py
│   └── test_exporter.py
├── data/                      # Place input videos here
├── outputs/                   # Generated video/CSV/JSON land here
├── docs/
│   └── ARCHITECTURE.md        # Diagrams: architecture, workflow, UML
└── report/
    └── PROJECT_REPORT.md
```

## Setup & Installation

Assumes Python 3.10+ and no prior context about this project.

```bash
# 1. Clone the repository
git clone https://github.com/manya296/vehped-counter
cd vehped-counter

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

The first run will automatically download the YOLOv8n weights
(`yolov8n.pt`, ~6 MB) via Ultralytics — no manual model download needed.

## Running the Project

Place a video in `data/` (any traffic, footpath, or entrance-camera clip
works), then run:

```bash
python main.py --input data/your_video.mp4 --output-dir outputs
```

This runs fully headless — no window is opened, and progress is printed
to stdout. Outputs appear in `outputs/`:

- `outputs/annotated_video.mp4`
- `outputs/detections_log.csv`
- `outputs/count_summary.json`

### Useful options

```bash
# Vertical line at the horizontal midpoint of the frame
python main.py --input data/your_video.mp4 --line-orientation vertical --line-position 0.5

# Faster processing on long/high-res video by skipping every other frame
python main.py --input data/your_video.mp4 --skip 1

# Limit to the first 300 frames (useful for quick evaluation)
python main.py --input data/your_video.mp4 --max-frames 300

# Optional local preview window (NOT used in headless evaluation)
python main.py --input data/your_video.mp4 --show
```

Run `python main.py --help` for the full list of CLI flags.

## Testing

```bash
python -m pytest -v
```

Expected output: `13 passed`.

Tests cover:
- Tracker: new-track creation, ID persistence under small motion, correct
  rejection of far-away detections, track expiry after disappearance,
  and label-aware matching.
- Counter: directional crossing detection for both horizontal and vertical
  lines, no double-counting, and no false counts when an object doesn't
  cross the line.
- Exporter: CSV row correctness and JSON summary structure.

## Screenshots

See `docs/ARCHITECTURE.md` for pipeline diagrams. Run the project on a
sample video to generate your own annotated output for screenshots.
