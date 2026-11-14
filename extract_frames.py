"""Save every Nth frame of a video as a JPG, for labelling.

  python extract_frames.py unloading.mp4 --every 15 --out frames
"""
import argparse
import os

import cv2


def extract(video, out_dir, every=15):
    os.makedirs(out_dir, exist_ok=True)
    cap = cv2.VideoCapture(video)
    if not cap.isOpened():
        raise SystemExit(f"Could not open {video}")
    name = os.path.splitext(os.path.basename(video))[0]
    index = saved = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if index % every == 0:
            cv2.imwrite(os.path.join(out_dir, f"{name}_{index:06d}.jpg"), frame)
            saved += 1
        index += 1
    cap.release()
    return saved


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("--every", type=int, default=15, help="keep 1 frame in N (15 = 2 per second at 30 fps)")
    p.add_argument("--out", default="frames")
    a = p.parse_args()
    print(f"Saved {extract(a.video, a.out, a.every)} frames to {a.out}/")
