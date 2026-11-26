"""Quadrant scatter chart. Built with Altair, no Streamlit, so it can be tested."""

import altair as alt
import pandas as pd

from assumptions import QUADRANT_CUTOFF

AXIS_MIN, AXIS_MAX = 1, 5

UNGATED_COLOUR = "#257de0"  # blue
GATED_COLOUR = "#dc3c3d"    # red: risk at or above the gate
TEXT_COLOUR = "#444444"
QUADRANT_TEXT_COLOUR = "#999999"
CUTOFF_COLOUR = "#888888"

GATED_LABEL = "Gated: govern first"
UNGATED_LABEL = "Not gated"


def chart_points(ranked, cutoff=QUADRANT_CUTOFF):
    """One row per point on the chart.

    Cases with exactly the same feasibility, value and gate status share a
    point, and their names are joined into one label so labels don't overlap.
    """
    df = ranked.copy()
    df["status"] = df["gated"].map({True: GATED_LABEL, False: UNGATED_LABEL})
    grouped = (
        df.groupby(["feasibility", "value", "status"], sort=False)
        .agg(
            label=("name", lambda s: " / ".join(s)),
            ranks=("rank", lambda s: ", ".join(f"#{r}" for r in s)),
            priority=("priority", "max"),
            quadrant=("quadrant", "first"),
        )
        .reset_index()
    )
    grouped["align"] = [
        label_align(x, label, cutoff) for x, label in zip(grouped["feasibility"], grouped["label"])
    ]
    return grouped


# Rough width of one label character in axis units, for a chart about 800px
# wide on a laptop screen. Used only to keep labels inside the plot.
CHAR_WIDTH = 0.035


def label_align(x, label, cutoff=QUADRANT_CUTOFF):
    """Which side of its point a label sits on.

    "left" means the text starts at the point and runs right; "right" means it
    ends at the point and runs left. Points left of the cutoff put their label
    on the left and points right of it on the right, so labels on either side
    of the cutoff line run apart instead of into each other. A label that would
    run off the edge of the plot flips side.
    """
    width = len(label) * CHAR_WIDTH + 0.1
    if x < cutoff:
        return "right" if x - width >= AXIS_MIN else "left"
    return "left" if x + width <= AXIS_MAX else "right"


def quadrant_chart(ranked, cutoff=QUADRANT_CUTOFF, height=460):
    """Scatter of feasibility (x) against value (y) with quadrant cutoffs."""
    points = chart_points(ranked, cutoff)
    scale = alt.Scale(domain=[AXIS_MIN, AXIS_MAX], nice=False)
    x = alt.X("feasibility:Q", title="Feasibility", scale=scale,
              axis=alt.Axis(values=[1, 2, 3, 4, 5], grid=True, gridColor="#e7e7e7"))
    y = alt.Y("value:Q", title="Value", scale=scale,
              axis=alt.Axis(values=[1, 2, 3, 4, 5], grid=True, gridColor="#e7e7e7"))

    colour = alt.Color(
        "status:N",
        title=None,
        scale=alt.Scale(domain=[UNGATED_LABEL, GATED_LABEL],
                        range=[UNGATED_COLOUR, GATED_COLOUR]),
        legend=alt.Legend(orient="top", direction="horizontal", symbolSize=120),
    )
    shape = alt.Shape(
        "status:N",
        title=None,
        scale=alt.Scale(domain=[UNGATED_LABEL, GATED_LABEL],
                        range=["circle", "diamond"]),
        legend=alt.Legend(orient="top", direction="horizontal", symbolSize=120),
    )
    tooltip = [
        alt.Tooltip("label:N", title="Use case"),
        alt.Tooltip("ranks:N", title="Rank"),
        alt.Tooltip("feasibility:Q", title="Feasibility", format=".2f"),
        alt.Tooltip("value:Q", title="Value", format=".2f"),
        alt.Tooltip("priority:Q", title="Priority", format=".2f"),
        alt.Tooltip("quadrant:N", title="Quadrant"),
        alt.Tooltip("status:N", title="Risk gate"),
    ]

    cutoff = pd.DataFrame({"c": [cutoff]})
    vline = alt.Chart(cutoff).mark_rule(color=CUTOFF_COLOUR, strokeDash=[4, 4]).encode(x=alt.X("c:Q", scale=scale))
    hline = alt.Chart(cutoff).mark_rule(color=CUTOFF_COLOUR, strokeDash=[4, 4]).encode(y=alt.Y("c:Q", scale=scale))

    pad = 0.08
    corners = pd.DataFrame([
        {"x": AXIS_MAX - pad, "y": AXIS_MAX - pad, "text": "Quick win", "align": "right", "baseline": "top"},
        {"x": AXIS_MIN + pad, "y": AXIS_MAX - pad, "text": "Strategic bet", "align": "left", "baseline": "top"},
        {"x": AXIS_MAX - pad, "y": AXIS_MIN + pad, "text": "Fill-in", "align": "right", "baseline": "bottom"},
        {"x": AXIS_MIN + pad, "y": AXIS_MIN + pad, "text": "Deprioritise", "align": "left", "baseline": "bottom"},
    ])
    corner_layers = [
        alt.Chart(corners[corners["text"] == row.text])
        .mark_text(align=row.align, baseline=row.baseline, fontSize=13,
                   fontWeight="bold", color=QUADRANT_TEXT_COLOUR)
        .encode(x=alt.X("x:Q", scale=scale), y=alt.Y("y:Q", scale=scale), text="text:N")
        for row in corners.itertuples()
    ]

    dots = (
        alt.Chart(points)
        .mark_point(size=110, filled=True, opacity=1, stroke="white", strokeWidth=1.5)
        .encode(x=x, y=y, color=colour, shape=shape, tooltip=tooltip)
    )
    label_layers = [
        alt.Chart(points[points["align"] == align])
        .mark_text(align=align, dx=dx, dy=-1, fontSize=11, color=TEXT_COLOUR)
        .encode(x=x, y=y, text="label:N", tooltip=tooltip)
        for align, dx in (("left", 9), ("right", -9))
    ]

    return (
        alt.layer(vline, hline, *corner_layers, dots, *label_layers)
        .properties(height=height)
        .configure_view(stroke="#cccccc")
    )
