"""
Transparent data provenance for every indicator the platform reports.

Rubric 2c explicitly asks:
  * Tool clearly communicates how results are generated
  * Simplifications, assumptions, and proxies are disclosed
  * Scope boundaries (what is and isn't covered) are explicit
  * Users can trace outputs back to data sources and methods

This module gives the Streamlit app a single source of truth for:
  * Which dataset each metric comes from
  * Its native resolution
  * What timeframe it covers
  * Whether it is a direct measurement, proxy, or screening estimate
  * A plain-language caveat

The UI shows this as a "How this was calculated" panel.
"""

from __future__ import annotations

from typing import Dict, List, Optional


DATA_SOURCES: List[Dict[str, str]] = [
    {
        "metric": "NDVI (current and historical)",
        "dataset": "Landsat 5/7/8/9 Surface Reflectance (LANDSAT/*_SR)",
        "resolution": "30 m",
        "timeframe": "1984 — present",
        "nature": "Direct measurement (satellite observation)",
        "caveat": (
            "Single-date NDVI is affected by cloud cover and phenology. Long-term trend is "
            "the more reliable signal than any single year."
        ),
    },
    {
        "metric": "Rainfall anomaly vs 1981–2010 baseline",
        "dataset": "CHIRPS Daily (UCSB-CHG/CHIRPS/DAILY)",
        "resolution": "~5 km",
        "timeframe": "1981 — present",
        "nature": "Direct measurement (satellite + gauge blend)",
        "caveat": (
            "CHIRPS is a blended product of satellite and station data. Coarse spatial "
            "resolution means it represents a landscape average, not the exact plant site."
        ),
    },
    {
        "metric": "Land surface temperature (LST)",
        "dataset": "MODIS MOD11A2 (MODIS/061/MOD11A2)",
        "resolution": "1 km, 8-day",
        "timeframe": "2001 — present",
        "nature": "Direct measurement",
        "caveat": (
            "Surface temperature is not air temperature. It is indicative of heat load on "
            "tanks, roofs and hardstand, but should not be cited as ambient air °C."
        ),
    },
    {
        "metric": "Flood hazard (1-in-100-year depth)",
        "dataset": "JRC Global Flood Hazard (JRC/CEMS_GLOFAS/FloodHazard/v2_1)",
        "resolution": "~90 m",
        "timeframe": "Static hazard layer",
        "nature": "Modelled hazard (not direct observation)",
        "caveat": (
            "Modelled depths. Local drainage, bunds and culverts are not represented — a "
            "local flood-line study is recommended before siting critical infrastructure."
        ),
    },
    {
        "metric": "Land cover composition",
        "dataset": "ESA WorldCover v200 (2021)",
        "resolution": "10 m",
        "timeframe": "2021 snapshot",
        "nature": "Classified map (proxy for ecosystem extent)",
        "caveat": (
            "One-year snapshot. Does not capture 2022–2025 changes. Cross-check with "
            "Dynamic World probabilities for more recent land-cover signal."
        ),
    },
    {
        "metric": "Forest loss",
        "dataset": "Hansen Global Forest Change (UMD/hansen/global_forest_change_2024_v1_12)",
        "resolution": "30 m",
        "timeframe": "2001 — 2024",
        "nature": "Classified map (annual loss)",
        "caveat": (
            "Detects tree-cover loss; does not distinguish clear-cut, fire, or pest-driven "
            "loss. Works best in closed-canopy areas."
        ),
    },
    {
        "metric": "Surface water occurrence / seasonality",
        "dataset": "JRC Global Surface Water (JRC/GSW1_4/*)",
        "resolution": "30 m",
        "timeframe": "1984 — present",
        "nature": "Direct measurement (Landsat-derived)",
        "caveat": (
            "Detects open surface water — not soil moisture or shallow groundwater."
        ),
    },
    {
        "metric": "Soil moisture",
        "dataset": "NASA SMAP L4 (NASA/SMAP/SPL4SMGP/008)",
        "resolution": "~9 km",
        "timeframe": "2015 — present",
        "nature": "Modelled (satellite-assimilated)",
        "caveat": (
            "Coarse resolution. Useful for catchment signal, not field-level agronomy."
        ),
    },
    {
        "metric": "Evapotranspiration",
        "dataset": "MODIS MOD16A2GF (MODIS/061/MOD16A2GF)",
        "resolution": "500 m, 8-day",
        "timeframe": "2000 — present",
        "nature": "Modelled from satellite inputs",
        "caveat": (
            "Useful for regional water-loss signal. Open digester lagoons will lose "
            "materially more water than a forested pixel of the same size."
        ),
    },
    {
        "metric": "Soil organic carbon",
        "dataset": "OpenLandMap SOC (OpenLandMap/SOL/SOL_ORGANIC-CARBON_USDA-6A1C_M/v02)",
        "resolution": "250 m",
        "timeframe": "Static map",
        "nature": "Modelled global map",
        "caveat": (
            "Global-scale model — useful as a baseline indicator for digestate offtake "
            "areas, not as a field sampling result."
        ),
    },
    {
        "metric": "Species Habitat Index (SHI) and species list",
        "dataset": "Map of Life (workbook supplied by MoL)",
        "resolution": "Site / zone polygon",
        "timeframe": "2001 — 2023",
        "nature": "Modelled habitat suitability",
        "caveat": (
            "SHI represents modelled habitat suitability for expected species — it is not "
            "a field survey. Useful as a screening signal for siting and buffers."
        ),
    },
    {
        "metric": "Avoided methane emissions from landfill diversion",
        "dataset": "Screening calculation (no satellite input)",
        "resolution": "Plant-level",
        "timeframe": "Annualised",
        "nature": "Screening estimate",
        "caveat": (
            "Indicative only. A formal carbon methodology (e.g. CDM ACM0022, Verra VM0039, "
            "Gold Standard) is required before any carbon credit claim."
        ),
    },
    {
        "metric": "Transport cost per ton and route risk",
        "dataset": "Haversine distance from OSM coordinates + local ZAR/km assumption",
        "resolution": "Route-level",
        "timeframe": "Current assumption",
        "nature": "Screening estimate",
        "caveat": (
            "Straight-line distance adjusted for typical route burden. Replace with real "
            "routing data (OSRM or a freight broker quote) for contract decisions."
        ),
    },
    {
        "metric": "Process water balance",
        "dataset": "Screening model built on CHIRPS rainfall + MOD16 ET + plant assumptions",
        "resolution": "Plant-level",
        "timeframe": "Daily and annual",
        "nature": "Screening estimate",
        "caveat": (
            "Slurry dilution rate, catchment area, and recycle fraction are defaults. "
            "Replace with BL Turner's engineering values once the design is finalised."
        ),
    },
]


def provenance_table() -> List[Dict[str, str]]:
    """Return the list in a form suitable for Streamlit dataframe display."""
    return [
        {
            "Indicator / output": row["metric"],
            "Dataset": row["dataset"],
            "Native resolution": row["resolution"],
            "Timeframe": row["timeframe"],
            "Nature of value": row["nature"],
            "Key caveat": row["caveat"],
        }
        for row in DATA_SOURCES
    ]


def scope_boundary_statement() -> Dict[str, List[str]]:
    """Explicitly tells the user what is and is not in scope."""
    return {
        "in_scope": [
            "Plant-site environmental screening (vegetation, heat, water, flood, fire)",
            "Feedstock sourcing geography across eThekwini, iLembe, uMgungundlovu and Western KZN",
            "Transport burden and route risk for feedstock",
            "Screening water balance for the AD process",
            "Indicative digestate offtake demand by area",
            "Map of Life species and habitat screening",
            "TNFD core disclosure metric mapping",
            "Nature Positive Initiative State of Nature indicators",
        ],
        "out_of_scope": [
            "Regulatory compliance certification (EIA, water use licence, waste licence)",
            "A formal GHG inventory or verified carbon credit calculation",
            "Financial forecasts, investor-grade CAPEX/OPEX, or detailed engineering design",
            "Real-time plant telemetry or SCADA integration",
            "Biodiversity field survey — species lists are modelled, not observed",
            "Legal advice on contracts, permits, or tenure",
        ],
        "who_should_verify": [
            "A qualified EAP (Environmental Assessment Practitioner) for EIA-grade flood / ecology",
            "A GHG accountant for carbon credits",
            "A water engineer for the formal plant water balance",
            "The relevant municipality for waste tonnage contracts",
        ],
    }
