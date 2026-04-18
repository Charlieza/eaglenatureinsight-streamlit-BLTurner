from __future__ import annotations

from typing import Any, Dict, List

NAMEPLATE_CAPACITY_TPD = 100.0
MONTHS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def calculate_total_supply(sources: List[Dict[str, Any]]) -> float:
    return round(sum(float(s.get("tons_per_day_est", 0.0) or 0.0) for s in sources), 2)


def calculate_utilisation(total_supply_tpd: float, nameplate_tpd: float = NAMEPLATE_CAPACITY_TPD) -> float:
    if nameplate_tpd <= 0:
        return 0.0
    return round((total_supply_tpd / nameplate_tpd) * 100.0, 2)


def calculate_headroom(total_supply_tpd: float, nameplate_tpd: float = NAMEPLATE_CAPACITY_TPD) -> float:
    return round(total_supply_tpd - nameplate_tpd, 2)


def monthly_projection(
    sources: List[Dict[str, Any]],
    source_monthly_multipliers: Dict[str, List[float]],
    nameplate_tpd: float = NAMEPLATE_CAPACITY_TPD,
) -> List[Dict[str, Any]]:
    monthly_totals = [0.0] * 12

    for source in sources:
        node_id = source.get("node_id")
        tons = float(source.get("tons_per_day_est", 0.0) or 0.0)
        multipliers = source_monthly_multipliers.get(node_id, [1.0] * 12)

        for i in range(12):
            monthly_totals[i] += tons * multipliers[i]

    rows = []
    for idx, month in enumerate(MONTHS):
        projected = round(monthly_totals[idx], 2)
        rows.append(
            {
                "month": month,
                "projected_tons_per_day": projected,
                "supply_tpd": projected,
                "nameplate_tpd": nameplate_tpd,
                "headroom_tpd": round(projected - nameplate_tpd, 2),
            }
        )
    return rows
