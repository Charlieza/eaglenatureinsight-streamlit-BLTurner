"""
TNFD and Nature Positive Initiative (NPI) alignment content for
BL Turner Group's organic waste-to-fertiliser and biogas facility.

Translates screening indicators into the TNFD core-metrics vocabulary
and the NPI State of Nature indicators the Challenge rubric asked for,
with honesty about what is a direct measurement, a proxy, or a
"comply or explain" placeholder (TNFD language).

References:
 - TNFD (Sept 2023) Recommendations, Annex 1: Core global disclosure
   metrics (14 core indicators across dependencies/impacts and
   risks/opportunities).
 - Nature Positive Initiative State of Nature metrics: ecosystem
   extent (IND1), ecosystem condition (IND2), landscape intactness
   (IND3), species extinction risk (IND4).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _fmt(value: Any, digits: int = 2, suffix: str = "") -> str:
    if value is None or value == "":
        return "Not measured yet"
    try:
        f = float(value)
    except Exception:
        return str(value)
    if f != f:
        return "Not measured yet"
    return f"{f:.{digits}f}{suffix}"


# -----------------------------------------------------------------------------
# TNFD Annex 1: Core global disclosure metrics mapping
# -----------------------------------------------------------------------------

def build_tnfd_core_metrics_rows(metrics: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Returns a list of rows, each one row of the TNFD Annex 1 Core Global
    Metrics dashboard as implemented by this platform for the BL Turner
    organic waste / AD / biogas / digestate project.
    """
    m = metrics

    return [
        {
            "metric_id": "C1.0",
            "metric_name": "Total spatial footprint",
            "what_it_means": "How much surface area the project controls or manages.",
            "what_we_report": (
                f"{_fmt(m.get('area_ha'), 2, ' ha')} plant-site footprint (Portion 159 of "
                f"New Guelderland, KwaDukuza, nominal 1.5 ha / 15,000 m²)."
            ),
            "status": "Direct measurement" if m.get("area_ha") else "Not available",
        },
        {
            "metric_id": "C1.1",
            "metric_name": "Extent of land / freshwater / ocean-use change",
            "what_it_means": "How much natural ecosystem has been converted, and by what activity.",
            "what_we_report": (
                f"Current landscape mix around the plant: tree cover "
                f"{_fmt(m.get('tree_cover_context_pct') or m.get('tree_pct'), 1, '%')}, "
                f"cropland {_fmt(m.get('cropland_pct'), 1, '%')}, "
                f"built-up {_fmt(m.get('built_pct'), 1, '%')}. "
                f"Forest loss in the landscape: {_fmt(m.get('forest_loss_pct'), 1, '%')} of baseline."
            ),
            "status": "Proxy (WorldCover + Hansen + Dynamic World)",
        },
        {
            "metric_id": "C2.0–C2.4",
            "metric_name": "Pollutants, waste, plastics, air pollutants",
            "what_it_means": (
                "Pollution released into soil, water and air; waste "
                "generated. For an AD plant this includes digestate liquor, "
                "odour, and CHP exhaust."
            ),
            "what_we_report": (
                "Not computed from satellite data. Comes from the plant's "
                "environmental monitoring (CHP stack, digestate sampling, "
                "odour boundary monitoring, noise)."
            ),
            "status": "Comply or explain: requires BL Turner operational data",
        },
        {
            "metric_id": "C2.5",
            "metric_name": "GHG emissions",
            "what_it_means": (
                "Scope 1, 2 and 3 greenhouse gas emissions. For this "
                "project, the key number is avoided methane emissions "
                "from landfill diversion."
            ),
            "what_we_report": (
                "Indicative landfill-diversion avoided emissions: ~9,125 tCO₂e/year "
                "at nameplate 100 t/day throughput (screening assumption, ~0.25 tCO₂e "
                "avoided per tonne diverted, net of process emissions). Final figure "
                "needs a formal GHG methodology (e.g. Verra VM0041 or a local equivalent)."
            ),
            "status": "Indicative screening figure",
        },
        {
            "metric_id": "C3.0",
            "metric_name": "Water withdrawal and consumption from water-scarce areas",
            "what_it_means": "How much water the business uses, and whether it draws from water-stressed places.",
            "what_we_report": (
                f"Water-stress context: rainfall anomaly {_fmt(m.get('rain_anom_pct'), 1, '%')}, "
                f"surface water signal {_fmt(m.get('water_context_signal_pct') or m.get('water_occ'), 1)}, "
                f"climate water deficit {_fmt(m.get('climate_water_deficit'), 1)}, "
                f"evapotranspiration {_fmt(m.get('evapotranspiration'), 1)}. "
                "Actual process-water withdrawal volumes come from plant metering."
            ),
            "status": "Context proxy (withdrawal volumes need plant data)",
        },
        {
            "metric_id": "C3.1",
            "metric_name": "High-risk natural commodities sourced",
            "what_it_means": "Tonnes of commodities sourced that are known to drive nature loss.",
            "what_we_report": (
                "Not applicable in the usual sense. The 'commodity' sourced here is organic waste, "
                "which is a waste stream rather than a primary commodity. Worth disclosing the "
                "100 t/day waste feedstock mix (municipal fruit/veg, restaurant food waste, "
                "distribution-centre expired food, abattoir meat and blood) as a sourcing disclosure."
            ),
            "status": "Adapted for waste feedstock reporting",
        },
        {
            "metric_id": "C4.0",
            "metric_name": "Invasive alien species: management measures",
            "what_it_means": "Whether the business has measures to prevent the unintentional spread of invasive species.",
            "what_we_report": (
                "Relevant for digestate distribution to KZN farmlands — weed seeds in feedstock "
                "and digestate should be managed via pasteurisation / thermophilic digestion and "
                "recipient guidance. Tracked via BL Turner process records."
            ),
            "status": "Comply or explain: TNFD placeholder indicator",
        },
        {
            "metric_id": "C5.0",
            "metric_name": "Ecosystem condition",
            "what_it_means": "How healthy the ecosystem is, compared to its natural reference state.",
            "what_we_report": (
                f"NDVI now: {_fmt(m.get('ndvi_current'), 3)}. NDVI trend over time: {_fmt(m.get('ndvi_trend'), 3)}. "
                f"Tree cover: {_fmt(m.get('tree_cover_context_pct') or m.get('tree_pct'), 1, '%')}. "
                "Used as a proxy for condition pending dedicated reference-state data."
            ),
            "status": "Proxy: TNFD placeholder C5.0",
        },
        {
            "metric_id": "C5.1",
            "metric_name": "Species extinction risk",
            "what_it_means": "Whether species expected at the site are at higher risk of disappearing.",
            "what_we_report": (
                "Species-risk context for the KZN coastal belt is provided qualitatively "
                "(grassland and forest-edge fauna, wetland-dependent species). A Map of Life "
                "species layer is recommended as a follow-on enhancement for the KwaDukuza site."
            ),
            "status": "Roadmap item (Map of Life integration)",
        },
        {
            "metric_id": "C6.x",
            "metric_name": "Nature-related transition risk exposure",
            "what_it_means": "Financial exposure to policy or market changes driven by nature concerns.",
            "what_we_report": (
                "The business is directly aligned with nature-positive transition — it profits from "
                "landfill-diversion regulation, organic-waste ban trends, and the growing organic "
                "fertiliser market. Transition risk is low on the upside; on the downside, changes "
                "in municipal waste contracts and feed-in tariffs for biogas should be monitored."
            ),
            "status": "Qualitative disclosure",
        },
        {
            "metric_id": "C7.0–C7.1",
            "metric_name": "Nature-related physical risk and opportunities",
            "what_it_means": "Physical exposure to heat, flood, fire and drought, and opportunity indicators.",
            "what_we_report": (
                f"Heat: {_fmt(m.get('lst_mean'), 1, ' °C')}. "
                f"Flood 1-in-100 depth: {_fmt(m.get('flood_risk'), 2, ' m')}. "
                f"Fire signal: {_fmt(m.get('fire_risk'), 1)}. "
                f"PDSI drought: {_fmt(m.get('pdsi'), 1)}. "
                "Opportunity: organic-fertiliser receiving areas with declining soil condition."
            ),
            "status": "Direct measurement / proxy",
        },
    ]


# -----------------------------------------------------------------------------
# Nature Positive Initiative — State of Nature indicators
# -----------------------------------------------------------------------------

def build_npi_state_of_nature_rows(metrics: Dict[str, Any]) -> List[Dict[str, str]]:
    m = metrics

    return [
        {
            "indicator": "IND1: Ecosystem extent",
            "what_it_means": "How much of the land still carries natural or semi-natural ecosystem cover.",
            "what_we_report": (
                f"Tree / semi-natural cover in the landscape around the plant: "
                f"{_fmt(m.get('tree_cover_context_pct') or m.get('tree_pct'), 1, '%')}. "
                f"Cropland: {_fmt(m.get('cropland_pct'), 1, '%')}. "
                f"Built-up: {_fmt(m.get('built_pct'), 1, '%')}."
            ),
            "maturity": "Available",
        },
        {
            "indicator": "IND2: Ecosystem condition",
            "what_it_means": "How healthy or degraded the ecosystem is compared to a good reference state.",
            "what_we_report": (
                f"Current NDVI: {_fmt(m.get('ndvi_current'), 3)}. "
                f"NDVI trend: {_fmt(m.get('ndvi_trend'), 3)}. "
                f"Soil organic carbon proxy: {_fmt(m.get('soil_organic_carbon'), 1)}. "
                "Digestate off-take to KZN farms is expected to improve ecosystem condition on "
                "receiving fields over time by raising soil carbon and reducing synthetic inputs."
            ),
            "maturity": "Proxy",
        },
        {
            "indicator": "IND3: Landscape intactness",
            "what_it_means": "How connected and undisturbed the surrounding landscape is.",
            "what_we_report": (
                f"Forest loss in the landscape: {_fmt(m.get('forest_loss_pct'), 1, '%')}. "
                f"Water seasonality: {_fmt(m.get('water_seasonality'), 1, ' months of water')}. "
                f"Built-up share: {_fmt(m.get('built_pct'), 1, '%')}. "
                "Landfill diversion contributes to landscape intactness by slowing landfill expansion."
            ),
            "maturity": "Proxy",
        },
        {
            "indicator": "IND4: Species extinction risk",
            "what_it_means": "Whether species expected at the site face higher extinction risk.",
            "what_we_report": (
                "Not directly computed in this version. KZN coastal belt supports species groups "
                "including wetland-associated birds and forest-edge fauna that benefit from reduced "
                "landfill leachate and odour pressure. A Map of Life integration is the intended next step."
            ),
            "maturity": "Future extension",
        },
    ]


# -----------------------------------------------------------------------------
# LEAP phase summaries written in plain language
# -----------------------------------------------------------------------------

def plain_language_leap_summary(
    preset: str,
    metrics: Dict[str, Any],
) -> Dict[str, List[str]]:
    """Return a dict keyed by LEAP phase, each value a short list of
    high-school-level sentences for the BL Turner organic waste project."""
    m = metrics

    rain = m.get("rain_anom_pct")
    lst = m.get("lst_mean")
    tree = m.get("tree_cover_context_pct") or m.get("tree_pct")
    ndvi_trend = m.get("ndvi_trend")
    flood = m.get("flood_risk")
    travel = m.get("travel_time_to_market")

    locate = [
        f"These results reflect satellite and environmental signals for {preset} and its surrounding landscape.",
        "The Locate phase defines where the plant meets nature, and where the organic waste comes from. "
        "The main processing site is Portion 159 of New Guelderland, KwaDukuza. Waste is collected from "
        "eThekwini municipality (restaurants, commercial kitchens, distribution centres) and the iLembe "
        "district. Digestate fertiliser is distributed to KZN farmlands.",
    ]
    if tree is not None:
        locate.append(
            f"Around the plant site, about {float(tree):.1f}% of the surrounding landscape carries trees or "
            "similar semi-natural cover. That matters because this buffer helps disperse odour, supports "
            "wildlife, and softens the visual impact of an industrial facility."
        )

    evaluate = [
        "The Evaluate phase looks at what the business depends on from nature and where operations may place "
        "pressure on natural systems.",
        "The plant depends on reliable organic-waste feedstock, process water, stable electricity for CHP "
        "startup, and flood/heat resilience. Off-site, the digestate product depends on KZN farms that can "
        "put organic fertiliser to good use.",
    ]
    if rain is not None:
        try:
            f = float(rain)
            if f < -10:
                evaluate.append(
                    f"Rain is running about {abs(f):.0f}% below the long-term average. That squeezes process "
                    "water and slurry preparation, and raises municipal water cost. Plan for water recycling "
                    "and storage."
                )
            elif f > 15:
                evaluate.append(
                    f"Rain is about {f:.0f}% above the long-term average. Check stormwater around digester "
                    "tanks and feedstock reception — KZN has recent history of severe floods."
                )
            else:
                evaluate.append("Rainfall is broadly close to the long-term average, so rainfall alone is not the main story here.")
        except Exception:
            pass
    if ndvi_trend is not None:
        try:
            t = float(ndvi_trend)
            if t < -0.02:
                evaluate.append(
                    "Vegetation in the landscape is trending downward. For the digestate side of the "
                    "business, that is both a risk (weaker landscape resilience) and an opportunity (farms "
                    "in need of organic fertiliser to rebuild soil carbon)."
                )
            elif t > 0.02:
                evaluate.append(
                    "Vegetation in the landscape is trending upward. That suggests the wider landscape "
                    "around the plant is holding up, and gives the project a stable environmental setting."
                )
        except Exception:
            pass

    assess = [
        "In 'Assess' we ask: so what? What do these signals mean for operations, revenue, and the "
        "nature-positive story?",
    ]
    if lst is not None and float(lst) > 30:
        assess.append(
            f"Surface heat around {float(lst):.1f} °C is high enough to raise CHP cooling load, affect "
            "reception-bay odour control, and reduce outdoor worker productivity."
        )
    if flood is not None and float(flood) > 0.1:
        assess.append(
            f"Modelled flood depth of about {float(flood):.2f} m in a 1-in-100-year event means digester "
            "tanks, CHP units and switchgear need to be sited on the highest ground and protected by bunds. "
            "KZN's 2022 floods showed why this matters."
        )
    if travel is not None and float(travel) > 90:
        assess.append(
            f"Estimated travel time to the main eThekwini feedstock market is about {float(travel):.0f} "
            "minutes. For meat and blood from abattoirs that is long — a refrigerated transfer station or "
            "off-peak collection windows could reduce spoilage and fuel cost."
        )
    assess.append(
        "On the upside, diverting 100 t/day of organic waste from landfill is a major nature-positive "
        "story. At screening assumptions this is roughly 9,125 tCO₂e avoided per year. Quantifying and "
        "verifying this is one of the most valuable things the business can do for TNFD alignment, "
        "municipal relationships, and potential carbon-market revenue."
    )

    prepare = [
        "In 'Prepare' we ask: what do we actually do next, and how do we show progress?",
        "Pick two or three recommendations that can start in the next 90 days: secure multi-source "
        "feedstock contracts, lock in process-water supply, and raise flood resilience of critical "
        "infrastructure. Track each one as a simple monthly KPI.",
        "When engaging eThekwini, iLembe, farmers, banks or funders, present these nature readings "
        "alongside financial and operational records. That is the whole point of nature intelligence: "
        "linking ecology to cash flow and to the social licence to operate.",
    ]

    return {
        "Locate": locate,
        "Evaluate": evaluate,
        "Assess": assess,
        "Prepare": prepare,
    }
