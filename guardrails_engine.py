"""
guardrails_engine.py
The "trust check" layer — runs BEFORE any metrics or statistics.
Answers one question: "Can we trust this experiment's data enough
to even analyze it?"

Four checks, each independent:
1. check_srm            -> was the traffic split fair?
2. check_sample_size    -> do we have enough users yet?
3. check_guardrail_metric -> did a "bad news" metric get worse?
4. check_segments       -> does the result agree across user segments?
"""

import pandas as pd
from scipy.stats import chisquare
from statsmodels.stats.proportion import proportions_ztest
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize


def check_srm(n_control: int, n_variant: int, expected_ratio: float = 0.5, alpha: float = 0.001) -> dict:
    """
    Sample Ratio Mismatch check.
    Compares observed split (n_control vs n_variant) against the
    expected split using a chi-square goodness-of-fit test.

    Note: alpha is deliberately stricter (0.001) than normal significance
    testing, because false SRM alarms are costly and real SRM issues
    tend to be large, obvious deviations — not borderline ones.
    """
    total = n_control + n_variant
    expected_control = total * expected_ratio
    expected_variant = total * (1 - expected_ratio)

    stat, p_value = chisquare(
        f_obs=[n_control, n_variant],
        f_exp=[expected_control, expected_variant],
    )

    passed = p_value >= alpha

    return {
        "check": "Sample Ratio Mismatch (SRM)",
        "passed": bool(passed),
        "p_value": round(p_value, 5),
        "observed": {"control": n_control, "variant": n_variant},
        "expected": {"control": round(expected_control), "variant": round(expected_variant)},
        "message": (
            "Traffic split looks fair."
            if passed
            else "Traffic split is significantly off — investigate assignment/tracking before trusting any result."
        ),
    }


def check_sample_size(
    n_control: int,
    n_variant: int,
    baseline_rate: float,
    mde: float = 0.02,
    alpha: float = 0.05,
    power: float = 0.8,
) -> dict:
    """
    Checks whether we have enough users to reliably detect the
    minimum effect size we care about (mde), given the baseline rate.

    mde: the smallest lift worth detecting, e.g. 0.02 = 2 percentage points.
    """
    effect_size = proportion_effectsize(baseline_rate, baseline_rate + mde)
    analysis = NormalIndPower()
    required_n_per_group = analysis.solve_power(
        effect_size=abs(effect_size), alpha=alpha, power=power, ratio=1.0
    )
    required_n_per_group = int(round(required_n_per_group))

    current_min = min(n_control, n_variant)
    passed = current_min >= required_n_per_group

    return {
        "check": "Sample Size",
        "passed": bool(passed),
        "required_per_group": required_n_per_group,
        "current_control": n_control,
        "current_variant": n_variant,
        "message": (
            "Enough data collected to trust a conclusion."
            if passed
            else f"Not enough data yet — need ~{required_n_per_group} per group, "
                 f"currently have {current_min}. Keep running."
        ),
    }


def check_guardrail_metric(
    control_successes: int,
    control_total: int,
    variant_successes: int,
    variant_total: int,
    metric_name: str = "Refund Rate",
    higher_is_bad: bool = True,
    alpha: float = 0.05,
) -> dict:
    """
    Checks a "bad news" metric (e.g. refund rate) the same way we'd
    check the primary metric — via a two-proportion z-test.
    Flags only if the Variant is SIGNIFICANTLY worse, not just
    numerically different.
    """
    count = [control_successes, variant_successes]
    nobs = [control_total, variant_total]
    stat, p_value = proportions_ztest(count, nobs)

    control_rate = control_successes / control_total
    variant_rate = variant_successes / variant_total

    got_worse = (variant_rate > control_rate) if higher_is_bad else (variant_rate < control_rate)
    passed = not (got_worse and p_value < alpha)

    return {
        "check": f"Guardrail Metric: {metric_name}",
        "passed": bool(passed),
        "p_value": round(p_value, 5),
        "control_rate": round(control_rate, 4),
        "variant_rate": round(variant_rate, 4),
        "message": (
            f"{metric_name} did not significantly worsen."
            if passed
            else f"{metric_name} got significantly worse in Variant ({control_rate:.1%} -> {variant_rate:.1%}). "
                 "This could offset the primary metric's gains — investigate before shipping."
        ),
    }


def check_segments(df: pd.DataFrame, segment_col: str = "segment", outcome_col: str = "purchased") -> dict:
    """
    Checks whether the direction of the effect (Variant better/worse
    than Control) agrees across segments (e.g. new vs returning users).
    Flags disagreement -> possible Simpson's Paradox.
    """
    results = {}
    for segment_value, segment_df in df.groupby(segment_col):
        control = segment_df[segment_df["variant"] == "control"]
        variant = segment_df[segment_df["variant"] == "variant"]

        control_rate = control[outcome_col].mean()
        variant_rate = variant[outcome_col].mean()

        results[segment_value] = {
            "control_rate": round(control_rate, 4),
            "variant_rate": round(variant_rate, 4),
            "direction": "variant_better" if variant_rate > control_rate else "control_better",
        }

    directions = {seg["direction"] for seg in results.values()}
    agree = len(directions) == 1

    return {
        "check": "Segment Agreement",
        "passed": bool(agree),
        "segments": results,
        "message": (
            "All segments agree on the direction of the effect."
            if agree
            else "Segments DISAGREE on direction — the aggregate result may be misleading (Simpson's Paradox risk)."
        ),
    }


def run_guardrails(df: pd.DataFrame, baseline_conversion: float = 0.10, mde: float = 0.02) -> list[dict]:
    """
    Runs all four guardrail checks on a raw experiment dataframe
    (the kind produced by data_generator.py) and returns a list of
    result dicts, one per check.
    """
    control = df[df["variant"] == "control"]
    variant = df[df["variant"] == "variant"]

    results = []

    results.append(check_srm(len(control), len(variant)))

    results.append(
        check_sample_size(len(control), len(variant), baseline_rate=baseline_conversion, mde=mde)
    )

    results.append(
        check_guardrail_metric(
            control_successes=control["refunded"].sum(),
            control_total=control["purchased"].sum(),
            variant_successes=variant["refunded"].sum(),
            variant_total=variant["purchased"].sum(),
            metric_name="Refund Rate",
        )
    )

    results.append(check_segments(df))

    return results


if __name__ == "__main__":
    df = pd.read_csv("experiment_data.csv")
    for result in run_guardrails(df):
        status = "PASS" if result["passed"] else "FAIL"
        print(f"[{status}] {result['check']}: {result['message']}")