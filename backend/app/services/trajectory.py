def calculate_trajectory(current: float, risk_24h: float, risk_72h: float) -> str:
    """Map risk progression across current, 24h, and 72h windows to a trajectory state."""
    delta_24 = risk_24h - current
    delta_72 = risk_72h - current

    if risk_72h >= 0.95 and max(delta_24, delta_72) >= 0.25:
        return "Critical"
    if risk_72h >= 0.8 and (delta_72 >= 0.2 or risk_24h >= 0.75):
        return "Rapidly Increasing"
    if delta_72 > 0.1 or risk_24h > current:
        return "Increasing"
    if delta_72 < -0.1 or risk_72h < current:
        return "Decreasing"
    if abs(delta_24) <= 0.05 and abs(delta_72) <= 0.05:
        return "Stable"
    return "Stable"
