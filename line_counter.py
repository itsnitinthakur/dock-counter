"""Line-crossing counter.

Counts tracked objects that cross a virtual line in a chosen direction.
Works with any tracker that gives each object a stable ID per frame.
Kept free of OpenCV and YOLO so it can be tested on its own.
"""


def side_of_line(point, a, b):
    """Return +1, -1 or 0: which side of line a->b the point is on."""
    (x, y), (x1, y1), (x2, y2) = point, a, b
    value = (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


class LineCounter:
    """Counts objects crossing a line.

    "in" means moving from the negative side to the positive side of a->b;
    swap a and b if your camera sees it the other way round.
    """

    def __init__(self, a, b):
        self.a = a
        self.b = b
        self.last_side = {}      # track id -> last non-zero side
        self.counted = set()     # track ids already counted (count once)
        self.in_count = 0
        self.out_count = 0

    def update(self, track_id, centre):
        """Feed one object's centre for this frame. Returns 'in', 'out' or None."""
        side = side_of_line(centre, self.a, self.b)
        if side == 0:
            return None
        previous = self.last_side.get(track_id)
        self.last_side[track_id] = side
        if previous is None or previous == side or track_id in self.counted:
            return None
        self.counted.add(track_id)
        if previous < 0 < side:
            self.in_count += 1
            return "in"
        self.out_count += 1
        return "out"

    @property
    def net(self):
        return self.in_count - self.out_count
