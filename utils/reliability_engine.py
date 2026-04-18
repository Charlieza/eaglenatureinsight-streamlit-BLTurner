def reliability_score(
    headroom: float,
    continuity_risks: list,
) -> int:

    score = 100

    if headroom < 0:

        score -= 40

    if headroom < -20:

        score -= 20

    if len(continuity_risks) > 1:

        score -= 20

    if score < 0:

        score = 0

    return score
