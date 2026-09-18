"""
video_processor.py
-------------------
Orchestrates the full pipeline: reads frames from the input video, runs
detection -> tracking -> counting -> visualization -> export for each
frame, and writes the annotated output video, CSV log, and JSON summary.

This module contains no detection, tracking, or counting logic itself —
it only wires the other modules together in the right order. Each stage
is unaware of the others, which is what makes the individual modules
easy to test in isolation (see tests/).
"""

import os
import time

import cv2

from src.counter import LineCounter
from src.exporter import CsvLogger, build_summary, write_summary
from src.visualizer import draw_hud, draw_line, draw_tracks


class VideoProcessor:
    def __init__(self, detector, tracker, output_dir: str,
                 line_orientation: str = "horizontal",
                 line_position: float = 0.5,
                 skip: int = 0,
                 max_frames: int = None,
                 show: bool = False):
        self.detector = detector
        self.tracker = tracker
        self.output_dir = output_dir
        self.line_orientation = line_orientation
        self.line_position = line_position
        self.skip = skip
        self.max_frames = max_frames
        self.show = show

    def run(self, input_path: str) -> dict:
        if not os.path.isfile(input_path):
            raise FileNotFoundError(f"Input video not found: {input_path}")

        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video file: {input_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        counter = LineCounter(
            orientation=self.line_orientation,
            position_fraction=self.line_position,
            frame_width=width,
            frame_height=height,
        )

        video_out_path = os.path.join(self.output_dir, "annotated_video.mp4")
        csv_out_path = os.path.join(self.output_dir, "detections_log.csv")
        summary_out_path = os.path.join(self.output_dir, "count_summary.json")

        os.makedirs(self.output_dir, exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(video_out_path, fourcc, fps, (width, height))
        csv_logger = CsvLogger(csv_out_path)

        frame_index = 0
        processed_count = 0
        start_time = time.time()

        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                if self.skip > 0 and frame_index % (self.skip + 1) != 0:
                    frame_index += 1
                    continue

                detections = self.detector.detect(frame)
                tracks = self.tracker.update(detections)
                counter.update(tracks)

                frame = draw_line(frame, counter)
                frame = draw_tracks(frame, tracks)
                frame = draw_hud(frame, counter, frame_index, len(tracks))

                writer.write(frame)
                csv_logger.log_frame(frame_index, tracks)

                if self.show:
                    cv2.imshow("Vehicle & Pedestrian Counter", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break

                processed_count += 1
                if processed_count % 50 == 0:
                    print(f"[CLI] Processed {processed_count} frames | "
                          f"Active: {len(tracks)} | "
                          f"Total crossings: {counter.grand_total()}")

                frame_index += 1
                if self.max_frames and processed_count >= self.max_frames:
                    break
        finally:
            cap.release()
            writer.release()
            csv_logger.close()
            if self.show:
                cv2.destroyAllWindows()

        elapsed = time.time() - start_time
        summary = build_summary(
            counter,
            frames_processed=processed_count,
            video_meta={
                "input_resolution": f"{width}x{height}",
                "video_fps": fps,
                "processing_seconds": round(elapsed, 2),
                "output_video": video_out_path,
                "csv_log": csv_out_path,
            },
        )
        write_summary(summary_out_path, summary)
        return summary
