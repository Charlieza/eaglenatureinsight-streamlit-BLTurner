from __future__ import annotations

from math import radians, sin, cos, sqrt, atan2
from typing import Any, Dict, List


EARTH_RADIUS_KM = 6371.0
DEFAULT_NAMEPLATE_TPD = 100.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1_r = radians(lat1)
    lon1_r = radians(lon1)
    lat2_r = radians(lat2)
    lon2_r = radians(lon2)

    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r

    a = sin(dlat / 2) ** 2 + cos(lat1_r) * cos(lat2_r) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return EARTH_RADIUS_KM * c


def classify_route(distance_km: float) -> str:
    if distance_km <= 25:
        return "Near-plant"
    if distance_km <= 60:
        return "Regional"
    if distance_km <= 120:
        return "Long-haul"
    return "Extended-haul"


def route_risk_band(distance_km: float) -> str:
    if distance_km <= 25:
        return "Low"
    if distance_km <= 60:
        return "Watch"
    if distance_km <= 120:
        return "Moderate"
    return "High"


def estimate_round_trip_km(distance_km: float) -> float:
    return round(distance_km * 2.0, 1)


def estimate_weekly_trips(collection_frequency: str) -> float:
    if not collection_frequency:
        return 1.0

    text = collection_frequency.lower()

    if "daily" in text:
        return 6.0
    if "weekly" in text:
        return 1.0
    if "2" in text and "week" in text:
        return 2.0
    if "3" in text and "week" in text:
        return 3.0
    if "4" in text and "week" in text:
        return 4.0
    if "5" in text and "week" in text:
        return 5.0
    if "6" in text and "week" in text:
        return 6.0

    if "3–6" in text or "3-6" in text:
        return 4.5
    if "2–4" in text or "2-4" in text:
        return 3.0
    if "3–5" in text or "3-5" in text:
        return 4.0

    return 1.0


def estimate_transport_cost_per_ton(
    distance_km: float,
    tons_per_day: float,
    collection_frequency: str,
    truck_cost_per_km: float = 18.0,
    load_factor: float = 0.85,
) -> float:
    """
    Simple screening estimate in ZAR per ton.

    Assumptions:
    - truck cost includes fuel, driver, tyre wear, maintenance
    - load_factor reflects imperfect loading and routing inefficiency
    """
    weekly_trips = estimate_weekly_trips(collection_frequency)
    round_trip_km = estimate_round_trip_km(distance_km)
    weekly_route_cost = round_trip_km * weekly_trips * truck_cost_per_km

    weekly_tons = max(tons_per_day * 7.0 * load_factor, 0.1)

    return round(weekly_route_cost / weekly_tons, 2)


def build_logistics_table(
    sources: List[Dict[str, Any]],
    plant_lat: float,
    plant_lon: float,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for src in sources:
        src_lat = float(src.get("lat", 0.0))
        src_lon = float(src.get("lon", 0.0))
        tons = float(src.get("tons_per_day_est", 0.0) or 0.0)
        freq = src.get("collection_frequency", "")

        distance_km = haversine_km(plant_lat, plant_lon, src_lat, src_lon)
        route_class = classify_route(distance_km)
        risk_band = route_risk_band(distance_km)
        round_trip_km = estimate_round_trip_km(distance_km)
        trips_per_week = estimate_weekly_trips(freq)
        transport_cost_per_ton = estimate_transport_cost_per_ton(
            distance_km=distance_km,
            tons_per_day=tons,
            collection_frequency=freq,
        )

        rows.append(
            {
                "Source": src.get("name"),
                "District": src.get("district"),
                "Stream": src.get("stream"),
                "Distance to plant (km)": round(distance_km, 1),
                "Round trip (km)": round_trip_km,
                "Trips/week (est.)": trips_per_week,
                "Route class": route_class,
                "Route risk": risk_band,
                "Transport cost (ZAR/ton)": transport_cost_per_ton,
                "Daily tonnage (est.)": tons,
                "Collection frequency": freq,
                "Role": src.get("role"),
            }
        )

    return rows


def logistics_summary(logistics_rows: List[Dict[str, Any]]) -> Dict[str, float]:
    if not logistics_rows:
        return {
            "weighted_avg_distance_km": 0.0,
            "weighted_avg_cost_per_ton": 0.0,
            "long_haul_share_pct": 0.0,
            "high_risk_route_count": 0,
        }

    total_tons = sum(float(r.get("Daily tonnage (est.)", 0.0) or 0.0) for r in logistics_rows)
    total_tons = max(total_tons, 0.1)

    weighted_distance = sum(
        float(r.get("Distance to plant (km)", 0.0)) * float(r.get("Daily tonnage (est.)", 0.0))
        for r in logistics_rows
    ) / total_tons

    weighted_cost = sum(
        float(r.get("Transport cost (ZAR/ton)", 0.0)) * float(r.get("Daily tonnage (est.)", 0.0))
        for r in logistics_rows
    ) / total_tons

    long_haul_tons = sum(
        float(r.get("Daily tonnage (est.)", 0.0))
        for r in logistics_rows
        if r.get("Route class") in ["Long-haul", "Extended-haul"]
    )

    high_risk_count = sum(
        1 for r in logistics_rows if r.get("Route risk") == "High"
    )

    return {
        "weighted_avg_distance_km": round(weighted_distance, 1),
        "weighted_avg_cost_per_ton": round(weighted_cost, 2),
        "long_haul_share_pct": round((long_haul_tons / total_tons) * 100.0, 1),
        "high_risk_route_count": high_risk_count,
    }
