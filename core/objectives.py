"""
Objective framework for the bus charging scheduler.

Each objective is a self-contained class with a single `score(ctx) -> float` method.
Negative scores = bad. The scheduler sums weighted scores across all objectives.

To add a new rule:
  1. Create a subclass of Objective below
  2. Implement score(ctx) -> float
  3. Register it in DEFAULT_OBJECTIVES

That's it. No changes to the scheduler engine.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List


# ---------------------------------------------------------------------------
# Context — everything an objective could ever need, packaged once per plan
# ---------------------------------------------------------------------------


@dataclass
class PlanContext:
    # the bus
    bus_id: str
    operator: str
    departure: int

    # result
    estimated_wait: int
    per_stop_waits: List[int]
    journey_duration: int
    stop_count: int

    operator_wait_time: Dict[str, int]
    station_backlogs: Dict[str, int]


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------


class Objective:
    """
    Subclass this and implement score(ctx) -> float.
    Return a negative number — the more negative, the worse the plan.
    Return 0 if this objective has no opinion on the plan.
    """

    name: str = "unnamed"

    def score(self, ctx: PlanContext) -> float:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Individual objective
# Minimise this bus's own wait time and journey length.
# A stop where the bus had to queue is penalised; a free stop is not.
# ---------------------------------------------------------------------------


class IndividualObjective(Objective):
    name = "individual"

    def score(self, ctx: PlanContext) -> float:
        from core.route import CHARGE_TIME

        # penalise stops where the bus actually queued
        stops_with_wait = sum(1 for w in ctx.per_stop_waits if w > 0)

        return (
            -(ctx.estimated_wait * 100)
            - (stops_with_wait * CHARGE_TIME)
            - (ctx.journey_duration * 0.1)
        )


# ---------------------------------------------------------------------------
# Operator objective
# Operators with already-high cumulative fleet wait are steered toward
# less congested plans, so no single operator's buses pile up.
# ---------------------------------------------------------------------------


class OperatorObjective(Objective):
    name = "operator"

    def score(self, ctx: PlanContext) -> float:
        fleet_wait = ctx.operator_wait_time.get(ctx.operator, 0)
        marginal_cost = ctx.estimated_wait * 100
        existing_burden = fleet_wait * 10
        return -(marginal_cost + existing_burden)


# ---------------------------------------------------------------------------
# Overall objective
# Penalise choosing stations that are already heavily queued.
# Steers later buses away from congested stations toward free ones,
# naturally distributing load across A, B, C, D.
# ---------------------------------------------------------------------------


class OverallObjective(Objective):
    name = "overall"

    def score(self, ctx: PlanContext) -> float:
        total_backlog = sum(ctx.station_backlogs.values())
        return -(total_backlog * 150)


# class ElectricityPriceObjective(Objective):
#     name = "electricity_price"

#     def score(self, ctx: PlanContext) -> float:
#         from core.route import CHARGE_TIME

#         # Reconstruct approximate charge start times from departure + journey
#         # Lower cost (off-peak midnight-6am = 0-360 mins) is rewarded
#         penalty = 0
#         sim_time = ctx.departure
#         for wait in ctx.per_stop_waits:
#             charge_start = sim_time + wait
#             hour_of_day = (charge_start // 60) % 24
#             if 0 <= hour_of_day < 6:
#                 penalty += 0  # cheap, no penalty
#             else:
#                 penalty += 50  # peak hours, penalise
#             sim_time = charge_start + CHARGE_TIME

#         return -penalty


# ---------------------------------------------------------------------------
# Registry — the scheduler uses this list, in this order.
# To add a new objective: append it here.
# ---------------------------------------------------------------------------

DEFAULT_OBJECTIVES: List[Objective] = [
    IndividualObjective(),
    OperatorObjective(),
    OverallObjective(),
]
