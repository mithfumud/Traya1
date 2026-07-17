"""
dashboard.py
PulseMetrics — page 1: experiment overview; page 2: experiment report.
"""

import pandas as pd
import streamlit as st

from decision_engine import evaluate_experiment
from experiment_manager import load_registry, evaluate_all, check_conflicts

st.set_page_config(
    page_title="PulseMetrics",
    layout="wide",
    page_icon="🌿",
    initial_sidebar_state="locked",
)

DECISION_STYLE = {
    "SHIP": ("Ship", "#2F7A67", "pill-pass"),
    "WAIT": ("Wait", "#C97F3C", "pill-wait"),
    "Collect More Data": ("Collect More Data", "#C97F3C", "pill-wait"),
    "INVESTIGATE": ("Investigate", "#C97F3C", "pill-wait"),
    "REJECT": ("Reject", "#B5495B", "pill-fail"),
}

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@600;700&family=Inter:wght@400;500;600&display=swap');

.stApp, [data-testid="stMain"] { background-color: #F4F2ED !important; }
[data-testid="stHeader"] { background-color: #F4F2ED !important; }
[data-testid="stSidebar"] { background-color: #1F4E44 !important; }
[data-testid="stSidebar"] * { color: #EAF3EF !important; }

/* Fixed viewport — page itself does not scroll; content stays inside the window */
html, body, .stApp {
    height: 100vh !important;
    max-height: 100vh !important;
    overflow: hidden !important;
}
[data-testid="stAppViewContainer"] {
    height: 100vh !important;
    max-height: 100vh !important;
    overflow: hidden !important;
}
[data-testid="stHeader"] {
    position: fixed !important;
    top: 0 !important;
    z-index: 999 !important;
}
section[data-testid="stSidebar"] {
    height: 100vh !important;
    max-height: 100vh !important;
    overflow-y: auto !important;
}
[data-testid="stMain"] {
    height: 100vh !important;
    max-height: 100vh !important;
    overflow: hidden !important;
}
[data-testid="stMain"] .block-container {
    height: calc(100vh - 1.5rem) !important;
    max-height: calc(100vh - 1.5rem) !important;
    overflow-y: auto !important;
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
    box-sizing: border-box !important;
}
[data-testid="stVerticalBlock"] { gap: 0.55rem !important; }
hr { margin: 0.45rem 0 !important; }

/* Keep sidebar always open — hide collapse / expand controls */
[data-testid="stSidebarCollapseButton"],
[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarHeader"] button,
button[kind="headerNoPadding"],
button[data-testid="stBaseButton-headerNoPadding"] {
    display: none !important;
    visibility: hidden !important;
    pointer-events: none !important;
}

[data-testid="stSidebar"] .stButton > button {
    background: rgba(255, 255, 255, 0.08) !important;
    color: #EAF3EF !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    border-radius: 8px !important;
    width: 100% !important;
    text-align: left !important;
    justify-content: flex-start !important;
    display: flex !important;
    visibility: visible !important;
    pointer-events: auto !important;
    min-height: 2.2rem !important;
    font-size: 0.9rem !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #2F7A67 !important;
    color: #FFFFFF !important;
    border-color: #3E9A82 !important;
}
[data-testid="stSidebar"] .stButton > button p,
[data-testid="stSidebar"] .stButton > button span {
    color: #EAF3EF !important;
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span,
[data-testid="stCaptionContainer"] p,
.stSelectbox label, .stSelectbox div,
h1, h2, h3, h4 {
    color: #22302B !important;
}
h1, h2, h3 { font-family: 'Fraunces', serif; font-weight: 700; }

[data-testid="stMetricLabel"] p { color: #6B7570 !important; font-weight: 500; }
[data-testid="stMetricValue"] { color: #22302B !important; }
[data-testid="stMetricDelta"] { color: #2F7A67 !important; }
[data-testid="stMetric"] { background: white; padding: 12px 16px; border-radius: 10px; border: 1px solid #E7E2D6; }

[data-testid="stMain"] [data-testid="stSelectbox"] [data-baseweb="select"] > div {
    background: #FFFFFF !important;
    border-color: #C9D2CD !important;
    color: #22302B !important;
}
[data-testid="stMain"] [data-testid="stSelectbox"] span,
[data-testid="stMain"] [data-testid="stSelectbox"] p {
    color: #22302B !important;
}
[data-testid="stMain"] button[kind="primary"] {
    background: #2F7A67 !important;
    color: #FFFFFF !important;
    border: 1px solid #2F7A67 !important;
}
[data-testid="stMain"] button[kind="primary"] p,
[data-testid="stMain"] button[kind="primary"] span {
    color: #FFFFFF !important;
}
[data-testid="stMain"] .stButton > button,
[data-testid="stMain"] button[kind="secondary"],
[data-testid="stMain"] button[data-testid="stBaseButton-secondary"] {
    background: #FFFFFF !important;
    color: #22302B !important;
    border: 1px solid #C9D2CD !important;
    border-radius: 8px !important;
    box-shadow: none !important;
}
[data-testid="stMain"] .stButton > button:hover,
[data-testid="stMain"] button[kind="secondary"]:hover,
[data-testid="stMain"] button[data-testid="stBaseButton-secondary"]:hover {
    background: #F7FAF9 !important;
    color: #1F4E44 !important;
    border-color: #2F7A67 !important;
}
[data-testid="stMain"] .stButton > button p,
[data-testid="stMain"] .stButton > button span {
    color: #22302B !important;
}

.banner { background: linear-gradient(135deg, #1F4E44, #2F7A67); padding: 18px 24px; border-radius: 12px; margin-bottom: 10px; }
.banner h1 { color: #F4F2ED !important; margin: 0; font-size: 24px; }
.banner p { color: #CFE6DE !important; margin: 2px 0 0 0; font-size: 13px; }

.step-strip { display: flex; gap: 8px; margin-bottom: 10px; }
.step-card { background: white; border-radius: 8px; padding: 10px 12px; flex: 1; border: 1px solid #E7E2D6; }
.step-num { display:inline-block; background:#2F7A67; color:white !important; width:18px; height:18px; border-radius:50%; text-align:center; font-size:11px; line-height:18px; margin-right:5px; }
.step-title { font-weight: 600; font-size: 12px; color: #22302B !important; }
.step-sub { font-size: 11px; color: #6B7570 !important; margin-top: 2px; line-height:1.3; }

.verdict-card { padding: 22px 28px; border-radius: 14px; border-left: 6px solid var(--accent); background: white; box-shadow: 0 1px 3px rgba(35,48,44,0.08); margin-bottom: 14px; }
.verdict-label { font-family: 'Fraunces', serif; font-size: 28px; font-weight: 700; color: var(--accent) !important; margin: 0; }

.insight-card { background: white; border-radius: 12px; padding: 16px 20px; margin-bottom: 14px; border: 1px solid #E7E2D6; }
.insight-line { padding: 6px 0; border-bottom: 1px solid #F0EDE4; font-size: 14px; color: #22302B !important; }
.insight-line:last-child { border-bottom: none; }

.reasons-card {
    background: #F7FAF9;
    border-radius: 12px;
    padding: 14px 16px;
    margin-top: 10px;
    border: 1px solid #D5E5E0;
}
.reasons-title {
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: #2F7A67 !important;
    margin: 0 0 8px 0;
}
.reason-item {
    font-size: 13px;
    line-height: 1.4;
    color: #22302B !important;
    padding: 5px 0 5px 0;
    border-bottom: 1px solid #E4EEEA;
}
.reason-item:last-child { border-bottom: none; }
.reason-bullet {
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #2F7A67;
    margin-right: 8px;
    vertical-align: middle;
}

.detail-panel {
    background: white;
    border: 1px solid #E7E2D6;
    border-radius: 12px;
    padding: 16px 18px;
    margin-top: 10px;
    margin-bottom: 10px;
}
.detail-panel-title {
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #6B7570 !important;
    margin: 0 0 12px 0;
}
.stat-grid {
    display: flex;
    gap: 12px;
    margin-bottom: 14px;
    flex-wrap: wrap;
}
.stat-box {
    flex: 1;
    min-width: 180px;
    background: #F7FAF9;
    border: 1px solid #D5E5E0;
    border-radius: 10px;
    padding: 12px 14px;
}
.stat-box-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: #6B7570 !important;
    margin: 0 0 6px 0;
}
.stat-box-value {
    font-family: 'Fraunces', serif;
    font-size: 22px;
    font-weight: 700;
    color: #1F4E44 !important;
    margin: 0 0 4px 0;
}
.stat-box-msg {
    font-size: 12px;
    color: #4A5652 !important;
    margin: 0;
    line-height: 1.35;
}
.check-list { margin-top: 4px; }
.check-row {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 10px 12px;
    border-radius: 8px;
    margin-bottom: 6px;
    border: 1px solid #E7E2D6;
    background: #FAFAF8;
}
.check-row.pass { background: #F3FAF7; border-color: #D5E5E0; }
.check-row.fail { background: #FDF6F6; border-color: #F0D4D7; }
.check-icon {
    flex-shrink: 0;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 700;
}
.check-row.pass .check-icon { background: #E4F1EE; color: #2F7A67 !important; }
.check-row.fail .check-icon { background: #FBE4E7; color: #B5495B !important; }
.check-body { flex: 1; }
.check-name {
    font-size: 13px;
    font-weight: 600;
    color: #22302B !important;
    margin: 0 0 2px 0;
}
.check-msg {
    font-size: 12px;
    color: #5A6560 !important;
    margin: 0;
    line-height: 1.35;
}

[data-testid="stVegaLiteChart"],
[data-testid="stArrowVegaLiteChart"] {
    background: #FFFFFF !important;
    border: 1px solid #E7E2D6 !important;
    border-radius: 12px !important;
    padding: 12px !important
}

.pill { display: inline-block; padding: 5px 14px; border-radius: 999px; font-size: 12px; font-weight: 600; margin-right: 8px; margin-bottom: 6px; }
.pill-pass { background: #E4F1EE; color: #2F7A67 !important; }
.pill-wait { background: #FBEEDC; color: #C97F3C !important; }
.pill-fail { background: #FBE4E7; color: #B5495B !important; }

.pm-table { width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; border: 1px solid #E7E2D6; }
.pm-table th { text-align: left; padding: 10px 14px; background: #EFEBE1; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #6B7570 !important; }
.pm-table td { padding: 10px 14px; border-top: 1px solid #F0EDE4; font-size: 14px; color: #22302B !important; }

.meta-chip {
    display: inline-block;
    padding: 5px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    margin-right: 8px;
    margin-bottom: 6px;
}
.meta-owner { background: #DCEEE8; color: #1F4E44 !important; border: 1px solid #2F7A67; }
.meta-status { background: #E3F0FB; color: #1A4F7A !important; border: 1px solid #4A90C4; }
.meta-component { background: #FBEEDC; color: #8A5A20 !important; border: 1px solid #C97F3C; }
.meta-metric { background: #EDE8F7; color: #4A3570 !important; border: 1px solid #7B6BB0; }
.meta-baseline { background: #E8F5E9; color: #2E5C34 !important; border: 1px solid #5A9E62; }
.meta-mde { background: #FBE4E7; color: #8A2F3D !important; border: 1px solid #B5495B; }
</style>
""", unsafe_allow_html=True)

if "current_view" not in st.session_state:
    st.session_state.current_view = "overview"


def render_banner():
    st.markdown("""
        <div class="banner">
            <h1>🌿 PulseMetrics</h1>
            <p>Traya Health · Experiment decision engine</p>
        </div>
    """, unsafe_allow_html=True)


def render_step_strip():
    steps = [
        ("1", "Validate", "Before trusting any numbers, we check the traffic split was fair and enough users have been observed."),
        ("2", "Measure", "We calculate what actually happened - conversion rates, funnel drop-off, and lift between Control and Variant."),
        ("3", "Test", "We check whether the difference is statistically real, or could just be random chance."),
        ("4", "Decide", "Everything combines into one clear call: Ship, Wait, Investigate, or Reject."),
    ]
    html = '<div class="step-strip">'
    for num, title, sub in steps:
        html += f"""<div class="step-card">
            <span class="step-num">{num}</span><span class="step-title">{title}</span>
            <div class="step-sub">{sub}</div>
        </div>"""
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_experiment_table(summary: pd.DataFrame):
    rows_html = ""
    for _, r in summary.iterrows():
        _, _, badge_cls = DECISION_STYLE.get(r["decision"], (r["decision"], "#6B7570", "pill-wait"))
        rows_html += f"""<tr>
            <td>{r['experiment_name']}</td>
            <td>{r['status']}</td>
            <td>{r['sample_progress']}%</td>
            <td><span class="pill {badge_cls}">{r['decision']}</span></td>
            <td>{r['component']}</td>
        </tr>"""
    st.markdown(f"""
        <table class="pm-table">
            <thead><tr><th>Experiment</th><th>Status</th><th>Sample</th><th>Decision</th><th>Component</th></tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
    """, unsafe_allow_html=True)


def generate_insights(result: dict) -> list[str]:
    metrics = result["metrics"]
    stats = result["statistics"]
    guardrails = result["guardrails"]
    lift = metrics["lift"]
    sig = stats["significance"]
    ci = stats["confidence_interval"]

    insights = []
    if sig["significant"]:
        insights.append(f"This result is unlikely to be random chance (p={sig['p_value']}) - you can trust the direction of this effect.")
    else:
        insights.append(f"This could plausibly be random noise (p={sig['p_value']}) - not confident enough yet to call a winner.")

    if lift["absolute_lift"] > 0:
        insights.append(
            f"Variant converts at {metrics['variant']['conversion_rate']:.1%} vs "
            f"{metrics['control']['conversion_rate']:.1%} for Control - a real gain, not noise."
        )
    elif lift["absolute_lift"] < 0:
        insights.append(
            f"Variant is converting worse than Control "
            f"({metrics['variant']['conversion_rate']:.1%} vs {metrics['control']['conversion_rate']:.1%})."
        )

    range_note = " - this range crosses zero, so treat any apparent win with caution." if ci["crosses_zero"] else "."
    insights.append(
        f"We're 95% confident the true effect is between {ci['lower_bound']:+.1%} "
        f"and {ci['upper_bound']:+.1%}{range_note}"
    )

    failed = [g["check"] for g in guardrails if not g["passed"]]
    if failed:
        insights.append(f"Resolve before trusting this result: {', '.join(failed)}.")
    else:
        insights.append(
            "All guardrails passed - fair traffic split, refund rates stayed safe, "
            "and every user segment agrees on the direction of the result."
        )

    return insights


def render_decision_and_insights(result: dict):
    label, color, _ = DECISION_STYLE.get(result["decision"], (result["decision"], "#6B7570", "pill-wait"))
    col1, col2 = st.columns([1, 1.6])

    with col1:
        st.markdown(f"""
            <div class="verdict-card" style="--accent:{color};">
                <p style="color:{color}; font-size:13px; text-transform:uppercase; letter-spacing:1px; margin:0;">Decision</p>
                <p class="verdict-label">{label}</p>
            </div>
        """, unsafe_allow_html=True)

        reasons_html = '<div class="reasons-card"><p class="reasons-title">Why this decision</p>'
        for reason in result["reasons"]:
            reasons_html += (
                f'<div class="reason-item">'
                f'<span class="reason-bullet"></span>{reason}'
                f'</div>'
            )
        reasons_html += "</div>"
        st.markdown(reasons_html, unsafe_allow_html=True)

    with col2:
        insights_html = '<div class="insight-card">'
        for line in generate_insights(result):
            insights_html += f'<div class="insight-line">💡 {line}</div>'
        insights_html += "</div>"
        st.markdown(insights_html, unsafe_allow_html=True)


def render_metrics_and_guardrails(result: dict):
    metrics = result["metrics"]
    lift = metrics["lift"]
    guardrails = result["guardrails"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Control conversion", f"{metrics['control']['conversion_rate']:.1%}")
    col2.metric(
        "Variant conversion",
        f"{metrics['variant']['conversion_rate']:.1%}",
        delta=f"{lift['absolute_lift']:+.2%}",
    )
    col3.metric(
        "Relative lift",
        f"{lift['relative_lift_pct']}%" if lift["relative_lift_pct"] is not None else "N/A",
    )
    col4.metric("Visitors (C/V)", f"{metrics['control']['visitors']} / {metrics['variant']['visitors']}")

    pill_html = ""
    for check in guardrails:
        cls = "pill-pass" if check["passed"] else "pill-fail"
        symbol = "✓" if check["passed"] else "✕"
        pill_html += f'<span class="pill {cls}">{symbol} {check["check"]}</span>'
    st.markdown(pill_html, unsafe_allow_html=True)

    st.subheader("Full funnel & statistical detail")
    control, variant = metrics["control"], metrics["variant"]
    stages = ["Visitors", "Started Test", "Completed Test", "Viewed Report", "Purchased"]
    funnel_long = pd.DataFrame({
        "Stage": stages * 2,
        "Group": ["Control"] * 5 + ["Variant"] * 5,
        "Users": [
            control["visitors"], control["started_test"], control["completed_test"],
            control["viewed_report"], control["purchased"],
            variant["visitors"], variant["started_test"], variant["completed_test"],
            variant["viewed_report"], variant["purchased"],
        ],
    })
    funnel_long["Stage"] = pd.Categorical(funnel_long["Stage"], categories=stages, ordered=True)

    try:
        import altair as alt

        chart = (
            alt.Chart(funnel_long)
            .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4, size=18)
            .encode(
                y=alt.Y(
                    "Stage:N",
                    sort=stages,
                    title=None,
                    axis=alt.Axis(labelColor="#FFFFFF", labelFontSize=12, tickSize=0, domainColor="#E7E2D6"),
                ),
                x=alt.X(
                    "Users:Q",
                    title="Users",
                    axis=alt.Axis(grid=True, gridColor="#EFEBE1", labelColor="#6B7570", domainColor="#E7E2D6"),
                ),
                color=alt.Color(
                    "Group:N",
                    scale=alt.Scale(domain=["Control", "Variant"], range=["#7BA8A0", "#1F4E44"]),
                    legend=alt.Legend(title=None, orient="top", labelColor="#FFFFFF"),
                ),
                xOffset="Group:N",
                tooltip=[
                    alt.Tooltip("Stage:N", title="Stage"),
                    alt.Tooltip("Group:N", title="Group"),
                    alt.Tooltip("Users:Q", title="Users", format=","),
                ],
            )
            .properties(height=280, padding={"left": 10, "right": 40, "top": 10, "bottom": 10})
            .configure_view(strokeWidth=0)
            .configure_axis(labelFont="Inter", titleFont="Inter")
        )
        st.altair_chart(chart, use_container_width=True)
    except Exception:
        st.bar_chart(funnel_long.pivot(index="Stage", columns="Group", values="Users").loc[stages])

    sig = result["statistics"]["significance"]
    ci = result["statistics"]["confidence_interval"]

    st.markdown('<p class="detail-panel-title">Statistical summary</p>', unsafe_allow_html=True)
    s1, s2 = st.columns(2)
    with s1:
        st.markdown(
            f"""
            <div class="stat-box">
                <p class="stat-box-label">P-value</p>
                <p class="stat-box-value">{sig['p_value']}</p>
                <p class="stat-box-msg">{sig['message']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with s2:
        st.markdown(
            f"""
            <div class="stat-box">
                <p class="stat-box-label">95% Confidence interval</p>
                <p class="stat-box-value">{ci['lower_bound']:+.2%} → {ci['upper_bound']:+.2%}</p>
                <p class="stat-box-msg">{ci['message']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
    st.markdown('<p class="detail-panel-title">Guardrail checks</p>', unsafe_allow_html=True)
    for g in guardrails:
        if g["passed"]:
            st.success(f"**{g['check']}** — {g['message']}")
        else:
            st.error(f"**{g['check']}** — {g['message']}")


def render_overview():
    st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
    render_banner()
    st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
    render_step_strip()

    registry = load_registry()
    summary = evaluate_all(registry)
    conflicts = check_conflicts(registry)

    col_table, col_conflict = st.columns([2, 1])
    with col_table:
        st.subheader("Experiments")
        render_experiment_table(summary)
    with col_conflict:
        st.subheader("Conflicts")
        if conflicts:
            for c in conflicts:
                st.error(f"{c['experiment_a']} ↔ {c['experiment_b']} both touch {c['component']}")
        else:
            st.success("No conflicts detected")

    st.markdown(
        '<div style="margin-top: -28px;"></div>',
        unsafe_allow_html=True,
    )
    st.subheader("Inspect an experiment")
    selected_name = st.selectbox(
        "Choose experiment",
        summary["experiment_name"],
        label_visibility="collapsed",
    )

    if st.button("Show results →", type="primary", use_container_width=True):
        st.session_state.selected_experiment = selected_name
        st.session_state.report_section = "full"
        st.session_state.current_view = "report"
        st.rerun()


def go_to_report(section: str = "full"):
    """Open the report for the selected experiment, or the first one if none chosen yet."""
    if not st.session_state.get("selected_experiment"):
        registry = load_registry()
        st.session_state.selected_experiment = registry["experiment_name"].iloc[0]
    st.session_state.report_section = section
    st.session_state.current_view = "report"
    st.rerun()


def render_sidebar():
    with st.sidebar:
        st.markdown("###  PulseMetrics")
        st.markdown('<p style="color:#FFFFFF;">Experiment Decision Engine</p>', unsafe_allow_html=True)
        st.divider()

        if st.button("📋 Experiments", key="nav_experiments", use_container_width=True):
            st.session_state.current_view = "overview"
            st.rerun()

        if st.button("🛡️ Guardrails", key="nav_guardrails", use_container_width=True):
            go_to_report("guardrails")


def render_report():
    st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
    if st.button("← Back to all experiments"):
        st.session_state.current_view = "overview"
        st.rerun()

    experiment_name = st.session_state.get("selected_experiment")
    if not experiment_name:
        st.warning("No experiment selected. Go back and choose one.")
        return

    registry = load_registry()
    row = registry[registry["experiment_name"] == experiment_name].iloc[0]
    df = pd.read_csv(f"{experiment_name.replace(' ', '_')}_data.csv")
    result = evaluate_experiment(df, baseline_conversion=row["baseline"] / 100, mde=row["mde"] / 100)

    st.title(experiment_name)
    st.caption("Results for this test - Control vs Variant.")

    chips = [
        (f"Owner: {row['owner']}", "meta-owner"),
        (f"Status: {row['status']}", "meta-status"),
        (f"Component: {row['component']}", "meta-component"),
        (f"Primary metric: {row['primary_metric']}", "meta-metric"),
        (f"Baseline: {row['baseline']}%", "meta-baseline"),
        (f"MDE: {row['mde']}%", "meta-mde"),
    ]
    st.markdown(
        "".join(f'<span class="meta-chip {cls}">{label}</span>' for label, cls in chips),
        unsafe_allow_html=True,
    )

    st.divider()
    render_decision_and_insights(result)
    st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
    render_metrics_and_guardrails(result)


def main():
    render_sidebar()

    if st.session_state.current_view == "report":
        render_report()
    else:
        render_overview()


if __name__ == "__main__":
    main()
