from __future__ import annotations

from typing import Any, Dict, List


def build_digestate_dashboard(offtake_areas: List[Dict[str, Any]], total_supply_tpd: float) -> Dict[str, Any]:
    # Screening assumption: digestate output is roughly 30% of incoming wet feedstock mass after biogas capture.
    annual_digestate_tons = max(total_supply_tpd, 0.0) * 365.0 * 0.30

    rows: List[Dict[str, Any]] = []
    total_demand = 0.0

    for area in offtake_areas:
        hectares = float(area.get("estimated_hectares", 0.0) or 0.0)
        uptake_rate = float(area.get("uptake_rate_t_per_ha", 0.0) or 0.0)
        demand_capacity = round(hectares * uptake_rate, 1)
        total_demand += demand_capacity

        rows.append(
            {
                "Offtake area": area.get("name"),
                "Region": area.get("region", "KZN"),
                "Estimated hectares": hectares,
                "Uptake rate (t/ha/year)": uptake_rate,
                "Annual demand capacity (t/year)": demand_capacity,
                "Priority": area.get("priority", "Medium"),
                "Why it matters": area.get("notes", area.get("description", "")),
            }
        )

    coverage_ratio = (total_demand / annual_digestate_tons * 100.0) if annual_digestate_tons > 0 else 0.0

    if coverage_ratio >= 120:
        market_posture = "Stronger"
    elif coverage_ratio >= 80:
        market_posture = "Watch"
    else:
        market_posture = "Fragile"

    narrative = [
        f"Indicative digestate output is about {annual_digestate_tons:,.0f} tons per year based on the current feedstock model.",
        f"Mapped offtake zones could absorb about {total_demand:,.0f} tons per year, which is {coverage_ratio:.1f}% of the current output estimate.",
        "This makes digestate market development a practical commercial issue as well as a nature-positive one, because the strongest benefits are realised when digestate is consistently applied on farmland rather than treated as residual waste.",
    ]

    actions = []
    if coverage_ratio < 100:
        actions.append("Expand the digestate offtake map so demand capacity comfortably exceeds projected digestate output.")
    actions.append("Prioritise offtake areas near the plant first to reduce transport cost and simplify market entry.")
    actions.append("Use digestate demand evidence in farmer, municipality, and funder conversations to show the circular value chain, not only the waste-diversion side.")

    return {
        "kpis": {
            "annual_digestate_tons": round(annual_digestate_tons, 1),
            "annual_demand_capacity_tons": round(total_demand, 1),
            "demand_coverage_ratio_pct": round(coverage_ratio, 1),
            "market_posture": market_posture,
        },
        "rows": rows,
        "narrative": narrative,
        "actions": actions,
    }
