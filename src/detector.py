"""
detector.py
-----------
Wraps a YOLO object-detection model and exposes a single, simple method
(`detect`) that returns only the object classes this project cares about
(people and road vehicles), each with a bounding box, class name, and
confidence score.

Keeping this logic in its own module means the rest of the pipeline
(tracking, counting, exporting) never has to know anything about YOLO,
COCO class indices, or the Ultralytics API. If the detection backend is
ever swapped out, only this file changes.
"""

from dataclasses import dataclass
from typing import List, Tuple


# COCO class names we care about for this project, and the label we want
# to show/store for each. Restricting to this set means a person walking
# past in the background doesn't get treated as "pedestrian traffic"
# unless that is actually the intent, and unrelated COCO classes
# (e.g. "backpack", "traffic light") are dropped immediately.
DEFAULT_CLASS_MAP = {
    "person": "pedestrian",
    "car": "car",
    "bus": "bus",
    "truck": "truck",
    "motorcycle": "motorcycle",
    "bicycle": "bicycle",
}


@dataclass
class Detection:
    """A single detected object in one frame."""
    box: Tuple[int, int, int, int]   # (x1, y1, x2, y2) in pixel coordinates
    label: str                       # mapped label, e.g. "car", "pedestrian"
    confidence: float

    @property
    def centroid(self) -> Tuple[int, int]:
        x1, y1, x2, y2 = self.box
        return ((x1 + x2) // 2, (y1 + y2) // 2)


class VehiclePedestrianDetector:
    """
    Thin wrapper around a YOLO model, filtered to the classes relevant to
    vehicle/pedestrian counting.

    Parameters
    ----------
    model_path : str
        Path or name of the YOLO weights (e.g. "yolov8n.pt"). Ultralytics
        will download this automatically the first time it is used.
    confidence : float
        Minimum confidence score required to keep a detection.
    imgsz : int
        Inference resolution passed to the model.
    device : str
        "cpu", "cuda", or a specific device index as a string.
    class_map : dict
        Maps COCO class names to the label used throughout this project.
        Any COCO class not present in this map is discarded.
    """

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        confidence: float = 0.35,
        imgsz: int = 640,
        device: str = "cpu",
        class_map: dict = None,
    ):
        self.confidence = confidence
        self.imgsz = imgsz
        self.device = device
        self.class_map = class_map or DEFAULT_CLASS_MAP
        self._model = None
        self._model_path = model_path

    def _ensure_model_loaded(self):
        if self._model is None:
            from ultralytics import YOLO
            self._model = YOLO(self._model_path)

    def detect(self, frame) -> List[Detection]:
        """
        Run detection on a single BGR frame (as read by OpenCV) and return
        a list of Detection objects for the classes we track.
        """
        self._ensure_model_loaded()

        results = self._model.predict(
            frame,
            imgsz=self.imgsz,
            conf=self.confidence,
            device=self.device,
            verbose=False,
        )

        detections: List[Detection] = []
        if not results:
            return detections

        result = results[0]
        names = result.names  # {class_index: coco_name}

        for box in result.boxes:
            class_index = int(box.cls[0])
            coco_name = names.get(class_index, "")
            mapped_label = self.class_map.get(coco_name)
            if mapped_label is None:
                continue  # not a class we track

            confidence = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detections.append(
                Detection(
                    box=(int(x1), int(y1), int(x2), int(y2)),
                    label=mapped_label,
                    confidence=confidence,
                )
            )

        return detections
