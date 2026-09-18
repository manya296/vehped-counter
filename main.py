#!/usr/bin/env python3
"""
main.py
-------
Headless command-line entry point for the Vehicle & Pedestrian Line-Crossing
Counter. Run `python main.py --help` for all options.

Example:
    python main.py --input data/sample.mp4 --line-orientation horizontal \
        --line-position 0.5 --max-frames 300
"""

import argparse
import json
import os
import sys

# Force headless-safe backend before any cv2/Qt window code can run.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from src.detector import VehiclePedestrianDetector
from src.tracker import CentroidTracker
from src.video_processor import VideoProcessor


def parse_args():
    parser = argparse.ArgumentParser(
        description="Vehicle & Pedestrian Line-Crossing Counter (headless CLI)"
    )
    parser.add_argument("--input", required=True, help="Path to input video file")
    parser.add_argument("--output-dir", default="outputs", help="Directory for output files")
    parser.add_argument("--model", default="yolov8n.pt", help="YOLO model weights")
    parser.add_argument("--conf", type=float, default=0.35, help="Detection confidence threshold")
    parser.add_argument("--imgsz", type=int, default=640, help="Inference image size")
    parser.add_argument("--device", default="cpu", help="Inference device: cpu, cuda, or index")
    parser.add_argument("--line-orientation", choices=["horizontal", "vertical"],
                         default="horizontal", help="Orientation of the counting line")
    parser.add_argument("--line-position", type=float, default=0.5,
                         help="Line position as a fraction (0.0-1.0) of frame height/width")
    parser.add_argument("--max-distance", type=float, default=80.0,
                         help="Max pixel distance for centroid track matching")
    parser.add_argument("--max-disappeared", type=int, default=15,
                         help="Frames a track may go unmatched before being dropped")
    parser.add_argument("--skip", type=int, default=0,
                         help="Number of frames to skip between processed frames")
    parser.add_argument("--max-frames", type=int, default=None,
                         help="Stop after processing this many frames (omit for full video)")
    parser.add_argument("--show", action="store_true",
                         help="Open a live preview window (local debugging only, not for headless eval)")
    return parser.parse_args()


def main():
    args = parse_args()

    if not os.path.isfile(args.input):
        print(f"[ERROR] Input video not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    detector = VehiclePedestrianDetector(
        model_path=args.model,
        confidence=args.conf,
        imgsz=args.imgsz,
        device=args.device,
    )
    tracker = CentroidTracker(
        max_distance=args.max_distance,
        max_disappeared=args.max_disappeared,
    )
    processor = VideoProcessor(
        detector=detector,
        tracker=tracker,
        output_dir=args.output_dir,
        line_orientation=args.line_orientation,
        line_position=args.line_position,
        skip=args.skip,
        max_frames=args.max_frames,
        show=args.show,
    )

    print(f"[CLI] Starting processing: {args.input}")
    try:
        summary = processor.run(args.input)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)

    print("[CLI] Done. Summary:")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
