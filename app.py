
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium

# Flexible imports so the file works whether helpers live in utils/ or beside this file
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
APP_TAGLINE = "Site viability • Nature dependencies • Operational risk • Business readiness"

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
    "lat": -29.2675,   # placeholder derived from KwaDukuza area; replace with exact site coordinates when confirmed
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
    "supply_areas": [
        "eThekwini Municipality",
        "iLembe District",
    ],
    "fertiliser_destination": "KZN farmlands and outer-lying areas",
    "business_stage": "Pre-development",
    "land_context": "Privately owned land close to landfill with intent to divert waste from landfill",
}

CATEGORY = "Circular Economy / Organic Waste Processing"

# ----------------------------
# State and login
# ----------------------------

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
    creds = {}
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


# ----------------------------
# Helpers
# ----------------------------

def has_data(value: Any) -> bool:
    if value is None or value == "":
        return False
    try:
        return pd.notna(value)
    except Exception:
        return True


def fmt_num(value: Any, digits: int = 1, suffix: str = "") -> str:
    if not has_data(value):
        return "Not available"
    try:
        return f"{float(value):.{digits}f}{suffix}"
    except Exception:
        return str(value)


def safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def metric_card(label: str, value: str, subtext: str = "") -> None:
    st.markdown(
        f"""
        <div style="padding:14px;border:1px solid {BRAND['border']};border-radius:18px;background:{BRAND['card']};height:124px;box-shadow:0 6px 18px rgba(17,24,39,0.06);">
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
        row = valid[i:i + per_row]
        cols = st.columns(per_row)
        for idx, item in enumerate(row):
            with cols[idx]:
                metric_card(item["label"], item["value"], item.get("subtext", ""))


def site_story(metrics: Dict[str, Any]) -> Dict[str, List[str] | str]:
    rain = safe_float(metrics.get("rain_anom_pct"))
    lst = safe_float(metrics.get("lst_mean"))
    flood = safe_float(metrics.get("flood_risk"))
    soil_moisture = safe_float(metrics.get("soil_moisture"))
    market = safe_float(metrics.get("travel_time_to_market"))
    water_occ = safe_float(metrics.get("water_occ"))

    strengths: List[str] = []
    pressures: List[str] = []
    actions: List[str] = []

    strengths.append("The site is close to landfill and aligned with a landfill-diversion use case, which supports the core waste-to-value business model.")
    if flood is not None and flood < 0.2:
        strengths.append("Flood exposure looks limited in the current screening, which is positive for siting and operations.")
    if market is not None and market <= 120:
        strengths.append("The site appears reasonably connected to nearby urban supply areas, which supports waste collection and product distribution.")
    if water_occ is not None and water_occ >= 5:
        strengths.append("The surrounding landscape shows at least some visible water context, which is helpful for broader water planning.")

    if rain is not None and rain < -10:
        pressures.append("Recent rainfall is below the long-term baseline, so water planning should be treated as an operational priority from the start.")
        actions.append("Build water security into the business model early, including storage, reuse, and contingency planning.")
    if lst is not None and lst >= 30:
        pressures.append("Heat conditions are elevated, which may affect worker comfort, odour management, and process performance.")
        actions.append("Design for heat management, shading, ventilation, and safe operating conditions.")
    if soil_moisture is not None and soil_moisture < 0.18:
        pressures.append("Surface soil conditions look relatively dry, which matters for landscaping, drainage, dust, and rehabilitation planning.")
        actions.append("Plan drainage, surfacing, and any greening or rehabilitation areas carefully.")
    if flood is not None and flood >= 0.2:
        pressures.append("Flood risk is visible in the landscape and may affect site design, storage, and access roads.")
        actions.append("Review drainage, bunding, and the placement of sensitive infrastructure.")
    if market is not None and market > 120:
        pressures.append("Travel time to market is extended, which may increase transport cost and affect supply reliability.")
        actions.append("Prioritise supplier mapping and route planning as part of pre-development work.")

    if not pressures:
        pressures.append("No single dominant environmental warning stands out in this early screening, but water, transport, and community fit should still be tested carefully.")
        actions.append("Use this screening as a decision-support layer before final site design and supplier agreements are locked in.")

    return {
        "headline": "This platform turns environmental data into a simple business story: can this site support a circular waste-to-fertiliser operation reliably and with manageable risk?",
        "strengths": strengths[:4],
        "pressures": pressures[:4],
        "actions": actions[:4],
    }


def dependency_impact_view(metrics: Dict[str, Any]) -> Dict[str, List[Dict[str, str]]]:
    water_occ = fmt_num(metrics.get("water_occ"), 1)
    rain = fmt_num(metrics.get("rain_anom_pct"), 1, "%")
    flood = fmt_num(metrics.get("flood_risk"), 2, " m")
    heat = fmt_num(metrics.get("lst_mean"), 1, " °C")
    market = fmt_num(metrics.get("travel_time_to_market"), 0, " min")

    dependencies = [
        {
            "name": "Waste supply",
            "story": "The business depends on a steady inflow of organic waste from municipalities, restaurants, distribution centres, and possibly agricultural and abattoir sources.",
            "what_to_watch": "Supply distance, seasonal variation, and continuity of feedstock contracts.",
        },
        {
            "name": "Water",
            "story": f"The business depends on water for operations and cleaning. The surrounding water context signal is {water_occ}, while rainfall conditions are currently {rain}.",
            "what_to_watch": "Water security, storage, and reuse options.",
        },
        {
            "name": "Land and access",
            "story": f"The business depends on a site that stays functional in wet and dry periods. Current flood signal is {flood}, and travel access is about {market}.",
            "what_to_watch": "Drainage, road access, layout, and logistics.",
        },
        {
            "name": "Operating conditions",
            "story": f"Heat conditions are around {heat}, which matters for workers, odour management, and process stability.",
            "what_to_watch": "Shade, airflow, and safe operational design.",
        },
    ]

    impacts = [
        {
            "name": "Landfill diversion",
            "story": "The project can reduce the amount of organic waste that ends up in landfill.",
            "business_link": "This supports a clear climate and circular-economy value proposition.",
        },
        {
            "name": "Biogas and fertiliser output",
            "story": "The project can convert waste into usable products: energy and soil inputs.",
            "business_link": "This creates revenue and strengthens the commercial case.",
        },
        {
            "name": "Local nuisance risk",
            "story": "Transport, odour, noise, and handling can create local concern if not well managed.",
            "business_link": "This can affect community acceptance and operating stability.",
        },
        {
            "name": "Nature pressure around the site",
            "story": "Poor drainage, heat, or unsuitable layout can worsen runoff, soil damage, or local environmental stress.",
            "business_link": "This can raise future operating and compliance costs.",
        },
    ]
    return {"dependencies": dependencies, "impacts": impacts}


def business_value_table(metrics: Dict[str, Any]) -> pd.DataFrame:
    rows = [
        ["Waste diverted", "Tonnes/day", "100", "Potential gate-fee income and landfill savings"],
        ["Biogas output", "Energy units", "Project-specific", "Reduced energy cost or energy sale potential"],
        ["Fertiliser output", "Tonnes/month", "Project-specific", "Revenue from soil-input product"],
        ["Water risk", "Environmental signal", fmt_num(metrics.get("rain_anom_pct"), 1, "%"), "Higher water risk can raise operating cost"],
        ["Flood exposure", "Depth proxy", fmt_num(metrics.get("flood_risk"), 2, " m"), "Higher flood risk can increase infrastructure cost"],
        ["Transport effort", "Travel time", fmt_num(metrics.get("travel_time_to_market"), 0, " min"), "Longer trips can reduce margins"],
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
        folium.GeoJson(
            existing_geojson,
            style_function=lambda _: {"color": "#ff0000", "weight": 3, "fillOpacity": 0.05},
        ).add_to(m)

    if lat is not None and lon is not None:
        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            color=BRAND["primary"],
            weight=2,
            fill=True,
            fill_color=BRAND["accent"],
            fill_opacity=0.95,
            tooltip="BL Turner site",
        ).add_to(m)
        folium.Circle(
            [lat, lon],
            radius=float(buffer_m),
            color="#ff0000",
            weight=2,
            fill=False,
        ).add_to(m)

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


# ----------------------------
# App
# ----------------------------

init_state()
if not st.session_state["authenticated"]:
    login_gate()

initialize_ee_from_secrets()

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
    st.caption("These fields shape the story shown in the platform.")
    tonnes = st.number_input("Daily waste capacity (tonnes/day)", min_value=1, value=100, step=1)
    stage = st.selectbox("Business stage", ["Pre-development", "Pilot", "Construction", "Operational"], index=0)
    include_npc = st.checkbox("Include non-profit women’s empowerment angle", value=True)
    run_button = st.button("Run BL Turner assessment", use_container_width=True, type="primary")

top1, top2 = st.columns([1.05, 1.15])

with top1:
    st.subheader("Business context")
    st.write(
        "This version is built for BL Turner’s planned organic waste-to-fertiliser and biogas project in KwaDukuza. "
        "It translates environmental data into a simple operating story: whether the site, supply footprint, and surrounding landscape are stable enough to support the business."
    )
    st.info(
        "Designed for non-experts: plain language, TNFD-aligned thinking, and clear links to operational and financial decisions."
    )

    dep = dependency_impact_view({})
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### What the business depends on")
        for item in [
            "Reliable organic waste supply",
            "Water for operations and cleaning",
            "A workable site with good access",
            "Community acceptance and practical operating conditions",
        ]:
            st.write(f"- {item}")
    with c2:
        st.markdown("#### What the business can change")
        for item in [
            "Less waste to landfill",
            "Biogas and fertiliser creation",
            "Potential cost savings and new revenue",
            "Possible odour, traffic, or drainage pressure if poorly managed",
        ]:
            st.write(f"- {item}")

with top2:
    st.subheader("Site map")
    lat_val = safe_float(st.session_state["lat_input"])
    lon_val = safe_float(st.session_state["lon_input"])
    m = build_map(
        center=st.session_state["map_center"],
        zoom=st.session_state["map_zoom"],
        lat=lat_val,
        lon=lon_val,
        buffer_m=float(st.session_state["buffer_input"]),
        existing_geojson=st.session_state["last_drawn_geojson"],
    )
    map_data = st_folium(m, height=430, width=None, returned_objects=["all_drawings"])
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
    story = site_story(metrics)
    dep_view = dependency_impact_view(metrics)

    st.markdown("---")
    st.subheader("1. Executive story")
    st.write(story["headline"])

    a, b, c = st.columns(3)
    with a:
        st.markdown("#### What looks positive")
        for item in story["strengths"]:
            st.write(f"- {item}")
    with b:
        st.markdown("#### What needs attention")
        for item in story["pressures"]:
            st.write(f"- {item}")
    with c:
        st.markdown("#### What to do next")
        for item in story["actions"]:
            st.write(f"- {item}")

    st.subheader("2. Quick view")
    display_metric_cards([
        {"label": "Site area", "value": fmt_num(metrics.get("area_ha"), 1, " ha"), "subtext": "Assessment area"},
        {"label": "Rainfall signal", "value": fmt_num(metrics.get("rain_anom_pct"), 1, "%"), "subtext": "Compared with long-term baseline"},
        {"label": "Heat signal", "value": fmt_num(metrics.get("lst_mean"), 1, " °C"), "subtext": "Recent land-surface temperature"},
        {"label": "Flood signal", "value": fmt_num(metrics.get("flood_risk"), 2, " m"), "subtext": "Flood-depth proxy"},
        {"label": "Soil moisture", "value": fmt_num(metrics.get("soil_moisture"), 3), "subtext": "Near-surface wetness"},
        {"label": "Travel access", "value": fmt_num(metrics.get("travel_time_to_market"), 0, " min"), "subtext": "Market and logistics context"},
        {"label": "Water context", "value": fmt_num(metrics.get("water_occ"), 1), "subtext": "Visible surface-water occurrence"},
        {"label": "Vegetation", "value": fmt_num(metrics.get("ndvi_current"), 3), "subtext": "Current vegetation condition"},
    ])

    st.subheader("3. TNFD-style dependency and impact view")
    left, right = st.columns(2)
    with left:
        st.markdown("#### Dependencies")
        for row in dep_view["dependencies"]:
            with st.container(border=True):
                st.markdown(f"**{row['name']}**")
                st.write(row["story"])
                st.caption(f"Watch: {row['what_to_watch']}")
    with right:
        st.markdown("#### Impacts")
        for row in dep_view["impacts"]:
            with st.container(border=True):
                st.markdown(f"**{row['name']}**")
                st.write(row["story"])
                st.caption(f"Business link: {row['business_link']}")

    st.subheader("4. Units of nature and units of money")
    st.dataframe(business_value_table(metrics), use_container_width=True, hide_index=True)

    st.subheader("5. Visual evidence")
    img_cols = st.columns(4)
    items = [
        ("Satellite view", payload["urls"]["satellite"], "The red outline shows the assessed site."),
        ("Vegetation", payload["urls"]["ndvi"], "Greener usually means stronger vegetation condition."),
        ("Land cover", payload["urls"]["landcover"], "Shows current land-cover classes around the site."),
        ("Flood risk", payload["urls"]["flood_risk"], "Darker blues indicate deeper flood exposure."),
        ("Heat stress", payload["urls"]["heat_stress"], "Warmer colours indicate hotter surfaces."),
        ("Soil condition", payload["urls"]["soil_condition"], "Gives a simple soil-condition view."),
        ("Vegetation change", payload["urls"]["veg_change"], "Green suggests improvement; red suggests decline."),
        ("Forest loss", payload["urls"]["forest_loss"], "Highlights detected forest-loss areas."),
    ]
    for idx, (title, url, caption) in enumerate(items):
        with img_cols[idx % 4]:
            st.markdown(f"**{title}**")
            st.image(url)
            st.caption(caption)

    st.subheader("6. Historical trends")
    if hist:
        c1, c2 = st.columns(2)
        with c1:
            if not hist["ndvi_hist"].empty:
                st.plotly_chart(px.line(hist["ndvi_hist"], x="year", y="value", title="Historical vegetation (NDVI)"), use_container_width=True)
            if not hist["lst_hist"].empty:
                st.plotly_chart(px.line(hist["lst_hist"], x="year", y="value", title="Historical land-surface temperature"), use_container_width=True)
            if not hist["water_hist"].empty:
                st.plotly_chart(px.line(hist["water_hist"], x="year", y="value", title="Historical water presence"), use_container_width=True)
        with c2:
            if not hist["rain_hist"].empty:
                st.plotly_chart(px.line(hist["rain_hist"], x="year", y="value", title="Historical rainfall"), use_container_width=True)
            if not hist["forest_hist"].empty:
                st.plotly_chart(px.bar(hist["forest_hist"], x="year", y="value", title="Historical forest loss"), use_container_width=True)
            if not hist["landcover_df"].empty and "class_name" in hist["landcover_df"].columns and "area_ha" in hist["landcover_df"].columns:
                st.plotly_chart(px.bar(hist["landcover_df"], x="class_name", y="area_ha", title="Current land-cover composition"), use_container_width=True)

    st.subheader("7. Plain-language recommendation pack")
    recommendations = [
        "Use this as a pre-development decision tool before final site design is locked in.",
        "Treat supplier mapping as seriously as site mapping. A strong waste stream is as important as a strong site.",
        "Include water security, odour management, drainage, and transport layout in the early design stage.",
        "Build a simple annual review version for TNFD-style reporting once the project moves from pre-development to operation.",
    ]
    if payload["include_npc"]:
        recommendations.append("Show the women’s empowerment and community development story as part of the wider social value case, but keep it separate from the environmental screening logic.")
    for rec in recommendations:
        st.write(f"- {rec}")

    st.subheader("8. Suggested commercial model")
    st.write("- Once-off pre-development screening")
    st.write("- Annual TNFD-aligned monitoring and update")
    st.write("- Investor, grant, or lender-ready summary pack")
    st.write("- Optional supplier and waste-catchment expansion module")

else:
    st.markdown("---")
    st.info("Run the BL Turner assessment to generate the platform outputs.")
