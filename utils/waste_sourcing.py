"""
BL Turner Group — Organic waste sourcing intelligence module.

This module captures the waste sourcing logic that is specific to BL
Turner's 100 t/day anaerobic-digestion facility at Portion 159 of New
Guelderland, KwaDukuza, drawing feedstock from:

  - iLembe District (KwaDukuza area — local municipal sources)
  - eThekwini Metropolitan Municipality (restaurants, commercial
    kitchens, distribution centres' expired food)
  - uMgungundlovu District (Pietermaritzburg area — abattoir, agri)
  - Western KZN (broader agricultural waste catchment)

Addresses the client brief:
  * Frequency of getting waste
  * Tons of waste
  * Seasonal patterns
  * Continuity of supply (risk mitigation via multi-source contracting)

Data used here are sector-level screening assumptions for pilot
purposes. Municipal, eThekwini Waste, and abattoir operators should
replace these with actual contracted volumes as they come online.
"""

from __future__ import annotations

from typing import Any, Dict, List


# -----------------------------------------------------------------------------
# Waste sources — geographic nodes relevant to BL Turner
# -----------------------------------------------------------------------------
# Each source node has: name, lat/lon, KZN municipality, waste stream(s),
# indicative daily tonnage available, collection frequency, seasonal
# pattern, and risk/continuity notes.

WASTE_SOURCES: List[Dict[str, Any]] = [
    # --- iLembe District (around KwaDukuza main site) ---
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
        "seasonality": (
            "Peaks Nov–Apr (summer fruits, mango, citrus, tropical). "
            "Lower volume in winter but relatively stable year-round."
        ),
        "continuity_notes": (
            "Low risk — core daily stream with short distance to plant "
            "(~15–20 km). Retain as one of the anchor local contracts."
        ),
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
        "seasonality": (
            "Peaks Dec–Jan and Mar–Apr holidays (coastal tourism). "
            "Low in Jun–Aug. Variation of ~40% between peak and trough."
        ),
        "continuity_notes": (
            "Moderate risk — volume sensitive to tourism cycles. Diversify "
            "across many outlets to avoid dependence on a handful of hotels."
        ),
        "role": "Seasonal peak source",
    },
    # --- eThekwini Metropolitan Municipality ---
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
        "seasonality": (
            "Strong peaks Dec–Feb (summer fruit) and Jun–Jul (citrus). "
            "Base volume present year-round."
        ),
        "continuity_notes": (
            "Low-to-moderate risk — volume is large and consistent, but the ~90 km "
            "distance to KwaDukuza drives fuel and spoilage cost. A refrigerated "
            "transfer / pre-sort station near the market would materially de-risk this stream."
        ),
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
        "seasonality": (
            "Peaks Dec–Jan, Mar–Apr (holidays, Easter), and Sep (spring). "
            "Weekly cycle: Thu–Sat volumes ~30% higher than Mon–Wed."
        ),
        "continuity_notes": (
            "Moderate risk — requires many micro-contracts. Aggregator model or "
            "partnership with a waste-management contractor is advised."
        ),
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
        "seasonality": (
            "Relatively flat year-round, with small peaks post-holidays (returns)."
        ),
        "continuity_notes": (
            "Low risk — DCs are consolidated points and prefer a single offtaker. "
            "High strategic value as a bankable baseload contract."
        ),
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
        "collection_frequency": "Weekly per household route (daily at consolidation point)",
        "seasonality": "Broadly flat, ~10% summer peak",
        "continuity_notes": (
            "Moderate-to-high risk depending on the status of eThekwini's "
            "organic-separation rollout. Confirm formal municipal contracts before "
            "relying on this volume."
        ),
        "role": "Growth opportunity",
    },
    # --- uMgungundlovu (Pietermaritzburg) ---
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
        "seasonality": (
            "Peaks Nov–Dec (festive meat demand) and Apr (Easter). "
            "Base volume runs evenly year-round."
        ),
        "continuity_notes": (
            "Moderate risk — requires cold-chain collection to prevent spoilage "
            "and biosecurity issues. Must be co-digested with high-C feedstocks "
            "(veg waste) to balance nitrogen."
        ),
        "role": "Energy-dense co-feed",
    },
    # --- Western KZN (broader agricultural catchment) ---
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
        "seasonality": (
            "Strongly seasonal. Maize residue peaks May–Jul; sugarcane "
            "trash Apr–Nov; vegetable culls Oct–Apr."
        ),
        "continuity_notes": (
            "Highest supply-variability risk. Use as a seasonal 'booster' stream "
            "rather than a baseload. Coordinate with harvest calendars."
        ),
        "role": "Seasonal booster (unconfirmed)",
    },
]

# --- Digestate off-take areas (where the fertiliser product is expected to go)

DIGESTATE_OFFTAKE_AREAS: List[Dict[str, Any]] = [
    {
        "name": "KZN North Coast sugarcane belt",
        "lat": -29.3100,
        "lon": 31.3500,
        "notes": (
            "Sugarcane and banana farms along the KZN north coast between "
            "KwaDukuza and Mtubatuba. Organic fertiliser supports soil carbon "
            "and reduces synthetic input dependence."
        ),
    },
    {
        "name": "iLembe & uMgungundlovu mixed-cropping areas",
        "lat": -29.5000,
        "lon": 30.8000,
        "notes": (
            "Vegetables, dryland maize and smallholder mixed cropping. "
            "Digestate can be positioned as a lower-cost organic amendment "
            "for cooperatives and agri-incubation programmes."
        ),
    },
    {
        "name": "Western KZN broadacre cropping",
        "lat": -28.9500,
        "lon": 29.9000,
        "notes": (
            "Maize, soya, wheat areas in Bergville / Winterton region. "
            "Volume sink for dewatered digestate; soil-carbon restoration "
            "opportunity on depleted soils."
        ),
    },
]

# -----------------------------------------------------------------------------
# Analytics
# -----------------------------------------------------------------------------

NAMEPLATE_TONS_PER_DAY = 100.0


def total_estimated_supply() -> float:
    return sum(float(s.get("tons_per_day_est", 0.0)) for s in WASTE_SOURCES)


def supply_headroom() -> Dict[str, float]:
    total = total_estimated_supply()
    return {
        "nameplate_tpd": NAMEPLATE_TONS_PER_DAY,
        "estimated_supply_tpd": total,
        "headroom_tpd": total - NAMEPLATE_TONS_PER_DAY,
        "coverage_pct": (total / NAMEPLATE_TONS_PER_DAY) * 100.0 if NAMEPLATE_TONS_PER_DAY > 0 else 0.0,
    }


def stream_mix_summary() -> List[Dict[str, Any]]:
    """Aggregate supply by waste stream category."""
    agg: Dict[str, float] = {}
    for s in WASTE_SOURCES:
        stream = s.get("stream", "Other")
        agg[stream] = agg.get(stream, 0.0) + float(s.get("tons_per_day_est", 0.0))
    total = sum(agg.values()) or 1.0
    rows = []
    for stream, tpd in sorted(agg.items(), key=lambda kv: kv[1], reverse=True):
        rows.append({
            "stream": stream,
            "tons_per_day": tpd,
            "share_pct": (tpd / total) * 100.0,
        })
    return rows


def district_mix_summary() -> List[Dict[str, Any]]:
    """Aggregate supply by district."""
    agg: Dict[str, float] = {}
    for s in WASTE_SOURCES:
        d = s.get("district", "Other")
        agg[d] = agg.get(d, 0.0) + float(s.get("tons_per_day_est", 0.0))
    total = sum(agg.values()) or 1.0
    rows = []
    for d, tpd in sorted(agg.items(), key=lambda kv: kv[1], reverse=True):
        rows.append({
            "district": d,
            "tons_per_day": tpd,
            "share_pct": (tpd / total) * 100.0,
        })
    return rows


def seasonal_supply_profile() -> List[Dict[str, Any]]:
    """
    Build an indicative monthly supply profile across all sources.
    Each source contributes a monthly multiplier (0.5–1.3) reflecting
    its stated seasonality, applied to its daily tonnage.

    This is a screening profile, not a forecast.
    """
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    # Per-source monthly multipliers (12 values each). Index 0 = Jan.
    profiles: Dict[str, List[float]] = {
        "ILEMBE_KWADUKUZA_FRESH_MARKET": [1.2, 1.2, 1.1, 1.1, 0.9, 0.8, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3],
        "ILEMBE_BALLITO_HOSPITALITY":     [1.3, 1.1, 1.2, 1.2, 0.8, 0.6, 0.6, 0.7, 0.9, 1.0, 1.1, 1.4],
        "ETHEKWINI_DURBAN_FRESH_PRODUCE": [1.3, 1.2, 1.1, 1.0, 0.9, 1.1, 1.2, 1.0, 0.9, 1.0, 1.1, 1.3],
        "ETHEKWINI_HOSPITALITY_DURBAN":   [1.2, 1.0, 1.2, 1.2, 0.9, 0.8, 0.8, 0.9, 1.1, 1.0, 1.1, 1.3],
        "ETHEKWINI_DISTRIBUTION_CENTRES": [1.1, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.1],
        "ETHEKWINI_MUNICIPAL_ORGANICS":   [1.1, 1.1, 1.0, 1.0, 0.9, 0.9, 0.9, 0.9, 1.0, 1.0, 1.1, 1.1],
        "UMGUNGUNDLOVU_ABATTOIR":         [1.0, 1.0, 1.0, 1.2, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.2, 1.3],
        "WESTERN_KZN_AGRI":               [1.2, 1.1, 0.9, 0.8, 1.3, 1.4, 1.3, 0.9, 0.8, 1.0, 1.0, 1.1],
    }

    monthly = [0.0] * 12
    for s in WASTE_SOURCES:
        nid = s["node_id"]
        tpd = float(s.get("tons_per_day_est", 0.0))
        mult = profiles.get(nid, [1.0] * 12)
        for i in range(12):
            monthly[i] += tpd * mult[i]

    rows = []
    for i, m in enumerate(months):
        rows.append({
            "month": m,
            "supply_tpd": monthly[i],
            "nameplate_tpd": NAMEPLATE_TONS_PER_DAY,
            "headroom_tpd": monthly[i] - NAMEPLATE_TONS_PER_DAY,
        })
    return rows


def continuity_risk_assessment() -> List[Dict[str, str]]:
    """
    Flag continuity-of-supply risks in plain language across the
    feedstock portfolio.
    """
    rows = []
    # Concentration risk
    streams = stream_mix_summary()
    top = streams[0] if streams else None
    if top and top["share_pct"] > 40:
        rows.append({
            "risk": "Feedstock concentration risk",
            "severity": "Moderate",
            "finding": (
                f"The '{top['stream']}' category accounts for about "
                f"{top['share_pct']:.0f}% of the screening supply portfolio."
            ),
            "mitigation": (
                "Target each major stream to sit under 40% of total intake. "
                "Expand contracts across at least 3 waste categories and "
                "across both eThekwini and iLembe sources."
            ),
        })
    else:
        rows.append({
            "risk": "Feedstock concentration risk",
            "severity": "Low",
            "finding": "No single waste stream dominates the screening portfolio.",
            "mitigation": (
                "Maintain diversified sourcing across food waste, municipal organics, "
                "abattoir and agricultural streams."
            ),
        })

    # Geographic risk (eThekwini distance)
    ethekwini_tpd = sum(s["tons_per_day_est"] for s in WASTE_SOURCES if s["district"] == "eThekwini Metro")
    total_tpd = total_estimated_supply() or 1.0
    if ethekwini_tpd / total_tpd > 0.55:
        rows.append({
            "risk": "Long-haul logistics risk",
            "severity": "Moderate",
            "finding": (
                f"eThekwini-sourced streams are {ethekwini_tpd:.0f} tpd of about "
                f"{total_tpd:.0f} tpd total (~{ethekwini_tpd/total_tpd*100:.0f}%), roughly 80–100 km from the plant."
            ),
            "mitigation": (
                "Consider a refrigerated pre-sort / transfer station closer to Durban to "
                "reduce fuel, spoilage and driver hours. Negotiate off-peak collection slots."
            ),
        })
    else:
        rows.append({
            "risk": "Long-haul logistics risk",
            "severity": "Low",
            "finding": f"eThekwini-sourced streams are a manageable share of total intake (~{ethekwini_tpd/total_tpd*100:.0f}%).",
            "mitigation": "Continue to monitor diesel cost and driver hours per load.",
        })

    # Seasonal variability risk
    profile = seasonal_supply_profile()
    peak = max(p["supply_tpd"] for p in profile)
    trough = min(p["supply_tpd"] for p in profile)
    variation = (peak - trough) / (peak or 1.0) * 100.0
    if variation > 20:
        rows.append({
            "risk": "Seasonal variability risk",
            "severity": "Moderate",
            "finding": (
                f"Modelled feedstock supply varies by about {variation:.0f}% between the "
                f"peak month (~{peak:.0f} tpd) and the trough month (~{trough:.0f} tpd)."
            ),
            "mitigation": (
                "Size silage / buffer storage for at least 7–14 days of feedstock. "
                "Use seasonal contracts with Western KZN agri sources to balance trough months."
            ),
        })
    else:
        rows.append({
            "risk": "Seasonal variability risk",
            "severity": "Low",
            "finding": f"Modelled seasonal swing is modest ({variation:.0f}%).",
            "mitigation": "Standard weekly operational planning is sufficient.",
        })

    # Municipal contract dependency
    municipal_tpd = sum(s["tons_per_day_est"] for s in WASTE_SOURCES if "municipal" in s["stream"].lower() or "Municipal" in s["stream"])
    if municipal_tpd > 0:
        rows.append({
            "risk": "Municipal contract dependency",
            "severity": "Watch",
            "finding": (
                f"About {municipal_tpd:.0f} tpd of potential supply depends on municipal "
                "organic-separation rollouts that may not yet be contracted."
            ),
            "mitigation": (
                "Secure MoUs with eThekwini and KwaDukuza waste departments early. Treat "
                "municipal organics as a growth stream rather than day-1 baseload."
            ),
        })

    # Abattoir biosecurity risk
    rows.append({
        "risk": "Abattoir biosecurity & odour risk",
        "severity": "Watch",
        "finding": (
            "Meat and blood waste requires cold-chain collection, pasteurisation / "
            "thermophilic digestion, and odour-controlled reception to meet biosecurity "
            "and community-relations expectations."
        ),
        "mitigation": (
            "Invest in a sealed cold-receiving bay, dedicated delivery slots, and a pre-treatment "
            "hygienisation step aligned with South African animal by-products requirements."
        ),
    })

    return rows


def collection_frequency_table() -> List[Dict[str, str]]:
    """Return a structured view of collection frequency per source, used in the UI."""
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
