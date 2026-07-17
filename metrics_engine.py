"""
metrics_engine.py
The "what happened" layer — pure facts, no judgments.
Runs AFTER guardrails pass. Computes funnel metrics, conversion,
and lift for Control vs Variant.
"""

import pandas as pd


def compute_funnel_metrics(df: pd.DataFrame, variant_label: str) -> dict:
    """
    Computes step-by-step funnel counts and rates for one variant
    (e.g. all 'control' rows or all 'variant' rows).
    """
    group = df[df["variant"] == variant_label]
    total = len(group)

    started = group["started_test"].sum()
    completed = group["completed_test"].sum()
    viewed_report = group["viewed_report"].sum()
    purchased = group["purchased"].sum()

    return {
        "variant": variant_label,
        "visitors": total,
        "started_test": int(started),
        "completed_test": int(completed),
        "viewed_report": int(viewed_report),
        "purchased": int(purchased),
        "form_fill_rate": round(completed / total, 4) if total else 0,
        "conversion_rate": round(purchased / total, 4) if total else 0,
        "report_to_purchase_rate": round(purchased / viewed_report, 4) if viewed_report else 0,
    }


def compute_lift(control_metrics: dict, variant_metrics: dict, metric_key: str = "conversion_rate") -> dict:
    """
    Computes absolute and relative lift between Control and Variant
    for a given metric (default: conversion_rate).
    """
    control_value = control_metrics[metric_key]
    variant_value = variant_metrics[metric_key]

    absolute_lift = round(variant_value - control_value, 4)
    relative_lift = round((absolute_lift / control_value) * 100, 2) if control_value else None

    return {
        "metric": metric_key,
        "control_value": control_value,
        "variant_value": variant_value,
        "absolute_lift": absolute_lift,
        "relative_lift_pct": relative_lift,
    }


def run_metrics(df: pd.DataFrame) -> dict:
    """
    Runs full metrics computation for both variants plus lift summary.
    Returns a single dict ready to hand to the Statistics Engine next.
    """
    control_metrics = compute_funnel_metrics(df, "control")
    variant_metrics = compute_funnel_metrics(df, "variant")
    lift = compute_lift(control_metrics, variant_metrics)

    return {
        "control": control_metrics,
        "variant": variant_metrics,
        "lift": lift,
    }


if __name__ == "__main__":
    df = pd.read_csv("experiment_data.csv")
    results = run_metrics(df)

    print("Control:", results["control"])
    print("Variant:", results["variant"])
    print("Lift:", results["lift"])