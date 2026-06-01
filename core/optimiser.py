from pulp import LpProblem, LpMaximize, LpVariable
from core.route import build_path, generate_valid_plans


class Optimiser:
    def choose_plans(self, buses):

        model = LpProblem(
            "BusCharging",
            LpMaximize,
        )

        bus_plans = {}

        x = {}

        for bus in buses:
            plans = bus_plans[bus.bus_id]

            for p in range(len(plans)):
                x[(bus.bus_id, p)] = LpVariable(
                    f"{bus.bus_id}_{p}",
                    cat="Binary",
                )
