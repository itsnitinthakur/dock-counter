"""Count items (boxes, rolls, bags) crossing a line, automatically, with no training needed.

Uses an open-vocabulary model (YOLO-World): you describe the object in words
("paper roll") and it finds it. Each roll is tracked and counted once when it
crosses the line you draw across the entrance.

Boxes loaded into a truck (draw the line across the truck's loading door;
the truck side should be the "in" side, so swap the points if counts come out reversed):
  python item_counter.py --source loading.mp4 --line 100 400 1180 400 --item box \
      --prompt "cardboard box" --show

Paper rolls unloaded into the store:
  python item_counter.py --source inbound.mp4 --line 100 400 1180 400 --item roll \
      --prompt "paper roll" --show

Outputs (in runs_<item>/ by default):
  <items>.csv        one row per counted item: number, time in video, direction, photo
  <item>_001.jpg ... frame at the moment each item crossed, with the item boxed
  summary.txt        total in, total out, net, first and last time

If items are missed, try --conf 0.1 or another --prompt ("box", "brown carton",
"cardboard box carried by a person"). For best accuracy later, train a custom
model on your own images and pass it with --model best.pt.
"""
import argparse
import csv
import os

# RTSP over TCP is more reliable for CCTV streams (CP Plus etc.).
os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp")

import cv2  # noqa: E402
from ultralytics import YOLO  # noqa: E402

from line_counter import LineCounter  # noqa: E402


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--source", required=True, help="video file or RTSP URL")
    p.add_argument("--line", type=int, nargs=4, required=True, metavar=("X1", "Y1", "X2", "Y2"))
    p.add_argument("--item", default="box", help="name used in files and on screen: box, roll, bag")
    p.add_argument("--prompt", nargs="+", default=None,
                   help="what to look for, in words (open-vocabulary model only)")
    p.add_argument("--model", default="yolov8s-worldv2.pt",
                   help="yolov8s-worldv2.pt (words) or your own trained best.pt")
    p.add_argument("--conf", type=float, default=0.15, help="detection confidence threshold")
    p.add_argument("--stride", type=int, default=1, help="process every Nth frame (2 = twice as fast)")
    p.add_argument("--out", default=None, help="output folder (default runs_<item>)")
    p.add_argument("--show", action="store_true", help="show a live window (press q to stop)")
    return p.parse_args()


def fmt_time(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def main():
    args = parse_args()
    item = args.item.strip().lower()
    label = item.capitalize()
    plural = item + ("es" if item.endswith(("x", "s", "sh", "ch")) else "s")
    plural_label = plural.capitalize()
    prompt = args.prompt or {"box": ["cardboard box"], "roll": ["paper roll"],
                             "bag": ["bag"]}.get(item, [item])
    args.out = args.out or f"runs_{item}"
    os.makedirs(args.out, exist_ok=True)

    model = YOLO(args.model)
    if "world" in os.path.basename(args.model).lower():
        model.set_classes(prompt)  # tell the model what to look for, in words

    a, b = (args.line[0], args.line[1]), (args.line[2], args.line[3])
    counter = LineCounter(a, b)

    cap = cv2.VideoCapture(args.source)
    if not cap.isOpened():
        raise SystemExit(f"Could not open {args.source}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

    csv_path = os.path.join(args.out, f"{plural}.csv")
    csv_file = open(csv_path, "w", newline="")
    writer = csv.writer(csv_file)
    writer.writerow([f"{item}_no", "video_time", "direction", "track_id", "confidence", "photo"])

    frame_index = 0
    events = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_index += 1
        if frame_index % args.stride:
            continue
        seconds = frame_index / fps

        result = model.track(frame, persist=True, conf=args.conf,
                             tracker="bytetrack.yaml", verbose=False)[0]

        if result.boxes is not None and result.boxes.id is not None:
            boxes = result.boxes.xyxy.cpu().numpy()
            ids = result.boxes.id.int().cpu().tolist()
            confs = result.boxes.conf.cpu().tolist()
            for (x1, y1, x2, y2), track_id, conf in zip(boxes, ids, confs):
                centre = (float((x1 + x2) / 2), float((y1 + y2) / 2))
                event = counter.update(track_id, centre)
                colour = (0, 200, 0)
                if event:
                    colour = (0, 0, 255)
                    number = len(events) + 1
                    photo = os.path.join(args.out, f"{item}_{number:03d}.jpg")
                    evidence = frame.copy()
                    cv2.rectangle(evidence, (int(x1), int(y1)), (int(x2), int(y2)), colour, 4)
                    cv2.putText(evidence, f"{label} {number} {event} {fmt_time(seconds)}",
                                (int(x1), max(30, int(y1) - 10)),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.0, colour, 3)
                    cv2.imwrite(photo, evidence)
                    writer.writerow([number, fmt_time(seconds), event, track_id,
                                     f"{conf:.2f}", photo])
                    csv_file.flush()
                    events.append((number, seconds, event))
                    print(f"{label} {number}: {event} at {fmt_time(seconds)}")
                if args.show:
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), colour, 2)

        if args.show:
            cv2.line(frame, a, b, (0, 0, 255), 3)
            cv2.putText(frame, f"{plural_label.upper()} IN {counter.in_count}  OUT {counter.out_count}",
                        (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
            cv2.imshow(f"{item} counter", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    csv_file.close()
    cv2.destroyAllWindows()

    lines = [f"{plural_label} in: {counter.in_count}",
             f"{plural_label} out: {counter.out_count}",
             f"Net (in minus out): {counter.net}"]
    if events:
        lines.append(f"First {item} at {fmt_time(events[0][1])}, last {item} at {fmt_time(events[-1][1])}"
                     f" (took about {fmt_time(events[-1][1] - events[0][1])})")
    lines.append(f"Details: {csv_path}")
    summary = "\n".join(lines)
    print("\n" + summary)
    with open(os.path.join(args.out, "summary.txt"), "w") as f:
        f.write(summary + "\n")


if __name__ == "__main__":
    main()
