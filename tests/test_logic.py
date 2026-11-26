import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from logic import quadrant, rank, score  # noqa: E402


def case(name="Case", benefit=3, strategic_fit=3, data_readiness=3,
         tech_maturity=3, clear_owner=3, risk=1):
    return {
        "name": name,
        "benefit": benefit,
        "strategic_fit": strategic_fit,
        "data_readiness": data_readiness,
        "tech_maturity": tech_maturity,
        "clear_owner": clear_owner,
        "risk": risk,
    }


def test_score_hand_computed():
    # Customer service chatbot from use_cases.csv.
    # value       = (4 + 4) / 2     = 4.0
    # feasibility = (3 + 4 + 3) / 3 = 10/3 = 3.3333
    # priority    = 0.6 * 4.0 + 0.4 * 10/3 = 2.4 + 1.3333 = 3.7333
    s = score(case(benefit=4, strategic_fit=4, data_readiness=3,
                   tech_maturity=4, clear_owner=3, risk=3))
    assert s["value"] == pytest.approx(4.0)
    assert s["feasibility"] == pytest.approx(10 / 3)
    assert s["priority"] == pytest.approx(3.7333, abs=1e-4)
    assert s["quadrant"] == "Quick win"
    assert s["gated"] is False
    assert "value = (4 + 4) / 2 = 4.00" in s["working"]
    assert "priority = 0.6 x 4.00 + 0.4 x 3.33 = 3.73" in s["working"]


def test_quadrant_boundary_exactly_cutoff_counts_as_high():
    # value = (3 + 3) / 2 = 3.0 and feasibility = (3 + 3 + 3) / 3 = 3.0
    s = score(case())
    assert s["value"] == 3.0
    assert s["feasibility"] == 3.0
    assert s["quadrant"] == "Quick win"
    # Just below the cutoff on each axis.
    assert quadrant(2.99, 3.0) == "Fill-in"
    assert quadrant(3.0, 2.99) == "Strategic bet"
    assert quadrant(2.99, 2.99) == "Deprioritise"


def test_gated_case():
    s = score(case(benefit=5, strategic_fit=5, risk=4))
    assert s["gated"] is True
    assert "risk 4 >= 4 -> gated" in s["working"]
    assert score(case(risk=3))["gated"] is False


def test_rank_puts_gated_below_lower_scoring_ungated():
    df = pd.DataFrame([
        case("High but risky", benefit=5, strategic_fit=5, data_readiness=5,
             tech_maturity=5, clear_owner=5, risk=5),   # priority 5.0, gated
        case("Low but safe", benefit=1, strategic_fit=1, data_readiness=1,
             tech_maturity=1, clear_owner=1, risk=1),   # priority 1.0
    ])
    ranked = rank(df)
    assert list(ranked["name"]) == ["Low but safe", "High but risky"]
    assert list(ranked["rank"]) == [1, 2]
    assert ranked.loc[1, "action"] == "Govern first"
    assert ranked.loc[0, "action"] == "Park and revisit next review"


def test_score_rejects_out_of_range():
    with pytest.raises(ValueError):
        score(case(benefit=6))


def test_sample_csv_ranks():
    df = pd.read_csv(Path(__file__).resolve().parent.parent / "use_cases.csv")
    ranked = rank(df)
    assert len(ranked) == 12
    assert set(ranked["quadrant"]) == {"Quick win", "Strategic bet", "Fill-in", "Deprioritise"}
    assert ranked["gated"].any()


def test_custom_value_weight():
    # value = 4.0, feasibility = 10/3; with value weight 0.3:
    # priority = 0.3 * 4.0 + 0.7 * 10/3 = 1.2 + 2.3333 = 3.5333
    s = score(case(benefit=4, strategic_fit=4, data_readiness=3,
                   tech_maturity=4, clear_owner=3), value_weight=0.3)
    assert s["priority"] == pytest.approx(3.5333, abs=1e-4)
    assert "priority = 0.3 x 4.00 + 0.7 x 3.33 = 3.53" in s["working"]


def test_value_weight_out_of_range():
    with pytest.raises(ValueError):
        score(case(), value_weight=1.5)


def test_top_changes_with_sample_data():
    from logic import top_cases, top_changes
    df = pd.read_csv(Path(__file__).resolve().parent.parent / "use_cases.csv")
    default_top = top_cases(rank(df), 3)
    assert list(default_top["name"]) == [
        "Invoice matching", "Demand forecasting", "Customer service chatbot"]
    # Favouring feasibility swaps in two easier cases.
    entered, left = top_changes(default_top, top_cases(rank(df, value_weight=0.3), 3))
    assert entered == ["Sales email drafting", "IT helpdesk ticket triage"]
    assert left == ["Demand forecasting", "Customer service chatbot"]
    # Default weight gives no change.
    assert top_changes(default_top, top_cases(rank(df, value_weight=0.6), 3)) == ([], [])
