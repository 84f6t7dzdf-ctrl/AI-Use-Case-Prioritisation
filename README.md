# AI-Use-Case-Prioritisation

Build a tool to decide which AI use cases a company should do first.

This repository holds a small Streamlit app that helps a CIO do that.
Each use case is scored 1 to 5 on six criteria, and the app ranks them,
places them in a quadrant, and holds back high-risk cases for governance.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Run the tests with:

```bash
pytest
```

## How the scoring works

| Step | Formula |
|---|---|
| Value | mean(benefit, strategic_fit) |
| Feasibility | mean(data_readiness, tech_maturity, clear_owner) |
| Priority | 0.6 × value + 0.4 × feasibility |
| Quadrant | value and feasibility each compared with 3.0 (a score of exactly 3.0 counts as high) |
| Gated | risk ≥ 4 |

Quadrants and their actions:

| Quadrant | Value | Feasibility | Action |
|---|---|---|---|
| Quick win | high | high | Start now |
| Strategic bet | high | low | Fund the groundwork (data, owner), then build |
| Fill-in | low | high | Do when spare capacity allows |
| Deprioritise | low | low | Park and revisit next review |

A sidebar slider sets the value weight from 0.3 to 0.8 (feasibility gets
1 minus it). The ranking, chart and working all use the chosen weights, and
a note lists any case that enters or leaves the top 3 compared with the
default 0.6 / 0.4.

A scatter chart plots every case by feasibility (x) and value (y), with
dashed lines at the quadrant cutoff and the quadrant names in the corners.
Gated cases are red diamonds; hover a point to see its scores.

Gated cases get the action **Govern first** and are ranked after every
ungated case, whatever their priority. The app recommends the top 3 ungated
cases (the capacity).

The app's Working section lists every step of the calculation for each case,
one step per line, so anyone can check a result by hand. The tables are sized
to fit a laptop screen without scrolling sideways.

## Files

- `assumptions.py`: criteria definitions (what 1, 3 and 5 mean), weights,
  cutoff, risk gate and capacity. **All of these are estimates**: agree them
  with the leadership team before relying on the ranking.
- `use_cases.csv`: 12 example use cases for a mid-size company. The scores are
  illustrative; replace them with your own.
- `logic.py`: pure scoring and ranking functions (no Streamlit).
- `charts.py`: the quadrant scatter chart, built with Altair (no Streamlit).
- `app.py`: the Streamlit interface. Load the default CSV or upload your own,
  edit scores in the table, and see the ranking update.
- `tests/test_logic.py`: pytest tests for the scoring and ranking.

## CSV format

Columns: `name`, `description` (optional), `benefit`, `strategic_fit`,
`data_readiness`, `tech_maturity`, `clear_owner`, `risk`. Scores must be
between 1 and 5.
