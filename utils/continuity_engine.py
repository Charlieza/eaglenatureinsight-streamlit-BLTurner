from typing import Dict, List


def continuity_risk_assessment(sources: List[dict]) -> List[Dict]:

    district_supply = {}

    for s in sources:

        d = s.get("district", "Unknown")

        district_supply[d] = (
            district_supply.get(d, 0)
            + float(s.get("tons_per_day_est", 0))
        )

    total = sum(district_supply.values())

    risks = []

    for district, tons in district_supply.items():

        if total == 0:
            continue

        pct = tons / total

        if pct > 0.6:

            risks.append(
                {
                    "level": "High",
                    "risk": "Geographic concentration",
                    "indicator": district,
                    "meaning": (
                        f"{district} provides more than 60% of supply"
                    ),
                    "mitigation": (
                        "Secure additional contracts "
                        "in other districts"
                    ),
                }
            )

    if not risks:

        risks.append(
            {
                "level": "Low",
                "risk": "Supply diversification",
                "indicator": "Multiple districts",
                "meaning": "Supply sources are diversified",
                "mitigation": "Maintain multiple supply contracts",
            }
        )

    return risks
