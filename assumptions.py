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
        "group": "value",
        1: "Small saving or nice to have",
        3: "Noticeable saving or revenue in one team",
        5: "Large, measurable impact across the business",
    },
    "strategic_fit": {
        "label": "Strategic fit",
        "group": "value",
        1: "Not linked to any stated priority",
        3: "Supports a departmental goal",
        5: "Directly delivers a board-level priority",
    },
    "data_readiness": {
        "label": "Data readiness",
        "group": "feasibility",
        1: "Data missing, scattered or poor quality",
        3: "Data exists but needs cleaning or joining",
        5: "Clean, accessible data already in use",
    },
    "tech_maturity": {
        "label": "Technology maturity",
        "group": "feasibility",
        1: "Research-grade, unproven in production",
        3: "Proven elsewhere, needs custom build",
        5: "Off-the-shelf product or standard feature",
    },
    "clear_owner": {
        "label": "Clear owner",
        "group": "feasibility",
        1: "No one owns the process or outcome",
        3: "Owner named but has limited time",
        5: "Committed owner with budget and authority",
    },
    "risk": {
        "label": "Risk",
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
