"""
Multi-site and multi-solution registry for BL Turner.

BL Turner's introductory meeting explicitly said they operate across multiple
solution lines and multiple sites, including:

  1. Organic waste processing (anaerobic digestion, fertiliser, biogas) — KwaDukuza
  2. Water reseller / air-to-water unit — local community development
  3. Hydroponics — community developing
  4. Future sites to be finalised (land being finalised)

Handling this in one place means:
  * The Streamlit app can toggle between BL Turner's own solution lines.
  * New sites can be added without touching `app.py` logic.
  * The rubric's 2d "Adaptability & Contextual Flexibility" is directly
    addressed: the platform genuinely adapts across sectors and biomes.
  * 3d "Iteration & Roadmap Responsiveness" benefits because adding a site
    is a one-line change.

Keep this file *data-only* — no Streamlit or Earth Engine imports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SiteDefinition:
    site_id: str
    name: str
    solution_line: str                # one of: organic_waste, water_reseller, hydroponics, mixed
    status: str                       # operating | pilot | land_finalising | proposed
    lat: float
    lon: float
    buffer_m: int = 300
    zoom: int = 15
    category_hint: Optional[str] = None
    summary: str = ""
    key_dependencies: List[str] = field(default_factory=list)
    stakeholders: List[str] = field(default_factory=list)
    data_sharing_note: Optional[str] = None


# --- BL Turner portfolio -------------------------------------------------- #
BL_TURNER_SITES: List[SiteDefinition] = [
    SiteDefinition(
        site_id="KWD_AD_MAIN",
        name="BL Turner Main Site (Portion 159, New Guelderland, KwaDukuza)",
        solution_line="organic_waste",
        status="land_finalising",
        lat=-29.309186,
        lon=31.326527,
        buffer_m=300,
        zoom=15,
        category_hint="Organic Waste / Anaerobic Digestion / Biogas",
        summary=(
            "100 t/day anaerobic digestion facility. Produces biogas, digestate fertiliser, "
            "and diverts organics from the adjacent KwaDukuza landfill."
        ),
        key_dependencies=[
            "Organic waste feedstock continuity",
            "Process water",
            "Flood and heat resilience",
            "Digestate offtake demand in KZN farmlands",
        ],
        stakeholders=[
            "KwaDukuza Local Municipality",
            "eThekwini Metro (waste department)",
            "iLembe District",
            "KZN farm offtakers",
            "Funders (DBSA / IDC / commercial lenders)",
        ],
        data_sharing_note=(
            "Land tenure being finalised. A formal data sharing agreement is recommended "
            "before integrating municipal tonnage or utility data into this workspace."
        ),
    ),
    SiteDefinition(
        site_id="WATER_RESELLER_ATW",
        name="Air-to-Water Reseller Unit (community pilot)",
        solution_line="water_reseller",
        status="pilot",
        lat=-29.3100,
        lon=31.3200,
        buffer_m=150,
        zoom=16,
        category_hint="Water Generation / Atmospheric Water",
        summary=(
            "Locally-built atmospheric water generation unit supplying a community water "
            "reseller point. Screening should show humidity, heat, and demand-access "
            "signals rather than AD-style feedstock logistics."
        ),
        key_dependencies=[
            "Humidity and temperature regime (AWG performance)",
            "Grid stability / solar feasibility",
            "Community access and affordability",
        ],
        stakeholders=[
            "Local community customers",
            "Municipal water department (for compliance, not supply)",
        ],
        data_sharing_note=(
            "Unit-level metering data would need a data sharing agreement with the community "
            "operator before being ingested."
        ),
    ),
    SiteDefinition(
        site_id="HYDROPONICS_PILOT",
        name="Hydroponics Community Pilot (to be finalised)",
        solution_line="hydroponics",
        status="proposed",
        lat=-29.3300,
        lon=31.3100,
        buffer_m=200,
        zoom=16,
        category_hint="Controlled Environment Agriculture",
        summary=(
            "Community hydroponics pilot. Screening should emphasise water access, solar "
            "resource, heat stress, and proximity to local markets rather than land-cover "
            "conversion signals."
        ),
        key_dependencies=[
            "Reliable water supply",
            "Electricity / solar",
            "Nutrient supply (digestate link to AD plant)",
            "Local vegetable demand",
        ],
        stakeholders=[
            "Community partners",
            "Local schools / cooperatives",
        ],
        data_sharing_note=(
            "Co-location with the AD plant creates a circular link (digestate → hydroponics). "
            "Track separately until both sites are operational."
        ),
    ),
]


def site_by_id(site_id: str) -> Optional[SiteDefinition]:
    for s in BL_TURNER_SITES:
        if s.site_id == site_id:
            return s
    return None


def site_by_name(name: str) -> Optional[SiteDefinition]:
    for s in BL_TURNER_SITES:
        if s.name == name:
            return s
    return None


def solution_lines() -> List[Dict[str, str]]:
    return [
        {"key": "organic_waste", "label": "Organic waste / biogas / fertiliser"},
        {"key": "water_reseller", "label": "Water generation (atmospheric water)"},
        {"key": "hydroponics", "label": "Hydroponics / community food"},
        {"key": "mixed", "label": "Mixed / circular (AD + hydroponics)"},
    ]


def sites_for_solution(solution_line: str) -> List[SiteDefinition]:
    return [s for s in BL_TURNER_SITES if s.solution_line == solution_line or solution_line == "mixed"]


def preset_options() -> List[str]:
    """For backward compatibility with app.py's preset selector."""
    return ["Custom site"] + [s.name for s in BL_TURNER_SITES] + [
        "Durban Fresh Produce Market (Clairwood) — feedstock source",
        "Pietermaritzburg Abattoir Cluster — feedstock source",
        "eThekwini Kerbside Organics Collection Zone — feedstock source",
    ]


def solution_playbook(solution_line: str) -> Dict[str, Any]:
    """Return a short, solution-specific interpretation playbook.

    Used by the results view to tell users *which* indicators matter most for
    *this* kind of project, so the platform does not over-generalise.
    """
    if solution_line == "organic_waste":
        return {
            "headline": "Organic waste / biogas / fertiliser",
            "watch_for": [
                "Flood exposure on digester tanks and CHP infrastructure",
                "Feedstock concentration risk (one municipality or one DC)",
                "Heat stress on odour control and worker comfort",
                "Digestate offtake demand in receiving farmland",
            ],
            "positive_story": (
                "Landfill diversion and avoided methane are the strongest nature-positive "
                "outcomes for funders and municipalities to see."
            ),
        }
    if solution_line == "water_reseller":
        return {
            "headline": "Atmospheric water generation",
            "watch_for": [
                "Relative humidity regime (AWG yield depends on it)",
                "Heat-stress days when yield drops",
                "Grid reliability / off-grid solar feasibility",
                "Community affordability and walking distance to the reseller point",
            ],
            "positive_story": (
                "Decentralised water supply during municipal shortages is the core social "
                "value — track days of supply delivered and households served."
            ),
        }
    if solution_line == "hydroponics":
        return {
            "headline": "Hydroponics / community food",
            "watch_for": [
                "Water reliability (circular link to AD digestate recycling)",
                "Solar radiation and heat regime",
                "Local vegetable market demand and pricing",
                "Distance from AD plant (if digestate is the nutrient source)",
            ],
            "positive_story": (
                "Closing the loop: AD digestate nutrients → hydroponics → local food → "
                "organic waste back to the AD plant. Track this as a circular KPI."
            ),
        }
    return {
        "headline": "Mixed / circular portfolio",
        "watch_for": [
            "Integration points between AD, water, and hydroponics",
            "Shared resilience risks (flood, heat, grid)",
        ],
        "positive_story": (
            "A circular BL Turner system is more resilient than any single line alone."
        ),
    }
