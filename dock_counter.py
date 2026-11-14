"""Count goods crossing a line in a video or camera stream (loading / unloading).

Usage examples:
  python dock_counter.py --source unloading.mp4 --line 100 400 1180 400
  python dock_counter.py --source rtsp://user:pass@192.168.1.20/stream1 \
      --model bags.pt --line 100 400 1180 400 --picking WH/IN/00012 --push

--line x1 y1 x2 y2 : the virtual line across the door or dock, in pixels.
"In" = crossing from one side to the other; if counts come out reversed,
swap the two points.

A standard YOLO model does NOT know what a sack or carton is. Train your own
model on photos of your bags and cartons (see README) and pass it with --model.
"""
import argparse
import os
import time
from datetime import datetime

import cv2
from ultralytics import YOLO

from line_counter import LineCounter


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--source", required=True, help="video file, camera index or RTSP URL")
    p.add_argument("--model", default="yolo11n.pt", help="YOLO weights (your trained bags.pt)")
    p.add_argument("--classes", type=int, nargs="*", default=None,
                   help="class ids to count (default: all classes in the model)")
    p.add_argument("--line", type=int, nargs=4, required=True, metavar=("X1", "Y1", "X2", "Y2"))
    p.add_argument("--conf", type=float, default=0.4, help="minimum detection confidence")
    p.add_argument("--show", action="store_true", help="show a live window")
    p.add_argument("--save-dir", default="runs", help="folder for snapshots and summary")
    p.add_argument("--picking", help="Odoo transfer reference, e.g. WH/IN/00012")
    p.add_argument("--push", action="store_true", help="post the result to the Odoo transfer")
    return p.parse_args()


def main():
    args = parse_args()
    source = int(args.source) if args.source.isdigit() else args.source
    os.makedirs(args.save_dir, exist_ok=True)

    model = YOLO(args.model)
    a, b = (args.line[0], args.line[1]), (args.line[2], args.line[3])
    counter = LineCounter(a, b)

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise SystemExit(f"Could not open source: {args.source}")

    started = datetime.now()
    last_frame = None
    while True:
        ok, frame = cap.read()
        if not ok:
            break  # end of file or lost stream
        last_frame = frame

        # persist=True keeps the same ID for the same object across frames.
        result = model.track(frame, persist=True, conf=args.conf,
                             classes=args.classes, tracker="bytetrack.yaml",
                             verbose=False)[0]

        if result.boxes is not None and result.boxes.id is not None:
            boxes = result.boxes.xyxy.cpu().numpy()
            ids = result.boxes.id.int().cpu().tolist()
            for (x1, y1, x2, y2), track_id in zip(boxes, ids):
                centre = (float((x1 + x2) / 2), float((y1 + y2) / 2))
                event = counter.update(track_id, centre)
                if args.show:
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 200, 0), 2)
                    cv2.putText(frame, str(track_id), (int(x1), int(y1) - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 2)
                if event:
                    # Keep a photo of every counted item as evidence.
                    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    cv2.imwrite(os.path.join(args.save_dir, f"{event}_{track_id}_{stamp}.jpg"), frame)

        if args.show:
            cv2.line(frame, a, b, (0, 0, 255), 3)
            cv2.putText(frame, f"IN {counter.in_count}  OUT {counter.out_count}",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
            cv2.imshow("dock counter", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()

    summary = (f"Started {started:%Y-%m-%d %H:%M}, finished {datetime.now():%H:%M}. "
               f"In: {counter.in_count}, Out: {counter.out_count}, Net: {counter.net}")
    print(summary)
    with open(os.path.join(args.save_dir, "summary.txt"), "w") as f:
        f.write(summary + "\n")
    snapshot = os.path.join(args.save_dir, "last_frame.jpg")
    if last_frame is not None:
        cv2.imwrite(snapshot, last_frame)

    if args.push:
        if not args.picking:
            raise SystemExit("--push needs --picking")
        from odoo_push import post_count_to_picking
        counted = counter.in_count if "/IN/" in args.picking else counter.out_count
        post_count_to_picking(args.picking, counted, snapshot if last_frame is not None else None)


if __name__ == "__main__":
    main()
