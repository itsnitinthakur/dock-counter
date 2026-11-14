"""Check that you can read a CP Plus camera or recorder stream, and save one frame.

  python test_stream.py "rtsp://USER:PASS@192.168.1.108:554/cam/realmonitor?channel=1&subtype=1"

subtype=1 is the smaller sub stream (good for testing); subtype=0 is the full-quality main stream.
If the password has special characters (@ : / #), URL-encode them, e.g. @ becomes %40.
"""
import os
import sys
import time

# Use TCP for RTSP; it's more reliable than UDP on most networks.
os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp")

import cv2  # noqa: E402  (import after setting the option)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    url = sys.argv[1]
    start = time.time()
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        raise SystemExit("Could not open the stream. Check IP, port 554, user, password and channel.")
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise SystemExit("Connected but got no frame. Try subtype=1 or another channel.")
    h, w = frame.shape[:2]
    cv2.imwrite("stream_test.jpg", frame)
    print(f"OK: {w}x{h} frame saved to stream_test.jpg in {time.time() - start:.1f} s")


if __name__ == "__main__":
    main()
