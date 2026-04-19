"""
EagleNatureInsight — BL Turner Group
========================================

Streamlit app tailored for BL Turner Group (Pty) Ltd's 100 t/day organic
waste-to-fertiliser and biogas operation at Portion 159 of New Guelderland,
KwaDukuza (iLembe District, KZN).

Developed by Space Eagle Enterprise (Pty) Ltd for the TNFD / Conservation X
Labs / UNDP Nature Intelligence for Business Grand Challenge SME user
testing phase (January - April 2026).

Key differentiators from the Panuka agribusiness variant:
  * Waste sourcing tab (feedstock nodes, frequency, tonnage, seasonality,
    continuity-of-supply risk)
  * AD-plant specific TNFD dependency pathways and monetary exposures
  * Digestate off-take (KZN farmlands) visualised on the main map
  * Landfill diversion / avoided methane as a positive environmental outcome
"""

from pathlib import Path
from datetime import date
from io import BytesIO

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import requests

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
    from utils.scoring import build_risk_and_recommendations
    from utils.pdf_report import build_pdf_report
    from utils.tnfd_alignment import (
        build_tnfd_core_metrics_rows,
        build_npi_state_of_nature_rows,
        plain_language_leap_summary,
    )
    from utils.feedback import render_feedback_widget, render_feedback_admin
    from utils.waste_sourcing import (
        WASTE_SOURCES,
        DIGESTATE_OFFTAKE_AREAS,
        total_estimated_supply,
        supply_headroom,
        stream_mix_summary,
        district_mix_summary,
        seasonal_supply_profile,
        continuity_risk_assessment,
        collection_frequency_table,
    )
    from utils.logistics_engine import (
        build_logistics_table,
        logistics_summary,
    )
    from utils.capacity_risk_engine import build_capacity_risk_dashboard
    from utils.digestate_demand_engine import build_digestate_dashboard
    from utils.mol_blturner import build_mol_insights, make_mol_shi_long_df, mol_shi_chart_bytes, mol_summary_chart_bytes, render_species_badges
    from utils.water_balance_engine import compute_water_balance
    from utils.portfolio_registry import (
        BL_TURNER_SITES,
        solution_playbook,
        site_by_name,
        solution_lines,
    )
    from utils.data_provenance import provenance_table, scope_boundary_statement
    from utils.stakeholder_engagement import (
        engagement_tracker_rows,
        data_sharing_agreement_checklist,
    )
except ModuleNotFoundError:
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
    from scoring import build_risk_and_recommendations
    from pdf_report import build_pdf_report
    from tnfd_alignment import (
        build_tnfd_core_metrics_rows,
        build_npi_state_of_nature_rows,
        plain_language_leap_summary,
    )
    from feedback import render_feedback_widget, render_feedback_admin
    from waste_sourcing import (
        WASTE_SOURCES,
        DIGESTATE_OFFTAKE_AREAS,
        total_estimated_supply,
        supply_headroom,
        stream_mix_summary,
        district_mix_summary,
        seasonal_supply_profile,
        continuity_risk_assessment,
        collection_frequency_table,
    )
    from logistics_engine import (
        build_logistics_table,
        logistics_summary,
    )
    from capacity_risk_engine import build_capacity_risk_dashboard
    from digestate_demand_engine import build_digestate_dashboard
    from mol_blturner import build_mol_insights, make_mol_shi_long_df, mol_shi_chart_bytes, mol_summary_chart_bytes, render_species_badges
    from water_balance_engine import compute_water_balance
    from portfolio_registry import (
        BL_TURNER_SITES,
        solution_playbook,
        site_by_name,
        solution_lines,
    )
    from data_provenance import provenance_table, scope_boundary_statement
    from stakeholder_engagement import (
        engagement_tracker_rows,
        data_sharing_agreement_checklist,
    )


st.set_page_config(page_title="EagleNatureInsight", layout="wide")

APP_TITLE = "EagleNatureInsight"
APP_SUBTITLE = "    Nature intelligence delivered through a simple, structured workflow"
APP_TAGLINE = "Locate • Evaluate • Assess • Prepare"

CURRENT_YEAR = date.today().year
LAST_FULL_YEAR = CURRENT_YEAR - 1

LOGO_PATH = Path("assets/logo.png")

# -----------------------------------------------------------------------------
# BL Turner site presets
# -----------------------------------------------------------------------------
# Main site coordinates: Portion 159 of New Guelderland, KwaDukuza.
# Bronwen provided the address but not exact corner coordinates.
# Using a representative centroid for KwaDukuza / New Guelderland area;
# user can draw the exact polygon on the map to refine.

PRESETS = [
    "Custom site",
    "BL Turner Main Site (Portion 159, New Guelderland, KwaDukuza)",
    "Durban Fresh Produce Market (Clairwood) — feedstock source",
    "Pietermaritzburg Abattoir Cluster — feedstock source",
    "eThekwini Kerbside Organics Collection Zone — feedstock source",
]

PRESET_TO_LOCATION = {
    "BL Turner Main Site (Portion 159, New Guelderland, KwaDukuza)": {
        "lat": -29.309186, "lon": 31.326527, "buffer_m": 300, "zoom": 15,
    },
    "Durban Fresh Produce Market (Clairwood) — feedstock source": {
        "lat": -29.9369, "lon": 30.9833, "buffer_m": 600, "zoom": 15,
    },
    "Pietermaritzburg Abattoir Cluster — feedstock source": {
        "lat": -29.6166, "lon": 30.3927, "buffer_m": 800, "zoom": 14,
    },
    "eThekwini Kerbside Organics Collection Zone — feedstock source": {
        "lat": -29.8587, "lon": 31.0218, "buffer_m": 2000, "zoom": 12,
    },
}

PRESET_TO_CATEGORY = {
    "BL Turner Main Site (Portion 159, New Guelderland, KwaDukuza)": "Organic Waste / Anaerobic Digestion / Biogas",
    "Durban Fresh Produce Market (Clairwood) — feedstock source": "Organic Waste / Anaerobic Digestion / Biogas",
    "Pietermaritzburg Abattoir Cluster — feedstock source": "Organic Waste / Anaerobic Digestion / Biogas",
    "eThekwini Kerbside Organics Collection Zone — feedstock source": "Organic Waste / Anaerobic Digestion / Biogas",
}

CATEGORIES = [
    "Organic Waste / Anaerobic Digestion / Biogas",
]


# -----------------------------------------------------------------------------
# Authentication
# -----------------------------------------------------------------------------
DEFAULT_USERNAME = "admin-blturner"
DEFAULT_PASSWORD = "BLTurnerPilot2026!"


def get_demo_credentials():
    creds = st.secrets.get("app_auth", {}) if hasattr(st, "secrets") else {}
    return {
        "username": creds.get("username", DEFAULT_USERNAME),
        "password": creds.get("password", DEFAULT_PASSWORD),
    }


def init_auth_state():
    for key, value in {
        "authenticated": False,
        "login_error": "",
    }.items():
        if key not in st.session_state:
            st.session_state[key] = value


def login_gate():
    creds = get_demo_credentials()

    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1320px;
            padding-top: 0.6rem !important;
            padding-bottom: 0.8rem !important;
        }
        header[data-testid="stHeader"] {
            background: transparent !important;
            height: 0 !important;
        }
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 12% 10%, rgba(96,165,250,0.10), transparent 24%),
                radial-gradient(circle at 88% 12%, rgba(34,197,94,0.07), transparent 18%),
                linear-gradient(180deg, #f8fbff 0%, #f2f7fb 100%);
        }
        div[data-testid="stVerticalBlock"] > div:empty,
        div[data-testid="stHorizontalBlock"] > div:empty,
        [data-testid="stMarkdownContainer"]:empty {
            display: none !important;
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        .login-hero { padding: 0.4rem 0.4rem 0.2rem 0.2rem; color: #0f172a; }
        .login-brand-chip {
            display: inline-flex; align-items: center; gap: 8px;
            padding: 8px 14px; border-radius: 999px;
            background: rgba(255,255,255,0.82);
            border: 1px solid rgba(148,163,184,0.24);
            font-size: 0.79rem; letter-spacing: 0.04em;
            text-transform: uppercase; color: #33506b;
            margin-bottom: 18px; backdrop-filter: blur(10px);
        }
        .login-title {
            font-size: 3.1rem; line-height: 0.98;
            font-weight: 800; letter-spacing: -0.03em;
            margin: 0 0 16px 0; max-width: 640px; color: #0b1f33;
        }
        .login-subtitle {
            max-width: 580px; font-size: 1.03rem; line-height: 1.62;
            color: #40576d; margin-bottom: 22px;
        }
        .login-feature-grid {
            display: grid; grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 14px; max-width: 620px; margin-top: 10px;
        }
        .login-feature {
            background: rgba(255,255,255,0.66);
            border: 1px solid rgba(148,163,184,0.18);
            border-radius: 20px; padding: 16px 18px;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
            backdrop-filter: blur(10px);
        }
        .login-feature-kicker {
            font-size: 0.74rem; text-transform: uppercase;
            letter-spacing: 0.08em; color: #1d4ed8; margin-bottom: 6px;
        }
        .login-feature-title { font-size: 1rem; font-weight: 700; color: #0f172a; margin: 0 0 4px 0; }
        .login-feature-copy { font-size: 0.88rem; line-height: 1.45; color: #4b6175; }
        .login-panel {
            margin-top: 0.15rem; border-radius: 28px;
            padding: 26px 24px 20px 24px;
            background: rgba(255,255,255,0.90);
            border: 1px solid rgba(148,163,184,0.20);
            box-shadow: 0 22px 50px rgba(15, 23, 42, 0.08);
            backdrop-filter: blur(18px);
        }
        .login-panel-kicker {
            font-size: 0.76rem; text-transform: uppercase;
            letter-spacing: 0.08em; color: #64748b; margin-bottom: 6px;
        }
        .login-panel-title { font-size: 1.6rem; line-height: 1.08; font-weight: 800; color: #0f172a; margin: 0; }
        .login-panel-copy { color: #475569; font-size: 0.95rem; line-height: 1.52; margin: 10px 0 14px 0; }
        .login-footer {
            margin-top: 14px; padding-top: 14px;
            border-top: 1px solid #e2e8f0;
            display: flex; align-items: center; justify-content: space-between;
            gap: 14px; color: #64748b; font-size: 0.82rem;
        }
        div[data-testid="stForm"] {
            border: none !important; padding: 0 !important;
            background: transparent !important; box-shadow: none !important;
        }
        .login-panel .stTextInput label {
            font-size: 0.84rem !important; font-weight: 600 !important; color: #334155 !important;
        }
        .login-panel input {
            border-radius: 14px !important;
            border: 1px solid #dbe3ee !important;
            background: rgba(248,250,252,0.94) !important;
            min-height: 48px !important;
        }
        .login-panel input:focus {
            border-color: #1d4ed8 !important;
            box-shadow: 0 0 0 1px rgba(29,78,216,0.18) !important;
        }
        .login-panel .stButton > button,
        .login-panel button[kind="primaryFormSubmit"] {
            width: 100% !important; border-radius: 14px !important; min-height: 50px !important;
            background: linear-gradient(135deg, #0d2f4d 0%, #103c63 55%, #1f5d8c 100%) !important;
            color: white !important; border: none !important;
            box-shadow: 0 18px 30px rgba(16,60,99,0.18) !important; font-weight: 700 !important;
        }
        .login-panel .stAlert { margin-top: 12px; border-radius: 14px !important; }
        @media (max-width: 980px) {
            .login-title { font-size: 2.35rem; max-width: none; }
            .login-feature-grid { grid-template-columns: 1fr; max-width: none; }
            .login-panel { margin-top: 0.75rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.45, 0.95], gap="large")

    with left:
        st.markdown('<div class="login-hero">', unsafe_allow_html=True)
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=132)
        st.markdown(
            """
            <div class="login-brand-chip">EagleNatureInsight · BL Turner Group Pilot</div>
            <h1 class="login-title">    Nature intelligence delivered through a simple, structured workflow.</h1>
            <div class="login-subtitle">
                A TNFD-aligned LEAP workspace for BL Turner Group's anaerobic digestion
                operations across a regional supply network — with site environmental screening
                and funder-ready outputs.
            </div>
            <div class="login-feature-grid">
                <div class="login-feature">
                    <div class="login-feature-kicker">Locate</div>
                    <div class="login-feature-title">Main site and feedstock sources on one map</div>
                    <div class="login-feature-copy">See the KwaDukuza plant plus every waste source node and digestate off-take area.</div>
                </div>
                <div class="login-feature">
                    <div class="login-feature-kicker">Evaluate</div>
                    <div class="login-feature-title">Waste frequency, tonnage, seasonality</div>
                    <div class="login-feature-copy">Understand supply headroom against plant processing capacity, and where it comes from.</div>
                </div>
                <div class="login-feature">
                    <div class="login-feature-kicker">Assess</div>
                    <div class="login-feature-title">Continuity-of-supply risk</div>
                    <div class="login-feature-copy">Concentration, logistics, contracts, seasonality, biosecurity — spelt out plainly.</div>
                </div>
                <div class="login-feature">
                    <div class="login-feature-kicker">Prepare</div>
                    <div class="login-feature-title">TNFD + NPI + landfill diversion</div>
                    <div class="login-feature-copy">Disclosure-ready indicators plus avoided-methane positioning for funders.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="login-panel">', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="login-panel-top">
                <div class="login-panel-kicker">Welcome</div>
                <h2 class="login-panel-title">Sign in to continue</h2>
            </div>
            <div class="login-panel-copy">
                Enter your BL Turner pilot access credentials to open the platform.
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submitted = st.form_submit_button("Access platform", use_container_width=True)
            if submitted:
                if username == creds["username"] and password == creds["password"]:
                    st.session_state["authenticated"] = True
                    st.session_state["login_error"] = ""
                    st.rerun()
                else:
                    st.session_state["login_error"] = "Incorrect username or password."
        if st.session_state.get("login_error"):
            st.error(st.session_state["login_error"])
        st.markdown(
            """
            <div class="login-footer">
                <span>BL Turner pilot workspace</span>
                <span>Secure login</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)


def logout_action():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state["authenticated"] = False
    st.rerun()


def reset_selection():
    keep_keys = {"authenticated"}
    auth_value = st.session_state.get("authenticated", False)
    for key in list(st.session_state.keys()):
        if key not in keep_keys:
            del st.session_state[key]
    st.session_state["authenticated"] = auth_value
    st.session_state["preset_selector"] = "Custom site"
    st.session_state["active_preset"] = "Custom site"
    st.rerun()


# -----------------------------------------------------------------------------
# Session state init
# -----------------------------------------------------------------------------
def init_state():
    defaults = {
        "preset_selector": "BL Turner Main Site (Portion 159, New Guelderland, KwaDukuza)",
        "active_preset": "BL Turner Main Site (Portion 159, New Guelderland, KwaDukuza)",
        "category_selector": "Organic Waste / Anaerobic Digestion / Biogas",
        "lat_input": "-29.309186",
        "lon_input": "31.326527",
        "buffer_input": 300,
        "map_center": [-29.309186, 31.326527],
        "map_zoom": 11,
        "draw_mode": "Enter coordinates",
        "last_drawn_geojson": None,
        "report_payload": None,
        "results_payload": None,
        "map_nonce": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def apply_preset(preset: str):
    st.session_state["active_preset"] = preset
    if preset in PRESET_TO_CATEGORY:
        st.session_state["category_selector"] = PRESET_TO_CATEGORY[preset]
    if preset in PRESET_TO_LOCATION:
        loc = PRESET_TO_LOCATION[preset]
        st.session_state["lat_input"] = str(loc["lat"])
        st.session_state["lon_input"] = str(loc["lon"])
        st.session_state["buffer_input"] = int(loc["buffer_m"])
        st.session_state["map_center"] = [loc["lat"], loc["lon"]]
        st.session_state["map_zoom"] = loc["zoom"]


def preset_changed():
    preset = st.session_state["preset_selector"]
    st.session_state["active_preset"] = preset
    if preset in PRESET_TO_LOCATION:
        apply_preset(preset)
    st.rerun()


# -----------------------------------------------------------------------------
# UI helpers
# -----------------------------------------------------------------------------
def has_data(val):
    if val is None:
        return False
    try:
        return pd.notna(val)
    except Exception:
        return True


def fmt_num(val, digits=1, suffix=""):
    if not has_data(val):
        return "Not available"
    try:
        return f"{float(val):.{digits}f}{suffix}"
    except Exception:
        return str(val)


def metric_card(label: str, value: str, subtext: str = ""):
    st.markdown(
        f"""
        <div class="eni-card">
            <div class="eni-card-label">{label}</div>
            <div class="eni-card-value">{value}</div>
            <div class="eni-card-subtext">{subtext}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def display_metric_cards(specs, per_row=3):
    available = [spec for spec in specs if has_data(spec.get("raw"))]
    if not available:
        return
    for start in range(0, len(available), per_row):
        row = available[start:start + per_row]
        cols = st.columns(per_row)
        for idx, spec in enumerate(row):
            with cols[idx]:
                metric_card(spec["label"], spec["value"], spec.get("subtext", ""))


def _safe_dataframe_for_display(df: pd.DataFrame) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()
    try:
        safe_df = df.copy()
        for col in safe_df.columns:
            safe_df[col] = safe_df[col].apply(lambda x: "" if x is None else str(x))
        return safe_df
    except Exception:
        try:
            return pd.DataFrame(df).astype(str)
        except Exception:
            return pd.DataFrame()


# -----------------------------------------------------------------------------
# Map building
# -----------------------------------------------------------------------------
MAIN_SITE = {
    "name": "BL Turner Main Site (Portion 159, New Guelderland)",
    "lat": -29.309186,
    "lon": 31.326527,
    "description": "100 t/day anaerobic digestion facility, KwaDukuza",
}


def build_map(center, zoom, draw_mode, lat=None, lon=None, buffer_m=None, existing_geojson=None, show_waste_network=True):
    """Build a folium map. Always renders BL Turner main site, all waste
    source nodes, and digestate off-take areas as colour-coded pins."""
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
            style_function=lambda x: {"color": "#ff0000", "weight": 3, "fillOpacity": 0.05},
        ).add_to(m)

    active_lat = None
    active_lon = None
    try:
        if lat not in [None, "", "None"] and lon not in [None, "", "None"]:
            active_lat = float(lat)
            active_lon = float(lon)
    except (TypeError, ValueError):
        pass

    # ----- Main site (always shown) -----
    fg_main = folium.FeatureGroup(name="BL Turner main site", show=True)
    folium.Marker(
        location=[MAIN_SITE["lat"], MAIN_SITE["lon"]],
        popup=folium.Popup(
            f"<b>{MAIN_SITE['name']}</b><br>{MAIN_SITE['description']}<br>"
            f"Lat {MAIN_SITE['lat']:.4f}, Lon {MAIN_SITE['lon']:.4f}",
            max_width=320,
        ),
        tooltip="BL Turner AD plant (KwaDukuza)",
        icon=folium.Icon(color="darkblue", icon="industry", prefix="fa"),
    ).add_to(fg_main)
    fg_main.add_to(m)

    if show_waste_network:
        # ----- Waste source nodes -----
        fg_sources = folium.FeatureGroup(name="Waste feedstock sources", show=True)
        for src in WASTE_SOURCES:
            popup_html = (
                f"<b>{src['name']}</b><br>"
                f"<i>{src.get('municipality', '')} · {src.get('district', '')}</i><br>"
                f"Stream: {src.get('waste_stream', '—')}<br>"
                f"~{src.get('tons_per_day_est', 0)} t/day · {src.get('collection_frequency', '—')}<br>"
                f"Role: {src.get('role', '—')}"
            )
            folium.CircleMarker(
                location=[src["lat"], src["lon"]],
                radius=max(5, min(14, (src.get("tons_per_day_est", 1) or 1) * 0.6)),
                color="#b45309",
                weight=2,
                fill=True,
                fill_color="#f59e0b",
                fill_opacity=0.75,
                popup=folium.Popup(popup_html, max_width=340),
                tooltip=f"{src['name']} (~{src.get('tons_per_day_est', 0)} t/day)",
            ).add_to(fg_sources)
            # Line from source to plant
            folium.PolyLine(
                locations=[[src["lat"], src["lon"]], [MAIN_SITE["lat"], MAIN_SITE["lon"]]],
                color="#f59e0b",
                weight=1.2,
                opacity=0.35,
                dash_array="6,6",
            ).add_to(fg_sources)
        fg_sources.add_to(m)

        # ----- Digestate off-take areas -----
        fg_offtake = folium.FeatureGroup(name="Digestate / fertiliser off-take", show=True)
        for area in DIGESTATE_OFFTAKE_AREAS:
            popup_html = (
                f"<b>{area['name']}</b><br>"
                f"<i>{area.get('description', '')}</i><br>"
                f"Role: {area.get('role', '—')}"
            )
            folium.CircleMarker(
                location=[area["lat"], area["lon"]],
                radius=9,
                color="#065f46",
                weight=2,
                fill=True,
                fill_color="#10b981",
                fill_opacity=0.65,
                popup=folium.Popup(popup_html, max_width=320),
                tooltip=f"Digestate off-take: {area['name']}",
            ).add_to(fg_offtake)
        fg_offtake.add_to(m)

    # Optional drawn coordinate marker / buffer ring
    if draw_mode == "Enter coordinates" and active_lat is not None and active_lon is not None:
        folium.Circle(
            [active_lat, active_lon],
            radius=float(buffer_m or 500),
            color="#ff0000",
            weight=2,
            fill=False,
        ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    return m


def extract_drawn_geometry(map_data):
    if not map_data:
        return None
    drawings = map_data.get("all_drawings") or []
    if not drawings:
        return None
    return drawings[-1]


def get_geometry_payload(drawn_geojson, lat, lon, buffer_m, mode):
    if mode == "Draw polygon":
        if drawn_geojson:
            return "Polygon captured from the map.", drawn_geojson, geojson_to_ee_geometry(drawn_geojson)
        return "No polygon has been drawn yet.", None, None

    try:
        lat_val = float(lat)
        lon_val = float(lon)
        geom = point_buffer_to_ee_geometry(lat_val, lon_val, float(buffer_m))
        payload = {
            "type": "PointBuffer",
            "lat": lat_val,
            "lon": lon_val,
            "buffer_m": float(buffer_m),
        }
        return (
            f"Point entered at ({lat_val:.5f}, {lon_val:.5f}) with {buffer_m} m buffer.",
            payload,
            geom,
        )
    except (TypeError, ValueError):
        return "Please enter valid latitude and longitude.", None, None


def _extract_coords_from_geojson(geom_obj):
    coords = []
    if not isinstance(geom_obj, dict):
        return coords
    gtype = (geom_obj.get("geometry") or geom_obj).get("type")
    gcoords = (geom_obj.get("geometry") or geom_obj).get("coordinates", [])
    if gtype == "Polygon":
        for ring in gcoords[:1]:
            for pt in ring:
                if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                    coords.append((float(pt[1]), float(pt[0])))
    elif gtype == "MultiPolygon":
        for poly in gcoords[:1]:
            for ring in poly[:1]:
                for pt in ring:
                    if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                        coords.append((float(pt[1]), float(pt[0])))
    return coords


def update_map_view_from_selection(geometry_payload, mode):
    try:
        if mode == "Enter coordinates" and isinstance(geometry_payload, dict) and geometry_payload.get("type") == "PointBuffer":
            lat_val = float(geometry_payload.get("lat"))
            lon_val = float(geometry_payload.get("lon"))
            buffer_m = float(geometry_payload.get("buffer_m", 500))
            st.session_state["map_center"] = [lat_val, lon_val]
            if buffer_m <= 500:
                st.session_state["map_zoom"] = 16
            elif buffer_m <= 1500:
                st.session_state["map_zoom"] = 15
            elif buffer_m <= 5000:
                st.session_state["map_zoom"] = 13
            else:
                st.session_state["map_zoom"] = 11
            return

        coords = _extract_coords_from_geojson(geometry_payload)
        if coords:
            lats = [c[0] for c in coords]
            lons = [c[1] for c in coords]
            st.session_state["map_center"] = [sum(lats) / len(lats), sum(lons) / len(lons)]
            lat_span = max(lats) - min(lats)
            lon_span = max(lons) - min(lons)
            span = max(lat_span, lon_span)
            if span <= 0.002:
                st.session_state["map_zoom"] = 16
            elif span <= 0.008:
                st.session_state["map_zoom"] = 15
            elif span <= 0.02:
                st.session_state["map_zoom"] = 14
            elif span <= 0.05:
                st.session_state["map_zoom"] = 12
            else:
                st.session_state["map_zoom"] = 10
    except Exception:
        pass


# -----------------------------------------------------------------------------
# Earth Engine data helpers
# -----------------------------------------------------------------------------
def fc_to_dataframe(fc) -> pd.DataFrame:
    info = fc.getInfo()
    rows = []
    for feature in info.get("features", []):
        props = feature.get("properties", {})
        rows.append(props)
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


def df_chart_to_png_bytes(df, x_col, y_col, title, kind="line", x_label="Year", y_label="Value"):
    if df is None or df.empty:
        return None
    fig, ax = plt.subplots(figsize=(10, 5.2))
    if kind == "bar":
        ax.bar(df[x_col], df[y_col])
    else:
        ax.plot(df[x_col], df[y_col], marker="o")
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def landcover_bar_to_png_bytes(df):
    if df is None or df.empty:
        return None
    df2 = df.sort_values("area_ha", ascending=False).copy()
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar(df2["class_name"], df2["area_ha"])
    ax.set_title("Current Land Cover Composition")
    ax.set_xlabel("Land-cover class")
    ax.set_ylabel("Area (ha)")
    ax.grid(True, axis="y", alpha=0.3)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def build_landcover_bar(df):
    fig = px.bar(
        df.sort_values("area_ha", ascending=False),
        x="class_name", y="area_ha",
        title="Current Land Cover Composition",
    )
    fig.update_layout(
        xaxis_title="Land-cover class",
        yaxis_title="Area (ha)",
        showlegend=False,
        margin=dict(l=40, r=20, t=60, b=80),
    )
    return fig


def fetch_image_bytes(url: str, timeout: int = 60):
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        buf = BytesIO(r.content)
        buf.seek(0)
        return buf
    except Exception:
        return None


def fetch_pdf_ee_image_bytes(image, geom, dimensions=900, retries=3):
    attempt_dims = [dimensions, 700, 500]
    for i in range(min(retries, len(attempt_dims))):
        try:
            url = image_thumb_url(image, geom, dimensions=attempt_dims[i])
            result = fetch_image_bytes(url, timeout=150)
            if result is not None:
                return result
        except Exception:
            pass
    return None


# -----------------------------------------------------------------------------
# Waste sourcing visualisation helpers (BL Turner differentiator)
# -----------------------------------------------------------------------------
def waste_sources_to_dataframe():
    rows = []
    for src in WASTE_SOURCES:
        rows.append({
            "Source": src.get("name"),
            "District": src.get("district"),
            "Municipality": src.get("municipality"),
            "Stream": src.get("stream"),
            "Est. tons/day": src.get("tons_per_day_est"),
            "Frequency": src.get("collection_frequency"),
            "Seasonality": src.get("seasonality"),
            "Role": src.get("role"),
        })
    return pd.DataFrame(rows)


def stream_mix_to_plotly_pie():
    data = stream_mix_summary()
    df = pd.DataFrame(data)
    if df.empty:
        return None
    fig = px.pie(df, values="tons_per_day", names="stream",
                 title="Feedstock mix by waste stream (est. tons/day)",
                 hole=0.4)
    fig.update_layout(margin=dict(l=20, r=20, t=60, b=20))
    return fig


def district_mix_to_plotly_pie():
    data = district_mix_summary()
    df = pd.DataFrame(data)
    if df.empty:
        return None
    fig = px.pie(df, values="tons_per_day", names="district",
                 title="Feedstock mix by district (est. tons/day)",
                 hole=0.4)
    fig.update_layout(margin=dict(l=20, r=20, t=60, b=20))
    return fig


def seasonal_profile_to_plotly_bar():
    data = seasonal_supply_profile()
    df = pd.DataFrame(data)
    if df.empty:
        return None
    fig = px.bar(df, x="month", y="projected_tons_per_day",
                 title="Projected monthly feedstock supply (t/day)",
                 labels={"month": "Month", "projected_tons_per_day": "Tons/day"})
    # Nameplate reference line
    fig.add_hline(y=100, line_dash="dash", line_color="#dc2626",
                  annotation_text="Nameplate 100 t/day", annotation_position="top right")
    fig.update_layout(margin=dict(l=40, r=20, t=60, b=60))
    return fig


def seasonal_profile_to_png_bytes():
    data = seasonal_supply_profile()
    if not data:
        return None
    df = pd.DataFrame(data)
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.bar(df["month"], df["projected_tons_per_day"], color="#f59e0b")
    ax.axhline(100, linestyle="--", color="#dc2626", linewidth=1.2,
               label="Nameplate 100 t/day")
    ax.set_title("Projected monthly feedstock supply")
    ax.set_xlabel("Month")
    ax.set_ylabel("Tons/day")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


# -----------------------------------------------------------------------------
# Automated risk flags (BL Turner context — includes feedstock continuity)
# -----------------------------------------------------------------------------
def build_automated_risk_flags(metrics, continuity_risks=None):
    flags = []

    def add_flag(level, title, current_value, meaning, action):
        flags.append({
            "Level": level,
            "Flag": title,
            "Current value": current_value,
            "Why it matters": meaning,
            "Suggested action": action,
        })

    # Site environmental flags
    try:
        val = metrics.get("flood_risk")
        if val is not None and float(val) >= 0.3:
            f = float(val)
            add_flag("High", "Flood exposure on AD plant site", f"{f:.2f} m",
                     f"Mapped 1-in-100 year flood depth of {f:.2f} m could affect digesters, "
                     "biogas holders, electrical equipment and feedstock reception areas.",
                     "Commission a local drainage assessment and plan for flood bunding or "
                     "raised infrastructure where pooling is likely.")
        elif val is not None and float(val) > 0.05:
            f = float(val)
            add_flag("Moderate", "Low-lying flood sensitivity", f"{f:.2f} m",
                     f"Some flood signal ({f:.2f} m) is present in the landscape around the plant.",
                     "Review stormwater drainage routes and keep critical equipment above the "
                     "local 1-in-100 flood line.")
    except Exception:
        pass

    try:
        val = metrics.get("lst_mean")
        if val is not None and float(val) >= 32:
            f = float(val)
            add_flag("Moderate", "Elevated heat load",
                     f"{f:.1f} °C",
                     f"Sustained surface heat ({f:.1f} °C) can raise digester cooling and "
                     "odour control loads in summer peaks.",
                     "Review heat management of digester jackets, CHP cooling and feedstock "
                     "reception during summer months.")
    except Exception:
        pass

    try:
        val = metrics.get("rain_anom_pct")
        if val is not None and float(val) < -15:
            f = float(val)
            add_flag("Moderate", "Dry rainfall regime",
                     f"{f:.1f}%",
                     f"Rainfall is running about {abs(f):.0f}% below baseline, which affects "
                     "process water availability and nearby digestate demand.",
                     "Plan process water storage and consider rainwater/recycled water capture.")
    except Exception:
        pass

    # Feedstock continuity risks from waste_sourcing module
    if continuity_risks:
        for risk in continuity_risks:
            add_flag(
                risk.get("level", "Moderate"),
                risk.get("risk", "Supply continuity"),
                risk.get("indicator", "—"),
                risk.get("meaning", "—"),
                risk.get("mitigation", "—"),
            )

    if not flags:
        add_flag("Monitor", "No dominant automated flag", "Current conditions",
                 "No single dominant warning sign has been triggered by the current metric set.",
                 "Continue routine monitoring and refresh the assessment as new data arrives.")

    return flags


def risk_flags_to_dataframe(flags):
    df = pd.DataFrame(flags)
    if df.empty:
        return df
    return df.fillna("Not available").astype(str)


# =============================================================================
# Main page
# =============================================================================

init_auth_state()
init_state()

if not st.session_state["authenticated"]:
    login_gate()
    st.stop()

try:
    initialize_ee_from_secrets(st)
except Exception as e:
    st.error("Earth Engine initialization failed. Check your Streamlit secrets and Google Cloud permissions.")
    st.exception(e)
    st.stop()

# -----------------------------------------------------------------------------
# Global CSS / hero
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    :root {
        --eni-bg: #f4f7fb;
        --eni-surface: #ffffff;
        --eni-ink: #0f172a;
        --eni-muted: #64748b;
        --eni-line: #e2e8f0;
        --eni-brand: #103c63;
        --eni-brand-2: #1f5d8c;
        --eni-accent: #dbeafe;
        --eni-shadow: 0 14px 40px rgba(15, 23, 42, 0.08);
    }
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(219,234,254,0.75), transparent 30%),
            linear-gradient(180deg, #f8fbff 0%, var(--eni-bg) 100%);
    }
    .block-container {
        padding-top: 2.4rem;
        padding-bottom: 2.5rem;
        max-width: 1400px;
    }
    .eni-top-spacer { height: 8px; }
    .eni-logo-wrap { padding-top: 10px; }
    .eni-hero {
        margin-top: 10px;
        background: linear-gradient(135deg, #0d2f4d 0%, #103c63 52%, #1f5d8c 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 28px;
        padding: 30px 34px;
        color: white;
        box-shadow: 0 24px 60px rgba(16,60,99,0.22);
        margin-bottom: 22px;
    }
    .eni-eyebrow {
        display: inline-block;
        padding: 7px 12px;
        border-radius: 999px;
        background: rgba(255,255,255,0.12);
        font-size: 0.80rem;
        letter-spacing: 0.02em;
        margin-bottom: 12px;
    }
    .eni-title { font-size: 2.35rem; line-height: 1.05; font-weight: 800; margin: 0 0 6px 0; }
    .eni-subtitle { color: rgba(255,255,255,0.88); font-size: 1rem; max-width: 800px; margin-bottom: 14px; }
    .eni-step-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
    .eni-step {
        background: rgba(255,255,255,0.10);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 18px;
        padding: 14px 16px;
        min-height: 98px;
    }
    .eni-step-num {
        font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em;
        color: rgba(255,255,255,0.72); margin-bottom: 4px;
    }
    .eni-step-title { font-size: 1rem; font-weight: 700; margin-bottom: 3px; overflow-wrap: anywhere; }
    .eni-step-copy { font-size: 0.84rem; line-height: 1.35; color: rgba(255,255,255,0.82); overflow-wrap: anywhere; }
    .eni-section {
        background: rgba(255,255,255,0.72);
        border: 1px solid rgba(226,232,240,0.95);
        border-radius: 24px;
        padding: 20px 22px;
        box-shadow: var(--eni-shadow);
        margin-bottom: 18px;
        backdrop-filter: blur(4px);
    }
    .eni-card {
        background: var(--eni-surface);
        border: 1px solid var(--eni-line);
        border-radius: 20px;
        padding: 16px 16px 14px 16px;
        min-height: 124px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
        overflow: hidden;
    }
    .eni-card-label { font-size: 0.80rem; color: var(--eni-muted); line-height: 1.25; overflow-wrap: anywhere; }
    .eni-card-value { font-size: 1.7rem; line-height: 1.12; font-weight: 800; color: var(--eni-ink); margin-top: 8px; overflow-wrap: anywhere; }
    .eni-card-subtext { font-size: 0.75rem; line-height: 1.35; color: var(--eni-muted); margin-top: 8px; overflow-wrap: anywhere; }
    .eni-kicker { font-size: 0.78rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #335b7f; margin-bottom: 8px; }
    .eni-small { color: var(--eni-muted); font-size: 0.92rem; }
    div[data-baseweb="tab-list"] { gap: 8px; padding-bottom: 8px; flex-wrap: wrap; }
    button[data-baseweb="tab"] {
        background: rgba(255,255,255,0.9);
        border: 1px solid var(--eni-line);
        border-radius: 999px;
        padding: 8px 14px;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background: #103c63;
        color: white;
        border-color: #103c63;
    }
    .stButton > button, .stDownloadButton > button {
        border-radius: 14px;
        min-height: 44px;
        font-weight: 700;
        border: 1px solid #103c63;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #103c63 0%, #1f5d8c 100%);
        border: none;
    }
    .stDataFrame, .stPlotlyChart, .stImage {
        border-radius: 18px;
        overflow: hidden;
    }
    @media (max-width: 768px) {
        .eni-step-grid { grid-template-columns: 1fr !important; gap: 10px !important; }
        .eni-title { font-size: 1.65rem !important; }
        .eni-subtitle { font-size: 0.92rem !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="eni-top-spacer"></div>', unsafe_allow_html=True)

hero_left, hero_right = st.columns([1.05, 4.95])

with hero_left:
    st.markdown('<div class="eni-logo-wrap">', unsafe_allow_html=True)
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=210)
    st.markdown('</div>', unsafe_allow_html=True)

with hero_right:
    st.markdown(
        f"""
        <div class="eni-hero">
            <div class="eni-eyebrow">Client workspace</div>
            <div class="eni-title">{APP_TITLE}</div>
            <div class="eni-subtitle">{APP_SUBTITLE}</div>
            <div class="eni-subtitle" style="margin-bottom:18px;">
                A TNFD LEAP workspace for a commercial-scale anaerobic digestion (AD) facility —
                with a dedicated view of feedstock sourcing and digestate utilisation across the
                regional supply network.
            </div>
            <div class="eni-step-grid">
                <div class="eni-step">
                    <div class="eni-step-num">LEAP · Locate</div>
                    <div class="eni-step-title">Plant & supply network</div>
                    <div class="eni-step-copy">Main facility, waste sources and digestate off-take areas on one map.</div>
                </div>
                <div class="eni-step">
                    <div class="eni-step-num">LEAP · Evaluate</div>
                    <div class="eni-step-title">Feedstock frequency & tonnage</div>
                    <div class="eni-step-copy">Daily, weekly and seasonal supply projections against plant processing capacity.</div>
                </div>
                <div class="eni-step">
                    <div class="eni-step-num">LEAP · Assess</div>
                    <div class="eni-step-title">Continuity of supply</div>
                    <div class="eni-step-copy">Concentration, logistics, biosecurity and contract dependencies.</div>
                </div>
                <div class="eni-step">
                    <div class="eni-step-num">LEAP · Prepare</div>
                    <div class="eni-step-title">TNFD · NPI · avoided methane</div>
                    <div class="eni-step-copy">Disclosure-ready outputs and a positive landfill-diversion narrative for funders.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# -----------------------------------------------------------------------------
# Site selection controls
# -----------------------------------------------------------------------------
control_left, control_mid, control_right = st.columns([1.85, 1.0, 0.75])
with control_left:
    st.selectbox("Site", PRESETS, key="preset_selector", on_change=preset_changed)
with control_mid:
    st.selectbox("Business category", CATEGORIES, key="category_selector")
with control_right:
    st.markdown("<div style='height: 1.9rem;'></div>", unsafe_allow_html=True)
    actions_a, actions_b = st.columns(2)
    with actions_a:
        st.button("Reset", width='stretch', on_click=reset_selection)
    with actions_b:
        if st.button("Sign out", width='stretch'):
            logout_action()

mode_col1, mode_col2 = st.columns([1, 1])
with mode_col1:
    st.radio(
        "Site definition method",
        ["Draw polygon", "Enter coordinates"],
        key="draw_mode",
        horizontal=True,
    )
with mode_col2:
    st.number_input(
        "Buffer radius (metres)",
        min_value=100,
        max_value=50000,
        step=100,
        key="buffer_input",
        disabled=(st.session_state["draw_mode"] == "Draw polygon"),
    )

if st.session_state["draw_mode"] == "Enter coordinates":
    lat_col, lon_col = st.columns(2)
    with lat_col:
        st.text_input("Latitude", key="lat_input", placeholder="-29.309186")
    with lon_col:
        st.text_input("Longitude", key="lon_input", placeholder="31.326527")

hist1, hist2 = st.columns(2)
with hist1:
    hist_start = st.number_input("Historical start year", min_value=1981, max_value=LAST_FULL_YEAR, value=2001, step=1)
with hist2:
    hist_end = st.number_input("Historical end year", min_value=1981, max_value=LAST_FULL_YEAR, value=LAST_FULL_YEAR, step=1)

st.markdown("### 1. Select the site and see the supply network")
st.caption(
    "The map shows BL Turner's main AD plant (dark blue), all feedstock source nodes "
    "(orange — sized by estimated daily tonnage) and digestate off-take areas (green). "
    "Zoom in and either draw a polygon or enter coordinates to screen a specific site."
)

m = build_map(
    center=st.session_state["map_center"],
    zoom=st.session_state["map_zoom"],
    draw_mode=st.session_state["draw_mode"],
    lat=st.session_state["lat_input"],
    lon=st.session_state["lon_input"],
    buffer_m=st.session_state["buffer_input"],
    existing_geojson=st.session_state["last_drawn_geojson"],
    show_waste_network=True,
)

map_data = st_folium(
    m,
    width=None,
    height=560,
    returned_objects=["all_drawings"],
    key=f"blturner_map_{st.session_state.get('map_nonce', 0)}",
)

drawn_geojson = extract_drawn_geometry(map_data)
if drawn_geojson is not None:
    st.session_state["last_drawn_geojson"] = drawn_geojson

summary_text, geometry_payload, ee_geom = get_geometry_payload(
    drawn_geojson=st.session_state["last_drawn_geojson"] if st.session_state["draw_mode"] == "Draw polygon" else None,
    lat=st.session_state["lat_input"],
    lon=st.session_state["lon_input"],
    buffer_m=st.session_state["buffer_input"],
    mode=st.session_state["draw_mode"],
)

st.markdown("### Current selection")
st.write(summary_text)

run_clicked = st.button("Generate Insights", type="primary", width='stretch')

if run_clicked:
    update_map_view_from_selection(geometry_payload, st.session_state["draw_mode"])
    st.session_state["map_nonce"] = int(st.session_state.get("map_nonce", 0)) + 1
    st.session_state["_run_after_zoom"] = True
    st.rerun()

run = st.session_state.pop("_run_after_zoom", False)

if run:
    if ee_geom is None:
        st.warning("Please draw a polygon or enter valid coordinates before generating insights.")
        st.stop()

    if hist_start > hist_end:
        st.warning("Historical start year must be earlier than or equal to end year.")
        st.stop()

    preset = st.session_state["active_preset"]
    category = st.session_state["category_selector"]

    with st.spinner("Running assessment (Earth Engine + waste sourcing analysis)..."):
        metrics = compute_metrics(
            geom=ee_geom,
            hist_start=int(hist_start),
            hist_end=int(hist_end),
            last_full_year=LAST_FULL_YEAR,
        )
        risk = build_risk_and_recommendations(
            preset=preset,
            category=category,
            metrics=metrics,
        )

        # Waste sourcing computations (BL Turner specific)
        waste_df = waste_sources_to_dataframe()
        stream_mix = stream_mix_summary()
        district_mix = district_mix_summary()
        monthly_supply = seasonal_supply_profile()
        continuity_risks = continuity_risk_assessment()
        frequency_table = collection_frequency_table()
        headroom = supply_headroom()
        logistics_rows = build_logistics_table(
            sources=WASTE_SOURCES,
            plant_lat=MAIN_SITE["lat"],
            plant_lon=MAIN_SITE["lon"],
        )
        logistics_kpis = logistics_summary(logistics_rows)

        capacity_risk = build_capacity_risk_dashboard(
            headroom=headroom,
            continuity_risks=continuity_risks,
            logistics_kpis=logistics_kpis,
        )
        digestate_outputs = build_digestate_dashboard(
            offtake_areas=DIGESTATE_OFFTAKE_AREAS,
            total_supply_tpd=headroom.get("total_supply_tpd", 0.0),
        )

        # Earth Engine imagery
        satellite_img = satellite_with_polygon(ee_geom, LAST_FULL_YEAR)
        ndvi_img = ndvi_with_polygon(ee_geom, LAST_FULL_YEAR)
        landcover_img = landcover_with_polygon(ee_geom)
        forest_loss_img = forest_loss_with_polygon(ee_geom)
        flood_risk_img = flood_risk_with_polygon(ee_geom)
        soil_condition_img = soil_condition_with_polygon(ee_geom)
        heat_stress_img = heat_stress_with_polygon(ee_geom, int(hist_end))
        veg_change_img = vegetation_change_with_polygon(ee_geom, int(hist_start), int(hist_end))

        satellite_url = image_thumb_url(satellite_img, ee_geom, 2200)
        ndvi_url = image_thumb_url(ndvi_img, ee_geom, 1400)
        landcover_url = image_thumb_url(landcover_img, ee_geom, 1400)
        forest_loss_url = image_thumb_url(forest_loss_img, ee_geom, 1400)
        flood_risk_url = image_thumb_url(flood_risk_img, ee_geom, 1400)
        soil_condition_url = image_thumb_url(soil_condition_img, ee_geom, 1400)
        heat_stress_url = image_thumb_url(heat_stress_img, ee_geom, 1400)
        try:
            veg_change_url = image_thumb_url(veg_change_img, ee_geom, 1400)
        except Exception:
            veg_change_url = None

        # Historical time-series
        ndvi_hist_df = prep_year_df(fc_to_dataframe(
            landsat_annual_ndvi_collection(ee_geom, max(int(hist_start), 1984), int(hist_end))
        ))
        rain_hist_df = prep_year_df(fc_to_dataframe(
            annual_rain_collection(ee_geom, max(int(hist_start), 1981), int(hist_end))
        ))
        lst_hist_df = prep_year_df(fc_to_dataframe(
            annual_lst_collection(ee_geom, max(int(hist_start), 2001), int(hist_end))
        ))
        forest_hist_df = prep_year_df(fc_to_dataframe(
            forest_loss_by_year_collection(ee_geom, int(hist_start), int(hist_end))
        ))
        water_hist_df = prep_year_df(fc_to_dataframe(
            water_history_collection(ee_geom, max(int(hist_start), 1984), int(hist_end))
        ))
        lc_df = fc_to_dataframe(landcover_feature_collection(ee_geom))
        if not lc_df.empty and "area_ha" in lc_df.columns:
            lc_df["area_ha"] = pd.to_numeric(lc_df["area_ha"], errors="coerce")
            lc_df = lc_df[lc_df["area_ha"].notna()].copy()
            lc_df = lc_df[lc_df["area_ha"] > 0].copy()

        # Automated risk flags
        automated_flags = build_automated_risk_flags(metrics, continuity_risks)

        # Map of Life insights
        mol_insights = build_mol_insights(preset)

        # PDF chart payloads
        seasonal_png = seasonal_profile_to_png_bytes()
        chart_payloads = [
            {
                "title": "Projected monthly feedstock supply",
                "description": "Month-by-month estimate of feedstock supply across all BL Turner source nodes, compared to the 100 t/day nameplate.",
                "bytes": seasonal_png,
            },
            {
                "title": "Historical NDVI",
                "description": "Vegetation condition around the AD plant over time.",
                "bytes": df_chart_to_png_bytes(ndvi_hist_df, "year", "value", "Historical NDVI (Landsat)", kind="line", y_label="NDVI"),
            },
            {
                "title": "Historical rainfall",
                "description": "Annual rainfall around the plant. Affects process water availability and downstream fertiliser demand.",
                "bytes": df_chart_to_png_bytes(rain_hist_df, "year", "value", "Historical Rainfall (CHIRPS)", kind="line", y_label="mm"),
            },
            {
                "title": "Historical land surface temperature",
                "description": "Annual mean LST at the site — relevant to digester cooling and odour control loads.",
                "bytes": df_chart_to_png_bytes(lst_hist_df, "year", "value", "Historical LST (MODIS)", kind="line", y_label="°C"),
            },
            {
                "title": "Historical forest loss",
                "description": "Annual forest loss in the surrounding landscape.",
                "bytes": df_chart_to_png_bytes(forest_hist_df, "year", "value", "Historical Forest Loss by Year (Hansen)", kind="bar", y_label="ha"),
            },
            {
                "title": "Historical water presence",
                "description": "Share of the area with mapped surface water each year.",
                "bytes": df_chart_to_png_bytes(water_hist_df, "year", "value", "Historical Water Presence (JRC)", kind="line", y_label="% water pixels"),
            },
            {
                "title": "Current land-cover composition",
                "description": "Current land-cover split around the selected site.",
                "bytes": landcover_bar_to_png_bytes(lc_df),
            },
        ]

        if mol_insights:
            mol_summary_png = mol_summary_chart_bytes(mol_insights)
            mol_trend_png = mol_shi_chart_bytes(mol_insights)
            if mol_summary_png:
                chart_payloads.append({
                    "title": "Map of Life species and habitat summary",
                    "description": "Map of Life summary for the BL Turner site or source zone, aligned to plant siting, habitat sensitivity, buffers and receiving-land decisions.",
                    "bytes": mol_summary_png,
                })
            if mol_trend_png:
                chart_payloads.append({
                    "title": "Map of Life Species Habitat Index trend",
                    "description": "Species Habitat Index trend for the matched BL Turner zone. Higher values generally indicate more suitable habitat for species over time.",
                    "bytes": mol_trend_png,
                })

        image_payloads = [
            {
                "title": "Satellite image with polygon",
                "description": "True-colour satellite view of the selected site.",
                "bytes": fetch_pdf_ee_image_bytes(satellite_img, ee_geom, dimensions=700),
            },
            {
                "title": "NDVI image with polygon",
                "description": "Vegetation condition around the site. Greener = stronger vegetation.",
                "bytes": fetch_pdf_ee_image_bytes(ndvi_img, ee_geom, dimensions=700),
            },
            {
                "title": "Land-cover image with polygon",
                "description": "Current land-cover classes around the site.",
                "bytes": fetch_pdf_ee_image_bytes(landcover_img, ee_geom, dimensions=850),
            },
            {
                "title": "Vegetation change map with polygon",
                "description": "Earlier vs later NDVI. Red = decline, green = improvement.",
                "bytes": fetch_pdf_ee_image_bytes(veg_change_img, ee_geom, dimensions=500),
            },
            {
                "title": "Forest loss map with polygon",
                "description": "Detected forest loss in and around the selected area.",
                "bytes": fetch_pdf_ee_image_bytes(forest_loss_img, ee_geom, dimensions=850),
            },
            {
                "title": "Flood risk map with polygon",
                "description": f"Mapped 1-in-100-year flood depth. Current value {fmt_num(metrics.get('flood_risk'), 2, ' m')}.",
                "bytes": fetch_pdf_ee_image_bytes(flood_risk_img, ee_geom, dimensions=850),
            },
            {
                "title": "Soil condition map with polygon",
                "description": f"Soil organic carbon proxy. Current value {fmt_num(metrics.get('soil_organic_carbon'), 1)}, topsoil texture class {metrics.get('soil_texture_class')}.",
                "bytes": fetch_pdf_ee_image_bytes(soil_condition_img, ee_geom, dimensions=850),
            },
            {
                "title": "Heat stress map with polygon",
                "description": f"Average land surface temperature. Current value {fmt_num(metrics.get('lst_mean'), 1, ' °C')}.",
                "bytes": fetch_pdf_ee_image_bytes(heat_stress_img, ee_geom, dimensions=850),
            },
        ]

        # PDF support payloads for the additional operational tabs
        water_balance = compute_water_balance(metrics)
        site_obj = site_by_name(preset)
        solution_key = site_obj.solution_line if site_obj else "organic_waste"
        solution_playbook_dict = solution_playbook(solution_key)
        engagement_rows = engagement_tracker_rows()
        data_sharing_checklist = data_sharing_agreement_checklist()
        provenance_rows = provenance_table()
        scope_boundary = scope_boundary_statement()

        # PDF report
        pdf_bytes = build_pdf_report(
            preset=preset,
            category=category,
            hist_start=int(hist_start),
            hist_end=int(hist_end),
            metrics=metrics,
            risk=risk,
            image_payloads=image_payloads,
            chart_payloads=chart_payloads,
            automated_flags=automated_flags,
            waste_sources=WASTE_SOURCES,
            monthly_supply=monthly_supply,
            continuity_risks=continuity_risks,
            stream_mix=stream_mix,
            district_mix=district_mix,
            supply_headroom_data=headroom,
            mol_insights=mol_insights,
            water_balance=water_balance,
            bl_turner_sites=BL_TURNER_SITES,
            solution_playbook_dict=solution_playbook_dict,
            engagement_rows=engagement_rows,
            data_sharing_checklist=data_sharing_checklist,
            provenance_rows=provenance_rows,
            scope_boundary=scope_boundary,
        )

        st.session_state["report_payload"] = {
            "pdf_bytes": pdf_bytes,
            "file_name": f"BLTurner_EagleNatureInsight_Report_{date.today().isoformat()}.pdf",
        }

        st.session_state["results_payload"] = {
            "preset": preset,
            "category": category,
            "metrics": metrics,
            "risk": risk,
            "automated_flags": automated_flags,
            "satellite_url": satellite_url,
            "ndvi_url": ndvi_url,
            "landcover_url": landcover_url,
            "forest_loss_url": forest_loss_url,
            "flood_risk_url": flood_risk_url,
            "soil_condition_url": soil_condition_url,
            "heat_stress_url": heat_stress_url,
            "veg_change_url": veg_change_url,
            "ndvi_hist_df": ndvi_hist_df,
            "rain_hist_df": rain_hist_df,
            "lst_hist_df": lst_hist_df,
            "forest_hist_df": forest_hist_df,
            "water_hist_df": water_hist_df,
            "lc_df": lc_df,
            "hist_start": int(hist_start),
            "hist_end": int(hist_end),
            "waste_df": waste_df,
            "stream_mix": stream_mix,
            "district_mix": district_mix,
            "monthly_supply": monthly_supply,
            "continuity_risks": continuity_risks,
            "frequency_table": frequency_table,
            "headroom": headroom,
            "logistics_rows": logistics_rows,
            "logistics_kpis": logistics_kpis,
            "capacity_risk": capacity_risk,
            "digestate_outputs": digestate_outputs,
            "mol_insights": mol_insights,
            "water_balance": water_balance,
            "engagement_rows": engagement_rows,
            "data_sharing_checklist": data_sharing_checklist,
            "provenance_rows": provenance_rows,
            "scope_boundary": scope_boundary,
            "solution_playbook_dict": solution_playbook_dict,
        }

    st.success("Assessment complete. Scroll down for the full LEAP view and download the PDF report.")

if st.session_state["report_payload"] is not None:
    st.download_button(
        label="Download PDF Report",
        data=st.session_state["report_payload"]["pdf_bytes"],
        file_name=st.session_state["report_payload"]["file_name"],
        mime="application/pdf",
        width='stretch',
    )


# -----------------------------------------------------------------------------
# Results view (tabs)
# -----------------------------------------------------------------------------
results = st.session_state["results_payload"]

if results is not None:
    preset = results["preset"]
    category = results["category"]
    metrics = results["metrics"]
    risk = results["risk"]
    automated_flags = results.get("automated_flags", [])
    satellite_url = results["satellite_url"]
    ndvi_url = results["ndvi_url"]
    landcover_url = results["landcover_url"]
    forest_loss_url = results.get("forest_loss_url")
    flood_risk_url = results.get("flood_risk_url")
    soil_condition_url = results.get("soil_condition_url")
    heat_stress_url = results.get("heat_stress_url")
    veg_change_url = results.get("veg_change_url")
    ndvi_hist_df = results["ndvi_hist_df"]
    rain_hist_df = results["rain_hist_df"]
    lst_hist_df = results["lst_hist_df"]
    forest_hist_df = results["forest_hist_df"]
    water_hist_df = results["water_hist_df"]
    lc_df = results["lc_df"]
    hist_start = results.get("hist_start")
    hist_end = results.get("hist_end")
    waste_df = results["waste_df"]
    stream_mix = results["stream_mix"]
    district_mix = results["district_mix"]
    monthly_supply = results["monthly_supply"]
    continuity_risks = results["continuity_risks"]
    frequency_table = results["frequency_table"]
    headroom = results["headroom"]
    logistics_rows = results["logistics_rows"]
    logistics_kpis = results["logistics_kpis"]
    capacity_risk = results["capacity_risk"]
    digestate_outputs = results["digestate_outputs"]
    mol_insights = results.get("mol_insights")

    leap_story = plain_language_leap_summary(preset, metrics, mol_insights)

    (tab1, tab2, tab3, tab4,
     tab_waste, tab_capacity, tab_digestate,
     tab_water, tab_portfolio, tab_engage,
     tab5, tab_tnfd, tab_npi, tab_mol, tab6, tab7, tab8, tab_prov) = st.tabs([
        "LEAP · Locate",
        "LEAP · Evaluate",
        "LEAP · Assess",
        "LEAP · Prepare",
        "Waste sourcing",
        "Capacity risk",
        "Digestate demand",
        "Water balance",
        "Portfolio & sites",
        "Stakeholders",
        "Risk flags",
        "TNFD core metrics",
        "Nature Positive (NPI)",
        "Nature & species",
        "Maps",
        "Trends",
        "Data",
        "How this is calculated",
    ])

    # ========================= LEAP · Locate =========================
    with tab1:
        st.markdown("## LEAP · Locate")
        st.write(
            "The BL Turner AD plant sits on a 1.5-ha private site (Portion 159 of New Guelderland, "
            "KwaDukuza) close to a landfill, diverting organic waste into fertiliser and biogas. "
            "This screen combines the site itself with the wider supply landscape across eThekwini, "
            "iLembe, uMgungundlovu and Western KZN."
        )
        st.caption(results["metrics"].get("analysis_context_method", ""))

        display_metric_cards([
            {"label": "Selected area", "value": fmt_num(metrics.get("area_ha"), 2, " ha"),
             "subtext": "Exact polygon used for screening", "raw": metrics.get("area_ha")},
            {"label": "Tree cover (context)", "value": fmt_num(metrics.get("tree_cover_context_pct", metrics.get("tree_pct")), 1, "%"),
             "subtext": "Wider landscape context", "raw": metrics.get("tree_cover_context_pct", metrics.get("tree_pct"))},
            {"label": "Surface water context", "value": fmt_num(metrics.get("water_context_signal_pct", metrics.get("water_occ")), 1),
             "subtext": "Wider landscape context", "raw": metrics.get("water_context_signal_pct", metrics.get("water_occ"))},
            {"label": "Built-up", "value": fmt_num(metrics.get("built_pct"), 1, "%"),
             "subtext": "Share of the selected area", "raw": metrics.get("built_pct")},
            {"label": "Cropland", "value": fmt_num(metrics.get("cropland_pct"), 1, "%"),
             "subtext": "Share of the selected area", "raw": metrics.get("cropland_pct")},
            {"label": "Flood hazard", "value": fmt_num(metrics.get("flood_risk"), 2, " m"),
             "subtext": "Mapped 1-in-100-year flood depth", "raw": metrics.get("flood_risk")},
        ], per_row=3)

        st.markdown("### LEAP · Locate narrative")
        for line in leap_story["Locate"]:
            st.write(f"- {line}")

        if not lc_df.empty:
            st.markdown("### Current land-cover composition")
            st.plotly_chart(build_landcover_bar(lc_df), width='stretch', key="locate_lc_bar")

        render_feedback_widget({"tab": "locate", "preset": preset})

    # ========================= Waste sourcing (BL Turner differentiator) =========================
    with tab_waste:
        st.markdown("## Waste sourcing intelligence")
        st.write(
            "This view addresses the four questions BL Turner asked directly: **where the waste "
            "comes from**, **how often**, **how much**, and **how continuity is maintained** "
            "through seasonal variability. Source volumes below are screening estimates — "
            "replace them with contracted tonnages as they are confirmed."
        )

        # Supply headroom summary
        st.markdown("### Supply vs nameplate capacity")
        display_metric_cards([
    {"label": "Total potential supply",
     "value": fmt_num(headroom.get("total_supply_tpd"), 1, " t/day"),
     "subtext": "Sum of all modelled source nodes",
     "raw": headroom.get("total_supply_tpd")},

    {"label": "Nameplate capacity",
     "value": fmt_num(headroom.get("nameplate_tpd"), 0, " t/day"),
     "subtext": "100 t/day AD plant design",
     "raw": headroom.get("nameplate_tpd")},

    {"label": "Headroom / shortfall",
     "value": fmt_num(headroom.get("headroom_tpd"), 1, " t/day"),
     "subtext": "Positive = headroom, negative = shortfall",
     "raw": headroom.get("headroom_tpd")},

    {"label": "Utilisation",
     "value": fmt_num(headroom.get("utilisation_pct"), 1, "%"),
     "subtext": "Estimated capacity utilisation",
     "raw": headroom.get("utilisation_pct")},

    {"label": "Supply reliability",
     "value": fmt_num(headroom.get("reliability_pct"), 0, "%"),
     "subtext": "Operational continuity index",
     "raw": headroom.get("reliability_pct")},

    {"label": "Avoided methane",
     "value": fmt_num(headroom.get("co2e_tons"), 0, " t CO₂e"),
     "subtext": "Annual landfill diversion benefit",
     "raw": headroom.get("co2e_tons")},
], per_row=3)

        st.markdown("### Logistics summary")
        display_metric_cards([
            {
                "label": "Weighted route distance",
                "value": fmt_num(logistics_kpis.get("weighted_avg_distance_km"), 1, " km"),
                "subtext": "Average source distance weighted by tonnage",
                "raw": logistics_kpis.get("weighted_avg_distance_km"),
            },
            {
                "label": "Weighted transport cost",
                "value": fmt_num(logistics_kpis.get("weighted_avg_cost_per_ton"), 2, " ZAR/t"),
                "subtext": "Estimated route burden per ton",
                "raw": logistics_kpis.get("weighted_avg_cost_per_ton"),
            },
            {
                "label": "Long-haul share",
                "value": fmt_num(logistics_kpis.get("long_haul_share_pct"), 1, "%"),
                "subtext": "Share of supply from long-haul routes",
                "raw": logistics_kpis.get("long_haul_share_pct"),
            },
            {
                "label": "High-risk routes",
                "value": str(logistics_kpis.get("high_risk_route_count", 0)),
                "subtext": "Routes classed as high logistics risk",
                "raw": logistics_kpis.get("high_risk_route_count"),
            },
        ], per_row=4)

        # Waste sources table
        st.markdown("### Waste source nodes")
        st.caption(
            "Each row is a feedstock source currently in scope for BL Turner. Tonnages are "
            "screening estimates only and will be refined as contracts are signed."
        )
        st.dataframe(_safe_dataframe_for_display(waste_df), width='stretch', hide_index=True)

        # Collection frequency table
        st.markdown("### Collection frequency by source")
        freq_df = pd.DataFrame(frequency_table)
        st.dataframe(_safe_dataframe_for_display(freq_df), width='stretch', hide_index=True)

        st.markdown("### Route optimisation view")
        st.caption(
            "This table shows how far each source is from the KwaDukuza plant, "
            "how demanding the route is, and the estimated transport cost per ton. "
            "Use it to decide which streams should be baseload contracts and which "
            "should be seasonal boosters only."
        )
        logistics_df = pd.DataFrame(logistics_rows)
        st.dataframe(
            _safe_dataframe_for_display(logistics_df),
            width='stretch',
            hide_index=True,
        )

        st.markdown("### What the logistics results mean")
        st.write(
            f"The weighted average source distance is about "
            f"{fmt_num(logistics_kpis.get('weighted_avg_distance_km'), 1, ' km')}, "
            f"and the weighted transport burden is about "
            f"{fmt_num(logistics_kpis.get('weighted_avg_cost_per_ton'), 2, ' ZAR/t')}. "
            f"About {fmt_num(logistics_kpis.get('long_haul_share_pct'), 1, '%')} of the "
            f"current feedstock mix comes from long-haul routes. This means route cost "
            f"and transport reliability are now becoming core operating issues, not just "
            f"background logistics."
        )
        st.write(
            "In practical terms, BL Turner should use nearby iLembe and KwaDukuza "
            "streams as the most stable base-load supply where possible, while more "
            "distant eThekwini and western KZN streams should be managed carefully "
            "so they strengthen supply without making the plant too dependent on costly "
            "or fragile routes."
        )

        # Stream mix and district mix
        mix_col1, mix_col2 = st.columns(2)
        with mix_col1:
            st.markdown("### Mix by waste stream")
            fig_stream = stream_mix_to_plotly_pie()
            if fig_stream:
                st.plotly_chart(fig_stream, width='stretch', key="waste_stream_pie")
        with mix_col2:
            st.markdown("### Mix by district")
            fig_district = district_mix_to_plotly_pie()
            if fig_district:
                st.plotly_chart(fig_district, width='stretch', key="waste_district_pie")

        # Seasonal profile
        st.markdown("### Seasonal supply profile")
        st.caption(
            "Projected monthly supply based on seasonal multipliers across each source "
            "(e.g. summer tourism peak in Ballito/Umhlali, harvest peaks in Western KZN agri)."
        )
        fig_seasonal = seasonal_profile_to_plotly_bar()
        if fig_seasonal:
            st.plotly_chart(fig_seasonal, width='stretch', key="waste_seasonal_bar")

        # Continuity risks
        st.markdown("### Continuity-of-supply risks")
        st.caption(
            "These are the risks most likely to interrupt or compress the 100 t/day supply, "
            "with the proposed mitigation for each."
        )
        cr_df = pd.DataFrame(continuity_risks)
        if not cr_df.empty:
            cr_df_display = cr_df.rename(columns={
                "level": "Level",
                "risk": "Risk",
                "indicator": "Indicator",
                "meaning": "What it means",
                "mitigation": "Mitigation",
            })
            available_cols = [c for c in ["Level", "Risk", "Indicator", "What it means", "Mitigation"]
                              if c in cr_df_display.columns]
            st.dataframe(_safe_dataframe_for_display(cr_df_display[available_cols]),
                         width='stretch', hide_index=True)

        render_feedback_widget({"tab": "waste_sourcing", "preset": preset})


    # ========================= Capacity risk =========================
    with tab_capacity:
        st.markdown("## Capacity risk dashboard")
        st.write(
            "This dashboard pulls together supply, seasonality, continuity, and logistics into one "
            "plain-language operating view. It is not a single TNFD risk score. It is a decision view "
            "for whether BL Turner can realistically keep the plant loaded at or near the 100 t/day target."
        )

        display_metric_cards([
            {
                "label": "Operating posture",
                "value": str(capacity_risk.get("operating_posture", "Watch")),
                "subtext": "Overall practical operating reading",
                "raw": capacity_risk.get("operating_posture"),
            },
            {
                "label": "Capacity buffer",
                "value": fmt_num(capacity_risk.get("capacity_buffer_pct"), 1, "%"),
                "subtext": "Headroom relative to nameplate",
                "raw": capacity_risk.get("capacity_buffer_pct"),
            },
            {
                "label": "Continuity pressure",
                "value": str(capacity_risk.get("continuity_pressure_band", "Watch")),
                "subtext": "Based on continuity risk count",
                "raw": capacity_risk.get("continuity_pressure_band"),
            },
            {
                "label": "Logistics pressure",
                "value": str(capacity_risk.get("logistics_pressure_band", "Watch")),
                "subtext": "Based on route distance and long-haul share",
                "raw": capacity_risk.get("logistics_pressure_band"),
            },
        ], per_row=4)

        risk_rows_df = pd.DataFrame(capacity_risk.get("risk_rows", []))
        if not risk_rows_df.empty:
            st.markdown("### Capacity-risk detail")
            st.dataframe(_safe_dataframe_for_display(risk_rows_df), width='stretch', hide_index=True)

        st.markdown("### What this means")
        for line in capacity_risk.get("narrative", []):
            st.write(f"- {line}")

        st.markdown("### Priority actions")
        for line in capacity_risk.get("priority_actions", []):
            st.write(f"- {line}")

    # ========================= Digestate demand =========================
    with tab_digestate:
        st.markdown("## Digestate demand and offtake view")
        st.write(
            "This view completes the circular model: waste comes in, the plant produces biogas and digestate, "
            "and the digestate needs a realistic market. These figures are screening estimates built from the "
            "existing BL Turner assumptions, so they are appropriate for pilot planning and stakeholder engagement."
        )

        digestate_kpis = digestate_outputs.get("kpis", {})
        display_metric_cards([
            {
                "label": "Indicative digestate output",
                "value": fmt_num(digestate_kpis.get("annual_digestate_tons"), 0, " t/year"),
                "subtext": "Estimated from total feedstock throughput",
                "raw": digestate_kpis.get("annual_digestate_tons"),
            },
            {
                "label": "Mapped demand capacity",
                "value": fmt_num(digestate_kpis.get("annual_demand_capacity_tons"), 0, " t/year"),
                "subtext": "Across current offtake zones",
                "raw": digestate_kpis.get("annual_demand_capacity_tons"),
            },
            {
                "label": "Demand coverage ratio",
                "value": fmt_num(digestate_kpis.get("demand_coverage_ratio_pct"), 1, "%"),
                "subtext": "How much of output could be absorbed",
                "raw": digestate_kpis.get("demand_coverage_ratio_pct"),
            },
            {
                "label": "Market posture",
                "value": str(digestate_kpis.get("market_posture", "Watch")),
                "subtext": "Plain-language market reading",
                "raw": digestate_kpis.get("market_posture"),
            },
        ], per_row=4)

        digestate_df = pd.DataFrame(digestate_outputs.get("rows", []))
        if not digestate_df.empty:
            st.markdown("### Offtake areas")
            st.dataframe(_safe_dataframe_for_display(digestate_df), width='stretch', hide_index=True)

            fig_digestate = px.bar(
                digestate_df,
                x="Offtake area",
                y="Annual demand capacity (t/year)",
                color="Priority",
                title="Indicative digestate demand by offtake area",
            )
            fig_digestate.update_layout(
                xaxis_title="Offtake area",
                yaxis_title="Annual demand capacity (t/year)",
                margin=dict(l=20, r=20, t=60, b=80),
            )
            st.plotly_chart(fig_digestate, width='stretch', key="digestate_demand_bar")

        st.markdown("### What this means")
        for line in digestate_outputs.get("narrative", []):
            st.write(f"- {line}")

        st.markdown("### Recommended next moves")
        for line in digestate_outputs.get("actions", []):
            st.write(f"- {line}")

    # ========================= Water balance =========================
    with tab_water:
        st.markdown("## Process water balance")
        st.write(
            "This view translates the plant's 100 t/day throughput and the "
            "satellite rainfall and evapotranspiration signals into a screening "
            "process-water balance. It is intended for early planning conversations "
            "with the municipality and the water engineer — not for billing."
        )
        wb = compute_water_balance(metrics)

        display_metric_cards([
            {"label": "Gross water demand",
             "value": fmt_num(wb["kpis"]["gross_demand_m3_day"], 1, " m³/day"),
             "subtext": "Before digestate recycling and rainwater harvesting",
             "raw": wb["kpis"]["gross_demand_m3_day"]},
            {"label": "Net municipal demand",
             "value": fmt_num(wb["kpis"]["municipal_m3_day"], 1, " m³/day"),
             "subtext": "After recycling and rainwater offset",
             "raw": wb["kpis"]["municipal_m3_day"]},
            {"label": "Annual municipal water cost",
             "value": f"R {wb['kpis']['annual_municipal_cost_zar']:,.0f}",
             "subtext": "Indicative, at assumed KwaDukuza tariff",
             "raw": wb["kpis"]["annual_municipal_cost_zar"]},
            {"label": "Dry-year emergency cost",
             "value": f"R {wb['kpis']['dry_year_emergency_cost_zar']:,.0f}",
             "subtext": "If rainfall −30% and trucked-in water is needed",
             "raw": wb["kpis"]["dry_year_emergency_cost_zar"]},
        ], per_row=4)

        st.markdown("### Water balance line items")
        st.dataframe(
            _safe_dataframe_for_display(pd.DataFrame(wb["rows"])),
            width='stretch', hide_index=True,
        )

        st.markdown("### What this means")
        for line in wb["narrative"]:
            st.write(f"- {line}")

        st.caption(wb["assumptions_note"])

    # ========================= Portfolio & multi-site =========================
    with tab_portfolio:
        st.markdown("## BL Turner portfolio view")
        st.write(
            "BL Turner operates across more than just the AD plant. This view "
            "keeps the organic-waste, water-reseller and hydroponics lines "
            "side by side so the platform reflects the full business."
        )

        lines = solution_lines()
        site = site_by_name(preset)
        solution_key = site.solution_line if site else "organic_waste"
        playbook = solution_playbook(solution_key)

        st.markdown(f"### Current view: **{playbook['headline']}**")
        st.markdown("**What matters most for this solution type:**")
        for item in playbook["watch_for"]:
            st.write(f"- {item}")
        st.markdown(f"_Positive story:_ {playbook['positive_story']}")

        st.markdown("### All BL Turner sites")
        portfolio_rows = []
        for s in BL_TURNER_SITES:
            portfolio_rows.append({
                "Site": s.name,
                "Solution line": s.solution_line.replace("_", " ").title(),
                "Status": s.status.replace("_", " ").title(),
                "Summary": s.summary,
                "Key dependencies": "; ".join(s.key_dependencies),
                "Key stakeholders": "; ".join(s.stakeholders),
                "Data sharing note": s.data_sharing_note or "",
            })
        st.dataframe(
            _safe_dataframe_for_display(pd.DataFrame(portfolio_rows)),
            width='stretch', hide_index=True,
        )

    # ========================= Stakeholders & behaviour change =========================
    with tab_engage:
        st.markdown("## Stakeholder engagement and behaviour change")
        st.write(
            "BL Turner's business depends on changing behaviour at the source: "
            "getting municipalities, restaurants, DCs, abattoirs and farmers to "
            "separate, package and deliver material differently. This view makes "
            "those asks, and their value exchange, explicit."
        )

        st.markdown("### Behaviour-change plays by source type")
        st.dataframe(
            _safe_dataframe_for_display(pd.DataFrame(engagement_tracker_rows())),
            width='stretch', hide_index=True,
        )

        st.markdown("### Data sharing agreement checklist")
        for item in data_sharing_agreement_checklist():
            st.write(f"- {item}")

    # ========================= LEAP · Evaluate =========================
    with tab2:
        st.markdown("## LEAP · Evaluate")
        for line in leap_story["Evaluate"]:
            st.write(f"- {line}")

        st.markdown("### Environmental conditions at the plant")
        display_metric_cards([
            {"label": "Rainfall anomaly",
             "value": fmt_num(metrics.get("rain_anom_pct"), 1, "%"),
             "subtext": "vs 1981–2010", "raw": metrics.get("rain_anom_pct")},
            {"label": "Heat context (LST)",
             "value": fmt_num(metrics.get("lst_mean"), 1, " °C"),
             "subtext": "Recent mean surface temperature",
             "raw": metrics.get("lst_mean")},
            {"label": "Current NDVI",
             "value": fmt_num(metrics.get("ndvi_current"), 3),
             "subtext": "Vegetation condition around plant",
             "raw": metrics.get("ndvi_current")},
            {"label": "Soil moisture",
             "value": fmt_num(metrics.get("soil_moisture"), 3),
             "subtext": "SMAP surface soil moisture",
             "raw": metrics.get("soil_moisture")},
            {"label": "Evapotranspiration",
             "value": fmt_num(metrics.get("evapotranspiration"), 1),
             "subtext": "Water loss context",
             "raw": metrics.get("evapotranspiration")},
            {"label": "Flood hazard",
             "value": fmt_num(metrics.get("flood_risk"), 2, " m"),
             "subtext": "Mapped 1-in-100-year flood depth",
             "raw": metrics.get("flood_risk")},
        ], per_row=3)

        st.markdown("### TNFD Dependencies (what the AD plant relies on)")
        dependencies = risk.get("dependencies", [])
        if dependencies:
            for dep in dependencies:
                with st.container():
                    st.markdown(f"**{dep.get('service', 'Dependency')}**")
                    st.write(dep.get("why_it_matters", ""))
        else:
            st.info("No dependency breakdown was returned by the scoring module.")

        render_feedback_widget({"tab": "evaluate", "preset": preset})

    # ========================= LEAP · Assess =========================
    with tab3:
        st.markdown("## LEAP · Assess")
        for line in leap_story["Assess"]:
            st.write(f"- {line}")

        st.markdown("### Portfolio of indicators")
        st.caption(
            "TNFD recommends reporting individual indicators rather than aggregating into one "
            "number. Each indicator below has its own status, meaning and suggested response."
        )
        portfolio = risk.get("portfolio") or []
        portfolio_summary = risk.get("portfolio_summary") or {}

        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("Favourable", portfolio_summary.get("Favourable", 0))
        sc2.metric("Watch", portfolio_summary.get("Watch", 0))
        sc3.metric("Warning", portfolio_summary.get("Warning", 0))
        sc4.metric("Not available", portfolio_summary.get("Not available", 0))

        port_df = pd.DataFrame(portfolio)
        if not port_df.empty:
            port_df = port_df.rename(columns={
                "name": "Indicator",
                "status": "Status",
                "plain_meaning": "What this means",
                "response": "Suggested response",
            })
            available_cols = [c for c in ["Indicator", "Status", "What this means", "Suggested response"]
                              if c in port_df.columns]
            st.dataframe(_safe_dataframe_for_display(port_df[available_cols]),
                         width='stretch', hide_index=True)

        st.markdown("### Indicative monetary exposures (units of currency)")
        st.caption(
            "These cards translate nature conditions into rough business-cost signals. They "
            "are screening figures, not quotes. The landfill-diversion card highlights a "
            "positive environmental outcome BL Turner can claim alongside risks."
        )
        monetary = risk.get("monetary_exposures", [])
        if monetary:
            for item in monetary:
                with st.container():
                    st.markdown(f"**{item.get('label', 'Exposure')}**")
                    st.write(item.get("headline", ""))
                    st.caption(item.get("assumption", ""))
        else:
            st.info("No monetary exposure cards are available for this run.")

        render_feedback_widget({"tab": "assess", "preset": preset})

    # ========================= LEAP · Prepare =========================
    with tab4:
        st.markdown("## LEAP · Prepare")
        for line in leap_story["Prepare"]:
            st.write(f"- {line}")
        st.markdown("### Recommended next actions")
        for rec in risk.get("recs", []):
            st.write(f"- {rec}")

        st.markdown("### Suggested review cadence")
        st.write(
            "- **Monthly**: feedstock tonnage actuals vs projections; update seasonal mix.\n"
            "- **Quarterly**: environmental screening refresh (NDVI, heat, water); review continuity risks.\n"
            "- **Annually**: full TNFD disclosure refresh; update avoided-methane calculation; funder and municipal reporting.\n"
            "- **After major weather events**: flood, drought or heatwave triggers an ad-hoc review.\n"
            "- **Before any capacity expansion or new contract**: rerun this assessment on the new footprint."
        )

        st.markdown("### How BL Turner can monetise this")
        st.write(
            "- Diverted tonnage and avoided methane can anchor a voluntary carbon narrative for local off-take buyers.\n"
            "- Feedstock continuity evidence supports municipal procurement conversations in eThekwini, iLembe and uMgungundlovu.\n"
            "- Digestate quality and off-take area mapping support fertiliser contracts with KZN sugarcane and mixed-cropping farms.\n"
            "- The dashboard itself is a funder-ready exhibit for DBSA / IDC / commercial lenders assessing nature-related risk."
        )

        render_feedback_widget({"tab": "prepare", "preset": preset})

    # ========================= Risk flags =========================
    with tab5:
        st.markdown("## Automated risk flags")
        st.caption(
            "These flags combine environmental signals at the plant with feedstock continuity "
            "risks derived from the waste-sourcing analysis."
        )
        flags_df = risk_flags_to_dataframe(automated_flags)
        st.dataframe(_safe_dataframe_for_display(flags_df), width='stretch', hide_index=True)

    # ========================= TNFD core metrics =========================
    with tab_tnfd:
        st.markdown("## TNFD core metrics")
        st.caption(
            "This table maps every result the platform produces to the TNFD core metrics. "
            "Where a metric is a placeholder or needs data directly from BL Turner, it is "
            "labelled honestly rather than silently skipped (TNFD comply-or-explain approach)."
        )
        tnfd_rows = build_tnfd_core_metrics_rows(metrics, mol_insights)
        tnfd_df = pd.DataFrame(tnfd_rows).rename(columns={
            "metric_id": "Metric",
            "metric_name": "Indicator",
            "what_it_means": "What it means",
            "what_we_report": "What we report here",
            "status": "Status",
        })
        available_cols = [c for c in ["Metric", "Indicator", "What it means", "What we report here", "Status"]
                          if c in tnfd_df.columns]
        st.dataframe(_safe_dataframe_for_display(tnfd_df[available_cols]),
                     width='stretch', hide_index=True)

    # ========================= NPI =========================
    with tab_npi:
        st.markdown("## Nature Positive Initiative — State of Nature indicators")
        st.caption(
            "The four indicators the Nature Positive Initiative recommends for measuring the "
            "state of nature around a business: ecosystem extent, condition, intactness and "
            "species extinction risk."
        )
        npi_rows = build_npi_state_of_nature_rows(metrics, mol_insights)
        npi_df = pd.DataFrame(npi_rows).rename(columns={
            "indicator": "Indicator",
            "what_it_means": "What it means",
            "what_we_report": "What we report here",
            "maturity": "Maturity",
        })
        available_cols = [c for c in ["Indicator", "What it means", "What we report here", "Maturity"]
                          if c in npi_df.columns]
        st.dataframe(_safe_dataframe_for_display(npi_df[available_cols]),
                     width='stretch', hide_index=True)


    # ========================= Nature & species (Map of Life) =========================
    with tab_mol:
        st.markdown("## Nature & species")
        if mol_insights:
            st.write(
                f"Map of Life adds species and habitat context for **{mol_insights['site_name']}**. "
                "This helps BL Turner read the plant site, source corridors, or receiving landscapes not only "
                "through land, water and climate signals, but also through species sensitivity and habitat quality."
            )
            st.caption(
                "Expected species are modelled possibilities for the area around the site, not a field survey count. "
                "Habitat scores are trend signals: higher values generally mean habitat is more suitable, while "
                "changes over time show whether conditions appear to be strengthening or weakening."
            )

            display_metric_cards([dict(card, raw=card.get("value")) for card in mol_insights["cards"]], per_row=4)

            st.markdown("### What this means for BL Turner")
            for note in mol_insights["advisory_notes"]:
                st.write(f"• {note}")

            st.markdown("### Operational priorities")
            for note in mol_insights["service_notes"]:
                st.write(f"• {note}")

            st.markdown("### Species groups represented")
            group_cards = []
            for group_name, key_prefix in [("Birds", "birds"), ("Mammals", "mammals"), ("Reptiles", "reptiles")]:
                count = int(mol_insights["group_counts"].get(group_name, 0))
                shi_val = mol_insights.get(f"{key_prefix}_shi")
                change_val = mol_insights.get(f"{key_prefix}_change")
                group_cards.append({
                    "label": group_name,
                    "value": str(count),
                    "subtext": f"Latest habitat score {fmt_num(shi_val, 1)} · change since 2001 {fmt_num(change_val, 2)}",
                    "raw": count,
                })
            display_metric_cards(group_cards, per_row=3)

            st.markdown("### Threat profile")
            st.caption(
                "These categories show how close species are to disappearing. For BL Turner, they help show where "
                "day-to-day siting, runoff, buffer and digestate-use decisions deserve extra care."
            )
            threat_cards = []
            for item in mol_insights["threat_profile_details"]:
                threat_cards.append({
                    "label": f"{item['code']} · {item['name']}",
                    "value": str(int(item["count"])),
                    "subtext": f"{item['plain'].capitalize()}. {item['count']} expected species in this group.",
                    "raw": item["count"],
                })
            display_metric_cards(threat_cards, per_row=2)

            st.markdown("### What each threat level means for BL Turner")
            for item in mol_insights["threat_profile_details"]:
                st.write(
                    f"• **{item['code']}: {item['name']}**: {item['count']} expected species. "
                    f"This means the species {item['plain']}. {item['business']}"
                )

            st.markdown("### Priority species expected in this zone")
            render_species_badges(st, mol_insights["top_species"])

            mol_long_df = make_mol_shi_long_df(mol_insights)
            if not mol_long_df.empty:
                fig = px.line(
                    mol_long_df,
                    x="year",
                    y="SHI",
                    color="Series",
                    title="Map of Life Species Habitat Index trend",
                    labels={"year": "Year", "SHI": "Species Habitat Index"},
                )
                st.plotly_chart(fig, width='stretch', key="trend_mol_shi")

            st.markdown("### TNFD LEAP view")
            for point in mol_insights["tnfd_points"]:
                st.write(f"• {point}")
            if mol_insights.get("dictionary_note"):
                st.caption(mol_insights["dictionary_note"])
        else:
            st.info("Map of Life species and habitat data is not available for this site selection.")

    # ========================= Maps =========================
    with tab6:
        st.markdown("## Map views")
        st.write("**NDVI image:** greener = stronger vegetation; redder = weaker vegetation.")
        st.write("**Vegetation change map:** green = improvement; red = decline.")
        st.write("**Land-cover image:** classes include tree cover, cropland, built-up land, water.")
        st.write("**Forest loss map:** highlights detected forest loss.")

        img1, img2 = st.columns(2)
        with img1:
            if satellite_url:
                st.image(satellite_url, caption="Satellite image with polygon", width='stretch')
            if ndvi_url:
                st.image(ndvi_url, caption="NDVI image with polygon", width='stretch')
            if veg_change_url:
                st.image(veg_change_url, caption="Vegetation change map with polygon", width='stretch')
            if flood_risk_url:
                st.image(flood_risk_url, caption=f"Flood risk map: {fmt_num(metrics.get('flood_risk'), 2, ' m')}", width='stretch')
        with img2:
            if landcover_url:
                st.image(landcover_url, caption="Land-cover image with polygon", width='stretch')
            if forest_loss_url:
                st.image(forest_loss_url, caption="Forest loss map with polygon", width='stretch')
            if soil_condition_url:
                st.image(soil_condition_url,
                         caption=f"Soil condition: SOC {fmt_num(metrics.get('soil_organic_carbon'), 1)}, texture class {metrics.get('soil_texture_class')}",
                         width='stretch')
            if heat_stress_url:
                st.image(heat_stress_url,
                         caption=f"Heat stress: {fmt_num(metrics.get('lst_mean'), 1, ' °C')}",
                         width='stretch')

    # ========================= Trends =========================
    with tab7:
        st.markdown("## Historical trends")
        if not ndvi_hist_df.empty:
            st.caption("Year-by-year greenness of the site — a rising line means vegetation is generally improving.")
            fig = px.line(ndvi_hist_df, x="year", y="value", title="Historical NDVI (Landsat)")
            st.plotly_chart(fig, width='stretch', key="trend_ndvi")
        if not rain_hist_df.empty:
            st.caption("Annual rainfall totals for the area — shows wet and dry years that shape water availability.")
            fig = px.line(rain_hist_df, x="year", y="value", title="Historical Rainfall (CHIRPS)")
            st.plotly_chart(fig, width='stretch', key="trend_rain")
        if not lst_hist_df.empty:
            st.caption("Average land-surface temperature over time — rising values point to a warmer operating environment.")
            fig = px.line(lst_hist_df, x="year", y="value", title="Historical Land Surface Temperature (MODIS)")
            st.plotly_chart(fig, width='stretch', key="trend_lst")
        if not forest_hist_df.empty:
            st.caption("Tree cover lost in the landscape each year — tall bars flag years of heavier clearing nearby.")
            fig = px.bar(forest_hist_df, x="year", y="value", title="Historical Forest Loss by Year (Hansen)")
            st.plotly_chart(fig, width='stretch', key="trend_forest")
        if not water_hist_df.empty:
            st.caption("Share of the area showing surface water each year — helps see wet/dry cycles and seasonal water presence.")
            fig = px.line(water_hist_df, x="year", y="value", title="Historical Water Presence (JRC)")
            st.plotly_chart(fig, width='stretch', key="trend_water")

    # ========================= Data =========================
    with tab8:
        st.markdown("## Supporting data")
        detail_rows = [
            ("Business preset", preset),
            ("Business category", category),
            ("Assessment period", f"{hist_start} to {hist_end}"),
            ("Area (ha)", metrics.get("area_ha")),
            ("Current NDVI", metrics.get("ndvi_current")),
            ("Tree cover context (%)", metrics.get("tree_cover_context_pct") or metrics.get("tree_pct")),
            ("Cropland (%)", metrics.get("cropland_pct")),
            ("Built-up (%)", metrics.get("built_pct")),
            ("Surface water context", metrics.get("water_context_signal_pct") or metrics.get("water_occ")),
            ("Recent LST mean (°C)", metrics.get("lst_mean")),
            ("Rainfall anomaly (%)", metrics.get("rain_anom_pct")),
            ("Soil moisture", metrics.get("soil_moisture")),
            ("Evapotranspiration", metrics.get("evapotranspiration")),
            ("Soil organic carbon", metrics.get("soil_organic_carbon")),
            ("Soil texture class", metrics.get("soil_texture_class")),
            ("Flood risk (m)", metrics.get("flood_risk")),
            ("Fire risk", metrics.get("fire_risk")),
            ("Total feedstock supply (t/day)", headroom.get("total_supply_tpd")),
            ("Nameplate capacity (t/day)", headroom.get("nameplate_tpd")),
            ("Headroom / shortfall (t/day)", headroom.get("headroom_tpd")),
            ("Utilisation (%)", headroom.get("utilisation_pct")),
        ]
        detail_df = pd.DataFrame(detail_rows, columns=["Metric", "Value"])
        detail_df = detail_df[detail_df["Value"].apply(has_data)].copy()
        detail_df["Value"] = detail_df["Value"].apply(str)
        st.dataframe(_safe_dataframe_for_display(detail_df), width='stretch', hide_index=True)

        if not lc_df.empty:
            fig = build_landcover_bar(lc_df)
            st.plotly_chart(fig, width='stretch', key="detail_landcover_bar")

    # ========================= How this is calculated =========================
    with tab_prov:
        st.markdown("## How this is calculated")
        st.write(
            "Every indicator below names its dataset, native resolution, "
            "timeframe, and whether it is a direct measurement, a proxy, or a "
            "screening estimate. This is how the platform addresses TNFD's "
            "transparency expectation (Recommended Disclosure B3) and the "
            "Grand Challenge rubric's transparency criterion."
        )
        st.dataframe(
            _safe_dataframe_for_display(pd.DataFrame(provenance_table())),
            width='stretch', hide_index=True,
        )

        st.markdown("### Scope boundaries")
        scope = scope_boundary_statement()

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**In scope**")
            for item in scope["in_scope"]:
                st.write(f"- {item}")
        with c2:
            st.markdown("**Out of scope**")
            for item in scope["out_of_scope"]:
                st.write(f"- {item}")

        st.markdown("### Who should verify before a formal decision")
        for item in scope["who_should_verify"]:
            st.write(f"- {item}")
