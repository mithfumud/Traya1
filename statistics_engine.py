"""
statistics_engine.py
The "is this real or random" layer — runs AFTER guardrails pass
and metrics are computed.

Uses a two-proportion z-test to compare Control vs Variant conversion,
plus a confidence interval on the lift, so we're not just reporting
a single p-value with no sense of the range of plausible outcomes.
"""

import math
import pandas as pd
from statsmodels.stats.proportion import proportions_ztest


def run_significance_test(
    control_successes: int,
    control_total: int,
    variant_successes: int,
    variant_total: int,
    alpha: float = 0.05,
) -> dict:
    """
    Two-proportion z-test comparing Control vs Variant conversion.
    Returns whether the difference is statistically significant at
    the given alpha, plus supporting numbers a PM would want to see.
    """
    count = [control_successes, variant_successes]
    nobs = [control_total, variant_total]

    stat, p_value = proportions_ztest(count, nobs)

    control_rate = control_successes / control_total
    variant_rate = variant_successes / variant_total

    significant = p_value < alpha

    return {
        "check": "Statistical Significance",
        "control_rate": round(control_rate, 4),
        "variant_rate": round(variant_rate, 4),
        "z_statistic": round(stat, 4),
        "p_value": round(p_value, 5),
        "alpha": alpha,
        "significant": bool(significant),
        "message": (
            f"Difference is statistically significant (p={p_value:.4f})."
            if significant
            else f"Difference is NOT statistically significant (p={p_value:.4f}) — "
                 "could plausibly be random noise."
        ),
    }


def compute_confidence_interval(
    control_successes: int,
    control_total: int,
    variant_successes: int,
    variant_total: int,
    confidence: float = 0.95,
) -> dict:
    """
    Computes a confidence interval for the ABSOLUTE lift
    (variant_rate - control_rate) using a normal approximation.

    This tells a PM the plausible RANGE of the true effect, not just
    a single point estimate — important because a lift of "+3%" means
    very different things if the interval is [+2.8%, +3.2%] versus
    [-1%, +7%].
    """
    p1 = control_successes / control_total
    p2 = variant_successes / variant_total

    diff = p2 - p1

    se = math.sqrt(
        (p1 * (1 - p1) / control_total) + (p2 * (1 - p2) / variant_total)
    )

    z_lookup = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
    z = z_lookup.get(confidence, 1.96)

    margin = z * se
    lower = round(diff - margin, 4)
    upper = round(diff + margin, 4)

    # If the interval crosses zero, we can't be confident about the direction
    crosses_zero = lower < 0 < upper

    return {
        "check": "Confidence Interval",
        "confidence_level": confidence,
        "point_estimate": round(diff, 4),
        "lower_bound": lower,
        "upper_bound": upper,
        "crosses_zero": bool(crosses_zero),
        "message": (
            f"We're {int(confidence*100)}% confident the true lift is between "
            f"{lower:+.2%} and {upper:+.2%}."
            + (" This range includes zero, so the direction of the effect is uncertain."
               if crosses_zero else "")
        ),
    }


def run_statistics(df: pd.DataFrame) -> dict:
    """
    Runs both the significance test and confidence interval on
    conversion (purchased) for Control vs Variant.
    Returns a combined dict ready for the Decision Engine next.
    """
    control = df[df["variant"] == "control"]
    variant = df[df["variant"] == "variant"]

    control_total = len(control)
    variant_total = len(variant)
    control_successes = control["purchased"].sum()
    variant_successes = variant["purchased"].sum()

    significance = run_significance_test(
        control_successes, control_total, variant_successes, variant_total
    )
    ci = compute_confidence_interval(
        control_successes, control_total, variant_successes, variant_total
    )

    return {
        "significance": significance,
        "confidence_interval": ci,
    }


if __name__ == "__main__":
    df = pd.read_csv("experiment_data.csv")
    results = run_statistics(df)

    print("Significance:", results["significance"]["message"])
    print("Confidence Interval:", results["confidence_interval"]["message"])