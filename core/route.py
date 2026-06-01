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


def route_distance(path):
    total = 0

    for i in range(len(path) - 1):
        seg = (path[i], path[i + 1])

        for start, end, dist in SEGMENTS:
            if (start, end) == seg:
                total += dist
                break
            if (end, start) == seg:
                total += dist
                break

    return total


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
