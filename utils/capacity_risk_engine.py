from __future__ import annotations

from typing import Any, Dict, List


def build_capacity_risk_dashboard(
    headroom: Dict[str, Any],
    continuity_risks: List[Dict[str, Any]],
    logistics_kpis: Dict[str, Any],
) -> Dict[str, Any]:
    total_supply = float(headroom.get("total_supply_tpd", 0.0) or 0.0)
    nameplate = float(headroom.get("nameplate_tpd", 100.0) or 100.0)
    headroom_tpd = float(headroom.get("headroom_tpd", 0.0) or 0.0)
    buffer_pct = (headroom_tpd / nameplate * 100.0) if nameplate > 0 else 0.0

    weighted_distance = float(logistics_kpis.get("weighted_avg_distance_km", 0.0) or 0.0)
    long_haul_share = float(logistics_kpis.get("long_haul_share_pct", 0.0) or 0.0)
    continuity_count = len(continuity_risks or [])

    if headroom_tpd >= 10 and continuity_count <= 2 and long_haul_share < 50:
        operating_posture = "Stronger"
    elif headroom_tpd >= -10 and continuity_count <= 4 and long_haul_share < 70:
        operating_posture = "Watch"
    else:
        operating_posture = "Fragile"

    if continuity_count <= 2:
        continuity_band = "Low"
    elif continuity_count <= 4:
        continuity_band = "Watch"
    else:
        continuity_band = "High"

    if weighted_distance <= 40 and long_haul_share <= 30:
        logistics_band = "Low"
    elif weighted_distance <= 80 and long_haul_share <= 60:
        logistics_band = "Watch"
    else:
        logistics_band = "High"

    risk_rows = [
        {
            "Dimension": "Supply vs capacity",
            "Current reading": f"{total_supply:.1f} t/day vs {nameplate:.0f} t/day",
            "Risk view": operating_posture,
            "Why it matters": "Shows whether the current mapped feedstock can realistically support the plant target.",
        },
        {
            "Dimension": "Capacity buffer",
            "Current reading": f"{buffer_pct:.1f}%",
            "Risk view": "Favourable" if buffer_pct >= 10 else "Watch" if buffer_pct >= 0 else "Warning",
            "Why it matters": "A positive buffer gives room for seasonal dips, missed pickups, and route disruption.",
        },
        {
            "Dimension": "Continuity pressure",
            "Current reading": f"{continuity_count} active continuity risk(s)",
            "Risk view": continuity_band,
            "Why it matters": "More continuity risks mean supply is less dependable even if headline tonnage looks sufficient.",
        },
        {
            "Dimension": "Logistics pressure",
            "Current reading": f"{weighted_distance:.1f} km weighted distance / {long_haul_share:.1f}% long-haul share",
            "Risk view": logistics_band,
            "Why it matters": "Longer and riskier routes can reduce delivered tonnage and increase cost per ton.",
        },
    ]

    narrative = [
        f"Current mapped supply is about {total_supply:.1f} t/day against a 100 t/day plant target, giving a capacity buffer of {buffer_pct:.1f}%.",
        f"There are {continuity_count} continuity risk signal(s) active in the current model, and the weighted logistics distance is about {weighted_distance:.1f} km.",
        "This means BL Turner should assess readiness using a portfolio of supply, continuity, and route signals rather than a single score.",
    ]

    priority_actions = []
    if headroom_tpd < 0:
        priority_actions.append("Increase secure feedstock volumes so the plant is not planned against a structural shortfall.")
    if continuity_count > 2:
        priority_actions.append("Reduce dependence on fragile supply streams by strengthening more reliable municipal, distribution-centre, or nearby sources.")
    if long_haul_share > 40:
        priority_actions.append("Keep long-haul sources as support streams unless they are strategically necessary and cost-controlled.")
    if not priority_actions:
        priority_actions.append("Maintain monthly review of supply, continuity, and route burden so the operating posture stays current.")

    return {
        "operating_posture": operating_posture,
        "capacity_buffer_pct": round(buffer_pct, 1),
        "continuity_pressure_band": continuity_band,
        "logistics_pressure_band": logistics_band,
        "risk_rows": risk_rows,
        "narrative": narrative,
        "priority_actions": priority_actions,
    }
