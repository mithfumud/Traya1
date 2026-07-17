# PulseMetrics

An internal experimentation decision-support platform, inspired by how
companies like Netflix and Microsoft evaluate A/B tests.

Instead of just calculating conversion rates, PulseMetrics validates
experiment quality (Sample Ratio Mismatch, minimum sample size, guardrail
metrics, segment analysis) before determining whether an experiment
should be shipped.

Simulated use case: Traya Health's "Success Stories above the fold" experiment.

## Structure
- `data_generator.py` — synthetic experiment data
- `guardrails_engine.py` — trust checks (SRM, sample size, guardrail metrics, segments)
- `metrics_engine.py` — conversion, lift, funnel metrics
- `statistics_engine.py` — significance testing
- `decision_engine.py` — combines everything into Ship/Wait/Investigate/Reject
- `dashboard.py` — Streamlit UI
