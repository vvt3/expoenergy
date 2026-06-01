def parse_time(t: str) -> int:
    """
    Parses time data

    Parameters:
    time in the string format: HH:MM

    Returns:
    An int as minutes since midnight
    """
    h, m = t.split(":")
    return int(h) * 60 + int(m)
