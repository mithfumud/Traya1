"""
data_generator.py
Generates a synthetic experiment dataset simulating Traya's
"Success Stories above the fold" A/B test.

This is intentionally NOT random noise — it's built so that
specific scenarios (SRM, low sample, refund spike, segment
disagreement) can be toggled on/off to test our engines later.
"""

import pandas as pd
import numpy as np


def generate_experiment_data(
    n_control: int = 4000,
    n_variant: int = 4000,
    control_conversion: float = 0.10,
    variant_conversion: float = 0.13,
    control_refund_rate: float = 0.02,
    variant_refund_rate: float = 0.02,
    new_user_ratio: float = 0.6,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Builds one row per user with:
    - variant: 'control' or 'variant'
    - segment: 'new' or 'returning'
    - started_test, completed_test, viewed_report: funnel steps (bool)
    - purchased: did they buy (bool)
    - refunded: did they refund after buying (bool)

    Change n_control / n_variant to simulate an SRM (uneven split).
    Change control_refund_rate / variant_refund_rate to simulate a
    guardrail-metric failure.
    """
    rng = np.random.default_rng(seed)
    rows = []

    for variant, n, conv_rate, refund_rate in [
        ("control", n_control, control_conversion, control_refund_rate),
        ("variant", n_variant, variant_conversion, variant_refund_rate),
    ]:
        segments = rng.choice(
            ["new", "returning"], size=n, p=[new_user_ratio, 1 - new_user_ratio]
        )

        # Funnel: each step has a chance of drop-off from the previous step
        started_test = rng.random(n) < 0.75
        completed_test = started_test & (rng.random(n) < 0.80)
        viewed_report = completed_test & (rng.random(n) < 0.90)

        # Purchases only possible if they viewed the report.
        # conv_rate is meant as an OVERALL conversion rate (purchases / all visitors),
        # so we back out the conditional probability using the actual reach rate.
        reach_rate = viewed_report.mean()
        conditional_purchase_prob = min(conv_rate / reach_rate, 1.0) if reach_rate > 0 else 0
        purchased = viewed_report & (rng.random(n) < conditional_purchase_prob)

        refunded = purchased & (rng.random(n) < refund_rate)

        for i in range(n):
            rows.append(
                {
                    "user_id": f"{variant}_{i}",
                    "variant": variant,
                    "segment": segments[i],
                    "started_test": bool(started_test[i]),
                    "completed_test": bool(completed_test[i]),
                    "viewed_report": bool(viewed_report[i]),
                    "purchased": bool(purchased[i]),
                    "refunded": bool(refunded[i]),
                }
            )

    return pd.DataFrame(rows)


if __name__ == "__main__":
    # Default: a "healthy" experiment — fair split, real lift, no refund spike
    df = generate_experiment_data()
    df.to_csv("experiment_data.csv", index=False)
    print(f"Generated {len(df)} rows -> experiment_data.csv")
    print(df.groupby("variant")[["purchased", "refunded"]].mean())