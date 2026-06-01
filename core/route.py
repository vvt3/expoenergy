SEGMENTS = [
    ("bengaluru", "A", 100),
    ("A", "B", 120),
    ("B", "C", 100),
    ("C", "D", 120),
    ("D", "kochi", 100),
]

STATIONS = ["A", "B", "C", "D"]

MAX_RANGE = 240

CHARGE_TIME = 25

SPEED = 60


def get_distance(a, b):
    """
    Get the distance between 2 segements
    """
    for s, e, d in SEGMENTS:
        if (s, e) == (a, b) or (e, s) == (a, b):
            return d
    raise ValueError(f"Invalid segment from {a} -> {b}")


def get_next_distance(path, i):

    if i >= len(path) - 1:
        return None

    start = path[i]
    end = path[i + 1]

    for s, e, d in SEGMENTS:
        if (s, e) == (start, end) or (e, s) == (start, end):
            return int(d)

    raise ValueError(f"Invalid segment from {start} -> {end}")


def compute_stops(path, max_range=240):
    stops = []
    distance_acc = 0

    last_charge_index = 0

    for i in range(len(path) - 1):
        dist = get_distance(path[i], path[i + 1])

        distance_acc += dist

        # if range is too great, charge at previous stop
        if distance_acc > max_range:
            stops.append(path[i])

            distance_acc = dist  # restart from this segment

    return stops


def build_path(source, destination):
    nodes = ["bengaluru", "A", "B", "C", "D", "kochi"]

    start_idx = nodes.index(source)
    end_idx = nodes.index(destination)

    if start_idx < end_idx:
        return nodes[start_idx : end_idx + 1]
    else:
        return list(reversed(nodes[end_idx : start_idx + 1]))


# TODO
def split_segments(path):
    return list(zip(path[:-1], path[1:]))
