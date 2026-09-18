"""
visualizer.py
-------------
Draws everything the annotated output video needs: bounding boxes with
track IDs, short motion trails, the counting line, and a heads-up
display (HUD) panel summarising counts by class. Kept separate from
video_processor.py so the drawing logic can be tweaked or unit-tested
without touching the frame-reading loop.
"""

import cv2

BOX_COLOR = (60, 200, 60)
LINE_COLOR = (0, 165, 255)
TEXT_COLOR = (255, 255, 255)
HUD_BG = (30, 30, 30)


def draw_tracks(frame, tracks):
    for track_id, track in tracks.items():
        x1, y1, x2, y2 = track.box
        cv2.rectangle(frame, (x1, y1), (x2, y2), BOX_COLOR, 2)
        label_text = f"#{track_id} {track.label}"
        cv2.putText(
            frame, label_text, (x1, max(y1 - 8, 0)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, BOX_COLOR, 2,
        )
        # motion trail
        points = track.history[-15:] + [track.centroid]
        for i in range(1, len(points)):
            cv2.line(frame, points[i - 1], points[i], BOX_COLOR, 1)
    return frame


def draw_line(frame, counter):
    line_pos = counter.line_pixel_position()
    if counter.orientation == "horizontal":
        cv2.line(frame, (0, line_pos), (counter.frame_width, line_pos), LINE_COLOR, 2)
    else:
        cv2.line(frame, (line_pos, 0), (line_pos, counter.frame_height), LINE_COLOR, 2)
    return frame


def draw_hud(frame, counter, frame_index, active_count):
    panel_height = 30 + 22 * (len(counter.counts) + 2)
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (330, panel_height), HUD_BG, -1)
    frame[:] = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)

    y = 22
    cv2.putText(frame, f"Frame {frame_index} | Active: {active_count}",
                (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, TEXT_COLOR, 1)
    y += 22
    cv2.putText(frame, f"Total crossings: {counter.grand_total()}",
                (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, TEXT_COLOR, 1)
    for label, c in counter.counts.items():
        y += 22
        cv2.putText(
            frame, f"{label}: in={c['in']} out={c['out']}",
            (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, TEXT_COLOR, 1,
        )
    return frame
