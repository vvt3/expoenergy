def score_station(station, arrival_time, station_free_time, operator, weights, context):
    """
    returns a score for a station
    """

    # 1. waiting time (less is better)
    wait = max(0, station_free_time[station] - arrival_time)

    individual_score = -wait

    # 2. operator fairness (simple)
    operator_penalty = context["operator_delay"].get(operator, 0)
    operator_score = -operator_penalty

    # 3. system score (simple)
    overall_score = -wait

    return (
        weights["individual"] * individual_score
        + weights["operator"] * operator_score
        + weights["overall"] * overall_score
    )
