"""
experiment_manager.py
Manages multiple experiments: metadata, sample progress, conflicts.
Does NOT do traffic allocation or bucketing.
"""

import pandas as pd
from decision_engine import evaluate_experiment
from guardrails_engine import check_sample_size


def load_registry(path: str = "experiments.csv") -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["start_date", "end_date"])


def evaluate_all(registry: pd.DataFrame) -> pd.DataFrame:
    """Runs evaluate_experiment() for each row, returns summary table."""
    results = []
    for _, row in registry.iterrows():
        data_path = f"{row['experiment_name'].replace(' ', '_')}_data.csv"
        try:
            df = pd.read_csv(data_path)
        except FileNotFoundError:
            results.append({**row, "decision": "No Data", "sample_progress": 0})
            continue

        control_n = len(df[df["variant"] == "control"])
        variant_n = len(df[df["variant"] == "variant"])
        sample_check = check_sample_size(
            control_n, variant_n,
            baseline_rate=row["baseline"] / 100,
            mde=row["mde"] / 100,
        )
        progress = min(round(min(control_n, variant_n) / sample_check["required_per_group"] * 100), 100)

        if row["status"] == "Running" and not sample_check["passed"]:
            decision = "Collect More Data"
        else:
            outcome = evaluate_experiment(df, baseline_conversion=row["baseline"] / 100, mde=row["mde"] / 100)
            decision = outcome["decision"]

        results.append({
            "experiment_name": row["experiment_name"],
            "status": row["status"],
            "sample_progress": progress,
            "decision": decision,
            "component": row["component"],
        })

    return pd.DataFrame(results)


def check_conflicts(registry: pd.DataFrame) -> list[dict]:
    """Flags pairs of Running experiments sharing a component with overlapping dates."""
    conflicts = []
    running = registry[registry["status"] == "Running"]

    for i, a in running.iterrows():
        for j, b in running.iterrows():
            if i >= j:
                continue
            same_component = a["component"] == b["component"]
            dates_overlap = a["start_date"] <= b["end_date"] and b["start_date"] <= a["end_date"]
            if same_component and dates_overlap:
                conflicts.append({
                    "experiment_a": a["experiment_name"],
                    "experiment_b": b["experiment_name"],
                    "component": a["component"],
                })
    return conflicts


if __name__ == "__main__":
    registry = load_registry()
    print(evaluate_all(registry))
    print("Conflicts:", check_conflicts(registry))