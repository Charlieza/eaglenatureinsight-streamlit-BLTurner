from typing import Dict

METHANE_FACTOR = 0.75
CO2_EQUIVALENT = 28


def calculate_avoided_methane(tons_per_day: float) -> Dict:
    annual_tons = tons_per_day * 365
    methane = annual_tons * METHANE_FACTOR
    co2e = methane * CO2_EQUIVALENT
    return {
        "annual_tons_diverted": round(annual_tons, 1),
        "methane_tons": round(methane, 1),
        "co2e_tons": round(co2e, 1),
    }
