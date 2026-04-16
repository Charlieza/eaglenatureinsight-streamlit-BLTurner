from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional, Tuple

import folium
import pandas as pd
import plotly.express as px
import streamlit as st
from folium.plugins import Draw
from streamlit_folium import st_folium

try:
    from utils.ee_helpers import (
        initialize_ee_from_secrets,
        geojson_to_ee_geometry,
        point_buffer_to_ee_geometry,
        compute_metrics,
        satellite_with_polygon,
        ndvi_with_polygon,
        landcover_with_polygon,
        forest_loss_with_polygon,
        flood_risk_with_polygon,
        soil_condition_with_polygon,
        heat_stress_with_polygon,
        vegetation_change_with_polygon,
        image_thumb_url,
        landsat_annual_ndvi_collection,
        annual_rain_collection,
        annual_lst_collection,
        forest_loss_by_year_collection,
        water_history_collection,
        landcover_feature_collection,
    )
except Exception:
    from ee_helpers import (
        initialize_ee_from_secrets,
        geojson_to_ee_geometry,
        point_buffer_to_ee_geometry,
        compute_metrics,
        satellite_with_polygon,
        ndvi_with_polygon,
        landcover_with_polygon,
        forest_loss_with_polygon,
        flood_risk_with_polygon,
        soil_condition_with_polygon,
        heat_stress_with_polygon,
        vegetation_change_with_polygon,
        image_thumb_url,
        landsat_annual_ndvi_collection,
        annual_rain_collection,
        annual_lst_collection,
        forest_loss_by_year_collection,
        water_history_collection,
        landcover_feature_collection,
    )


st.set_page_config(page_title="EagleNatureInsight | BL Turner", layout="wide")

APP_TITLE = "EagleNatureInsight | BL Turner Nature Intelligence"
APP_SUBTITLE = "TNFD-aligned circular economy screening platform"
APP_TAGLINE = "Locate • Evaluate • Assess • Prepare"

CURRENT_YEAR = date.today().year
LAST_FULL_YEAR = CURRENT_YEAR - 1

BRAND = {
    "primary": "#163d63",
    "accent": "#1f8f5f",
    "warn": "#d9911a",
    "danger": "#c0392b",
    "muted": "#6b7280",
    "bg": "#f6f8fb",
    "card": "#ffffff",
    "border": "#e5e7eb",
    "text": "#111827",
    "subtext": "#4b5563",
    "soft": "#eef2f7",
}

BL_TURNER_SITE = {
    "name": "BL Turner | KwaDukuza organic waste project",
    "lat": -29.2675,
    "lon": 31.2860,
    "buffer_m": 900,
    "zoom": 12,
    "site_area_m2": 15000,
    "municipality": "KwaDukuza",
    "district_context": "iLembe District, KZN",
    "process": "Organic food waste processed in an anaerobic digestion facility producing fertiliser and biogas energy.",
    "waste_streams": [
        "Food waste from restaurants and commercial kitchens",
        "Expired food from distribution centres",
        "Agricultural waste where available",
        "Abattoir waste including meat and blood",
    ],
    "supply_areas": ["eThekwini Municipality", "iLembe District"],
    "fertiliser_destination": "KZN farmlands and outer-lying areas",
    "business_stage": "Pre-development",
    "land_context": "Privately owned land close to landfill with intent to divert waste from landfill",
}

CATEGORY = "Circular Economy / Organic Waste Processing"


def init_state() -> None:
    defaults = {
        "authenticated": False,
        "username": "",
        "auth_error": "",
        "draw_mode": "Enter coordinates",
        "lat_input": str(BL_TURNER_SITE["lat"]),
        "lon_input": str(BL_TURNER_SITE["lon"]),
        "buffer_input": BL_TURNER_SITE["buffer_m"],
        "map_center": [BL_TURNER_SITE["lat"], BL_TURNER_SITE["lon"]],
        "map_zoom": BL_TURNER_SITE["zoom"],
        "last_drawn_geojson": None,
        "results_payload": None,
        "historical_payload": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def check_login(username: str, password: str) -> bool:
    try:
        creds = st.secrets.get("auth", {})
    except Exception:
        creds = {}
    configured_user = creds.get("username", "admin")
    configured_pass = creds.get("password", "spaceeagle-demo")
    return username == configured_user and password == configured_pass


def login_gate() -> None:
    st.markdown(
        f"""
        <div style="padding:28px;border:1px solid {BRAND['border']};border-radius:24px;background:{BRAND['card']};max-width:480px;margin:50px auto;box-shadow:0 10px 25px rgba(17,24,39,0.08);">
            <div style="font-size:28px;font-weight:800;color:{BRAND['primary']};margin-bottom:8px;">BL Turner Platform Login</div>
            <div style="font-size:14px;color:{BRAND['subtext']};margin-bottom:18px;">
                Secure access for the BL Turner circular-economy pilot.
            </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", use_container_width=True)
        if submitted:
            if check_login(username.strip(), password):
                st.session_state["authenticated"] = True
                st.session_state["username"] = username.strip()
                st.session_state["auth_error"] = ""
                st.rerun()
            else:
                st.session_state["auth_error"] = "Incorrect username or password."
    if st.session_state.get("auth_error"):
        st.error(st.session_state["auth_error"])
    st.caption("Tip: set auth.username and auth.password in Streamlit secrets for production.")
    st.stop()


def has_data(value: Any) -> bool:
    if value is None or value == "":
        return False
    try:
        return pd.notna(value)
    except Exception:
        return True


def safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def fmt_num(value: Any, digits: int = 1, suffix: str = "") -> str:
    number = safe_float(value)
    if number is None:
        return "Not available"
    return f"{number:.{digits}f}{suffix}"


def yes_no(flag: bool) -> str:
    return "Yes" if flag else "No"


def metric_card(label: str, value: str, subtext: str = "") -> None:
    st.markdown(
        f"""
        <div style="padding:14px;border:1px solid {BRAND['border']};border-radius:18px;background:{BRAND['card']};height:126px;box-shadow:0 6px 18px rgba(17,24,39,0.06);">
            <div style="font-size:12px;color:{BRAND['muted']};">{label}</div>
            <div style="font-size:28px;font-weight:700;color:{BRAND['text']};margin-top:6px;">{value}</div>
            <div style="font-size:11px;color:{BRAND['muted']};margin-top:5px;">{subtext}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def display_metric_cards(items: List[Dict[str, str]], per_row: int = 4) -> None:
    valid = [item for item in items if item.get("value") != "Not available"]
    if not valid:
        return
    for i in range(0, len(valid), per_row):
        row = valid[i : i + per_row]
        cols = st.columns(per_row)
        for idx, item in enumerate(row):
            with cols[idx]:
                metric_card(item["label"], item["value"], item.get("subtext", ""))


def status_from_range(value: Optional[float], favourable_max: Optional[float] = None, watch_max: Optional[float] = None,
                      warning_max: Optional[float] = None, inverse: bool = False) -> str:
    if value is None:
        return "Not available"
    if not inverse:
        if favourable_max is not None and value <= favourable_max:
            return "Favourable"
        if watch_max is not None and value <= watch_max:
            return "Watch"
        if warning_max is not None and value <= warning_max:
            return "Warning"
        return "High concern"
    if favourable_max is not None and value >= favourable_max:
        return "Favourable"
    if watch_max is not None and value >= watch_max:
        return "Watch"
    if warning_max is not None and value >= warning_max:
        return "Warning"
    return "High concern"


def rainfall_status(rain: Optional[float]) -> str:
    if rain is None:
        return "Not available"
    if rain > -5:
        return "Favourable"
    if rain > -10:
        return "Watch"
    if rain > -20:
        return "Warning"
    return "High concern"


def ndvi_status(ndvi: Optional[float]) -> str:
    return status_from_range(ndvi, favourable_max=0.50, watch_max=0.35, warning_max=0.20, inverse=True)


def heat_status(lst: Optional[float]) -> str:
    return status_from_range(lst, favourable_max=28, watch_max=30, warning_max=33)


def flood_status(flood: Optional[float]) -> str:
    return status_from_range(flood, favourable_max=0, watch_max=0.2, warning_max=0.5)


def soil_moisture_status(v: Optional[float]) -> str:
    return status_from_range(v, favourable_max=0.25, watch_max=0.18, warning_max=0.12, inverse=True)


def access_status(minutes: Optional[float]) -> str:
    return status_from_range(minutes, favourable_max=60, watch_max=120, warning_max=180)


def value_or_phrase(value: Optional[float], good_text: str, mid_text: str, bad_text: str,
                    good_test, mid_test) -> str:
    if value is None:
        return "The dataset does not return a reliable reading for this indicator at the selected boundary."
    if good_test(value):
        return good_text
    if mid_test(value):
        return mid_text
    return bad_text


def site_story(metrics: Dict[str, Any], tonnes: int, stage: str) -> Dict[str, Any]:
    rain = safe_float(metrics.get("rain_anom_pct"))
    lst = safe_float(metrics.get("lst_mean"))
    flood = safe_float(metrics.get("flood_risk"))
    soil_moisture = safe_float(metrics.get("soil_moisture"))
    market = safe_float(metrics.get("travel_time_to_market"))
    water = safe_float(metrics.get("water_context_signal_pct") or metrics.get("water_occ"))
    tree = safe_float(metrics.get("tree_cover_context_pct") or metrics.get("tree_pct"))
    slope = safe_float(metrics.get("slope"))

    strengths: List[str] = []
    pressures: List[str] = []
    actions: List[str] = []

    strengths.append(
        f"At {tonnes} tonnes per day, the project is large enough for site conditions, transport reliability, drainage, and water planning to materially affect the business case."
    )
    strengths.append(
        f"The operation is still at the {stage.lower()} stage, which means layout, drainage, water storage, traffic routing, and buffer decisions can still be improved before capital is locked in."
    )

    if flood is not None and flood < 0.2:
        strengths.append(f"Flood depth is about {flood:.2f} m, which suggests flood exposure is present but not currently dominant in this screening.")
    elif flood is not None:
        pressures.append(f"Flood depth is about {flood:.2f} m, which means drainage and placement of digesters, storage, and roads should be treated as a design issue, not an afterthought.")
        actions.append("Review road levels, bunding, runoff pathways, and where sensitive equipment or stockpiles would sit on the site.")

    if market is not None and market <= 120:
        strengths.append(f"Travel time to market or urban access is about {market:.0f} minutes, which is workable for moving waste in and products out if routing is planned properly.")
    elif market is not None:
        pressures.append(f"Travel time to market is about {market:.0f} minutes, so transport cost and feedstock continuity could weaken margins if routes are not tightly managed.")
        actions.append("Map the main waste suppliers and prioritise route efficiency, backhauls, and supply contracts before scale-up.")

    if rain is not None and rain < -10:
        pressures.append(f"Rainfall is {rain:.1f}% below the long-term baseline, which raises the importance of water storage, reuse, and drought-proof operating design.")
        actions.append("Treat water security as part of the financial model, not only as an environmental issue.")
    elif rain is not None:
        strengths.append(f"Rainfall is {rain:.1f}% relative to the long-term baseline, which does not by itself suggest an extreme rainfall signal at this stage.")

    if lst is not None and lst >= 30:
        pressures.append(f"Recent land-surface temperature is about {lst:.1f} °C, which may increase odour pressure, worker discomfort, and the need for heat-conscious site design.")
        actions.append("Build shade, ventilation, and heat-safe operating zones into the site design and community-management plan.")
    elif lst is not None:
        strengths.append(f"Recent land-surface temperature is about {lst:.1f} °C, which does not indicate an extreme heat signal for the selected boundary.")

    if soil_moisture is not None and soil_moisture < 0.18:
        pressures.append(f"Soil moisture is {soil_moisture:.3f}, which points to relatively dry near-surface conditions; that matters for dust, landscaping, rehabilitation, and runoff control.")
        actions.append("Plan hardstanding, dust control, and rehabilitation areas carefully so the site does not create avoidable nuisance or erosion pressure.")

    if water is not None:
        if water >= 15:
            strengths.append(f"The broader water-context signal is {water:.1f}, which suggests visible water features are part of the wider landscape and should be considered in drainage and protection planning.")
        elif water < 5:
            pressures.append(f"The broader water-context signal is only {water:.1f}, which suggests low visible water presence and reinforces the need for conservative water planning.")
            actions.append("Design with low-water assumptions in mind and emphasise storage, reuse, and operational efficiency.")

    if tree is not None and tree < 10:
        pressures.append(f"Tree-cover context is about {tree:.1f}%, so the site does not sit in a strongly buffered or wooded landscape; screening, wind, heat, and visual buffering may therefore need more deliberate design.")
        actions.append("Use planting, screening, and landscape buffers where needed to support community fit and site resilience.")

    if slope is not None and slope > 8:
        pressures.append(f"Average slope is about {slope:.1f}°, which may complicate drainage, civil works, and access design.")
        actions.append("Check cut-and-fill, drainage direction, and vehicle movement areas before final engineering decisions.")

    if not pressures:
        pressures.append("No single dominant environmental warning stands out in this first screening, but feedstock continuity, drainage, odour, community fit, and water design still need disciplined planning.")
        actions.append("Use this screening as an early decision-support tool before finalising detailed design, supplier contracts, and investor messaging.")

    headline = (
        "This platform asks a simple business question: can BL Turner run a waste-to-fertiliser and biogas operation here reliably, "
        "without avoidable environmental or operating friction? The answer depends less on one score and more on a portfolio of signals across water, heat, access, flood exposure, and site fit."
    )
    return {"headline": headline, "strengths": strengths[:5], "pressures": pressures[:5], "actions": actions[:5]}


def dependency_impact_view(metrics: Dict[str, Any], tonnes: int) -> Dict[str, List[Dict[str, str]]]:
    water = safe_float(metrics.get("water_context_signal_pct") or metrics.get("water_occ"))
    rain = safe_float(metrics.get("rain_anom_pct"))
    flood = safe_float(metrics.get("flood_risk"))
    heat = safe_float(metrics.get("lst_mean"))
    market = safe_float(metrics.get("travel_time_to_market"))
    tree = safe_float(metrics.get("tree_cover_context_pct") or metrics.get("tree_pct"))

    dependencies = [
        {
            "name": "Feedstock continuity",
            "story": f"At {tonnes} tonnes per day, the business depends on a steady inflow of food waste, commercial kitchen waste, distribution-centre waste, and other approved organic streams. The environmental platform cannot replace commercial contracts, but it does show whether the site is likely to add transport, flood, or heat friction to that supply model.",
            "watch": f"Access signal {fmt_num(market, 0, ' min')}; flood signal {fmt_num(flood, 2, ' m')}.",
        },
        {
            "name": "Water for operations and cleaning",
            "story": f"The site depends on water for processing, washdown, and general operations. Current rainfall is {fmt_num(rain, 1, '%')} relative to the long-term baseline and the broader water-context signal is {fmt_num(water, 1)}.",
            "watch": "Storage, reuse, washdown planning, and whether water stress could push up operating cost.",
        },
        {
            "name": "A workable site and stable access",
            "story": f"Current flood depth is {fmt_num(flood, 2, ' m')} and travel access is about {fmt_num(market, 0, ' min')}. These are practical design and operating signals, not abstract ESG numbers.",
            "watch": "Drainage layout, road access, all-weather operations, and safe movement of heavy vehicles.",
        },
        {
            "name": "Operating conditions and community fit",
            "story": f"Recent land-surface temperature is about {fmt_num(heat, 1, ' °C')} and tree-cover context is {fmt_num(tree, 1, '%')}. Those signals matter because hotter, less-buffered sites can intensify worker discomfort, visual exposure, and nuisance management.",
            "watch": "Shade, screening, odour routing, and how the site presents to surrounding communities.",
        },
    ]

    impacts = [
        {
            "name": "Landfill diversion",
            "story": f"If the plant runs at the entered capacity of {tonnes} tonnes per day, it can materially reduce the amount of organic waste that goes to landfill.",
            "link": "This is the clearest circular-economy story in the platform and should be central in funding and partnership discussions.",
        },
        {
            "name": "Biogas and fertiliser output",
            "story": "The project can convert a disposal problem into usable products. That improves the business case only if the site remains operationally stable and feedstock keeps flowing.",
            "link": "Nature and operations affect revenue quality, not just compliance.",
        },
        {
            "name": "Local nuisance and acceptance risk",
            "story": f"Heat at {fmt_num(heat, 1, ' °C')}, access at {fmt_num(market, 0, ' min')}, and any unmanaged runoff or poor layout could create odour, traffic, or neighbour concern.",
            "link": "Community resistance can slow the project even where the core technology is sound.",
        },
        {
            "name": "Nature pressure around the site",
            "story": f"Flood signal {fmt_num(flood, 2, ' m')} and tree-cover context {fmt_num(tree, 1, '%')} help show whether the surrounding landscape is likely to absorb disturbance well or whether the project should use more careful buffers and drainage controls.",
            "link": "This affects future operating cost and reputational resilience.",
        },
    ]
    return {"dependencies": dependencies, "impacts": impacts}


def tnfd_portfolio_matrix(metrics: Dict[str, Any], tonnes: int, stage: str) -> pd.DataFrame:
    rain = safe_float(metrics.get("rain_anom_pct"))
    heat = safe_float(metrics.get("lst_mean"))
    flood = safe_float(metrics.get("flood_risk"))
    water = safe_float(metrics.get("water_context_signal_pct") or metrics.get("water_occ"))
    soil = safe_float(metrics.get("soil_moisture"))
    access = safe_float(metrics.get("travel_time_to_market"))
    tree = safe_float(metrics.get("tree_cover_context_pct") or metrics.get("tree_pct"))
    slope = safe_float(metrics.get("slope"))

    rows = [
        {
            "TNFD lens": "Dependency",
            "Indicator": "Water planning",
            "Current reading": fmt_num(rain, 1, "%"),
            "Status": rainfall_status(rain),
            "What it means": f"Rainfall is {fmt_num(rain, 1, '%')} against the long-term baseline, so the site should not assume water will always be abundant.",
            "Why it matters to BL Turner": "Water is needed for operations, cleaning, and stable processing.",
            "What BL Turner should do": "Build storage, reuse, and dry-period planning into the business model.",
        },
        {
            "TNFD lens": "Dependency",
            "Indicator": "Visible water context",
            "Current reading": fmt_num(water, 1),
            "Status": status_from_range(water, favourable_max=15, watch_max=5, warning_max=0, inverse=True),
            "What it means": f"The broader water-context signal is {fmt_num(water, 1)}, which helps show whether the surrounding landscape has visible water features or a drier operating context.",
            "Why it matters to BL Turner": "It shapes drainage, protection, and water-security thinking.",
            "What BL Turner should do": "Overlay this with internal water demand, storage, and washdown design.",
        },
        {
            "TNFD lens": "Risk",
            "Indicator": "Flood exposure",
            "Current reading": fmt_num(flood, 2, " m"),
            "Status": flood_status(flood),
            "What it means": f"Mapped flood depth is {fmt_num(flood, 2, ' m')}, which gives an early signal on whether roads, digesters, and storage areas may need more careful siting.",
            "Why it matters to BL Turner": "Flooding can interrupt operations and raise infrastructure cost.",
            "What BL Turner should do": "Use drainage, levels, bunding, and access design to reduce operational disruption.",
        },
        {
            "TNFD lens": "Risk",
            "Indicator": "Heat and odour pressure",
            "Current reading": fmt_num(heat, 1, " °C"),
            "Status": heat_status(heat),
            "What it means": f"Land-surface temperature is {fmt_num(heat, 1, ' °C')}, which is an early warning for worker comfort, nuisance management, and heat-aware design.",
            "Why it matters to BL Turner": "Higher heat can make site management harder and community issues more sensitive.",
            "What BL Turner should do": "Plan shade, airflow, and operations so hot periods do not create avoidable friction.",
        },
        {
            "TNFD lens": "Dependency",
            "Indicator": "Soil and drainage condition",
            "Current reading": fmt_num(soil, 3),
            "Status": soil_moisture_status(soil),
            "What it means": f"Soil moisture is {fmt_num(soil, 3)}, which helps indicate whether near-surface conditions are dry or wet in a way that could affect dust, drainage, and rehabilitation.",
            "Why it matters to BL Turner": "This influences runoff control, landscaping, and nuisance prevention.",
            "What BL Turner should do": "Use hardstanding, drainage control, and landscaping deliberately.",
        },
        {
            "TNFD lens": "Opportunity",
            "Indicator": "Access and logistics",
            "Current reading": fmt_num(access, 0, " min"),
            "Status": access_status(access),
            "What it means": f"Estimated travel time is {fmt_num(access, 0, ' min')}, which is a practical logistics signal for collecting waste and distributing outputs.",
            "Why it matters to BL Turner": f"At {tonnes} tonnes/day, weak routing can quickly erode margins.",
            "What BL Turner should do": "Match site selection with supplier mapping and route planning.",
        },
        {
            "TNFD lens": "Impact",
            "Indicator": "Landscape buffering",
            "Current reading": fmt_num(tree, 1, "%"),
            "Status": status_from_range(tree, favourable_max=20, watch_max=10, warning_max=5, inverse=True),
            "What it means": f"Tree-cover context is {fmt_num(tree, 1, '%')}, which helps show whether the project sits in a buffered landscape or a more exposed one.",
            "Why it matters to BL Turner": "It affects visual screening, heat, and site fit with neighbours.",
            "What BL Turner should do": "Use buffers, screening, and planting where the site is visually or climatically exposed.",
        },
        {
            "TNFD lens": "Risk",
            "Indicator": "Terrain slope",
            "Current reading": fmt_num(slope, 1, "°"),
            "Status": status_from_range(slope, favourable_max=3, watch_max=6, warning_max=10),
            "What it means": f"Average slope is {fmt_num(slope, 1, '°')}, which is a practical civil-works and runoff signal rather than a cosmetic number.",
            "Why it matters to BL Turner": f"It matters most at the {stage.lower()} stage while the layout can still change.",
            "What BL Turner should do": "Check cut-and-fill, vehicle movement, and runoff direction before detailed engineering.",
        },
    ]
    return pd.DataFrame(rows)


def prepare_actions(metrics: Dict[str, Any], tonnes: int, stage: str) -> List[str]:
    rain = safe_float(metrics.get("rain_anom_pct"))
    flood = safe_float(metrics.get("flood_risk"))
    heat = safe_float(metrics.get("lst_mean"))
    access = safe_float(metrics.get("travel_time_to_market"))
    water = safe_float(metrics.get("water_context_signal_pct") or metrics.get("water_occ"))
    actions: List[str] = []

    actions.append(
        f"Use this as a {stage.lower()} decision tool: it is most valuable now, before site layout, drainage, traffic flow, and buffer design become expensive to change."
    )
    actions.append(
        f"Build the feedstock model around the entered capacity of {tonnes} tonnes/day. The site view and the supplier view should be treated as one operating system, not two separate workstreams."
    )
    if rain is not None and rain < -10:
        actions.append(f"Because rainfall is {rain:.1f}% below baseline, treat storage, washdown efficiency, and water reuse as core design issues.")
    if flood is not None and flood >= 0.2:
        actions.append(f"Because flood depth is {flood:.2f} m, review levels, stormwater routing, bunding, and vehicle access in wet periods.")
    if heat is not None and heat >= 30:
        actions.append(f"Because heat is around {heat:.1f} °C, include shading, odour-aware layout, and worker-safety controls early in the design.")
    if access is not None and access > 120:
        actions.append(f"Because access time is about {access:.0f} minutes, build route efficiency and supplier contracting into the financial case before scaling volumes.")
    if water is not None and water < 5:
        actions.append(f"Because the broader water-context signal is only {water:.1f}, do not assume local conditions will naturally support a water-intensive operating model.")
    actions.append("Translate the strongest signals into lender, grant, and investor language: landfill diversion, operational continuity, avoided disruption, and fit-for-site design.")
    return actions[:6]


def business_value_table(metrics: Dict[str, Any], tonnes: int) -> pd.DataFrame:
    annual_tonnes = tonnes * 330
    rain = safe_float(metrics.get("rain_anom_pct"))
    flood = safe_float(metrics.get("flood_risk"))
    access = safe_float(metrics.get("travel_time_to_market"))
    rows = [
        ["Waste diverted from landfill", "Tonnes/year", f"{annual_tonnes:,.0f}", "Direct scale indicator based on entered daily capacity × 330 operating days."],
        ["Water stress signal", "Rainfall anomaly", fmt_num(rain, 1, "%"), "Helps explain whether water planning may raise operating cost or resilience needs."],
        ["Flood-disruption signal", "Flood depth proxy", fmt_num(flood, 2, " m"), "Helps show whether access, storage, and infrastructure may require extra spend."],
        ["Transport effort", "Travel time", fmt_num(access, 0, " min"), "Longer trips can reduce margins and make feedstock continuity harder."],
        ["Biogas and fertiliser outputs", "Commercial outputs", "Project-specific", "Value depends on technology conversion rates and market offtake, not satellite data alone."],
        ["Community-fit value", "Risk reduction", "Design-dependent", "Better drainage, buffers, and odour controls can prevent delay, complaint, and reputational cost."],
    ]
    return pd.DataFrame(rows, columns=["Item", "Unit", "Current view", "Business meaning"])


def build_map(center: List[float], zoom: int, lat: Optional[float], lon: Optional[float], buffer_m: float, existing_geojson: Optional[dict]) -> folium.Map:
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        min_zoom=5,
        control_scale=True,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri Satellite",
    )
    Draw(
        export=False,
        draw_options={
            "polyline": False,
            "rectangle": True,
            "polygon": True,
            "circle": False,
            "marker": False,
            "circlemarker": False,
        },
        edit_options={"edit": True, "remove": True},
    ).add_to(m)
    if existing_geojson:
        folium.GeoJson(existing_geojson, style_function=lambda _: {"color": "#ff0000", "weight": 3, "fillOpacity": 0.05}).add_to(m)
    if lat is not None and lon is not None:
        folium.CircleMarker(
            location=[lat, lon], radius=8, color=BRAND["primary"], weight=2,
            fill=True, fill_color=BRAND["accent"], fill_opacity=0.95, tooltip="BL Turner site"
        ).add_to(m)
        folium.Circle([lat, lon], radius=float(buffer_m), color="#ff0000", weight=2, fill=False).add_to(m)
    return m


def extract_drawn_geometry(map_data: dict | None) -> Optional[dict]:
    if not map_data:
        return None
    drawings = map_data.get("all_drawings") or []
    if not drawings:
        return None
    return drawings[-1]


def get_geometry_payload(mode: str, drawn_geojson: Optional[dict], lat: str, lon: str, buffer_m: float):
    if mode == "Draw polygon":
        if drawn_geojson:
            return drawn_geojson, geojson_to_ee_geometry(drawn_geojson)
        return None, None
    try:
        lat_val = float(lat)
        lon_val = float(lon)
        payload = {"type": "PointBuffer", "lat": lat_val, "lon": lon_val, "buffer_m": float(buffer_m)}
        return payload, point_buffer_to_ee_geometry(lat_val, lon_val, float(buffer_m))
    except Exception:
        return None, None


def fc_to_df(fc) -> pd.DataFrame:
    info = fc.getInfo()
    rows = []
    for feature in info.get("features", []):
        rows.append(feature.get("properties", {}))
    return pd.DataFrame(rows)


def prep_year_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if "value" in df.columns:
        df = df[df["value"].notna()].copy()
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce")
        df = df[df["year"].notna()].copy()
        df["year"] = df["year"].astype(int)
    return df.sort_values("year")


def render_plot(df: pd.DataFrame, x: str, y: str, title: str, kind: str = "line") -> None:
    if df.empty or x not in df.columns or y not in df.columns:
        st.info(f"No data available for {title.lower()}.")
        return
    fig = px.bar(df, x=x, y=y, title=title) if kind == "bar" else px.line(df, x=x, y=y, title=title)
    fig.update_layout(margin=dict(l=20, r=20, t=60, b=20))
    st.plotly_chart(fig, use_container_width=True)


init_state()
if not st.session_state["authenticated"]:
    login_gate()

initialize_ee_from_secrets(st)

st.markdown(
    f"""
    <div style="padding:24px 26px;border-radius:24px;background:linear-gradient(135deg,{BRAND['primary']} 0%, #204f84 60%, #2d6ca8 100%);color:white;margin-bottom:20px;">
        <div style="font-size:30px;font-weight:800;">{APP_TITLE}</div>
        <div style="font-size:15px;opacity:0.95;margin-top:4px;">{APP_SUBTITLE}</div>
        <div style="font-size:13px;opacity:0.9;margin-top:8px;">{APP_TAGLINE}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Access")
    st.success(f"Signed in as {st.session_state['username']}")
    if st.button("Log out", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

    st.markdown("### Project setup")
    st.text_input("Project", value=BL_TURNER_SITE["name"], disabled=True)
    st.text_input("Category", value=CATEGORY, disabled=True)
    st.text_input("Municipality", value=BL_TURNER_SITE["municipality"], disabled=True)

    st.session_state["draw_mode"] = st.radio(
        "Boundary input",
        ["Enter coordinates", "Draw polygon"],
        index=0 if st.session_state["draw_mode"] == "Enter coordinates" else 1,
    )
    st.session_state["lat_input"] = st.text_input("Latitude", value=st.session_state["lat_input"])
    st.session_state["lon_input"] = st.text_input("Longitude", value=st.session_state["lon_input"])
    st.session_state["buffer_input"] = st.number_input("Buffer radius (m)", min_value=100, max_value=5000, value=int(st.session_state["buffer_input"]), step=100)

    hist_start = st.number_input("Historical start year", min_value=1984, max_value=LAST_FULL_YEAR, value=2015, step=1)
    hist_end = st.number_input("Historical end year", min_value=1984, max_value=LAST_FULL_YEAR, value=LAST_FULL_YEAR, step=1)

    st.markdown("### Business profile")
    tonnes = st.number_input("Daily waste capacity (tonnes/day)", min_value=1, value=100, step=1)
    stage = st.selectbox("Business stage", ["Pre-development", "Pilot", "Construction", "Operational"], index=0)
    include_npc = st.checkbox("Include non-profit women’s empowerment angle", value=True)
    run_button = st.button("Run BL Turner assessment", use_container_width=True, type="primary")

left_top, right_top = st.columns([1.05, 1.15])
with left_top:
    st.subheader("Business context")
    st.write(
        "This version is built for BL Turner’s planned organic waste-to-fertiliser and biogas project in KwaDukuza. "
        "It is designed to speak in plain language, but every core statement should still come back to an environmental signal, a business dependency, or a real operating implication."
    )
    st.info(
        "Focus: site viability, feedstock continuity, water and flood context, heat and nuisance pressure, access, and what these mean for project readiness."
    )
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### What the business depends on")
        for item in [
            "Reliable organic waste supply",
            "Water for operations and cleaning",
            "A workable site with stable drainage and access",
            "Community fit and nuisance management",
        ]:
            st.write(f"- {item}")
    with c2:
        st.markdown("#### What the business can change")
        for item in [
            "Landfill diversion",
            "Biogas and fertiliser production",
            "Operating cost and resilience",
            "Neighbour and partner confidence",
        ]:
            st.write(f"- {item}")

with right_top:
    st.subheader("Site map")
    lat_val = safe_float(st.session_state["lat_input"])
    lon_val = safe_float(st.session_state["lon_input"])
    site_map = build_map(
        center=st.session_state["map_center"],
        zoom=st.session_state["map_zoom"],
        lat=lat_val,
        lon=lon_val,
        buffer_m=float(st.session_state["buffer_input"]),
        existing_geojson=st.session_state["last_drawn_geojson"],
    )
    map_data = st_folium(site_map, height=430, width=None, returned_objects=["all_drawings"])
    drawn_geojson = extract_drawn_geometry(map_data)
    if drawn_geojson:
        st.session_state["last_drawn_geojson"] = drawn_geojson

if run_button:
    geom_payload, geom = get_geometry_payload(
        st.session_state["draw_mode"],
        st.session_state["last_drawn_geojson"],
        st.session_state["lat_input"],
        st.session_state["lon_input"],
        float(st.session_state["buffer_input"]),
    )
    if geom is None:
        st.error("Please provide valid coordinates or draw a polygon.")
    else:
        with st.spinner("Running Earth Engine assessment..."):
            metrics = compute_metrics(geom, int(hist_start), int(hist_end), LAST_FULL_YEAR)
            ndvi_hist = prep_year_df(fc_to_df(landsat_annual_ndvi_collection(geom, max(int(hist_start), 1984), int(hist_end))))
            rain_hist = prep_year_df(fc_to_df(annual_rain_collection(geom, max(int(hist_start), 1984), int(hist_end))))
            lst_hist = prep_year_df(fc_to_df(annual_lst_collection(geom, max(int(hist_start), 2001), int(hist_end))))
            forest_hist = prep_year_df(fc_to_df(forest_loss_by_year_collection(geom, int(hist_start), int(hist_end))))
            water_hist = prep_year_df(fc_to_df(water_history_collection(geom, max(int(hist_start), 1984), int(hist_end))))
            landcover_df = fc_to_df(landcover_feature_collection(geom))
            images = {
                "satellite": satellite_with_polygon(geom, LAST_FULL_YEAR),
                "ndvi": ndvi_with_polygon(geom, LAST_FULL_YEAR),
                "landcover": landcover_with_polygon(geom),
                "veg_change": vegetation_change_with_polygon(geom, int(hist_start), int(hist_end)),
                "forest_loss": forest_loss_with_polygon(geom),
                "flood_risk": flood_risk_with_polygon(geom),
                "soil_condition": soil_condition_with_polygon(geom),
                "heat_stress": heat_stress_with_polygon(geom, LAST_FULL_YEAR),
            }
            urls = {name: image_thumb_url(img, geom, dimensions=1600) for name, img in images.items()}
        st.session_state["results_payload"] = {
            "geom_payload": geom_payload,
            "metrics": metrics,
            "urls": urls,
            "tonnes": tonnes,
            "stage": stage,
            "include_npc": include_npc,
            "hist_start": int(hist_start),
            "hist_end": int(hist_end),
        }
        st.session_state["historical_payload"] = {
            "ndvi_hist": ndvi_hist,
            "rain_hist": rain_hist,
            "lst_hist": lst_hist,
            "forest_hist": forest_hist,
            "water_hist": water_hist,
            "landcover_df": landcover_df,
        }

payload = st.session_state.get("results_payload")
hist = st.session_state.get("historical_payload")

if payload:
    metrics = payload["metrics"]
    tonnes = payload["tonnes"]
    stage = payload["stage"]
    story = site_story(metrics, tonnes, stage)
    dep_view = dependency_impact_view(metrics, tonnes)
    matrix_df = tnfd_portfolio_matrix(metrics, tonnes, stage)

    st.markdown("---")
    st.subheader("1. Executive story")
    st.write(story["headline"])

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("#### What looks positive")
        for item in story["strengths"]:
            st.write(f"- {item}")
    with col_b:
        st.markdown("#### What needs attention")
        for item in story["pressures"]:
            st.write(f"- {item}")
    with col_c:
        st.markdown("#### What to do next")
        for item in story["actions"]:
            st.write(f"- {item}")

    st.subheader("2. Quick view")
    display_metric_cards([
        {"label": "Site area", "value": fmt_num(metrics.get("area_ha"), 1, " ha"), "subtext": "Assessment area"},
        {"label": "Rainfall signal", "value": fmt_num(metrics.get("rain_anom_pct"), 1, "%"), "subtext": rainfall_status(safe_float(metrics.get("rain_anom_pct")))},
        {"label": "Heat signal", "value": fmt_num(metrics.get("lst_mean"), 1, " °C"), "subtext": heat_status(safe_float(metrics.get("lst_mean")))},
        {"label": "Flood signal", "value": fmt_num(metrics.get("flood_risk"), 2, " m"), "subtext": flood_status(safe_float(metrics.get("flood_risk")))},
        {"label": "Soil moisture", "value": fmt_num(metrics.get("soil_moisture"), 3), "subtext": soil_moisture_status(safe_float(metrics.get("soil_moisture")))},
        {"label": "Travel access", "value": fmt_num(metrics.get("travel_time_to_market"), 0, " min"), "subtext": access_status(safe_float(metrics.get("travel_time_to_market")))},
        {"label": "Water context", "value": fmt_num(metrics.get("water_context_signal_pct") or metrics.get("water_occ"), 1), "subtext": "Landscape water signal"},
        {"label": "Tree context", "value": fmt_num(metrics.get("tree_cover_context_pct") or metrics.get("tree_pct"), 1, "%"), "subtext": "Landscape buffer signal"},
    ])

    st.subheader("3. TNFD portfolio view")
    st.caption("This is not one score. It is a portfolio of site signals translated into business meaning.")
    st.dataframe(matrix_df, use_container_width=True, hide_index=True)

    st.subheader("4. Dependencies and impacts")
    left, right = st.columns(2)
    with left:
        st.markdown("#### Dependencies")
        for row in dep_view["dependencies"]:
            with st.container(border=True):
                st.markdown(f"**{row['name']}**")
                st.write(row["story"])
                st.caption(f"Watch: {row['watch']}")
    with right:
        st.markdown("#### Impacts")
        for row in dep_view["impacts"]:
            with st.container(border=True):
                st.markdown(f"**{row['name']}**")
                st.write(row["story"])
                st.caption(f"Business link: {row['link']}")

    st.subheader("5. Units of nature and units of money")
    st.dataframe(business_value_table(metrics, tonnes), use_container_width=True, hide_index=True)
    st.caption("Only the waste-diversion line is calculated directly from the entered operating capacity. Other rows are decision signals or project-specific commercial lines that need engineering and market inputs.")

    st.subheader("6. Visual evidence")
    img_cols = st.columns(4)
    image_items = [
        ("Satellite view", payload["urls"]["satellite"], "The red outline shows the assessed site boundary."),
        ("Vegetation", payload["urls"]["ndvi"], "Greener usually means stronger vegetation condition."),
        ("Land cover", payload["urls"]["landcover"], "Shows the current land-cover context around the site."),
        ("Flood risk", payload["urls"]["flood_risk"], "Darker blues indicate deeper flood exposure."),
        ("Heat stress", payload["urls"]["heat_stress"], "Warmer colours indicate hotter surfaces."),
        ("Soil condition", payload["urls"]["soil_condition"], "Simple view of surrounding soil-organic-carbon context."),
        ("Vegetation change", payload["urls"]["veg_change"], "Green suggests improvement; red suggests decline."),
        ("Forest loss", payload["urls"]["forest_loss"], "Highlights detected forest-loss areas in the surrounding context."),
    ]
    for idx, (title, url, caption) in enumerate(image_items):
        with img_cols[idx % 4]:
            st.markdown(f"**{title}**")
            st.image(url)
            st.caption(caption)

    st.subheader("7. Historical trends")
    if hist:
        p1, p2 = st.columns(2)
        with p1:
            render_plot(hist["ndvi_hist"], "year", "value", "Historical vegetation (NDVI)")
            render_plot(hist["lst_hist"], "year", "value", "Historical land-surface temperature")
            render_plot(hist["water_hist"], "year", "value", "Historical water presence")
        with p2:
            render_plot(hist["rain_hist"], "year", "value", "Historical rainfall")
            render_plot(hist["forest_hist"], "year", "value", "Historical forest loss", kind="bar")
            render_plot(hist["landcover_df"], "class_name", "area_ha", "Current land-cover composition", kind="bar")

    st.subheader("8. Prepare")
    for action in prepare_actions(metrics, tonnes, stage):
        st.write(f"- {action}")
    if payload["include_npc"]:
        st.info(
            "The non-profit women’s empowerment angle can strengthen the wider partnership story, but it should sit alongside the environmental and operating case rather than replace it."
        )

    st.subheader("9. Analysis notes")
    if metrics.get("analysis_context_method"):
        st.caption(str(metrics["analysis_context_method"]))
else:
    st.markdown("---")
    st.info("Run the BL Turner assessment to generate the platform outputs.")
