from __future__ import annotations

from typing import Dict, List


NAMEPLATE_CAPACITY_TPD = 100.0

MONTHS = [
    "Jan", "Feb", "Mar", "Apr",
    "May", "Jun", "Jul", "Aug",
    "Sep", "Oct", "Nov", "Dec",
]


def calculate_total_supply(sources: List[dict]) -> float:
    return round(
        sum(float(s.get("tons_per_day_est", 0.0) or 0.0) for s in sources),
        2,
    )


def calculate_utilisation(total_supply: float) -> float:

    if NAMEPLATE_CAPACITY_TPD <= 0:
        return 0.0

    return round(
        (total_supply / NAMEPLATE_CAPACITY_TPD) * 100,
        2,
    )


def calculate_headroom(total_supply: float) -> float:

    return round(
        total_supply - NAMEPLATE_CAPACITY_TPD,
        2,
    )
