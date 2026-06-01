def parse_time(t: str) -> int:
    """
    Parses time data from HH:MM to the minutes since midnight

    Parameters:
    HH:MM as a string

    Returns:
    minutes since midnight as an integer
    """
    h, m = t.split(":")
    return int(h) * 60 + int(m)
