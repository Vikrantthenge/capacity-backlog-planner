"""Daily capacity and backlog calculations for a five-day service operation."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence

DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")


@dataclass(frozen=True)
class StaffingPlan:
    name: str
    regular_hours: Sequence[float]
    overtime_hours: Sequence[float]


DEFAULT_PLANS = (
    StaffingPlan("Current staffing", (48, 48, 48, 48, 48), (0, 0, 0, 0, 0)),
    StaffingPlan("Shift regular hours", (60, 56, 44, 40, 40), (0, 0, 0, 0, 0)),
    StaffingPlan("Add overtime", (48, 48, 48, 48, 48), (16, 8, 0, 0, 0)),
    StaffingPlan("Shift hours + targeted overtime", (60, 56, 44, 40, 40), (6, 0, 0, 0, 0)),
)


def nonnegative_decimal(value):
    amount = Decimal(str(value))
    if not amount.is_finite() or amount < 0:
        raise ValueError("Rates and hours must be finite and non-negative.")
    return amount


def simulate(demand, plans, requests_per_hour, regular_rate, overtime_rate, opening_backlog=0):
    """Return daily rows and weekly summaries in input plan order."""
    if len(demand) != len(DAYS) or any(type(count) is not int or count < 0 for count in demand):
        raise ValueError("Enter five whole, non-negative daily request counts.")
    if type(opening_backlog) is not int or opening_backlog < 0:
        raise ValueError("Opening backlog must be a whole, non-negative count.")
    rate = nonnegative_decimal(requests_per_hour)
    regular_cost = nonnegative_decimal(regular_rate)
    overtime_cost = nonnegative_decimal(overtime_rate)
    daily_rows, weekly_rows = [], []
    for plan in plans:
        if len(plan.regular_hours) != len(DAYS) or len(plan.overtime_hours) != len(DAYS):
            raise ValueError(f"{plan.name} must contain staffing hours for all five days.")
        backlog = opening_backlog
        plan_days = []
        for index, (day, new, regular, overtime) in enumerate(
            zip(DAYS, demand, plan.regular_hours, plan.overtime_hours), start=1
        ):
            regular = nonnegative_decimal(regular)
            overtime = nonnegative_decimal(overtime)
            available = backlog + new
            capacity = int((regular + overtime) * rate)
            completed = min(available, capacity)
            closing = available - completed
            plan_days.append({
                "Plan": plan.name,
                "Day order": index,
                "Day": day,
                "New requests": new,
                "Regular hours": float(regular),
                "Overtime hours": float(overtime),
                "Opening backlog": backlog,
                "Work available": available,
                "Capacity": capacity,
                "Completed": completed,
                "Closing backlog": closing,
                "Labour cost (INR)": regular * regular_cost + overtime * overtime_cost,
            })
            backlog = closing
        total_completed = sum(day["Completed"] for day in plan_days)
        total_cost = sum(day["Labour cost (INR)"] for day in plan_days)
        weekly_rows.append({
            "Plan": plan.name,
            "New requests": sum(demand),
            "Opening backlog": opening_backlog,
            "Completed": total_completed,
            "Peak backlog": max(day["Closing backlog"] for day in plan_days),
            "Friday backlog": backlog,
            "Regular hours": sum(day["Regular hours"] for day in plan_days),
            "Overtime hours": sum(day["Overtime hours"] for day in plan_days),
            "Labour cost (INR)": float(total_cost),
            "Cost per completed request (INR)": float(total_cost / total_completed) if total_completed else None,
        })
        for day in plan_days:
            day["Labour cost (INR)"] = float(day["Labour cost (INR)"])
        daily_rows.extend(plan_days)
    return daily_rows, weekly_rows


def meets_targets(row, friday_limit, peak_limit=None):
    return row["Friday backlog"] <= friday_limit and (
        peak_limit is None or row["Peak backlog"] <= peak_limit
    )


def recommend(weekly_rows, friday_limit, peak_limit=None):
    """Choose the lowest-cost entered plan that meets the backlog targets."""
    eligible = [
        row for row in weekly_rows
        if meets_targets(row, friday_limit, peak_limit)
    ]
    return min(eligible, key=lambda row: (
        row["Labour cost (INR)"], row["Friday backlog"], row["Peak backlog"]
    ), default=None)
