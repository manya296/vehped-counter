# System Architecture & Design

## 1. Architecture Overview

The pipeline is split into independent, single-responsibility modules.
Each stage only depends on the data structures produced by the stage
before it, which keeps every module independently testable.

```mermaid
flowchart TD
    A[Input Video File] --> B[VideoProcessor]
    B --> C[VehiclePedestrianDetector]
    C -->|Detections: box, label, confidence| D[CentroidTracker]
    D -->|Active Tracks: id, label, centroid, history| E[LineCounter]
    E -->|Updated in/out counts| F[Visualizer]
    F --> G[Annotated MP4 Video]
    D --> H[CsvLogger]
    H --> I[detections_log.csv]
    E --> J[Summary Builder]
    J --> K[count_summary.json]
```

## 2. Component Responsibilities

| Module | File | Responsibility |
|---|---|---|
| `VehiclePedestrianDetector` | `src/detector.py` | Wraps YOLO; filters to relevant classes; returns `Detection` objects |
| `CentroidTracker` | `src/tracker.py` | Associates detections across frames into persistent `Track` objects |
| `LineCounter` | `src/counter.py` | Detects line crossings per track and tallies directional counts by class |
| `Visualizer` | `src/visualizer.py` | Draws boxes, IDs, trails, the line, and the HUD panel |
| `CsvLogger` / `exporter.py` | `src/exporter.py` | Writes per-frame CSV rows and the final JSON summary |
| `VideoProcessor` | `src/video_processor.py` | Orchestrates the frame loop, wiring all modules together |
| `main.py` | `main.py` | CLI argument parsing and headless entry point |

## 3. Process Flow / Workflow Diagram

```mermaid
flowchart TD
    Start([Start CLI]) --> Validate{Input video exists?}
    Validate -- No --> Fail[Print error, exit 1]
    Validate -- Yes --> Open[Open video, read FPS/resolution]
    Open --> Loop{More frames?}
    Loop -- No --> Summary[Build & write JSON summary]
    Summary --> End([End])
    Loop -- Yes --> Detect[Run YOLO detection]
    Detect --> Track[Update centroid tracker]
    Track --> Count[Check line crossings]
    Count --> Draw[Draw overlays]
    Draw --> Write[Write video frame + CSV row]
    Write --> Loop
```

## 4. Use Case Diagram

```mermaid
flowchart LR
    User((User / Evaluator))
    User --> UC1[Provide input video via CLI]
    User --> UC2[Configure counting line orientation & position]
    User --> UC3[Run headless processing]
    UC3 --> UC4[Generate annotated video]
    UC3 --> UC5[Generate CSV observation log]
    UC3 --> UC6[Generate JSON count summary]
    User --> UC7[Run automated test suite]
```

## 5. Sequence Diagram

```mermaid
sequenceDiagram
    participant U as User (CLI)
    participant M as main.py
    participant VP as VideoProcessor
    participant D as Detector
    participant T as Tracker
    participant C as Counter
    participant V as Visualizer
    participant E as Exporter

    U->>M: python main.py --input video.mp4
    M->>VP: run(input_path)
    loop for each frame
        VP->>D: detect(frame)
        D-->>VP: List[Detection]
        VP->>T: update(detections)
        T-->>VP: Dict[track_id, Track]
        VP->>C: update(tracks)
        C-->>VP: updated counts
        VP->>V: draw_tracks / draw_line / draw_hud
        VP->>E: log_frame(frame_index, tracks)
    end
    VP->>E: build_summary() / write_summary()
    VP-->>M: summary dict
    M-->>U: print JSON summary
```

## 6. Class / Component Diagram

```mermaid
classDiagram
    class Detection {
        +box: Tuple
        +label: str
        +confidence: float
        +centroid: Tuple
    }

    class VehiclePedestrianDetector {
        -model
        -confidence: float
        -class_map: dict
        +detect(frame) List~Detection~
    }

    class Track {
        +track_id: int
        +label: str
        +centroid: Tuple
        +box: Tuple
        +disappeared: int
        +history: List
        +update_position(centroid, box)
    }

    class CentroidTracker {
        -max_distance: float
        -max_disappeared: int
        -tracks: Dict
        +update(detections) Dict~Track~
    }

    class LineCounter {
        +orientation: str
        +position_fraction: float
        +counts: Dict
        +update(tracks)
        +grand_total() int
    }

    class VideoProcessor {
        -detector: VehiclePedestrianDetector
        -tracker: CentroidTracker
        +run(input_path) dict
    }

    VehiclePedestrianDetector --> Detection : produces
    CentroidTracker --> Track : manages
    VideoProcessor --> VehiclePedestrianDetector
    VideoProcessor --> CentroidTracker
    VideoProcessor --> LineCounter
    LineCounter --> Track : reads
```

## 7. Output Schemas

### `detections_log.csv`

| Column | Type | Description |
|---|---|---|
| frame | int | Zero-indexed frame number |
| track_id | int | Persistent tracker ID |
| label | str | Object class (`car`, `pedestrian`, etc.) |
| x, y | int | Top-left corner of bounding box |
| width, height | int | Bounding box dimensions |

### `count_summary.json`

```json
{
  "frames_processed": 300,
  "total_crossings": 42,
  "crossings_by_class": {
    "car": {"in": 20, "out": 15, "total": 35},
    "pedestrian": {"in": 4, "out": 3, "total": 7}
  },
  "line_orientation": "horizontal",
  "line_position_fraction": 0.5,
  "input_resolution": "1280x720",
  "video_fps": 25.0,
  "processing_seconds": 18.4,
  "output_video": "outputs/annotated_video.mp4",
  "csv_log": "outputs/detections_log.csv"
}
```

## 8. Error Handling & Robustness

- Missing input file → prints a clear stderr message and exits with code `1`
  instead of raising an unhandled traceback.
- Unreadable/corrupt video → `VideoProcessor.run` raises a `RuntimeError`
  that `main.py` catches and reports cleanly.
- No GUI dependency by default (`--show` is opt-in only), and
  `QT_QPA_PLATFORM=offscreen` is set before any OpenCV window code can run,
  so the pipeline works on headless grading servers.
