"""Click two points on the first frame of a video to choose the counting line.

  python pick_line.py unloading.mp4

Click once at each end of the line across the door, then press any key.
It prints the --line values to use with dock_counter.py.
"""
import sys

import cv2

points = []


def on_click(event, x, y, flags, frame):
    if event == cv2.EVENT_LBUTTONDOWN and len(points) < 2:
        points.append((x, y))
        cv2.circle(frame, (x, y), 6, (0, 0, 255), -1)
        if len(points) == 2:
            cv2.line(frame, points[0], points[1], (0, 0, 255), 3)
        cv2.imshow("pick line", frame)


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: python pick_line.py video.mp4")
    cap = cv2.VideoCapture(sys.argv[1])
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise SystemExit("Could not read the video")
    cv2.imshow("pick line", frame)
    cv2.setMouseCallback("pick line", on_click, frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    if len(points) == 2:
        (x1, y1), (x2, y2) = points
        print(f"--line {x1} {y1} {x2} {y2}")
    else:
        print("Click two points next time.")


if __name__ == "__main__":
    main()
