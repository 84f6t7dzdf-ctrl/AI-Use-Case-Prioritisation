"""Streamlit app: which AI use cases should we do first?

Run with:  streamlit run app.py
"""

from pathlib import Path

import pandas as pd
import streamlit as st

import assumptions as A
from charts import quadrant_chart
from logic import apply_adjustments, criterion_help, describe_adjustments, gated_cases, rank, settings_changed, top_cases, top_changes

HERE = Path(__file__).resolve().parent
DEFAULT_CSV = HERE / "use_cases.csv"

st.set_page_config(page_title="AI use case prioritisation", layout="wide")
st.title("Which AI use cases should we do first?")

DEFAULTS = {
    "value_weight": A.VALUE_WEIGHT,
    "cutoff": A.QUADRANT_CUTOFF,
    "risk_gate": A.RISK_GATE,
    "capacity": A.CAPACITY,
}
for _key, _value in DEFAULTS.items():
    st.session_state.setdefault(_key, _value)
st.session_state.setdefault("scenario", A.DEFAULT_SCENARIO)


def load_scenario():
    """Copy the chosen scenario's assumptions into the controls."""
    scenario = A.SCENARIOS[st.session_state["scenario"]]
    for key in DEFAULTS:
        st.session_state[key] = scenario[key]


def reset_assumptions():
    st.session_state["scenario"] = A.DEFAULT_SCENARIO
    for key, value in DEFAULTS.items():
        st.session_state[key] = value


SETTING_NAMES = {
    "scores": "scenario score adjustments",
    "value_weight": "value weight",
    "cutoff": "quadrant cutoff",
    "risk_gate": "risk gate",
    "capacity": "capacity",
}

# Sidebar: data source and the assumptions behind the scores.
with st.sidebar:
    st.header("Data")
    upload = st.file_uploader("Load a CSV (same columns as use_cases.csv)", type="csv")
    st.header("Scenario")
    scenario_name = st.selectbox(
        "Example scenario (estimate)",
        list(A.SCENARIOS),
        key="scenario",
        on_change=load_scenario,
        help="Loads a set of assumptions below. You can still adjust them afterwards.",
    )
    scenario = A.SCENARIOS[scenario_name]
    st.caption(scenario["description"])
    st.header("Assumptions")
    st.caption("Every value here is an estimate. Change them to test the ranking. "
               "Defaults come from assumptions.py.")
    st.button("Reset to defaults", on_click=reset_assumptions, width="stretch")
    value_weight = st.slider(
        "Value weight (estimate)",
        min_value=A.VALUE_WEIGHT_MIN,
        max_value=A.VALUE_WEIGHT_MAX,
        step=0.05,
        key="value_weight",
        help="How much value counts in the priority score. Feasibility gets the rest.",
    )
    feasibility_weight = round(1 - value_weight, 2)
    st.caption(f"Feasibility weight: **{feasibility_weight:g}** (1 minus value weight). "
               f"Default {A.VALUE_WEIGHT:g} / {A.FEASIBILITY_WEIGHT:g}.")
    cutoff = st.slider(
        "Quadrant cutoff (estimate)",
        min_value=A.QUADRANT_CUTOFF_MIN,
        max_value=A.QUADRANT_CUTOFF_MAX,
        step=0.25,
        key="cutoff",
        help="Value or feasibility at or above this counts as high. "
             f"Default {A.QUADRANT_CUTOFF:g}.",
    )
    risk_gate = st.slider(
        "Risk gate (estimate)",
        min_value=1,
        max_value=5,
        step=1,
        key="risk_gate",
        help=f"Cases with risk at or above this must be governed first. Default {A.RISK_GATE}.",
    )
    capacity = st.number_input(
        "Capacity (estimate)",
        min_value=1,
        max_value=A.CAPACITY_MAX,
        step=1,
        key="capacity",
        help=f"How many use cases can be delivered at once. Default {A.CAPACITY}.",
    )
    with st.expander("What the scores mean"):
        for key, c in A.CRITERIA.items():
            st.markdown(f"**{c['label']}** ({c['group']})")
            st.markdown(f"- 1: {c[1]}\n- 3: {c[3]}\n- 5: {c[5]}")

source = pd.read_csv(upload) if upload is not None else pd.read_csv(DEFAULT_CSV)

missing = [c for c in ["name"] + A.SCORE_COLUMNS if c not in source.columns]
if missing:
    st.error(f"The CSV is missing these columns: {', '.join(missing)}")
    st.stop()

st.subheader("Use cases")
st.caption("Edit scores directly in the table, or add and delete rows. The ranking updates as you go. "
           "Hover a score column's heading to see what 1, 3 and 5 mean.")
score_cfg = {
    col: st.column_config.NumberColumn(
        A.CRITERIA[col]["short"], min_value=1, max_value=5, step=1,
        help=criterion_help(col),
    )
    for col in A.SCORE_COLUMNS
}
edited = st.data_editor(
    source,
    num_rows="dynamic",
    width="stretch",
    hide_index=True,
    column_config={
        "name": st.column_config.TextColumn("Name", required=True),
        "description": st.column_config.TextColumn("Description", width="medium"),
        **score_cfg,
    },
    key=f"editor_{upload.name if upload else 'default'}",
)

# Drop rows that are still being filled in.
complete = edited.dropna(subset=["name"] + A.SCORE_COLUMNS)
if len(complete) < len(edited):
    st.info(f"{len(edited) - len(complete)} row(s) with missing scores are left out of the ranking.")

adjustments = scenario["score_adjustments"]
scored_input = apply_adjustments(complete.reset_index(drop=True), adjustments)
if adjustments:
    st.info(f"**{scenario_name}** scenario: {describe_adjustments(adjustments)}. "
            "The table shows your scores; the ranking below uses the adjusted ones.")

try:
    ranked = rank(scored_input, value_weight, cutoff, risk_gate)
    default_ranked = rank(complete.reset_index(drop=True))
except ValueError as e:
    st.error(f"Could not score the table: {e}")
    st.stop()

if ranked.empty:
    st.warning("No complete use cases to rank yet.")
    st.stop()

# Top cases to start with.
st.subheader(f"Start with these {capacity}")
top = top_cases(ranked, capacity)
st.caption(
    f"Scenario: {scenario_name}. Using value weight {value_weight:g}, feasibility weight {feasibility_weight:g}, "
    f"quadrant cutoff {cutoff:.2f}, risk gate {risk_gate} and capacity {capacity}."
)
changed = settings_changed(value_weight, cutoff, risk_gate, capacity, DEFAULTS)
if adjustments:
    changed = changed + ["scores"]
if changed:
    entered, left = top_changes(top_cases(default_ranked, A.CAPACITY), top)
    changed_text = ", ".join(SETTING_NAMES[k] for k in changed)
    if entered or left:
        parts = []
        if entered:
            parts.append(f"**Enters the top:** {', '.join(entered)}")
        if left:
            parts.append(f"**Leaves the top:** {', '.join(left)}")
        st.warning(
            f"Compared with the default top {A.CAPACITY} (changed: {changed_text}):  \n"
            + "  \n".join(parts)
        )
    else:
        st.info(f"Same cases as the default top {A.CAPACITY} (changed: {changed_text}), "
                "though the order may differ.")
if top.empty:
    st.warning("Every case is gated on risk. Govern them before starting any.")
else:
    cols = st.columns(len(top))
    for col, (_, row) in zip(cols, top.iterrows()):
        with col:
            st.metric(f"#{row['rank']} {row['name']}", f"{row['priority']:.2f}")
            st.markdown(f"**{row['quadrant']}**: {row['action']}")
            st.caption(f"Value {row['value']:.2f} · Feasibility {row['feasibility']:.2f}")

# Quadrant chart.
st.subheader("Value against feasibility")
st.caption(
    f"Dashed lines mark the quadrant cutoff of {cutoff:.2f}. "
    f"Red diamonds are gated (risk {risk_gate} or higher) and need governance first. "
    "Hover a point for its scores."
)
st.altair_chart(quadrant_chart(ranked, cutoff), width="stretch")

# Full ranking. Kept narrow enough to fit a laptop screen; the working is
# shown in full below, one step per line, instead of in a wide column.
st.subheader("Full ranking")
display_cols = ["rank", "name", "value", "feasibility", "priority", "quadrant", "action"]
st.dataframe(
    ranked[display_cols],
    width="stretch",
    hide_index=True,
    column_config={
        "rank": "Rank",
        "name": "Name",
        "value": st.column_config.NumberColumn("Value", format="%.2f"),
        "feasibility": st.column_config.NumberColumn("Feasibility", format="%.2f"),
        "priority": st.column_config.NumberColumn("Priority", format="%.2f"),
        "quadrant": "Quadrant",
        "action": "Action",
    },
)

st.subheader("Working")
st.caption("How each score was worked out. Open a case to see every step.")
for _, row in ranked.iterrows():
    with st.expander(f"#{row['rank']} {row['name']}: priority {row['priority']:.2f}"):
        steps = row["working"].split("; ")
        st.markdown("\n".join(f"- {step}" for step in steps))

# Gated cases.
st.subheader("Govern first")
gated = gated_cases(ranked)
if gated.empty:
    st.success(f"No case has risk at or above {risk_gate}.")
else:
    st.caption(
        f"These cases have risk {risk_gate} or higher. They need legal, data protection "
        "and ethics review before delivery starts, whatever their priority score."
    )
    st.dataframe(
        gated[["rank", "name", "priority", "quadrant", "risk", "action"]],
        width="stretch",
        hide_index=True,
        column_config={
            "rank": "Rank",
            "name": "Name",
            "priority": st.column_config.NumberColumn("Priority", format="%.2f"),
            "quadrant": "Quadrant",
            "risk": "Risk",
            "action": "Action",
        },
    )

st.download_button(
    "Download ranking as CSV",
    ranked.to_csv(index=False).encode("utf-8"),
    file_name="ranked_use_cases.csv",
    mime="text/csv",
)
