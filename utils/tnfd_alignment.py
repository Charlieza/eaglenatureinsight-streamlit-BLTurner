
"""
TNFD and Nature Positive Initiative alignment content for BL Turner,
extended to incorporate Map of Life where available.
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


def build_tnfd_core_metrics_rows(metrics: Dict[str, Any], mol_insights: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
    m = metrics
    species_status = "Roadmap item (Map of Life integration)"
    species_report = (
        "Species-risk context for the KZN coastal belt is provided qualitatively "
        "(grassland and forest-edge fauna, wetland-dependent species). A Map of Life "
        "species layer is recommended as a follow-on enhancement for the KwaDukuza site."
    )
    if mol_insights:
        species_status = "Map of Life screening layer"
        species_report = (
            f"Map of Life indicates {mol_insights.get('species_total', 'Not measured yet')} expected species "
            f"for {mol_insights.get('site_name', 'the mapped area')}, including "
            f"{mol_insights.get('threatened_total', 'Not measured yet')} threatened or near-threatened species. "
            f"Latest SHI: {_fmt(mol_insights.get('latest_shi'), 1)}; change since 2001: "
            f"{_fmt(mol_insights.get('shi_change_total'), 2)}."
        )

    return [
        {
            "metric_id": "C1.0",
            "metric_name": "Total spatial footprint",
            "what_it_means": "How much surface area the project controls or manages.",
            "what_we_report": (
                f"{_fmt(m.get('area_ha'), 2, ' ha')} plant-site footprint "
                f"(Portion 159 of New Guelderland, KwaDukuza, nominal 1.5 ha / 15,000 m²)."
            ),
            "status": "Direct measurement" if m.get("area_ha") else "Not available",
        },
        {
            "metric_id": "C1.1",
            "metric_name": "Extent of land / freshwater / ecosystem-use change",
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
            "metric_name": "Pollutants, waste and air emissions",
            "what_it_means": "Pollution released into soil, water and air; waste generated.",
            "what_we_report": (
                "Not computed from satellite data. For BL Turner this comes from plant environmental "
                "monitoring such as CHP stack, digestate sampling, odour boundary monitoring and noise."
            ),
            "status": "Comply or explain: requires BL Turner operational data",
        },
        {
            "metric_id": "C2.5",
            "metric_name": "GHG emissions",
            "what_it_means": "Greenhouse gas emissions and avoided emissions.",
            "what_we_report": (
                "Indicative landfill-diversion avoided emissions: ~9,125 tCO₂e/year at nameplate "
                "100 t/day throughput (screening assumption, ~0.25 tCO₂e avoided per tonne diverted, "
                "net of process emissions). Final figure needs a formal GHG methodology."
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
            "metric_id": "C5.0",
            "metric_name": "Ecosystem condition",
            "what_it_means": "How healthy or degraded the ecosystem is compared to its natural reference state.",
            "what_we_report": (
                f"NDVI now: {_fmt(m.get('ndvi_current'), 3)}. NDVI trend over time: {_fmt(m.get('ndvi_trend'), 3)}. "
                f"Tree cover: {_fmt(m.get('tree_cover_context_pct') or m.get('tree_pct'), 1, '%')}. "
                f"Map of Life SHI: {_fmt(mol_insights.get('latest_shi'), 1) if mol_insights else 'Not measured yet'}."
            ),
            "status": "Proxy",
        },
        {
            "metric_id": "C5.1",
            "metric_name": "Species extinction risk",
            "what_it_means": "Whether species expected at the site face higher extinction risk.",
            "what_we_report": species_report,
            "status": species_status,
        },
        {
            "metric_id": "C7.0–C7.1",
            "metric_name": "Nature-related physical risk and opportunities",
            "what_it_means": "Physical exposure to heat, flood, fire and drought, and opportunity indicators.",
            "what_we_report": (
                f"Heat: {_fmt(m.get('lst_mean'), 1, ' °C')}. "
                f"Flood depth: {_fmt(m.get('flood_risk'), 2, ' m')}. "
                f"Fire signal: {_fmt(m.get('fire_risk'), 1)}. "
                f"PDSI drought: {_fmt(m.get('pdsi'), 1)}. "
                "Opportunity: digestate use in receiving landscapes with weaker soil condition."
            ),
            "status": "Direct measurement / proxy",
        },
    ]


def build_npi_state_of_nature_rows(metrics: Dict[str, Any], mol_insights: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
    m = metrics
    ind4_report = (
        "Not directly computed in this version. KZN coastal belt supports species groups "
        "including wetland-associated birds and forest-edge fauna that benefit from reduced "
        "landfill leachate and odour pressure. A Map of Life integration is the intended next step."
    )
    ind4_maturity = "Future extension"
    if mol_insights:
        ind4_report = (
            f"Map of Life indicates {mol_insights.get('species_total', 'Not measured yet')} expected species "
            f"for {mol_insights.get('site_name', 'the mapped area')}, including "
            f"{mol_insights.get('threatened_total', 'Not measured yet')} threatened or near-threatened species. "
            f"Latest SHI {_fmt(mol_insights.get('latest_shi'), 1)}; SHI change since 2001 "
            f"{_fmt(mol_insights.get('shi_change_total'), 2)}."
        )
        ind4_maturity = "Available (Map of Life screening layer)"

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
                f"Map of Life SHI: {_fmt(mol_insights.get('latest_shi'), 1) if mol_insights else 'Not measured yet'}."
            ),
            "maturity": "Proxy",
        },
        {
            "indicator": "IND3: Landscape intactness",
            "what_it_means": "How connected and undisturbed the surrounding landscape is.",
            "what_we_report": (
                f"Forest loss in the landscape: {_fmt(m.get('forest_loss_pct'), 1, '%')}. "
                f"Water seasonality: {_fmt(m.get('water_seasonality'), 1, ' months of water')}. "
                f"Built-up share: {_fmt(m.get('built_pct'), 1, '%')}."
            ),
            "maturity": "Proxy",
        },
        {
            "indicator": "IND4: Species extinction risk",
            "what_it_means": "Whether species expected at the site face higher extinction risk.",
            "what_we_report": ind4_report,
            "maturity": ind4_maturity,
        },
    ]


def plain_language_leap_summary(
    preset: str,
    metrics: Dict[str, Any],
    mol_insights: Optional[Dict[str, Any]] = None,
) -> Dict[str, List[str]]:
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
        "eThekwini municipality, the iLembe district, and the uMgungundlovu abattoir corridor.",
    ]
    if tree is not None:
        locate.append(
            f"Around the site, about {float(tree):.1f}% of the surrounding landscape carries trees or "
            "similar semi-natural cover. That matters because buffers help with runoff control, habitat, "
            "visual impact and the social licence to operate."
        )
    if mol_insights:
        locate.append(
            f"Map of Life adds species context for {mol_insights.get('site_name', 'this zone')}: "
            f"{mol_insights.get('species_total', 'Not measured yet')} expected species, including "
            f"{mol_insights.get('threatened_total', 'Not measured yet')} threatened or near-threatened."
        )

    evaluate = [
        "The Evaluate phase looks at what the business depends on from nature and where operations may place pressure on natural systems.",
        "The plant depends on reliable organic-waste feedstock, process water, stable electricity for CHP startup, and flood and heat resilience. "
        "Off-site, the digestate product depends on receiving farms that can use organic fertiliser well.",
    ]
    try:
        if rain is not None:
            f = float(rain)
            if f < -10:
                evaluate.append(
                    f"Rain is running about {abs(f):.0f}% below the long-term average. That squeezes process water "
                    "and raises the importance of storage and recycling."
                )
            elif f > 15:
                evaluate.append(
                    f"Rain is about {f:.0f}% above the long-term average. Check stormwater around the site and access routes."
                )
    except Exception:
        pass
    try:
        if ndvi_trend is not None:
            t = float(ndvi_trend)
            if t < -0.02:
                evaluate.append(
                    "Vegetation in the landscape is trending downward. That can point to a wider landscape under pressure and makes buffers and receiving-land management more important."
                )
            elif t > 0.02:
                evaluate.append(
                    "Vegetation in the landscape is trending upward, which suggests the wider setting is holding up relatively well."
                )
    except Exception:
        pass
    if mol_insights:
        evaluate.append(
            f"The latest Map of Life habitat score is {_fmt(mol_insights.get('latest_shi'), 1)} with change since 2001 of "
            f"{_fmt(mol_insights.get('shi_change_total'), 2)}. This adds a species and habitat suitability signal to the land, water and climate indicators."
        )

    assess = [
        "In Assess we ask what these signals mean for operations, resilience and the wider nature-positive story.",
    ]
    try:
        if lst is not None and float(lst) > 30:
            assess.append(
                f"Surface heat around {float(lst):.1f} °C is high enough to raise CHP cooling load, affect odour control and reduce outdoor worker comfort."
            )
    except Exception:
        pass
    try:
        if flood is not None and float(flood) > 0.1:
            assess.append(
                f"Modelled flood depth of about {float(flood):.2f} m in a 1-in-100-year event means tanks, CHP units and switchgear need flood-resilient siting."
            )
    except Exception:
        pass
    try:
        if travel is not None and float(travel) > 90:
            assess.append(
                f"Estimated travel time to the main eThekwini feedstock market is about {float(travel):.0f} minutes, which matters for meat, blood and perishable food-waste loads."
            )
    except Exception:
        pass
    if mol_insights:
        assess.append(
            f"Species sensitivity matters too: Map of Life identifies {mol_insights.get('threatened_total', 'Not measured yet')} threatened or near-threatened species in this zone. "
            "That raises the importance of keeping wet areas, drainage lines, edge habitat and natural buffers in good condition."
        )

    prepare = [
        "In Prepare we ask what to do next and how to show progress.",
        "Start with practical actions: secure multi-source feedstock contracts, lock in process-water supply, and protect the most sensitive buffers and drainage lines around the site.",
        "When engaging municipalities, farmers, banks or funders, present species and habitat context alongside operational metrics. That is the value of nature intelligence: linking ecology to decisions and cash flow.",
    ]
    if mol_insights:
        prepare.append(
            "Use the Map of Life layer as an early screening tool before siting new infrastructure, extending routes, or planning digestate receiving areas."
        )

    return {"Locate": locate, "Evaluate": evaluate, "Assess": assess, "Prepare": prepare}
