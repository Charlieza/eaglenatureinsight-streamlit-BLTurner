"""
BL Turner Group — Organic waste sourcing intelligence module.

Operational screening assumptions for BL Turner's 100 t/day anaerobic-
digestion facility at Portion 159 of New Guelderland, KwaDukuza.
"""

from __future__ import annotations

from typing import Any, Dict, List

from supply_engine import calculate_total_supply, calculate_utilisation, calculate_headroom, monthly_projection
from carbon_engine import calculate_avoided_methane
from reliability_engine import reliability_score


WASTE_SOURCES: List[Dict[str, Any]] = [
    {
        "node_id": "ILEMBE_KWADUKUZA_FRESH_MARKET",
        "name": "KwaDukuza fresh produce market",
        "district": "iLembe District",
        "municipality": "KwaDukuza Local Municipality",
        "lat": -29.3367,
        "lon": 31.2819,
        "stream": "Fruit & vegetable waste",
        "tons_per_day_est": 4.0,
        "collection_frequency": "Daily (6 days/week)",
        "seasonality": "Summer peak, winter base flow",
        "continuity_notes": "Low risk anchor stream close to the plant.",
        "role": "Anchor local source",
    },
    {
        "node_id": "ILEMBE_BALLITO_HOSPITALITY",
        "name": "Ballito / Umhlali hospitality belt",
        "district": "iLembe District",
        "municipality": "KwaDukuza Local Municipality",
        "lat": -29.5389,
        "lon": 31.2147,
        "stream": "Food waste (restaurants & hotels)",
        "tons_per_day_est": 5.5,
        "collection_frequency": "Daily in high season, 3× per week in low season",
        "seasonality": "Holiday-driven peak with winter dip",
        "continuity_notes": "Moderate risk due to tourism seasonality.",
        "role": "Seasonal peak source",
    },
    {
        "node_id": "ETHEKWINI_DURBAN_FRESH_PRODUCE",
        "name": "Durban Fresh Produce Market (Clairwood)",
        "district": "eThekwini Metro",
        "municipality": "eThekwini Metropolitan Municipality",
        "lat": -29.9369,
        "lon": 30.9833,
        "stream": "Fruit & vegetable waste",
        "tons_per_day_est": 22.0,
        "collection_frequency": "Daily",
        "seasonality": "Year-round base with summer and citrus peaks",
        "continuity_notes": "Large-volume stream but distance adds cost and route burden.",
        "role": "Primary bulk stream",
    },
    {
        "node_id": "ETHEKWINI_HOSPITALITY_DURBAN",
        "name": "Durban CBD & Umhlanga restaurants",
        "district": "eThekwini Metro",
        "municipality": "eThekwini Metropolitan Municipality",
        "lat": -29.7266,
        "lon": 31.0750,
        "stream": "Food waste (commercial kitchens)",
        "tons_per_day_est": 12.0,
        "collection_frequency": "3–6× per week per outlet",
        "seasonality": "Holiday and weekend peaks",
        "continuity_notes": "Requires aggregation across many outlets to stay dependable.",
        "role": "Distributed commercial stream",
    },
    {
        "node_id": "ETHEKWINI_DISTRIBUTION_CENTRES",
        "name": "Durban distribution centres (expired food)",
        "district": "eThekwini Metro",
        "municipality": "eThekwini Metropolitan Municipality",
        "lat": -29.8000,
        "lon": 30.9500,
        "stream": "Expired / near-date food from DCs",
        "tons_per_day_est": 10.0,
        "collection_frequency": "2–4× per week per DC",
        "seasonality": "Relatively stable year-round",
        "continuity_notes": "Good baseload opportunity if agreements are secured.",
        "role": "Baseload contract target",
    },
    {
        "node_id": "ETHEKWINI_MUNICIPAL_ORGANICS",
        "name": "eThekwini kerbside organics (pilot catchments)",
        "district": "eThekwini Metro",
        "municipality": "eThekwini Metropolitan Municipality",
        "lat": -29.8587,
        "lon": 31.0218,
        "stream": "Municipal organic fraction",
        "tons_per_day_est": 15.0,
        "collection_frequency": "Weekly per route (daily at consolidation point)",
        "seasonality": "Broadly flat with light summer uplift",
        "continuity_notes": "Growth stream but should not be treated as guaranteed day-one baseload.",
        "role": "Growth opportunity",
    },
    {
        "node_id": "UMGUNGUNDLOVU_ABATTOIR",
        "name": "Pietermaritzburg abattoir cluster",
        "district": "uMgungundlovu District",
        "municipality": "Msunduzi Local Municipality",
        "lat": -29.6166,
        "lon": 30.3927,
        "stream": "Meat & blood waste (abattoir)",
        "tons_per_day_est": 8.0,
        "collection_frequency": "Daily",
        "seasonality": "Steady year-round with festive peaks",
        "continuity_notes": "High-value stream but needs cold-chain and odour control.",
        "role": "Energy-dense co-feed",
    },
    {
        "node_id": "WESTERN_KZN_AGRI",
        "name": "Western KZN agricultural waste catchment (to be confirmed)",
        "district": "uThukela / uMzinyathi",
        "municipality": "Multiple",
        "lat": -28.9500,
        "lon": 29.7833,
        "stream": "Agricultural waste (crop residues, culled produce)",
        "tons_per_day_est": 6.0,
        "collection_frequency": "Seasonal — 3–5× per week during harvest windows",
        "seasonality": "Strong seasonal windows",
        "continuity_notes": "Use as a seasonal booster, not a baseload stream.",
        "role": "Seasonal booster (unconfirmed)",
    },
]

DIGESTATE_OFFTAKE_AREAS: List[Dict[str, Any]] = [
    {
        "name": "KZN North Coast sugarcane belt",
        "region": "North Coast",
        "lat": -29.3100,
        "lon": 31.3500,
        "priority": "High",
        "estimated_hectares": 1200,
        "uptake_rate_t_per_ha": 8.0,
        "description": "Sugarcane and banana areas close to the plant.",
        "notes": "Strong early market because it is close to the plant and aligned to nutrient-recycling messaging.",
        "role": "Primary digestate market",
    },
    {
        "name": "iLembe & uMgungundlovu mixed-cropping areas",
        "region": "iLembe / uMgungundlovu",
        "lat": -29.5000,
        "lon": 30.8000,
        "priority": "High",
        "estimated_hectares": 900,
        "uptake_rate_t_per_ha": 6.0,
        "description": "Vegetable, maize and mixed-cropping farms.",
        "notes": "Useful for farmer outreach and blended digestate market entry.",
        "role": "Secondary digestate market",
    },
    {
        "name": "Western KZN broadacre cropping",
        "region": "Western KZN",
        "lat": -28.9500,
        "lon": 29.9000,
        "priority": "Medium",
        "estimated_hectares": 1400,
        "uptake_rate_t_per_ha": 5.0,
        "description": "Maize, soya and broadacre cropping zones.",
        "notes": "Large demand sink but more transport-intensive.",
        "role": "Volume sink",
    },
]

NAMEPLATE_TONS_PER_DAY = 100.0

MONTHLY_MULTIPLIERS: Dict[str, List[float]] = {
    "ILEMBE_KWADUKUZA_FRESH_MARKET": [1.2, 1.2, 1.1, 1.1, 0.9, 0.8, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3],
    "ILEMBE_BALLITO_HOSPITALITY": [1.3, 1.1, 1.2, 1.2, 0.8, 0.6, 0.6, 0.7, 0.9, 1.0, 1.1, 1.4],
    "ETHEKWINI_DURBAN_FRESH_PRODUCE": [1.3, 1.2, 1.1, 1.0, 0.9, 1.1, 1.2, 1.0, 0.9, 1.0, 1.1, 1.3],
    "ETHEKWINI_HOSPITALITY_DURBAN": [1.2, 1.0, 1.2, 1.2, 0.9, 0.8, 0.8, 0.9, 1.1, 1.0, 1.1, 1.3],
    "ETHEKWINI_DISTRIBUTION_CENTRES": [1.1, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.1],
    "ETHEKWINI_MUNICIPAL_ORGANICS": [1.1, 1.1, 1.0, 1.0, 0.9, 0.9, 0.9, 0.9, 1.0, 1.0, 1.1, 1.1],
    "UMGUNGUNDLOVU_ABATTOIR": [1.0, 1.0, 1.0, 1.2, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.2, 1.3],
    "WESTERN_KZN_AGRI": [1.2, 1.1, 0.9, 0.8, 1.3, 1.4, 1.3, 0.9, 0.8, 1.0, 1.0, 1.1],
}


def total_estimated_supply() -> float:
    return calculate_total_supply(WASTE_SOURCES)


def stream_mix_summary() -> List[Dict[str, Any]]:
    agg: Dict[str, float] = {}
    for s in WASTE_SOURCES:
        stream = s.get("stream", "Other")
        agg[stream] = agg.get(stream, 0.0) + float(s.get("tons_per_day_est", 0.0))
    total = sum(agg.values()) or 1.0
    return [
        {"stream": stream, "tons_per_day": tpd, "share_pct": (tpd / total) * 100.0}
        for stream, tpd in sorted(agg.items(), key=lambda kv: kv[1], reverse=True)
    ]


def district_mix_summary() -> List[Dict[str, Any]]:
    agg: Dict[str, float] = {}
    for s in WASTE_SOURCES:
        district = s.get("district", "Other")
        agg[district] = agg.get(district, 0.0) + float(s.get("tons_per_day_est", 0.0))
    total = sum(agg.values()) or 1.0
    return [
        {"district": district, "tons_per_day": tpd, "share_pct": (tpd / total) * 100.0}
        for district, tpd in sorted(agg.items(), key=lambda kv: kv[1], reverse=True)
    ]


def seasonal_supply_profile() -> List[Dict[str, Any]]:
    return monthly_projection(WASTE_SOURCES, MONTHLY_MULTIPLIERS, NAMEPLATE_TONS_PER_DAY)


def continuity_risk_assessment() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []

    streams = stream_mix_summary()
    top = streams[0] if streams else None
    if top and top["share_pct"] > 40:
        rows.append({
            "level": "Moderate",
            "risk": "Feedstock concentration risk",
            "indicator": f"{top['stream']} ({top['share_pct']:.0f}% of supply)",
            "meaning": f"The '{top['stream']}' category contributes about {top['share_pct']:.0f}% of screening supply, so disruption in that stream would materially affect plant loading.",
            "mitigation": "Keep each major stream below about 40% of total intake and diversify across multiple source categories.",
        })
    else:
        rows.append({
            "level": "Low",
            "risk": "Feedstock concentration risk",
            "indicator": "No dominant stream",
            "meaning": "No single waste stream dominates the current supply mix.",
            "mitigation": "Maintain diversity across municipal, hospitality, produce, abattoir and agricultural streams.",
        })

    ethekwini_tpd = sum(s["tons_per_day_est"] for s in WASTE_SOURCES if s["district"] == "eThekwini Metro")
    total_tpd = total_estimated_supply() or 1.0
    ethekwini_share = (ethekwini_tpd / total_tpd) * 100.0
    if ethekwini_share > 55:
        rows.append({
            "level": "Moderate",
            "risk": "Long-haul logistics risk",
            "indicator": f"eThekwini share ~{ethekwini_share:.0f}%",
            "meaning": f"About {ethekwini_share:.0f}% of supply sits in longer-haul eThekwini routes, which increases fuel cost, spoilage exposure and routing complexity.",
            "mitigation": "Use nearer iLembe streams as base-load where possible and keep Durban-heavy routes cost-controlled.",
        })
    else:
        rows.append({
            "level": "Low",
            "risk": "Long-haul logistics risk",
            "indicator": f"eThekwini share ~{ethekwini_share:.0f}%",
            "meaning": "Long-haul exposure is present but still manageable in the current portfolio.",
            "mitigation": "Continue monitoring route cost and source concentration as volumes grow.",
        })

    profile = seasonal_supply_profile()
    peak = max(p["supply_tpd"] for p in profile) if profile else 0.0
    trough = min(p["supply_tpd"] for p in profile) if profile else 0.0
    variation = ((peak - trough) / peak * 100.0) if peak else 0.0
    if variation > 20:
        rows.append({
            "level": "Moderate",
            "risk": "Seasonal variability risk",
            "indicator": f"~{variation:.0f}% seasonal swing",
            "meaning": f"The current supply model swings by about {variation:.0f}% between peak and trough months, so stable plant loading will require active feedstock balancing.",
            "mitigation": "Keep buffer storage and use seasonal booster streams to support trough months.",
        })
    else:
        rows.append({
            "level": "Low",
            "risk": "Seasonal variability risk",
            "indicator": f"~{variation:.0f}% seasonal swing",
            "meaning": "Seasonal variation is present but not severe in the current mix.",
            "mitigation": "Standard monthly planning should be sufficient if the current source mix holds.",
        })

    municipal_tpd = sum(s["tons_per_day_est"] for s in WASTE_SOURCES if "municipal" in s["stream"].lower())
    if municipal_tpd > 0:
        rows.append({
            "level": "Watch",
            "risk": "Municipal contract dependency",
            "indicator": f"~{municipal_tpd:.0f} t/day municipal potential",
            "meaning": "Part of the model depends on municipal organics streams that may take time to formalise or scale.",
            "mitigation": "Treat municipal organics as a growth stream unless formal agreements are already in place.",
        })

    rows.append({
        "level": "Watch",
        "risk": "Abattoir biosecurity and odour risk",
        "indicator": "Meat and blood waste stream",
        "meaning": "Abattoir waste is energy-dense but operationally sensitive because it needs cold-chain handling, hygienic pre-treatment and strong odour control.",
        "mitigation": "Use sealed receiving, controlled delivery windows and appropriate hygienisation before digestion.",
    })

    return rows


def supply_headroom() -> Dict[str, float]:
    total = calculate_total_supply(WASTE_SOURCES)
    utilisation = calculate_utilisation(total)
    headroom = calculate_headroom(total)
    continuity = continuity_risk_assessment()
    reliability = reliability_score(headroom, continuity)
    carbon = calculate_avoided_methane(total)

    return {
        "nameplate_tpd": NAMEPLATE_TONS_PER_DAY,
        "total_supply_tpd": total,
        "estimated_supply_tpd": total,
        "headroom_tpd": headroom,
        "coverage_pct": utilisation,
        "utilisation_pct": utilisation,
        "reliability_pct": reliability,
        "co2e_tons": carbon["co2e_tons"],
        "annual_tons_diverted": carbon["annual_tons_diverted"],
        "methane_tons": carbon["methane_tons"],
    }


def collection_frequency_table() -> List[Dict[str, str]]:
    rows = []
    for s in WASTE_SOURCES:
        rows.append({
            "Source": s["name"],
            "District": s["district"],
            "Stream": s["stream"],
            "Daily tonnage (est.)": f"{s['tons_per_day_est']:.1f} t/day",
            "Collection frequency": s["collection_frequency"],
            "Seasonality": s["seasonality"],
            "Role": s["role"],
            "Continuity note": s["continuity_notes"],
        })
    return rows
