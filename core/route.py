from itertools import combinations

SEGMENTS = [
    ("bengaluru", "A", 100),
    ("A", "B", 120),
    ("B", "C", 100),
    ("C", "D", 120),
    ("D", "kochi", 100),
]

# Station: No. Chargers
STATIONS = {
    "A": 1,
    "B": 1,
    "C": 1,
    "D": 1,
}

MAX_RANGE = 220

CHARGE_TIME = 25

SPEED = 60


def get_station_nodes(path):
    return path[1:-1]


def is_valid_plan(path, charging_stations):
    checkpoints = [path[0], *charging_stations, path[-1]]

    for i in range(len(checkpoints) - 1):
        start = checkpoints[i]
        end = checkpoints[i + 1]

        start_idx = path.index(start)
        end_idx = path.index(end)

        section = path[start_idx : end_idx + 1]

        if distance_between_nodes(section) > MAX_RANGE:
            return False

    return True


def generate_valid_plans(path):
    stations = get_station_nodes(path)

    valid_plans = []

    for r in range(1, len(stations) + 1):
        for plan in combinations(stations, r):
            if is_valid_plan(path, list(plan)):
                valid_plans.append(list(plan))

    return valid_plans


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


def distance_between_nodes(path):
    total = 0

    for i in range(len(path) - 1):
        start = path[i]
        end = path[i + 1]

        for s, e, d in SEGMENTS:
            if (s, e) == (start, end) or (e, s) == (start, end):
                total += d
                break

    return total


def build_path(source, destination):
    nodes = ["bengaluru", *STATIONS.keys(), "kochi"]

    start_idx = nodes.index(source)
    end_idx = nodes.index(destination)

    if start_idx < end_idx:
        return nodes[start_idx : end_idx + 1]
    else:
        return list(reversed(nodes[end_idx : start_idx + 1]))


def split_segments(path):
    return list(zip(path[:-1], path[1:]))
