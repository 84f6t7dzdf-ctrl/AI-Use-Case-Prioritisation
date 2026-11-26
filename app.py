"""Streamlit app: which AI use cases should we do first?

Run with:  streamlit run app.py
"""

from pathlib import Path

import pandas as pd
import streamlit as st

import assumptions as A
from logic import gated_cases, rank, top_cases

HERE = Path(__file__).resolve().parent
DEFAULT_CSV = HERE / "use_cases.csv"

st.set_page_config(page_title="AI use case prioritisation", layout="wide")
st.title("Which AI use cases should we do first?")

# Sidebar: data source and the assumptions behind the scores.
with st.sidebar:
    st.header("Data")
    upload = st.file_uploader("Load a CSV (same columns as use_cases.csv)", type="csv")
    st.header("Assumptions (estimates)")
    st.markdown(
        f"- Value weight: **{A.VALUE_WEIGHT}**\n"
        f"- Feasibility weight: **{A.FEASIBILITY_WEIGHT}**\n"
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
        A.CRITERIA[col]["label"], min_value=1, max_value=5, step=1,
        help=f"1: {A.CRITERIA[col][1]} | 3: {A.CRITERIA[col][3]} | 5: {A.CRITERIA[col][5]}",
    )
    for col in A.SCORE_COLUMNS
}
edited = st.data_editor(
    source,
    num_rows="dynamic",
    width="stretch",
    hide_index=True,
    column_config={"name": st.column_config.TextColumn("Name", required=True), **score_cfg},
    key=f"editor_{upload.name if upload else 'default'}",
)

# Drop rows that are still being filled in.
complete = edited.dropna(subset=["name"] + A.SCORE_COLUMNS)
if len(complete) < len(edited):
    st.info(f"{len(edited) - len(complete)} row(s) with missing scores are left out of the ranking.")

try:
    ranked = rank(complete.reset_index(drop=True))
except ValueError as e:
    st.error(f"Could not score the table: {e}")
    st.stop()

if ranked.empty:
    st.warning("No complete use cases to rank yet.")
    st.stop()

# Top cases to start with.
st.subheader(f"Start with these {A.CAPACITY}")
top = top_cases(ranked, A.CAPACITY)
if top.empty:
    st.warning("Every case is gated on risk. Govern them before starting any.")
else:
    cols = st.columns(len(top))
    for col, (_, row) in zip(cols, top.iterrows()):
        with col:
            st.metric(f"#{row['rank']} {row['name']}", f"{row['priority']:.2f}")
            st.markdown(f"**{row['quadrant']}**: {row['action']}")
            st.caption(f"Value {row['value']:.2f} · Feasibility {row['feasibility']:.2f}")

# Full ranking with the working.
st.subheader("Full ranking")
display_cols = ["rank", "name", "value", "feasibility", "priority", "quadrant",
                "risk", "gated", "action", "working"]
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
        "risk": "Risk",
        "gated": "Gated",
        "action": "Action",
        "working": st.column_config.TextColumn("Working", width="large"),
    },
)

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
        column_config={"priority": st.column_config.NumberColumn("Priority", format="%.2f")},
    )

st.download_button(
    "Download ranking as CSV",
    ranked.to_csv(index=False).encode("utf-8"),
    file_name="ranked_use_cases.csv",
    mime="text/csv",
)
