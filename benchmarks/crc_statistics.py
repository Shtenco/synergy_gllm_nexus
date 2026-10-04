from __future__ import annotations

import math

WILSON_95_Z = 1.959963984540054


def wilson_interval(successes: int, trials: int, *, z: float = WILSON_95_Z) -> tuple[float, float]:
    """Return the two-sided Wilson score interval for a binomial proportion."""
    successes = int(successes)
    trials = int(trials)
    if trials <= 0:
        raise ValueError("trials must be positive")
    if successes < 0 or successes > trials:
        raise ValueError("successes must lie in [0, trials]")
    z = float(z)
    if z <= 0:
        raise ValueError("z must be positive")

    p = successes / trials
    z2 = z * z
    denominator = 1.0 + z2 / trials
    center = (p + z2 / (2.0 * trials)) / denominator
    radius = z * math.sqrt(p * (1.0 - p) / trials + z2 / (4.0 * trials * trials)) / denominator
    lower = max(0.0, center - radius)
    upper = min(1.0, center + radius)
    return lower, upper


def wilson_lower(successes: int, trials: int, *, z: float = WILSON_95_Z) -> float:
    return wilson_interval(successes, trials, z=z)[0]
