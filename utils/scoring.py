def build_risk_and_recommendations(preset: str, category: str, metrics: dict) -> dict:
    score = 0
    flags = []
    streamlit_recs = []
    ee_recs = []

    def add_flag(condition, pts, flag_text, rec_text):
        nonlocal score
        if condition:
            score += pts
            flags.append(flag_text)
            streamlit_recs.append(rec_text)
            ee_recs.append(rec_text)

    rain_anom_pct = metrics.get("rain_anom_pct")
    built_pct = metrics.get("built_pct")
    lst_mean = metrics.get("lst_mean")
    water_occ = metrics.get("water_occ")
    flood_risk = metrics.get("flood_risk")
    tree_pct = metrics.get("tree_pct")
    ndvi_trend = metrics.get("ndvi_trend")

    add_flag(
        rain_anom_pct is not None and rain_anom_pct < -10,
        12,
        "Recent rainfall is below the long-term average.",
        "Review water-security assumptions for cleaning, processing, and surrounding site management."
    )
    add_flag(
        lst_mean is not None and lst_mean > 30,
        14,
        "Heat conditions are elevated.",
        "Plan for odour management, storage stress, worker comfort, and facility ventilation under hotter conditions."
    )
    add_flag(
        flood_risk is not None and flood_risk > 0.1,
        16,
        "Flood exposure is visible in the site context.",
        "Review drainage, lower-lying areas, stormwater management, and critical equipment placement before construction."
    )
    add_flag(
        water_occ is not None and water_occ < 5,
        12,
        "Visible surface water is limited.",
        "Treat the site as more dependent on storage, groundwater-linked systems, or external supply."
    )
    add_flag(
        built_pct is not None and built_pct >= 15,
        10,
        "Built-up areas are already important in the surrounding landscape.",
        "Treat community-facing controls such as traffic, noise, and odour as part of early design rather than later mitigation."
    )
    add_flag(
        tree_pct is not None and tree_pct < 10,
        8,
        "Ecological buffering from tree cover is limited.",
        "Consider vegetated buffers or screening where practical to improve site resilience and reduce nuisance exposure."
    )
    add_flag(
        ndvi_trend is not None and ndvi_trend < -0.03,
        8,
        "Vegetation is weakening in parts of the surrounding landscape.",
        "Review whether land pressure or reduced buffering could affect long-term site resilience."
    )

    base_recs = [
        "Use this dashboard as an early site-screening tool before development is finalised.",
        "Review drainage and flood design early because site interruption risk is harder to correct after construction.",
        "Treat water reliability as an operational issue, not only an environmental one.",
        "Build odour, traffic, and community-facing controls into the project design from the start.",
        "Use the land-cover, heat, and water maps together when discussing site suitability with partners and funders.",
        "Update the assessment when the final plant footprint, truck routes, and waste catchment are confirmed.",
    ]
    streamlit_recs.extend(base_recs)
    ee_recs.extend(base_recs)

    # de-duplicate
    seen = set()
    streamlit_recs = [r for r in streamlit_recs if not (r in seen or seen.add(r))]
    seen = set()
    ee_recs = [r for r in ee_recs if not (r in seen or seen.add(r))]

    score = min(score, 100)
    band = "Low"
    if score >= 60:
        band = "High"
    elif score >= 30:
        band = "Moderate"

    return {"score": score, "band": band, "flags": flags, "recs": streamlit_recs[:8], "ee_recs": ee_recs[:8]}
