"""
decision_engine.py
The "final verdict" layer — combines Guardrails + Metrics + Statistics
into one recommendation: SHIP, WAIT, INVESTIGATE, or REJECT.

This is the only output a Product Manager actually needs to see first;
everything else (guardrails, metrics, stats) exists to justify this
one decision transparently.
"""

import pandas as pd

from guardrails_engine import run_guardrails
from metrics_engine import run_metrics
from statistics_engine import run_statistics


def make_decision(guardrail_results: list[dict], metrics_results: dict, stats_results: dict) -> dict:
    """
    Decision logic, in priority order:

    1. If ANY guardrail fails in a way that makes data untrustworthy
       (SRM or Sample Size) -> INVESTIGATE / WAIT, don't even look at stats.
    2. If a guardrail METRIC (e.g. refund rate) got significantly worse
       -> REJECT, regardless of how good the primary metric looks.
    3. If segments disagree -> INVESTIGATE (don't blindly ship to everyone).
    4. Otherwise, defer to statistical significance:
       - Significant + positive lift -> SHIP
       - Not significant -> WAIT (need more data / more time)
       - Significant + negative lift -> REJECT
    """
    guardrail_map = {g["check"]: g for g in guardrail_results}

    srm = guardrail_map["Sample Ratio Mismatch (SRM)"]
    sample_size = guardrail_map["Sample Size"]
    refund_guardrail = guardrail_map["Guardrail Metric: Refund Rate"]
    segments = guardrail_map["Segment Agreement"]

    reasons = []

    # --- Step 1: data trustworthiness gates ---
    if not srm["passed"]:
        reasons.append(srm["message"])
        return _verdict("INVESTIGATE", reasons, guardrail_results, metrics_results, stats_results)

    if not sample_size["passed"]:
        reasons.append(sample_size["message"])
        return _verdict("WAIT", reasons, guardrail_results, metrics_results, stats_results)

    # --- Step 2: guardrail metric gate ---
    if not refund_guardrail["passed"]:
        reasons.append(refund_guardrail["message"])
        return _verdict("REJECT", reasons, guardrail_results, metrics_results, stats_results)

    # --- Step 3: segment agreement gate ---
    if not segments["passed"]:
        reasons.append(segments["message"])
        return _verdict("INVESTIGATE", reasons, guardrail_results, metrics_results, stats_results)

    # --- Step 4: statistical verdict ---
    significance = stats_results["significance"]
    lift = metrics_results["lift"]

    if significance["significant"] and lift["absolute_lift"] > 0:
        reasons.append(significance["message"])
        reasons.append(f"Positive lift of {lift['relative_lift_pct']}% observed.")
        return _verdict("SHIP", reasons, guardrail_results, metrics_results, stats_results)

    if significance["significant"] and lift["absolute_lift"] < 0:
        reasons.append(significance["message"])
        reasons.append("Effect is significant but NEGATIVE — Variant underperforms Control.")
        return _verdict("REJECT", reasons, guardrail_results, metrics_results, stats_results)

    reasons.append(significance["message"])
    reasons.append("Data is trustworthy, but the result isn't conclusive yet.")
    return _verdict("WAIT", reasons, guardrail_results, metrics_results, stats_results)


def _verdict(decision: str, reasons: list[str], guardrail_results, metrics_results, stats_results) -> dict:
    """Packages the final verdict with everything that justified it."""
    return {
        "decision": decision,
        "reasons": reasons,
        "guardrails": guardrail_results,
        "metrics": metrics_results,
        "statistics": stats_results,
    }


def evaluate_experiment(df: pd.DataFrame, baseline_conversion: float = 0.10, mde: float = 0.02) -> dict:
    """
    The single entry point: takes raw experiment data and returns
    the full verdict, ready for the dashboard to display.
    """
    guardrail_results = run_guardrails(df, baseline_conversion=baseline_conversion, mde=mde)
    metrics_results = run_metrics(df)
    stats_results = run_statistics(df)

    return make_decision(guardrail_results, metrics_results, stats_results)


if __name__ == "__main__":
    df = pd.read_csv("experiment_data.csv")
    result = evaluate_experiment(df)

    print(f"\n{'='*50}")
    print(f"DECISION: {result['decision']}")
    print(f"{'='*50}")
    for reason in result["reasons"]:
        print(f"- {reason}")