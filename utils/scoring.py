"""
EagleNatureInsight scoring / interpretation layer — BL Turner edition.

Tailored for BL Turner Group's organic waste-to-fertiliser and biogas
project at Portion 159 of New Guelderland, KwaDukuza (iLembe District,
Northern KwaZulu-Natal), with feedstock sourced from eThekwini
Metropolitan Municipality and the wider iLembe / Western KZN catchment.

Design choices (aligned with TNFD September 2023 recommendations and
TNFD-client feedback received during the Nature Intelligence for
Business Grand Challenge):

1. No single aggregate risk score. TNFD explicitly advises against
   reducing nature-related issues to one number. This module returns a
   portfolio of indicators, each with its own status, plain-language
   meaning, suggested response, and (where possible) an indicative
   monetary exposure proxy.

2. Dependencies are framed as TNFD-style dependency pathways
   (ecosystem services the business relies on), not as a generic
   water/heat/habitat list. For an anaerobic-digestion and organic
   fertiliser producer, the material dependencies centre on: organic
   waste feedstock supply, process water, nutrient cycling, soil
   health in fertiliser receiving areas, flood/heat resilience of the
   plant, and avoided methane emissions from landfill diversion.

3. Recommendations avoid jargon and are written at roughly a high
   school reading level, per TNFD feedback. Each recommendation is a
   complete sentence that says what to do and why, in plain English.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _as_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        f = float(value)
    except Exception:
        return None
    if f != f:  # NaN
        return None
    return f


def _band_higher_is_better(value: Optional[float], good: float, watch: float) -> str:
    if value is None:
        return "Not available"
    if value >= good:
        return "Favourable"
    if value >= watch:
        return "Watch"
    return "Warning"


def _band_lower_is_better(value: Optional[float], good: float, watch: float) -> str:
    if value is None:
        return "Not available"
    if value <= good:
        return "Favourable"
    if value <= watch:
        return "Watch"
    return "Warning"


# -----------------------------------------------------------------------------
# TNFD-style dependency pathways, tailored to organic waste / AD / fertiliser
# -----------------------------------------------------------------------------
# Each dependency names an ecosystem service that a 100 t/day organic
# waste-to-fertiliser and biogas plant relies on, why it matters, and
# which satellite indicator gives a partial view.
#
# Sources: TNFD Additional Guidance on the LEAP Approach (Sept 2023),
# TNFD sector guidance appendices for Food & Agriculture and Water &
# Waste Utilities, and the ENCORE dependency database for waste
# management and nutrient cycling.

ORGANIC_WASTE_DEPENDENCIES = [
    {
        "service": "Organic waste feedstock supply (anthropogenic resource)",
        "why_it_matters": (
            "The plant's core input is 100 tonnes of organic waste per day. "
            "This comes from vegetable and fruit waste from municipalities, "
            "food waste from restaurants and distribution centres in "
            "eThekwini, and meat and blood from abattoirs. If these flows "
            "are disrupted by strikes, load-shedding of cold rooms, or "
            "seasonal shortages, the plant cannot operate at capacity."
        ),
        "linked_indicators": ["built_pct", "travel_time_to_market", "area_ha"],
    },
    {
        "service": "Water provisioning (process water for anaerobic digestion)",
        "why_it_matters": (
            "Anaerobic digesters need process water for slurry preparation, "
            "dilution and equipment cleaning. KZN has recurrent water-"
            "restriction cycles, so dependable water supply and internal "
            "water recycling are critical for 100 t/day continuity."
        ),
        "linked_indicators": ["rain_anom_pct", "water_occ", "soil_moisture", "climate_water_deficit"],
    },
    {
        "service": "Water flow regulation (flood and stormwater management)",
        "why_it_matters": (
            "New Guelderland sits in a low-lying coastal landscape that has "
            "been hit by severe flooding, including the April 2022 KZN "
            "floods. Healthy wetlands and vegetated drainage lines slow "
            "runoff and protect digester tanks, CHP units and feedstock "
            "reception bays from inundation."
        ),
        "linked_indicators": ["flood_risk", "tree_cover_context_pct", "water_seasonality"],
    },
    {
        "service": "Nutrient cycling and soil-condition support (fertiliser use areas)",
        "why_it_matters": (
            "The digestate fertiliser product is distributed to KZN "
            "farmlands and outer-lying areas. Its value to off-takers "
            "depends on soil condition, cropping intensity, nitrogen "
            "demand, and organic-carbon levels in the receiving fields."
        ),
        "linked_indicators": ["soil_organic_carbon", "soil_texture_class", "ndvi_trend", "cropland_pct"],
    },
    {
        "service": "Landfill diversion capacity (waste-regulating service)",
        "why_it_matters": (
            "Diverting organic waste away from the adjacent KwaDukuza "
            "landfill avoids methane emissions, reduces leachate pressure, "
            "and extends the life of the landfill cell. This is a direct "
            "nature-positive outcome that funders, municipalities and "
            "off-takers increasingly want to see quantified."
        ),
        "linked_indicators": ["built_pct", "forest_loss_pct"],
    },
    {
        "service": "Microclimate and heat regulation (plant operations)",
        "why_it_matters": (
            "Digesters are temperature-sensitive (mesophilic 35–40 °C, "
            "thermophilic 50–55 °C). Extreme ambient heat raises cooling "
            "load on CHP systems and affects the safety of outdoor "
            "reception areas handling abattoir and food waste."
        ),
        "linked_indicators": ["lst_mean", "tree_cover_context_pct"],
    },
    {
        "service": "Surrounding habitat and species context",
        "why_it_matters": (
            "The site sits close to KwaZulu-Natal coastal habitat, "
            "including species that use wetland, forest and field-edge "
            "cover. Poor odour or leachate management can affect nearby "
            "wetlands, bird habitat, and communities."
        ),
        "linked_indicators": ["bio_proxy"],
    },
]


# -----------------------------------------------------------------------------
# Monetary / business exposure proxies
# -----------------------------------------------------------------------------
# Indicative directional signals specific to a 100 t/day organic
# waste-to-fertiliser and biogas facility. All assumptions are stated
# in plain English so the user can sense-check.

def _feedstock_disruption_exposure(
    rain_anom_pct: Optional[float],
    flood_m: Optional[float],
    travel_min: Optional[float],
) -> Optional[Dict[str, Any]]:
    """Risk of feedstock supply disruption translated into revenue at risk."""
    # Revenue at risk assumption:
    # - 100 t/day * 365 days = 36,500 t/year
    # - Combined tipping fees + biogas + fertiliser revenue ~ USD 60/t
    # - Annual revenue ~ USD 2.19 million; daily exposure ~ USD 6,000/day
    daily_revenue = 6000.0
    disruption_days = 0
    drivers: List[str] = []

    if flood_m is not None:
        try:
            f = float(flood_m)
            if f >= 0.5:
                disruption_days += 7
                drivers.append(f"mapped 1-in-100 year flood depth of {f:.2f} m around the site")
            elif f > 0.1:
                disruption_days += 2
                drivers.append(f"mapped flood depth of {f:.2f} m on surrounding land")
        except Exception:
            pass

    if travel_min is not None:
        try:
            t = float(travel_min)
            if t > 120:
                disruption_days += 3
                drivers.append(f"travel time to the main collection market of about {t:.0f} minutes")
        except Exception:
            pass

    if rain_anom_pct is not None:
        try:
            r = float(rain_anom_pct)
            if r < -20:
                disruption_days += 2
                drivers.append(f"rainfall sitting about {abs(r):.0f}% below the long-term average")
        except Exception:
            pass

    if disruption_days == 0:
        return {
            "headline": "No dominant feedstock-disruption signal from the current indicators.",
            "assumption": (
                "Based on flood, rainfall and logistics signals being within "
                "a manageable range. Actual risk also depends on contracts "
                "with municipalities, abattoirs and distribution centres."
            ),
        }

    usd = daily_revenue * disruption_days
    drivers_text = "; ".join(drivers) if drivers else "current environmental and logistics signals"
    return {
        "headline": f"Indicative feedstock-disruption revenue at risk of around USD {usd:,.0f} per year.",
        "assumption": (
            f"Screening figure assuming roughly USD {daily_revenue:,.0f} per day of combined "
            f"tipping-fee, biogas and fertiliser revenue at nameplate 100 t/day, and that the "
            f"following drivers could together cause {disruption_days} day(s) of reduced "
            f"throughput in a typical year: {drivers_text}. Actual exposure depends on "
            f"contractual cover, on-site storage, and backup logistics."
        ),
    }


def _water_cost_exposure(rain_anom_pct: Optional[float]) -> Optional[Dict[str, Any]]:
    """Process water cost under dry conditions."""
    if rain_anom_pct is None:
        return None
    if rain_anom_pct >= 0:
        return {
            "headline": "No additional process-water cost signal from rainfall right now.",
            "assumption": (
                "Based on rainfall being at or above the long-term baseline "
                "for this site."
            ),
        }
    # 100 t/day feedstock typically requires ~30–50 m3/day of process water.
    # Assume baseline cost of USD 1.50/m3 in KZN municipal supply, rising by
    # roughly 5% for each 10% rainfall shortfall due to restrictions and
    # trucked-in top-ups.
    pct_shortfall = abs(rain_anom_pct)
    uplift_pct = (pct_shortfall / 10.0) * 5.0
    baseline_annual = 40.0 * 365.0 * 1.5  # USD ~21,900 baseline
    extra = baseline_annual * (uplift_pct / 100.0)
    return {
        "headline": f"Indicative extra process-water cost of around USD {extra:,.0f} this year.",
        "assumption": (
            f"Rough screening figure assuming about 40 m³/day of process water at "
            f"around USD 1.50/m³ baseline, with cost rising ~5% for every 10% the "
            f"rainfall sits below the long-term average (covering restrictions, "
            f"trucked-in water, and internal recycling top-up). Actual cost depends "
            f"on municipal tariffs and internal water recycling design."
        ),
    }


def _heat_operations_exposure(lst_mean: Optional[float]) -> Optional[Dict[str, Any]]:
    if lst_mean is None:
        return None
    if lst_mean < 28:
        return {
            "headline": "Heat levels do not suggest a strong operations penalty right now.",
            "assumption": "Based on average land surface temperature below about 28 °C.",
        }
    if lst_mean < 30:
        pct = 2
    elif lst_mean < 33:
        pct = 5
    else:
        pct = 8
    return {
        "headline": (
            f"Potential CHP cooling and worker-productivity uplift of about {pct}% "
            f"while surface heat stays around {lst_mean:.1f} °C."
        ),
        "assumption": (
            "Illustrative screening figure. Hotter surface conditions increase "
            "chiller and CHP cooling load, raise odour volatility at reception "
            "bays, and reduce outdoor worker productivity. The exact cost depends "
            "on CHP unit specs, reception shed ventilation, and staffing rosters."
        ),
    }


def _flood_asset_exposure(flood_risk_m: Optional[float], area_ha: Optional[float]) -> Optional[Dict[str, Any]]:
    if flood_risk_m is None or area_ha is None:
        return None
    if flood_risk_m <= 0.05:
        return {
            "headline": "No meaningful mapped flood exposure on the plant site.",
            "assumption": "Based on modelled 1-in-100-year flood depth at or near zero.",
        }
    # Industrial asset density for a biogas + digestate plant is higher than
    # a farm field — use ~ USD 18,000/ha per 0.5 m depth as a screening
    # heuristic (tanks, CHP units, gas cleaning, pumps, feedstock handling).
    exposure = (flood_risk_m / 0.5) * 18000.0 * max(area_ha, 1.0)
    return {
        "headline": f"Indicative flood exposure in the order of USD {exposure:,.0f} per 1-in-100-year event.",
        "assumption": (
            "Screening figure only. Assumes roughly USD 18,000 per hectare in "
            "exposed digester, CHP, pumps and feedstock-handling infrastructure "
            "for every half-metre of mapped flood depth. Actual loss depends on "
            "tank bunds, electrical switchgear elevation, and drainage design."
        ),
    }


def _landfill_diversion_benefit(area_ha: Optional[float]) -> Optional[Dict[str, Any]]:
    """Positive-side figure: indicative avoided methane emissions from landfill diversion."""
    # 100 t/day * 365 = 36,500 t/year of organic waste diverted.
    # IPCC / EPA screening figure: ~0.25 t CO2e avoided per tonne of food waste
    # diverted from landfill (methane avoided minus process emissions).
    annual_tonnes = 36500.0
    avoided_co2e = annual_tonnes * 0.25
    # Indicative carbon price in voluntary markets: USD 8 / tCO2e.
    revenue_signal = avoided_co2e * 8.0
    return {
        "headline": (
            f"Indicative avoided emissions of about {avoided_co2e:,.0f} tCO₂e per year, "
            f"equivalent to around USD {revenue_signal:,.0f} in voluntary carbon-market value."
        ),
        "assumption": (
            "Screening figure assuming nameplate throughput of 100 t/day of food and "
            "organic waste diverted from landfill, an avoided-methane factor of "
            "roughly 0.25 tCO₂e per tonne diverted (net of process emissions), and "
            "a voluntary carbon price around USD 8/tCO₂e. Actual value depends on "
            "methodology approval (e.g. Verra, Gold Standard) and the buyer contract."
        ),
    }


def build_monetary_exposures(metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return a list of indicative monetary / business exposure cards."""
    rain = _as_float(metrics.get("rain_anom_pct"))
    lst = _as_float(metrics.get("lst_mean"))
    flood = _as_float(metrics.get("flood_risk"))
    travel = _as_float(metrics.get("travel_time_to_market"))
    area = _as_float(metrics.get("area_ha"))

    exposures = []

    item = _feedstock_disruption_exposure(rain, flood, travel)
    if item:
        exposures.append({"label": "Feedstock-disruption revenue at risk", **item})

    item = _water_cost_exposure(rain)
    if item:
        exposures.append({"label": "Process-water cost exposure", **item})

    item = _heat_operations_exposure(lst)
    if item:
        exposures.append({"label": "Heat and CHP cooling exposure", **item})

    item = _flood_asset_exposure(flood, area)
    if item:
        exposures.append({"label": "Flood asset exposure", **item})

    item = _landfill_diversion_benefit(area)
    if item:
        exposures.append({"label": "Landfill diversion benefit (nature-positive side)", **item})

    return exposures


# -----------------------------------------------------------------------------
# Portfolio of indicators (replaces the old single risk score)
# -----------------------------------------------------------------------------
# Each indicator returns: {name, status, plain_meaning, response}
# Statuses: Favourable / Watch / Warning / Not available
# This mirrors TNFD's guidance that indicators should be reported
# individually ("comply or explain") rather than aggregated into one
# number.

def build_indicator_portfolio(metrics: Dict[str, Any]) -> List[Dict[str, str]]:
    rows = []

    rain = _as_float(metrics.get("rain_anom_pct"))
    rows.append({
        "name": "Rainfall vs long-term baseline",
        "status": _band_higher_is_better(rain, -5, -15) if rain is not None else "Not available",
        "plain_meaning": (
            f"Recent rainfall is about {rain:.1f}% relative to the long-term baseline." if rain is not None else
            "Rainfall comparison was not available for this site."
        ),
        "response": (
            "If rainfall is well below average, plan ahead with process-water "
            "storage, water recycling from digestate dewatering, and contracts "
            "with alternative water providers. If well above, check flood "
            "defences and stormwater drains around digester tanks."
        ),
    })

    ndvi = _as_float(metrics.get("ndvi_current"))
    rows.append({
        "name": "Current vegetation condition around the plant",
        "status": _band_higher_is_better(ndvi, 0.40, 0.25) if ndvi is not None else "Not available",
        "plain_meaning": (
            f"Vegetation 'greenness' around the plant reads {ndvi:.2f}. Higher means more living vegetation." if ndvi is not None else
            "Vegetation greenness was not available."
        ),
        "response": (
            "Maintain a green buffer around the plant — it helps with odour "
            "dispersion, worker amenity, and community relations, and signals "
            "ecological care to funders and local stakeholders."
        ),
    })

    ndvi_trend = _as_float(metrics.get("ndvi_trend"))
    rows.append({
        "name": "Vegetation trend in the surrounding landscape",
        "status": _band_higher_is_better(ndvi_trend, 0.0, -0.03) if ndvi_trend is not None else "Not available",
        "plain_meaning": (
            f"The vegetation trend is {ndvi_trend:.3f}. Below zero means the landscape is losing green cover over time." if ndvi_trend is not None else
            "Vegetation trend was not available."
        ),
        "response": (
            "A falling trend can mean land-use change, fire, or drought pressure. "
            "For the digestate off-take business, it can also mean farms "
            "needing organic fertiliser to rebuild soil carbon — a commercial "
            "opportunity worth mapping."
        ),
    })

    lst = _as_float(metrics.get("lst_mean"))
    rows.append({
        "name": "Heat stress (land surface temperature)",
        "status": _band_lower_is_better(lst, 28, 32) if lst is not None else "Not available",
        "plain_meaning": (
            f"Average land surface temperature reads about {lst:.1f} °C." if lst is not None else
            "Heat stress was not available."
        ),
        "response": (
            "High heat raises CHP cooling needs, odour volatility at reception "
            "bays and worker-safety risk. Check chiller capacity, ventilation, "
            "and shaded storage for meat and blood inputs."
        ),
    })

    tree = _as_float(metrics.get("tree_cover_context_pct")) or _as_float(metrics.get("tree_pct"))
    rows.append({
        "name": "Tree cover and vegetated buffer around the plant",
        "status": _band_higher_is_better(tree, 15, 5) if tree is not None else "Not available",
        "plain_meaning": (
            f"Roughly {tree:.1f}% of the surrounding landscape carries tree or tall semi-natural cover." if tree is not None else
            "Tree cover context was not available."
        ),
        "response": (
            "Retain or plant vegetated buffers along the plant perimeter. "
            "They dampen odour, reduce dust and noise, support biodiversity, "
            "and strengthen the social licence to operate."
        ),
    })

    water = _as_float(metrics.get("water_context_signal_pct")) or _as_float(metrics.get("water_occ"))
    rows.append({
        "name": "Surface water presence in the landscape",
        "status": _band_higher_is_better(water, 15, 5) if water is not None else "Not available",
        "plain_meaning": (
            f"The mapped surface water signal is about {water:.1f}. Lower values mean less visible standing water near the site." if water is not None else
            "Surface water signal was not available."
        ),
        "response": (
            "Less visible surface water raises dependence on the municipal supply "
            "and on-site storage. Invest in digestate-liquor recycling and design "
            "for zero-liquid-discharge where feasible."
        ),
    })

    flood = _as_float(metrics.get("flood_risk"))
    rows.append({
        "name": "Flood hazard (1-in-100-year modelled depth)",
        "status": _band_lower_is_better(flood, 0.1, 0.5) if flood is not None else "Not available",
        "plain_meaning": (
            f"Modelled 1-in-100-year flood depth is about {flood:.2f} m across the site." if flood is not None else
            "Flood hazard was not available."
        ),
        "response": (
            "Site digester tanks, CHP units, gas cleaning, and switchgear on the "
            "highest ground available, with bunds around tanks. Review drainage "
            "before each rainy season. KZN has recent history of severe floods "
            "so this is a priority."
        ),
    })

    travel_time = _as_float(metrics.get("travel_time_to_market"))
    rows.append({
        "name": "Logistics and travel time to the main waste market (eThekwini)",
        "status": _band_lower_is_better(travel_time, 60, 120) if travel_time is not None else "Not available",
        "plain_meaning": (
            f"Estimated travel time to the main market is about {travel_time:.0f} minutes." if travel_time is not None else
            "Market access was not available."
        ),
        "response": (
            "Longer travel time raises diesel and driver cost per load, "
            "increases spoilage risk for meat and blood waste, and tightens "
            "the contract terms you can offer. Consider a satellite transfer "
            "station or refrigerated pre-sorting closer to the feedstock."
        ),
    })

    fire = _as_float(metrics.get("fire_risk"))
    rows.append({
        "name": "Fire signal in the surrounding landscape",
        "status": _band_lower_is_better(fire, 0.5, 5) if fire is not None else "Not available",
        "plain_meaning": (
            f"The recent burned-area indicator reads {fire:.1f}." if fire is not None else
            "Fire signal was not available."
        ),
        "response": (
            "Biogas facilities handle flammable methane. Maintain firebreaks "
            "around the plant perimeter, avoid dry vegetation build-up near "
            "gas storage, and align with local fire-management plans."
        ),
    })

    forest_loss = _as_float(metrics.get("forest_loss_pct"))
    rows.append({
        "name": "Forest loss in the surrounding landscape",
        "status": _band_lower_is_better(forest_loss, 1, 5) if forest_loss is not None else "Not available",
        "plain_meaning": (
            f"About {forest_loss:.1f}% of the surrounding baseline forest has been lost in the observed period." if forest_loss is not None else
            "Forest loss was not available."
        ),
        "response": (
            "Continued loss weakens natural buffers around the plant and can "
            "worsen runoff and flood risk. Where the business can influence "
            "land use (e.g. via digestate off-take contracts), favour farmers "
            "who keep woodlots and wetlands."
        ),
    })

    return rows


def portfolio_summary(rows: List[Dict[str, str]]) -> Dict[str, int]:
    counts = {"Favourable": 0, "Watch": 0, "Warning": 0, "Not available": 0}
    for r in rows:
        s = r.get("status", "Not available")
        if s not in counts:
            s = "Not available"
        counts[s] += 1
    return counts


# -----------------------------------------------------------------------------
# Sector-specific recommendations (plain language)
# -----------------------------------------------------------------------------

def _organic_waste_recommendations(metrics: Dict[str, Any]) -> List[str]:
    recs: List[str] = []
    rain = _as_float(metrics.get("rain_anom_pct"))
    if rain is not None and rain < -10:
        recs.append(
            f"Rainfall is about {abs(rain):.0f}% below the long-term average. Before the next dry season, "
            "confirm process-water contracts with the municipality, size on-site water storage for at least "
            "a week of autonomy, and design digestate-liquor recycling into the slurry prep loop."
        )
    if rain is not None and rain > 15:
        recs.append(
            f"Rainfall is about {rain:.0f}% above the long-term average. Check stormwater drains around the "
            "digester tanks and feedstock reception bays, and make sure fuel and gas storage areas are above "
            "any possible standing water."
        )
    lst = _as_float(metrics.get("lst_mean"))
    if lst is not None and lst > 30:
        recs.append(
            f"Surface heat is running around {lst:.1f} °C. Review CHP cooling capacity, ventilation in the "
            "reception hall handling meat and blood waste, and make sure outdoor workers have shaded rest areas "
            "and hydration."
        )
    flood = _as_float(metrics.get("flood_risk"))
    if flood is not None and flood > 0.1:
        recs.append(
            f"There is mapped 1-in-100-year flood depth of about {flood:.2f} m around parts of the site. "
            "Raise digester tank plinths, put switchgear and control rooms above the flood line, and build "
            "bunds around chemical and gas storage."
        )
    tree = _as_float(metrics.get("tree_cover_context_pct")) or _as_float(metrics.get("tree_pct"))
    if tree is not None and tree < 10:
        recs.append(
            "Tree cover around the site is limited. Plant a vegetated buffer along the plant perimeter — "
            "it dampens odour and dust, softens the visual impact, and improves community relations. Choose "
            "indigenous species suited to KZN coastal conditions."
        )
    travel = _as_float(metrics.get("travel_time_to_market"))
    if travel is not None and travel > 90:
        recs.append(
            f"Feedstock travel time to eThekwini is about {travel:.0f} minutes. For meat, blood and food-waste "
            "loads, consider a refrigerated transfer station closer to the city, or off-peak collection windows, "
            "to reduce spoilage and fuel cost."
        )
    ndvi_trend = _as_float(metrics.get("ndvi_trend"))
    if ndvi_trend is not None and ndvi_trend < -0.02:
        recs.append(
            "Vegetation in the surrounding landscape is trending downward. For the digestate off-take side of "
            "the business, this is both a risk and an opportunity: target farms where organic-fertiliser can "
            "rebuild soil carbon, and document the improvement over time as a nature-positive outcome."
        )
    fire = _as_float(metrics.get("fire_risk"))
    if fire is not None and fire > 5:
        recs.append(
            "A recent burned-area signal is present in the landscape. Given the site handles flammable biogas, "
            "keep firebreaks around the plant perimeter, avoid dry vegetation near gas storage, and align "
            "fire-response plans with local municipal services."
        )

    # Always-on recommendations specific to an anaerobic-digestion business.
    recs.extend([
        "Secure multi-source feedstock contracts (municipal organics, restaurant waste, distribution-centre "
        "expired food, abattoir waste) so that no single stream accounts for more than about 40% of input. "
        "This protects continuity when any one supplier has a disruption.",
        "Build a seasonal feedstock plan: fruit and vegetable waste peaks with seasonal harvests, restaurant "
        "waste peaks over holiday periods, and abattoir waste runs more evenly. Match digester feeding to "
        "these patterns to keep biogas output stable.",
        "Quantify avoided methane emissions from landfill diversion early and track them monthly. This is the "
        "single strongest nature-positive story the business has, and it is exactly what TNFD, banks, and "
        "off-takers want to see.",
        "Include the digestate fertiliser receiving areas (KZN farmlands and outer-lying areas) in the nature "
        "assessment, not only the plant site. The biggest nature benefit of this business happens off-site, "
        "on the fields that replace synthetic fertiliser with organic digestate.",
    ])

    # De-duplicate while keeping order.
    seen = set()
    clean = []
    for r in recs:
        if r not in seen:
            clean.append(r)
            seen.add(r)
    return clean


def build_risk_and_recommendations(preset: str, category: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main public function. Returns a dict shaped for compatibility with
    the existing app.py, BUT no longer exposes a single score or band.

    Keys:
      - recs: list of plain-language recommendations
      - portfolio: list of indicators (replaces score + band)
      - portfolio_summary: counts of each status
      - dependencies: list of TNFD-style dependency pathways
      - monetary_exposures: list of indicative USD / productivity exposures
      - flags: retained for back-compat; list of the indicator names in
               Watch or Warning status
      - score / band: kept but deprecated (None / "Not applicable")
    """
    portfolio = build_indicator_portfolio(metrics)
    summary = portfolio_summary(portfolio)
    deps = ORGANIC_WASTE_DEPENDENCIES
    mone = build_monetary_exposures(metrics)

    flags = [r["name"] for r in portfolio if r.get("status") in ("Watch", "Warning")]

    recs = _organic_waste_recommendations(metrics)

    if preset and "blturner" in preset.lower().replace(" ", ""):
        recs.append(
            "Use these results in BL Turner's stakeholder engagements with eThekwini, iLembe and KZN farm "
            "partners. They give an evidence-based starting point for conversations on landfill diversion, "
            "water use, flood resilience and the nature-positive story of organic fertiliser."
        )

    return {
        "score": None,
        "band": "Not applicable",
        "flags": flags,
        "recs": recs[:12],
        "portfolio": portfolio,
        "portfolio_summary": summary,
        "dependencies": deps,
        "monetary_exposures": mone,
    }
