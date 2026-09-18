def calculate_priority(
    risk: float,
    future_risk: float,
    trajectory: str,
    exposure: float,
    vulnerability: float,
) -> str:
    """Aggregate risk, hazard trend, exposure, and vulnerability into a decision priority."""
    weighted_score = (
        risk * 0.35
        + future_risk * 0.35
        + exposure * 0.15
        + vulnerability * 0.15
    )

    if trajectory in {"Critical", "Rapidly Increasing"} or weighted_score >= 0.8:
        return "Immediate Assessment"
    if weighted_score >= 0.6:
        return "High"
    if weighted_score >= 0.35:
        return "Medium"
    return "Low"
