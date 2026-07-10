"""
Reusable product narrative for Plenara — Healthcare Operations Readiness Lab.

Centralizes the product-facing copy (positioning, users, workflows, readiness
definitions, value, safety, human-in-the-loop, design-partner framing) so the
Streamlit app, README, and docs stay consistent. This module holds text and
data only — no business logic and no data access.

Everything here describes a **synthetic prototype**. It is not a production
healthcare system, not clinical decision support, and makes no PHI or
approval/denial-prediction claims.
"""

from __future__ import annotations

ONE_LINER = (
    "Plenara is a professional synthetic healthcare operations SaaS prototype for "
    "prior authorization, provider onboarding, and revenue-cycle readiness."
)

POSITIONING = (
    "Plenara is a professional synthetic healthcare operations SaaS prototype for "
    "prior authorization, provider onboarding, and revenue-cycle readiness. It "
    "demonstrates how clinics could turn fragmented operational workflows into "
    "explainable readiness states, blockers, work queues, SQL-backed metrics, "
    "data-quality checks, and executive dashboards — while preserving clear safety "
    "boundaries before any real PHI or production deployment."
)

VALUE_PROPOSITION = (
    "Turn fragmented prior authorization, onboarding, and claims work into one "
    "explainable readiness picture so an operations team knows what is blocked, "
    "why, who owns it, and what to do next — before work moves forward."
)

SYNTHETIC_SAFETY_NOTE = (
    "Synthetic / mock data only. No PHI and no real patient, provider, payer, or "
    "claims data. Human-in-the-loop workflow support — not autonomous decisions, "
    "not clinical decision support, and not approval/denial prediction."
)

# --- Audiences -------------------------------------------------------------
TARGET_USERS = [
    "Prior authorization managers",
    "Revenue cycle / billing managers",
    "Clinic operations managers",
    "Provider onboarding teams",
    "Healthcare data / operations analysts",
]

TARGET_JOB_ROLES = [
    "Data Analyst",
    "Operations Analyst",
    "Data Quality Analyst",
    "Business Analyst",
    "Healthcare Operations Analyst",
    "Implementation Analyst",
    "Client Reporting Analyst",
]

SKILLS_DEMONSTRATED = [
    "Python",
    "pandas",
    "SQL",
    "DuckDB",
    "Streamlit",
    "data-quality checks",
    "metric definitions",
    "workflow rules",
    "work queues",
    "executive reporting",
    "synthetic-data safety",
    "testing",
]

# --- Workflows -------------------------------------------------------------
WORKFLOWS = [
    {
        "name": "Prior Authorization Readiness",
        "question": "Is a synthetic PA packet complete enough to submit?",
        "signals": "missing documentation, payer criteria, confidence, completeness",
    },
    {
        "name": "Provider / Clinic / Insurance Onboarding Readiness",
        "question": "Is a synthetic provider-clinic-payer relationship ready for operational use?",
        "signals": "credentialing, contract, enrollment, CAQH, NPI, license, directory, effective date",
    },
    {
        "name": "Diagnostic / Lab Revenue Cycle Readiness",
        "question": "Is a synthetic diagnostic/lab claim ready for clean submission?",
        "signals": "eligibility, coding, modifier, documentation, payer rule, timely filing",
    },
]

# --- Readiness definitions -------------------------------------------------
READINESS_DEFINITIONS = {
    "READY": "Checks pass — the record is ready to move forward / submit.",
    "NEEDS REVIEW": "A softer signal (low confidence, aging, or a gap) needs a human check.",
    "BLOCKED": "A critical requirement fails — fix the blocker before the record moves forward.",
}

# --- Operator guidance -----------------------------------------------------
OPERATOR_FIRST_LOOK = [
    "Start at the Command Center: critical blockers, aging, unassigned work, and readiness rate.",
    "Read the Top actions for today — the highest-severity, highest-impact items first.",
    "Work the unified queue from High to Low severity; assign any unowned items.",
    "Open a record to see its blockers and the recommended next action.",
]

# --- Boundaries ------------------------------------------------------------
SAFETY_BOUNDARIES = [
    "Synthetic / mock data only — no PHI, no real patient/provider/payer/claims data.",
    "No EHR or payer integrations, no claim submission, no network calls at runtime.",
    "No approval/denial prediction, no medical recommendations, no clinical decision support.",
    "No production authentication, database, or real user accounts.",
    "Not a HIPAA-compliant production system; safety boundaries precede any real PHI.",
]

DOES_NOT_CLAIM = [
    "HIPAA-compliant production system",
    "Clinical decision support",
    "Predicts payer approvals or denials",
    "Guaranteed savings or real revenue recovered",
    "Automated payer submission",
    "Ready for real patient data",
]

HUMAN_IN_THE_LOOP = (
    "Plenara surfaces explainable readiness states and recommended next actions to "
    "help people prioritize. Every decision stays with a human reviewer — the "
    "system does not submit, approve, deny, or make clinical or billing decisions."
)

DESIGN_PARTNER_POSITIONING = (
    "Plenara is at the synthetic-demo stage. It is designed for design-partner "
    "discovery conversations with clinics and operators using synthetic data only — "
    "to map real workflows and pain points before any PHI, integration, or pilot."
)

DESIGN_PARTNER_QUESTIONS = [
    "Where does your team currently lose the most time?",
    "Which workflow creates the most rework?",
    "How do you prioritize blocked cases today?",
    "Who owns prior auth, onboarding, and claim readiness issues?",
    "Which metrics would matter most to your team?",
    "What would make this useful enough to pilot?",
]


def workflow_names() -> list[str]:
    return [w["name"] for w in WORKFLOWS]


def readiness_legend() -> str:
    """One-line legend for READY / NEEDS REVIEW / BLOCKED."""
    return " · ".join(f"{k}: {v}" for k, v in READINESS_DEFINITIONS.items())
