
"""
Map of Life support for BL Turner.

This module reuses the same style of MoL integration used in the Panuka app,
but aligns the narrative to BL Turner's use cases:
- plant-site sensitivity around KwaDukuza
- feedstock source corridors in eThekwini and uMgungundlovu
- digestate receiving landscapes in KZN
- site planning, buffers, runoff, wetland and species-risk awareness

It is intentionally additive: if no MoL workbook / csv bundle is present,
the app should continue working without MoL content.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import pandas as pd

MOL_REQUIRED_SHEETS = ["data_dictionary", "site_species", "site_shi_by_year", "site_shi_change"]

# Map BL Turner presets to MoL site names expected in the workbook.
PRESET_TO_MOL_SITE = {
    "BL Turner Main Site (Portion 159, New Guelderland, KwaDukuza)": "KwaDukuza",
    "Durban Fresh Produce Market (Clairwood) — feedstock source": "eThekwini",
    "eThekwini Kerbside Organics Collection Zone — feedstock source": "eThekwini",
    "Pietermaritzburg Abattoir Cluster — feedstock source": "uMgungundlovu",
}


MOL_THREAT_DETAILS = {
    "CR": {
        "name": "Critically Endangered",
        "plain": "is at extremely high risk of disappearing",
        "business": (
            "For BL Turner, this means the site and nearby sourcing or receiving landscapes should "
            "treat wetlands, drainage lines, forest-edge habitat, uncultivated buffers and other "
            "semi-natural cover as highly sensitive when planning plant works, roads, storage, "
            "digestate application areas or route expansions."
        ),
    },
    "EN": {
        "name": "Endangered",
        "plain": "is at very high risk of disappearing",
        "business": (
            "For BL Turner, this points to tighter control over clearing, runoff, disturbance, "
            "odour, leachate and fragmentation around the plant and digestate receiving areas."
        ),
    },
    "VU": {
        "name": "Vulnerable",
        "plain": "is under pressure and can move into a more serious category if conditions worsen",
        "business": (
            "For BL Turner, this is an early warning to keep buffers, edge habitat, connected "
            "vegetation and water-linked areas intact wherever possible."
        ),
    },
    "NT": {
        "name": "Near Threatened",
        "plain": "is not yet in the higher-risk categories, but is close enough to need attention",
        "business": (
            "For BL Turner, this works as a watchlist. Good site layout, runoff control, habitat "
            "buffers and careful digestate use can help prevent avoidable pressure later."
        ),
    },
}


def resolve_mol_resources() -> Optional[Dict[str, Any]]:
    candidate_workbooks = [
        "MOL Data - for Space Eagle.xlsx",
        "MOL Data for Space Eagle.xlsx",
        "MOL_Data_-_for_Space_Eagle.xlsx",
    ]
    candidate_csv_dirs = [
        "mol_data",
        "MOL Data - for Space Eagle",
        "MOL_Data_for_Space_Eagle",
        "mol",
        "utils/mol_data",
        "data/mol_data",
    ]
    search_dirs: List[Path] = []
    try:
        search_dirs.append(Path(__file__).resolve().parent)
        search_dirs.append(Path(__file__).resolve().parent.parent)
    except Exception:
        pass
    search_dirs.extend([Path.cwd(), Path.cwd().parent, Path("/mnt/data")])

    seen = set()
    ordered_dirs: List[Path] = []
    for d in search_dirs:
        if d and str(d) not in seen and d.exists():
            ordered_dirs.append(d)
            seen.add(str(d))

    for directory in ordered_dirs:
        for candidate in candidate_workbooks:
            p = directory / candidate
            if p.exists() and p.is_file():
                return {"kind": "xlsx", "path": p}

    for directory in ordered_dirs:
        for pattern in ["*MOL*.xlsx", "*Map*Life*.xlsx", "*Space*Eagle*.xlsx"]:
            for p in sorted(directory.glob(pattern)):
                if p.is_file():
                    return {"kind": "xlsx", "path": p}

    for directory in ordered_dirs:
        for candidate in candidate_csv_dirs:
            d = directory / candidate
            if d.exists() and d.is_dir():
                names = {f.stem.lower(): f for f in d.glob("*.csv")}
                if all(sheet in names for sheet in MOL_REQUIRED_SHEETS):
                    return {"kind": "csv_dir", "path": d}

    for directory in ordered_dirs:
        names = {f.stem.lower(): f for f in directory.glob("*.csv")}
        if all(sheet in names for sheet in MOL_REQUIRED_SHEETS):
            return {"kind": "csv_dir", "path": directory}

    return None


def load_mol_reference_data(resource_path: str) -> Optional[Dict[str, pd.DataFrame]]:
    path = Path(resource_path)
    if not path.exists():
        return None
    try:
        if path.is_dir():
            names = {f.stem.lower(): f for f in path.glob("*.csv")}
            if not all(sheet in names for sheet in MOL_REQUIRED_SHEETS):
                return None
            dictionary_df = pd.read_csv(names["data_dictionary"])
            species_df = pd.read_csv(names["site_species"])
            shi_by_year_df = pd.read_csv(names["site_shi_by_year"])
            shi_change_df = pd.read_csv(names["site_shi_change"])
        else:
            dictionary_df = pd.read_excel(path, sheet_name="data_dictionary")
            species_df = pd.read_excel(path, sheet_name="site_species")
            shi_by_year_df = pd.read_excel(path, sheet_name="site_shi_by_year")
            shi_change_df = pd.read_excel(path, sheet_name="site_shi_change")
    except Exception:
        return None

    for df in (dictionary_df, species_df, shi_by_year_df, shi_change_df):
        df.columns = [str(c).strip() if c is not None else "" for c in df.columns]

    if "Highest IUCN Threat Level" in species_df.columns:
        species_df["Highest IUCN Threat Level"] = (
            species_df["Highest IUCN Threat Level"].fillna("").astype(str).str.strip()
        )
    if "Taxonomic Group" in species_df.columns:
        species_df["Taxonomic Group"] = (
            species_df["Taxonomic Group"].fillna("").astype(str).str.strip().str.title()
        )
    if "Vernacular Name" in species_df.columns:
        species_df["Vernacular Name"] = (
            species_df["Vernacular Name"].fillna("").astype(str).str.strip("{}")
        )

    return {
        "dictionary": dictionary_df,
        "species": species_df,
        "shi_by_year": shi_by_year_df,
        "shi_change": shi_change_df,
    }


def _first_non_empty(series, fallback="Not available"):
    try:
        iterable = list(series)
    except Exception:
        return fallback
    for val in iterable:
        if pd.notna(val) and str(val).strip() and str(val).strip().lower() != "nan":
            return str(val).strip()
    return fallback


def get_mol_site_for_preset(preset: str, mol_data: Optional[Dict[str, pd.DataFrame]]) -> Optional[str]:
    if preset in PRESET_TO_MOL_SITE:
        return PRESET_TO_MOL_SITE[preset]
    return None


def build_mol_insights(preset: str) -> Optional[Dict[str, Any]]:
    mol_resources = resolve_mol_resources()
    mol_data = load_mol_reference_data(str(mol_resources["path"])) if mol_resources else None
    if not mol_data:
        return None
    site_name = get_mol_site_for_preset(preset, mol_data)
    if not site_name:
        return None

    dictionary_df = mol_data["dictionary"]
    species_df = mol_data["species"]
    shi_by_year_df = mol_data["shi_by_year"]
    shi_change_df = mol_data["shi_change"]

    site_species = species_df[species_df["Site Name"].astype(str).str.strip() == site_name].copy()
    site_shi = shi_by_year_df[shi_by_year_df["Site Name"].astype(str).str.strip() == site_name].copy().sort_values("Year")
    site_change = shi_change_df[shi_change_df["Site Name"].astype(str).str.strip() == site_name].copy()

    if site_species.empty and site_shi.empty and site_change.empty:
        return None

    threat_order = {"CR": 0, "EN": 1, "VU": 2, "NT": 3, "DD": 4, "LC": 5}
    if not site_species.empty:
        site_species["threat_rank"] = site_species["Highest IUCN Threat Level"].map(threat_order).fillna(9)
    else:
        site_species["threat_rank"] = []

    latest_row = site_shi.iloc[-1].to_dict() if not site_shi.empty else {}
    change_row = site_change.iloc[0].to_dict() if not site_change.empty else {}

    group_counts = site_species["Taxonomic Group"].value_counts().to_dict() if not site_species.empty else {}
    threat_counts = site_species["Highest IUCN Threat Level"].value_counts().to_dict() if not site_species.empty else {}

    threatened_df = site_species[
        site_species["Highest IUCN Threat Level"].isin(["CR", "EN", "VU", "NT"])
    ].copy().sort_values(["threat_rank", "Taxonomic Group", "Scientific Name"])

    top_species = []
    for _, row in threatened_df.head(8).iterrows():
        common_name = row.get("Vernacular Name") or row.get("Scientific Name")
        top_species.append({
            "name": common_name,
            "scientific_name": row.get("Scientific Name"),
            "group": row.get("Taxonomic Group"),
            "threat": row.get("Highest IUCN Threat Level"),
        })

    latest_shi = latest_row.get("Species Habitat Index (SHI)")
    birds_shi = latest_row.get("Species Habitat Index (SHI) - Birds")
    mammals_shi = latest_row.get("Species Habitat Index (SHI) - Mammals")
    reptiles_shi = latest_row.get("Species Habitat Index (SHI) - Reptiles")
    shi_change_total = change_row.get("SHI Change Since 2001")
    birds_change = change_row.get("SHI Change Since 2001 - Birds")
    mammals_change = change_row.get("SHI Change Since 2001 - Mammals")
    reptiles_change = change_row.get("SHI Change Since 2001 - Reptiles")

    species_total = int(len(site_species))
    threatened_total = int(threatened_df.shape[0])
    critical_total = int(sum(threat_counts.get(code, 0) for code in ["CR", "EN"]))

    trend_df = pd.DataFrame()
    if not site_shi.empty:
        use_cols = [c for c in [
            "Year",
            "Species Habitat Index (SHI)",
            "Species Habitat Index (SHI) - Birds",
            "Species Habitat Index (SHI) - Mammals",
            "Species Habitat Index (SHI) - Reptiles",
        ] if c in site_shi.columns]
        trend_df = site_shi[use_cols].rename(columns={
            "Year": "year",
            "Species Habitat Index (SHI)": "All species",
            "Species Habitat Index (SHI) - Birds": "Birds",
            "Species Habitat Index (SHI) - Mammals": "Mammals",
            "Species Habitat Index (SHI) - Reptiles": "Reptiles",
        })

    latest_year_label = int(latest_row.get("Year")) if latest_row and pd.notna(latest_row.get("Year")) else "latest year"

    def fmt_num(val, digits=1, suffix=""):
        if val is None or val == "":
            return "Not available"
        try:
            return f"{float(val):.{digits}f}{suffix}"
        except Exception:
            return str(val)

    cards = [
        {"label": "Expected species", "value": f"{species_total}", "subtext": "Modelled birds, mammals and reptiles that could use habitat in this zone"},
        {"label": "Threatened / near-threatened", "value": f"{threatened_total}", "subtext": "Higher-risk species that deserve closer attention"},
        {"label": "Latest habitat score", "value": fmt_num(latest_shi, 1), "subtext": f"For {latest_year_label}. Higher values mean habitat is more suitable."},
        {"label": "Change since 2001", "value": fmt_num(shi_change_total, 2), "subtext": "Shows whether habitat conditions strengthened or weakened over time"},
    ]

    threat_profile_details = []
    for level in ["CR", "EN", "VU", "NT"]:
        count = int(threat_counts.get(level, 0))
        detail = MOL_THREAT_DETAILS[level]
        threat_profile_details.append({
            "code": level,
            "name": detail["name"],
            "count": count,
            "plain": detail["plain"],
            "business": detail["business"],
        })

    advisory_notes = []
    advisory_notes.append(
        f"Map of Life indicates that around {site_name}, as many as {species_total} bird, mammal and reptile species could use habitat in and around the area reviewed. "
        f"{threatened_total} of these fall into higher-risk categories. For BL Turner, that means plant layout, drainage, buffers, odour control, routing and digestate-use decisions can affect species that rely on the same landscape."
    )
    if latest_shi is not None and pd.notna(latest_shi):
        advisory_notes.append(
            f"The latest habitat score is {fmt_num(latest_shi, 1)} for {latest_year_label}. "
            "A higher score usually means the surrounding landscape is offering better cover, food, water access and movement space for species."
        )
    if shi_change_total is not None and pd.notna(shi_change_total):
        if float(shi_change_total) < 0:
            advisory_notes.append(
                f"The overall habitat score has fallen by {abs(float(shi_change_total)):.2f} points since 2001. "
                "For BL Turner, this suggests the wider landscape may already be under pressure, making wet areas, field edges, drainage lines and remaining natural buffers more important."
            )
        elif float(shi_change_total) > 0:
            advisory_notes.append(
                f"The overall habitat score has improved by {float(shi_change_total):.2f} points since 2001. "
                "For BL Turner, that is a positive sign that parts of the surrounding landscape are still supporting species and ecological function."
            )

    if critical_total > 0:
        advisory_notes.append(
            f"{critical_total} expected species fall into the most sensitive categories, Critically Endangered or Endangered. "
            "For BL Turner, this makes water-linked habitat, remaining natural cover and undisturbed buffers especially important when placing infrastructure, managing runoff or planning digestate application."
        )

    service_notes = [
        "The species picture should be read together with the water, vegetation, heat and flood results already shown for the site.",
        "For BL Turner, the practical value is in spotting where the same area may matter both for operations and for nature — for example wetlands, drainage lines, field edges, forest remnants and receiving landscapes for digestate.",
        "This supports clearer advice on where to protect buffers, where to avoid unnecessary disturbance, and where on-the-ground checks should come before plant expansion or new sourcing arrangements.",
    ]

    tnfd_points = [
        f"Locate: MOL identifies {species_total} expected bird, mammal and reptile species at {site_name}, with {threatened_total} in threatened or near-threatened categories.",
        f"Evaluate: the latest Species Habitat Index is {fmt_num(latest_shi, 1)} and total SHI change since 2001 is {fmt_num(shi_change_total, 2)}, adding a species-state signal to the land, water and climate indicators already shown in the platform.",
        "Assess: these patterns matter to BL Turner because runoff, odour, leachate, site clearing and digestate distribution can affect habitat quality and species resilience.",
        "Prepare: maintain buffers, avoid unnecessary clearing, protect wet patches and water sources, and use species-sensitive areas as a screen when planning infrastructure, sourcing routes or digestate application areas.",
    ]

    dictionary_note = ""
    if not dictionary_df.empty and {"sheet_name", "column_name"}.issubset(dictionary_df.columns):
        used_cols = dictionary_df[
            dictionary_df["sheet_name"].isin(["site_species", "site_shi_by_year", "site_shi_change"])
            & dictionary_df["column_name"].isin([
                "Scientific Name",
                "Highest IUCN Threat Level",
                "Species Habitat Index (SHI)",
                "SHI Change Since 2001",
            ])
        ]
        if not used_cols.empty:
            dictionary_note = "The workbook data dictionary was used to interpret species names, IUCN threat levels, Species Habitat Index values, and SHI change since 2001."

    return {
        "site_name": site_name,
        "project_name": _first_non_empty(site_species.get("Project Name", []), "Space Eagle"),
        "country": _first_non_empty(site_species.get("Country", []), "South Africa"),
        "species_total": species_total,
        "group_counts": group_counts,
        "threat_counts": threat_counts,
        "threatened_total": threatened_total,
        "critical_total": critical_total,
        "top_species": top_species,
        "latest_year": int(latest_row.get("Year")) if latest_row and pd.notna(latest_row.get("Year")) else None,
        "latest_shi": latest_shi,
        "birds_shi": birds_shi,
        "mammals_shi": mammals_shi,
        "reptiles_shi": reptiles_shi,
        "shi_change_total": shi_change_total,
        "birds_change": birds_change,
        "mammals_change": mammals_change,
        "reptiles_change": reptiles_change,
        "trend_df": trend_df,
        "cards": cards,
        "service_notes": service_notes,
        "advisory_notes": advisory_notes,
        "threat_profile_details": threat_profile_details,
        "tnfd_points": tnfd_points,
        "dictionary_note": dictionary_note,
    }


def make_mol_shi_long_df(mol_insights: Optional[Dict[str, Any]]) -> pd.DataFrame:
    if not mol_insights or mol_insights.get("trend_df") is None or mol_insights["trend_df"].empty:
        return pd.DataFrame()
    return mol_insights["trend_df"].melt(id_vars="year", var_name="Series", value_name="SHI")


def mol_shi_chart_bytes(mol_insights: Optional[Dict[str, Any]]) -> Optional[bytes]:
    long_df = make_mol_shi_long_df(mol_insights)
    if long_df.empty:
        return None
    plot_df = long_df.dropna(subset=["SHI"]).copy()
    if plot_df.empty:
        return None
    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    for series_name, subdf in plot_df.groupby("Series"):
        ax.plot(subdf["year"], subdf["SHI"], marker="o", label=series_name)
    ax.set_title("Map of Life Species Habitat Index trend")
    ax.set_xlabel("Year")
    ax.set_ylabel("Species Habitat Index")
    ax.grid(True, alpha=0.25)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()




def mol_summary_chart_bytes(mol_insights: Optional[Dict[str, Any]]) -> Optional[bytes]:
    if not mol_insights:
        return None

    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    ax.axis("off")

    lines = [
        f"Map of Life site: {mol_insights.get('site_name', 'Not available')}",
        f"Expected species: {mol_insights.get('species_total', 'Not available')}",
        f"Threatened / near-threatened: {mol_insights.get('threatened_total', 'Not available')}",
        f"Latest SHI: {mol_insights.get('latest_shi', 'Not available')}",
        f"SHI change since 2001: {mol_insights.get('shi_change_total', 'Not available')}",
        "",
        "BL Turner relevance:",
    ]
    for note in (mol_insights.get("advisory_notes") or [])[:3]:
        lines.append(f"• {note}")

    ax.text(
        0.01, 0.98, "\n".join(lines),
        va="top", ha="left", fontsize=9, wrap=True
    )

    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()

def render_species_badges(st, top_species: List[Dict[str, Any]]) -> None:
    if not top_species:
        st.write("No threatened or near-threatened species were provided for the mapped site.")
        return
    badge_cols = st.columns(2)
    for idx, sp in enumerate(top_species[:8]):
        with badge_cols[idx % 2]:
            st.markdown(
                f"""
                <div style="background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:12px 14px;margin-bottom:10px;">
                    <div style="font-size:0.80rem;color:#64748b;">{sp['group']}</div>
                    <div style="font-size:1rem;font-weight:700;color:#0f172a;">{sp['name']}</div>
                    <div style="font-size:0.82rem;color:#475569;">{sp['scientific_name']}</div>
                    <div style="margin-top:6px;font-size:0.84rem;color:#163d63;font-weight:700;">{sp['threat']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
