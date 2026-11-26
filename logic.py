"""Pure scoring and ranking functions. No Streamlit here, so it can be tested."""

from statistics import mean

import pandas as pd

from assumptions import (
    ACTIONS,
    FEASIBILITY_CRITERIA,
    FEASIBILITY_WEIGHT,
    GOVERN_FIRST,
    QUADRANT_CUTOFF,
    RISK_GATE,
    SCORE_COLUMNS,
    VALUE_CRITERIA,
    VALUE_WEIGHT,
)


def validate(case):
    """Raise ValueError if any score is missing or outside 1 to 5."""
    for col in SCORE_COLUMNS:
        if col not in case or pd.isna(case[col]):
            raise ValueError(f"Missing score for '{col}'")
        v = case[col]
        if not (1 <= float(v) <= 5):
            raise ValueError(f"'{col}' must be between 1 and 5, got {v}")


def quadrant(value, feasibility, cutoff=QUADRANT_CUTOFF):
    """Place a case in a quadrant. A score exactly at the cutoff counts as high."""
    high_value = value >= cutoff
    high_feas = feasibility >= cutoff
    if high_value and high_feas:
        return "Quick win"
    if high_value:
        return "Strategic bet"
    if high_feas:
        return "Fill-in"
    return "Deprioritise"


def _fmt(x):
    return f"{float(x):g}"


def weights(value_weight=None):
    """Return (value_weight, feasibility_weight).

    None means the defaults from assumptions.py. Otherwise the feasibility
    weight is 1 minus the value weight.
    """
    if value_weight is None:
        return VALUE_WEIGHT, FEASIBILITY_WEIGHT
    if not 0 <= value_weight <= 1:
        raise ValueError(f"value_weight must be between 0 and 1, got {value_weight}")
    return value_weight, round(1 - value_weight, 10)


def score(case, value_weight=None):
    """Score one use case (a dict or pandas Series of criterion scores).

    value_weight overrides VALUE_WEIGHT; feasibility then gets 1 minus it.
    Returns a dict with value, feasibility, priority, quadrant, gated and
    working (a readable string showing each step).
    """
    validate(case)
    v_scores = [float(case[c]) for c in VALUE_CRITERIA]
    f_scores = [float(case[c]) for c in FEASIBILITY_CRITERIA]
    risk = float(case["risk"])

    value = mean(v_scores)
    feasibility = mean(f_scores)
    v_w, f_w = weights(value_weight)
    priority = v_w * value + f_w * feasibility
    quad = quadrant(value, feasibility)
    gated = risk >= RISK_GATE

    v_cmp = ">=" if value >= QUADRANT_CUTOFF else "<"
    f_cmp = ">=" if feasibility >= QUADRANT_CUTOFF else "<"
    r_cmp = ">=" if gated else "<"
    working = (
        f"value = ({' + '.join(_fmt(s) for s in v_scores)}) / {len(v_scores)} = {value:.2f}; "
        f"feasibility = ({' + '.join(_fmt(s) for s in f_scores)}) / {len(f_scores)} = {feasibility:.2f}; "
        f"priority = {v_w:g} x {value:.2f} + {f_w:g} x {feasibility:.2f} = {priority:.2f}; "
        f"quadrant = {quad} (value {value:.2f} {v_cmp} {QUADRANT_CUTOFF}, "
        f"feasibility {feasibility:.2f} {f_cmp} {QUADRANT_CUTOFF}); "
        f"risk {_fmt(risk)} {r_cmp} {RISK_GATE} -> {'gated' if gated else 'not gated'}"
    )

    return {
        "value": value,
        "feasibility": feasibility,
        "priority": priority,
        "quadrant": quad,
        "gated": gated,
        "working": working,
    }


def rank(df, value_weight=None):
    """Score every case and return them ranked.

    Ungated cases come first, by priority (highest first), then gated cases
    by priority. Ties keep the input order. Adds rank and action columns;
    gated cases get the action "Govern first".
    """
    if df.empty:
        cols = list(df.columns) + ["value", "feasibility", "priority",
                                   "quadrant", "gated", "working", "action", "rank"]
        return pd.DataFrame(columns=cols)

    scored = pd.DataFrame([score(row, value_weight) for _, row in df.iterrows()], index=df.index)
    out = pd.concat([df, scored], axis=1)
    out["action"] = [
        GOVERN_FIRST if g else ACTIONS[q] for g, q in zip(out["gated"], out["quadrant"])
    ]
    out = out.sort_values(["gated", "priority"], ascending=[True, False], kind="stable")
    out = out.reset_index(drop=True)
    out.insert(0, "rank", range(1, len(out) + 1))
    return out


def top_cases(ranked, capacity):
    """The first `capacity` ungated cases from a ranked table."""
    return ranked[~ranked["gated"]].head(capacity)


def gated_cases(ranked):
    """All cases that must be governed before they can start."""
    return ranked[ranked["gated"]]


def top_changes(default_top, new_top):
    """Compare two top lists by name.

    Returns (entered, left): names in new_top but not default_top, and names
    in default_top but not new_top, each in ranked order.
    """
    old = list(default_top["name"])
    new = list(new_top["name"])
    entered = [n for n in new if n not in old]
    left = [n for n in old if n not in new]
    return entered, left
