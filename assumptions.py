"""Scoring assumptions for AI use case prioritisation.

Every number in this file is an ESTIMATE chosen as a sensible starting
point. None of them is derived from data. Review and agree them with the
leadership team before using the ranking to make decisions.
"""

# ESTIMATE: what scores 1, 3 and 5 mean on each criterion. Scores 2 and 4
# sit between the anchors. All criteria are scored 1 (low) to 5 (high).
CRITERIA = {
    "benefit": {
        "label": "Business benefit",
        "short": "Benefit",
        "group": "value",
        1: "Small saving or nice to have",
        3: "Noticeable saving or revenue in one team",
        5: "Large, measurable impact across the business",
    },
    "strategic_fit": {
        "label": "Strategic fit",
        "short": "Fit",
        "group": "value",
        1: "Not linked to any stated priority",
        3: "Supports a departmental goal",
        5: "Directly delivers a board-level priority",
    },
    "data_readiness": {
        "label": "Data readiness",
        "short": "Data",
        "group": "feasibility",
        1: "Data missing, scattered or poor quality",
        3: "Data exists but needs cleaning or joining",
        5: "Clean, accessible data already in use",
    },
    "tech_maturity": {
        "label": "Technology maturity",
        "short": "Tech",
        "group": "feasibility",
        1: "Research-grade, unproven in production",
        3: "Proven elsewhere, needs custom build",
        5: "Off-the-shelf product or standard feature",
    },
    "clear_owner": {
        "label": "Clear owner",
        "short": "Owner",
        "group": "feasibility",
        1: "No one owns the process or outcome",
        3: "Owner named but has limited time",
        5: "Committed owner with budget and authority",
    },
    "risk": {
        "label": "Risk",
        "short": "Risk",
        "group": "gate",
        1: "Low stakes, easy to reverse, no personal data",
        3: "Some customer impact or personal data",
        5: "Decisions about people, regulated or hard to reverse",
    },
}

VALUE_CRITERIA = ["benefit", "strategic_fit"]
FEASIBILITY_CRITERIA = ["data_readiness", "tech_maturity", "clear_owner"]
SCORE_COLUMNS = VALUE_CRITERIA + FEASIBILITY_CRITERIA + ["risk"]

# ESTIMATE: value matters a little more than feasibility in the priority score.
VALUE_WEIGHT = 0.6

# ESTIMATE: share of the priority score given to feasibility (1 - VALUE_WEIGHT).
FEASIBILITY_WEIGHT = 0.4

# ESTIMATE: midpoint of the 1 to 5 scale. A value or feasibility score at or
# above this counts as "high" when placing a case in a quadrant.
QUADRANT_CUTOFF = 3.0

# ESTIMATE: risk score at or above which a case must go through governance
# (legal, data protection, ethics review) before delivery can start.
RISK_GATE = 4

# ESTIMATE: range for the value weight slider in the app. Feasibility weight
# is always 1 minus the value weight.
VALUE_WEIGHT_MIN = 0.3
VALUE_WEIGHT_MAX = 0.8

# ESTIMATE: range for the quadrant cutoff control in the app.
QUADRANT_CUTOFF_MIN = 2.0
QUADRANT_CUTOFF_MAX = 4.0

# ESTIMATE: largest capacity the app lets you choose.
CAPACITY_MAX = 10

# ESTIMATE: number of use cases the organisation can deliver at once.
CAPACITY = 3

# ESTIMATE: suggested next step for each quadrant.
ACTIONS = {
    "Quick win": "Start now",
    "Strategic bet": "Fund the groundwork (data, owner), then build",
    "Fill-in": "Do when spare capacity allows",
    "Deprioritise": "Park and revisit next review",
}

GOVERN_FIRST = "Govern first"

# ESTIMATE: example scenarios. Each one loads a set of assumption values into
# the app, and can shift criterion scores for every case (clipped to 1 to 5)
# to reflect the organisation. They are illustrations, not benchmarks.
DEFAULT_SCENARIO = "Default"
SCENARIOS = {
    DEFAULT_SCENARIO: {
        "description": "The defaults from assumptions.py, with scores as entered.",
        "value_weight": VALUE_WEIGHT,
        "cutoff": QUADRANT_CUTOFF,
        "risk_gate": RISK_GATE,
        "capacity": CAPACITY,
        "score_adjustments": {},
    },
    "Regulated bank": {
        "description": (
            "Regulators and model risk teams review anything that touches "
            "customers, so the risk gate is stricter (3), feasibility counts "
            "for more (value weight 0.5) and change capacity is tighter (2)."
        ),
        "value_weight": 0.5,
        "cutoff": QUADRANT_CUTOFF,
        "risk_gate": 3,
        "capacity": 2,
        "score_adjustments": {},
    },
    "Fast-growing retailer": {
        "description": (
            "Growth matters most and the business accepts more risk, so value "
            "counts for more (value weight 0.7), only risk 5 is gated, and "
            "there is budget for 4 cases at once."
        ),
        "value_weight": 0.7,
        "cutoff": QUADRANT_CUTOFF,
        "risk_gate": 5,
        "capacity": 4,
        "score_adjustments": {},
    },
    "Company with poor data": {
        "description": (
            "Data is scattered and poorly governed, so every case's data "
            "readiness drops by 2 (minimum 1). Other assumptions stay at "
            "their defaults."
        ),
        "value_weight": VALUE_WEIGHT,
        "cutoff": QUADRANT_CUTOFF,
        "risk_gate": RISK_GATE,
        "capacity": CAPACITY,
        "score_adjustments": {"data_readiness": -2},
    },
}
