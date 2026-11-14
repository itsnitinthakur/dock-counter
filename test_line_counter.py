from line_counter import LineCounter

# Horizontal line across the door at y = 100, from x=0 to x=200.
A, B = (0, 100), (200, 100)


def run(tracks):
    counter = LineCounter(A, B)
    for frame in tracks:
        for track_id, centre in frame:
            counter.update(track_id, centre)
    return counter


def test_one_bag_in():
    c = run([[(1, (50, 80))], [(1, (50, 95))], [(1, (50, 120))]])
    assert (c.in_count, c.out_count) == (1, 0)


def test_one_bag_out():
    c = run([[(1, (50, 130))], [(1, (50, 90))]])
    assert (c.in_count, c.out_count) == (0, 1)


def test_counted_only_once_even_if_it_wobbles():
    c = run([[(1, (50, 90))], [(1, (50, 110))], [(1, (50, 95))], [(1, (50, 115))]])
    assert c.in_count + c.out_count == 1


def test_no_crossing_no_count():
    c = run([[(1, (50, 20))], [(1, (60, 40))], [(1, (70, 60))]])
    assert (c.in_count, c.out_count) == (0, 0)


def test_two_bags_together():
    c = run([[(1, (40, 90)), (2, (80, 92))], [(1, (40, 110)), (2, (80, 111))]])
    assert c.in_count == 2


def test_on_the_line_is_ignored():
    c = run([[(1, (50, 90))], [(1, (50, 100))], [(1, (50, 110))]])
    assert c.in_count == 1
