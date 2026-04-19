"""
Stakeholder engagement and behaviour-change tracker for BL Turner.

In the intro meeting BL Turner explicitly said:
    "Not just processing (What is the impact, change? Restaurants, change
     elements of behaviour)"
    "Frequency of getting waste... To have continuity..."
    "Data sharing agreement"

This module gives the app a structured view of:
  * Each source category (municipalities, restaurants, abattoirs, DCs, farms)
  * What BL Turner is asking them to do differently (separation at source)
  * Where the relationship currently sits (prospect / MoU / contract)
  * Whether a data sharing agreement is in place

It is intentionally lightweight — a CRM-lite — so BL Turner can use the tool
during partner conversations without needing Salesforce or HubSpot.
"""

from __future__ import annotations

from typing import Any, Dict, List


BEHAVIOUR_CHANGE_PLAYS: List[Dict[str, Any]] = [
    {
        "source_type": "Municipal waste department",
        "example_partners": ["eThekwini Metro", "KwaDukuza LM", "Msunduzi LM"],
        "behaviour_ask": (
            "Enable source-separated organics in pilot collection routes and share monthly "
            "tonnage data with BL Turner."
        ),
        "value_to_them": (
            "Landfill airspace saved, reduced leachate cost, and a measurable contribution "
            "to the municipality's climate and circular-economy targets."
        ),
        "relationship_stage": "MoU preferred before contract",
        "data_sharing_needed": True,
        "kpi": "Tonnes per month delivered + contamination rate (%)",
    },
    {
        "source_type": "Restaurants and hospitality outlets",
        "example_partners": ["Ballito hotels", "Umhlanga restaurant clusters", "Durban CBD outlets"],
        "behaviour_ask": (
            "Separate food waste from packaging, keep it in dedicated bins, and make it "
            "available on a predictable schedule."
        ),
        "value_to_them": (
            "Cheaper disposal than general waste, a documented sustainability story for "
            "their own marketing, and a cleaner kitchen back-of-house."
        ),
        "relationship_stage": "Multi-outlet pilot via aggregator",
        "data_sharing_needed": False,
        "kpi": "Collected litres/week per outlet + contamination rate",
    },
    {
        "source_type": "Distribution centres (expired/near-date food)",
        "example_partners": ["Durban DCs (multiple retailers)"],
        "behaviour_ask": (
            "Divert expired food from landfill to BL Turner AD feedstock with a clean "
            "pull-load schedule that fits DC shift patterns."
        ),
        "value_to_them": (
            "Consolidated single-offtaker contract reduces DC admin, disposal cost, and "
            "ESG / nature-disclosure risk in the supermarket's supply chain."
        ),
        "relationship_stage": "Baseload contract target — highest priority",
        "data_sharing_needed": True,
        "kpi": "Tonnes/week + steady-state vs holiday returns",
    },
    {
        "source_type": "Abattoirs (meat, blood, stomach contents)",
        "example_partners": ["Pietermaritzburg abattoir cluster"],
        "behaviour_ask": (
            "Load blood and gut contents into dedicated, cold-chain tankers on a daily "
            "schedule that keeps biosecurity risk low."
        ),
        "value_to_them": (
            "Dependable disposal route, compliant with animal by-product regulations, and "
            "avoids landfill cost and odour complaints."
        ),
        "relationship_stage": "Requires cold-chain infrastructure agreement",
        "data_sharing_needed": True,
        "kpi": "Tonnes/day + temperature compliance logs",
    },
    {
        "source_type": "Farmers and cooperatives (digestate offtake)",
        "example_partners": ["KZN north coast sugarcane farms", "uMgungundlovu vegetable cooperatives"],
        "behaviour_ask": (
            "Substitute part of synthetic fertiliser with BL Turner digestate on suitable "
            "crops, and allow soil-carbon measurement before/after."
        ),
        "value_to_them": (
            "Lower fertiliser cost, improved soil carbon and moisture retention, and "
            "differentiated 'regenerative' story for downstream buyers."
        ),
        "relationship_stage": "Field trial → offtake agreement",
        "data_sharing_needed": True,
        "kpi": "Hectares applied + soil organic carbon change over seasons",
    },
    {
        "source_type": "Farming / agricultural waste providers",
        "example_partners": ["Western KZN mixed-cropping operations"],
        "behaviour_ask": (
            "Bale or otherwise consolidate crop residues and culled produce for BL Turner "
            "collection during harvest windows."
        ),
        "value_to_them": (
            "Revenue or avoided-disposal cost on material that would otherwise be burned "
            "or left to rot."
        ),
        "relationship_stage": "Seasonal booster stream — not baseload",
        "data_sharing_needed": False,
        "kpi": "Tonnes per harvest window",
    },
]


def engagement_tracker_rows() -> List[Dict[str, str]]:
    """Flatten for a Streamlit dataframe."""
    rows = []
    for p in BEHAVIOUR_CHANGE_PLAYS:
        rows.append({
            "Source type": p["source_type"],
            "Example partners": ", ".join(p["example_partners"]),
            "What we're asking them to do": p["behaviour_ask"],
            "Why they should care": p["value_to_them"],
            "Relationship stage": p["relationship_stage"],
            "Data sharing needed": "Yes" if p["data_sharing_needed"] else "No",
            "KPI to track": p["kpi"],
        })
    return rows


def data_sharing_agreement_checklist() -> List[str]:
    """Checklist BL Turner can use when starting conversations with municipalities."""
    return [
        "Confirm which party is the legal data controller for waste tonnage data.",
        "Specify what data is being shared (tonnage, waste type, contamination rate) and at what frequency.",
        "Agree on a retention period and whether aggregate / anonymised sharing with funders is permitted.",
        "Record who within each organisation can request changes or deletion.",
        "Align with the Protection of Personal Information Act (POPIA) for any staff-level data.",
        "Note that satellite and weather data in this platform are from public datasets — no sharing agreement required for those.",
        "Capture the agreement start and review date, and store the signed document outside this tool.",
    ]
