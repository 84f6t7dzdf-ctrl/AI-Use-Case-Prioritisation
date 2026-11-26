"""Streamlit app: which AI use cases should we do first?

Run with:  streamlit run app.py
"""

from pathlib import Path

import pandas as pd
import streamlit as st

import assumptions as A
from charts import quadrant_chart
from logic import gated_cases, rank, top_cases, top_changes

HERE = Path(__file__).resolve().parent
DEFAULT_CSV = HERE / "use_cases.csv"

st.set_page_config(page_title="AI use case prioritisation", layout="wide")
st.title("Which AI use cases should we do first?")

# Sidebar: data source and the assumptions behind the scores.
with st.sidebar:
    st.header("Data")
    upload = st.file_uploader("Load a CSV (same columns as use_cases.csv)", type="csv")
    st.header("Weights")
    value_weight = st.slider(
        "Value weight",
        min_value=A.VALUE_WEIGHT_MIN,
        max_value=A.VALUE_WEIGHT_MAX,
        value=A.VALUE_WEIGHT,
        step=0.05,
        help="How much value counts in the priority score. Feasibility gets the rest.",
    )
    feasibility_weight = round(1 - value_weight, 2)
    st.caption(
        f"Feasibility weight: **{feasibility_weight:g}** (1 minus value weight). "
        f"Default is {A.VALUE_WEIGHT:g} / {A.FEASIBILITY_WEIGHT:g}."
    )
    st.header("Assumptions (estimates)")
    st.markdown(
        f"- Quadrant cutoff: **{A.QUADRANT_CUTOFF}**\n"
        f"- Risk gate: risk **>= {A.RISK_GATE}** means govern first\n"
        f"- Capacity: **{A.CAPACITY}** cases at once"
    )
    st.caption("All numbers are estimates. Change them in assumptions.py.")
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
st.caption("Edit scores directly in the table, or add and delete rows. The ranking updates as you go.")
score_cfg = {
    col: st.column_config.NumberColumn(
        A.CRITERIA[col]["short"], min_value=1, max_value=5, step=1,
        help=f"{A.CRITERIA[col]['label']}. 1: {A.CRITERIA[col][1]} | 3: {A.CRITERIA[col][3]} | 5: {A.CRITERIA[col][5]}",
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

try:
    ranked = rank(complete.reset_index(drop=True), value_weight)
    default_ranked = rank(complete.reset_index(drop=True))
except ValueError as e:
    st.error(f"Could not score the table: {e}")
    st.stop()

if ranked.empty:
    st.warning("No complete use cases to rank yet.")
    st.stop()

# Top cases to start with.
st.subheader(f"Start with these {A.CAPACITY}")
top = top_cases(ranked, A.CAPACITY)
st.caption(f"Using value weight {value_weight:g} and feasibility weight {feasibility_weight:g}.")
if abs(value_weight - A.VALUE_WEIGHT) > 1e-9:
    entered, left = top_changes(top_cases(default_ranked, A.CAPACITY), top)
    if entered or left:
        parts = []
        if entered:
            parts.append(f"**Enters the top {A.CAPACITY}:** {', '.join(entered)}")
        if left:
            parts.append(f"**Leaves the top {A.CAPACITY}:** {', '.join(left)}")
        st.warning(
            f"Compared with the default weights ({A.VALUE_WEIGHT:g} / {A.FEASIBILITY_WEIGHT:g}):  \n"
            + "  \n".join(parts)
        )
    else:
        st.info(
            f"Same top {A.CAPACITY} as with the default weights "
            f"({A.VALUE_WEIGHT:g} / {A.FEASIBILITY_WEIGHT:g}), though the order may differ."
        )
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
    f"Dashed lines mark the quadrant cutoff of {A.QUADRANT_CUTOFF}. "
    f"Red diamonds are gated (risk {A.RISK_GATE} or higher) and need governance first. "
    "Hover a point for its scores."
)
st.altair_chart(quadrant_chart(ranked), width="stretch")

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
    st.success(f"No case has risk at or above {A.RISK_GATE}.")
else:
    st.caption(
        f"These cases have risk {A.RISK_GATE} or higher. They need legal, data protection "
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
