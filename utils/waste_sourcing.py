
from typing import List, Dict, Any
import numpy as np

NAMEPLATE_TONS_PER_DAY = 100

def seasonal_supply_profile() -> List[Dict[str, Any]]:
    """Generate a realistic seasonal supply profile for feedstock."""

    months = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]

    # Example seasonal pattern (can be replaced with real logic)
    base_supply = 105
    seasonal_variation = np.array([
        0.95, 0.97, 1.02, 1.05, 1.08, 1.10,
        1.12, 1.09, 1.04, 1.01, 0.98, 0.96
    ])

    monthly = base_supply * seasonal_variation

    rows: List[Dict[str, Any]] = []

    for i, m in enumerate(months):
        rows.append({
            "month": m,
            # FIXED: standardized column name used across the app
            "projected_tons_per_day": float(monthly[i]),
            # kept for backward compatibility
            "supply_tpd": float(monthly[i]),
            "nameplate_tpd": NAMEPLATE_TONS_PER_DAY,
            "headroom_tpd": float(monthly[i]) - NAMEPLATE_TONS_PER_DAY,
        })

    return rows
