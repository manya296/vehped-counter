# Project Statement

## Title
**Vehicle & Pedestrian Line-Crossing Counter**

## Course
CSE3010 — Computer Vision

---

## 1. Problem Statement

Counting how many people or vehicles pass a fixed point — a doorway, a
footpath, a single road lane — is a common but tedious manual task. Simple
turnstile or sensor-based counters can't distinguish between object types
(a pedestrian vs. a bicycle vs. a car) and can't be retrofitted onto
existing CCTV or webcam footage.

This project builds an automated computer vision system that ingests
ordinary video, detects and classifies people and vehicles, tracks each
one across frames, and counts directional crossings of a configurable
virtual line — entirely from the command line, with no GUI dependency.

## 2. Scope of the Project

- **Input**: A single fixed-camera video file (any common format OpenCV
  can decode — mp4, avi, mov).
- **Detected classes**: pedestrian, car, bus, truck, motorcycle, bicycle.
- **Counting model**: A single virtual line (horizontal or vertical,
  positioned anywhere in the frame) with directional (in/out) counts
  tracked separately per object class.
- **Execution environment**: Headless CLI only — designed to run in
  terminals, SSH sessions, and automated grading environments without a
  display server.
- **Exclusions**: Multi-camera handoff, real-world speed/velocity
  estimation, and live camera-stream ingestion are out of scope — the
  project focuses on detection, tracking, and line-crossing counting from
  a single recorded video.

## 3. Target Users

1. **Small business / building owners** wanting simple footfall counts
   without expensive dedicated hardware.
2. **Students and researchers** studying multi-object detection and
   tracking pipelines on standard CPU hardware.
3. **Traffic or urban-planning enthusiasts** wanting a lightweight way to
   estimate vehicle/pedestrian volume at a location from existing footage.

## 4. High-Level Features

- YOLO-based multi-class object detection restricted to relevant classes.
- Lightweight centroid-distance multi-object tracker with configurable
  matching distance and track-loss tolerance.
- Configurable directional line-crossing counter, counted once per track
  to avoid double-counting.
- Annotated video output with bounding boxes, track IDs, motion trails,
  the counting line, and a live count HUD.
- CSV per-frame observation log and a JSON summary report.
- Fully headless execution with graceful error handling for missing or
  unreadable input files.
- Automated test suite (pytest) covering tracking and counting logic.
