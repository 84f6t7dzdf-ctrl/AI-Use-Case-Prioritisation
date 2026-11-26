import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from charts import GATED_LABEL, UNGATED_LABEL, chart_points, quadrant_chart  # noqa: E402
from logic import rank  # noqa: E402

CSV = Path(__file__).resolve().parent.parent / "use_cases.csv"


def test_points_share_label_when_coordinates_match():
    pts = chart_points(rank(pd.read_csv(CSV)))
    # Customer service chatbot and Contract review both score value 4.0,
    # feasibility 3.33, so they share one point.
    shared = pts[pts["label"].str.contains("Customer service chatbot")]
    assert len(shared) == 1
    assert "Contract review" in shared.iloc[0]["label"]
    assert len(pts) == 11


def test_gated_cases_marked():
    pts = chart_points(rank(pd.read_csv(CSV)))
    gated = set(pts.loc[pts["status"] == GATED_LABEL, "label"])
    assert gated == {"CV screening", "Customer credit scoring"}
    assert (pts["status"] == UNGATED_LABEL).sum() == 9


def test_chart_builds():
    spec = quadrant_chart(rank(pd.read_csv(CSV))).to_dict()
    assert "layer" in spec


def test_label_side_keeps_labels_inside_plot():
    from charts import label_align
    # Left of the cutoff with room: label runs left, away from the cutoff line.
    assert label_align(2.67, "Internal knowledge search") == "right"
    # Too close to the left edge to run left: flips to run right.
    assert label_align(1.2, "Internal knowledge search") == "left"
    # Right of the cutoff with room: label runs right.
    assert label_align(3.33, "Contract review") == "left"
    # Near the right edge: flips to run left.
    assert label_align(4.9, "Invoice matching") == "right"
