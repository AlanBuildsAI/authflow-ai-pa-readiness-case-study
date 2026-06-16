"""
Unified operations work queue across the three Plenara modules.

Combines prior authorization, provider onboarding, and diagnostic/lab claims
into one prioritized queue with a severity, an owner, an age, and a
deterministic, operator-friendly recommended next action. Powers the Command
Center and Work Queue screens.

All inputs and outputs are synthetic. Recommended actions are deterministic
string lookups — not predictions or clinical guidance.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .claims_readiness import evaluate_claim_readiness
from .readiness import BLOCKED, NEEDS_REVIEW, READY

# Module labels (match the app tab names).
PRIOR_AUTH = "Prior auth"
ONBOARDING = "Provider onboarding"
REVENUE_CYCLE = "Revenue cycle"

# Synthetic internal-SLA aging thresholds (days) per module. Designed, not benchmarks.
SLA_DAYS = {PRIOR_AUTH: 14, ONBOARDING: 30, REVENUE_CYCLE: 60}
# Synthetic revenue-at-risk threshold that elevates a blocked claim to High.
HIGH_REVENUE_AT_RISK = 600.0

UNASSIGNED = {"", "unassigned", "none", "n/a", "nan"}

WORK_QUEUE_COLUMNS = [
    "module",
    "record_id",
    "clinic_id",
    "payer",
    "readiness_status",
    "severity",
    "blocker_category",
    "owner_team",
    "age_days",
    "recommended_action",
    "synthetic_impact",
]


def _is_unassigned(owner_team: Any) -> bool:
    return str(owner_team).strip().lower() in UNASSIGNED


def severity_from_record(
    module: str,
    status: str,
    age_days: float,
    synthetic_impact: float,
    owner_team: Any,
) -> str:
    """Deterministic severity:

    * High   — unassigned non-ready work, or BLOCKED that is aging beyond its
               internal SLA or carries high synthetic revenue at risk.
    * Medium — any other BLOCKED or NEEDS REVIEW work.
    * Low    — READY / informational.
    """
    sla = SLA_DAYS.get(module, 30)
    age = age_days or 0
    impact = synthetic_impact or 0.0

    if _is_unassigned(owner_team) and status != READY:
        return "High"
    if status == BLOCKED and (age >= sla or impact >= HIGH_REVENUE_AT_RISK):
        return "High"
    if status in (BLOCKED, NEEDS_REVIEW):
        return "Medium"
    return "Low"


# Operator-friendly recommended actions keyed by (module, blocker_category).
_PA_ACTIONS = {
    "missing clinical documentation": "Request missing clinical documentation before submission.",
    "payer criteria not met": "Re-check payer-specific criteria and medical necessity evidence.",
    "documentation / confidence review": "Review low-confidence fields and confirm documentation.",
}
_ONB_ACTIONS = {
    "missing credentialing packet": "Complete and submit the credentialing packet.",
    "payer contract not active": "Update provider directory / payer contract status.",
    "missing state license verification": "Complete state license verification.",
    "NPI mismatch": "Resolve the NPI verification mismatch.",
    "effective date missing": "Set the payer effective date.",
    "provider directory not updated": "Update the provider directory.",
    "enrollment incomplete": "Complete payer enrollment.",
    "aging onboarding task": "Refresh CAQH / advance the aging onboarding task.",
    "review required": "Review documentation and CAQH attestation status.",
}
_CLAIM_ACTIONS = {
    "eligibility mismatch": "Verify eligibility and payer-rule requirements.",
    "missing prior authorization": "Obtain prior authorization before submission.",
    "procedure / diagnosis mismatch": "Review documentation and coding mismatch.",
    "payer-specific rule failed": "Review the payer-rule failure for this claim.",
    "timely filing risk": "Resolve timely filing risk before claim submission.",
    "eligibility unverified": "Verify eligibility before submission.",
    "payer documentation incomplete": "Close the documentation gap for payer requirements.",
    "modifier required": "Confirm the modifier requirement with the billing team.",
    "payer rule needs review": "Review the payer rule for this claim.",
    "timely filing at risk": "Resolve timely filing risk before claim submission.",
}


def recommended_action_from_record(
    module: str,
    status: str,
    blocker_category: str | None,
    owner_team: Any,
) -> str:
    """Deterministic, human-readable next action."""
    if status == READY:
        return "Ready for submission — no action needed."
    if _is_unassigned(owner_team):
        return "Assign owner team before queue handoff."

    category = (blocker_category or "").strip()
    if module == PRIOR_AUTH:
        return _PA_ACTIONS.get(category, "Review readiness blockers and confirm documentation.")
    if module == ONBOARDING:
        return _ONB_ACTIONS.get(category, "Review onboarding blockers and owner assignment.")
    if module == REVENUE_CYCLE:
        return _CLAIM_ACTIONS.get(category, "Review claim readiness blockers before submission.")
    return "Review readiness blockers."


def _pa_blocker_category(row: dict[str, Any]) -> str:
    status = row.get("readiness_status")
    if status == READY:
        return "none"
    if status == BLOCKED:
        critical = {"diagnosis", "medication", "authorization_type", "disease_activity_evidence", "provider_specialty"}
        if int(row.get("missing_field_count") or 0) > 0 and str(row.get("top_missing_field")) in critical:
            return "missing clinical documentation"
        return "payer criteria not met"
    return "documentation / confidence review"


def _normalize_pa(pa_df: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for _, r in pa_df.iterrows():
        d = r.to_dict()
        status = d.get("readiness_status")
        category = _pa_blocker_category(d)
        age = float(d.get("days_to_ready") or 0)
        rows.append(
            {
                "module": PRIOR_AUTH,
                "record_id": d.get("case_id"),
                "clinic_id": d.get("clinic_id"),
                "payer": d.get("payer_type"),
                "readiness_status": status,
                "blocker_category": category,
                "owner_team": d.get("owner_team"),
                "age_days": age,
                "synthetic_impact": 0.0,
            }
        )
    return rows


def _normalize_onboarding(onb_df: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for _, r in onb_df.iterrows():
        d = r.to_dict()
        status = d.get("readiness_status")
        category = d.get("blocker_category") if status != READY else "none"
        age = float(d.get("days_in_stage") or 0)
        rows.append(
            {
                "module": ONBOARDING,
                "record_id": d.get("provider_id"),
                "clinic_id": d.get("clinic_id"),
                "payer": d.get("payer_name_mock"),
                "readiness_status": status,
                "blocker_category": category,
                "owner_team": d.get("owner_team"),
                "age_days": age,
                "synthetic_impact": 0.0,
            }
        )
    return rows


def _normalize_claims(claims_df: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for _, r in claims_df.iterrows():
        d = r.to_dict()
        status = d.get("claim_readiness_status")
        category = evaluate_claim_readiness(d).blocker_category or "none"
        age = float(d.get("days_since_service") or 0)
        rows.append(
            {
                "module": REVENUE_CYCLE,
                "record_id": d.get("claim_id"),
                "clinic_id": d.get("clinic_id"),
                "payer": d.get("payer_name_mock"),
                "readiness_status": status,
                "blocker_category": category,
                "owner_team": d.get("owner_team"),
                "age_days": age,
                "synthetic_impact": float(d.get("estimated_revenue_at_risk_synthetic") or 0.0),
            }
        )
    return rows


_SEVERITY_RANK = {"High": 0, "Medium": 1, "Low": 2}


def build_unified_work_queue(
    pa_df: pd.DataFrame,
    onb_df: pd.DataFrame,
    claims_df: pd.DataFrame,
    include_ready: bool = False,
) -> pd.DataFrame:
    """Build one prioritized work queue across all three modules."""
    rows = _normalize_pa(pa_df) + _normalize_onboarding(onb_df) + _normalize_claims(claims_df)
    for row in rows:
        row["severity"] = severity_from_record(
            row["module"], row["readiness_status"], row["age_days"], row["synthetic_impact"], row["owner_team"]
        )
        row["recommended_action"] = recommended_action_from_record(
            row["module"], row["readiness_status"], row["blocker_category"], row["owner_team"]
        )

    queue = pd.DataFrame(rows, columns=WORK_QUEUE_COLUMNS)
    if not include_ready:
        queue = queue[queue["readiness_status"] != READY]
    queue["_sev"] = queue["severity"].map(_SEVERITY_RANK).fillna(3)
    queue = queue.sort_values(
        ["_sev", "synthetic_impact", "age_days"], ascending=[True, False, False]
    ).drop(columns="_sev")
    return queue.reset_index(drop=True)


# "Why it matters" copy keyed by blocker category (operator-friendly, synthetic).
_WHY = {
    "missing clinical documentation": "Packets without required documentation cannot be submitted cleanly.",
    "payer criteria not met": "Payer-specific criteria gaps drive avoidable rework.",
    "documentation / confidence review": "Low-confidence fields need a human check before submission.",
    "missing credentialing packet": "Providers cannot go live without a complete credentialing packet.",
    "payer contract not active": "An inactive payer contract blocks billing for the provider.",
    "missing state license verification": "License gaps block credentialing and enrollment.",
    "NPI mismatch": "NPI mismatches cause downstream claim and directory errors.",
    "effective date missing": "A missing effective date stalls enrollment go-live.",
    "provider directory not updated": "Directory gaps create patient-access and claim issues.",
    "enrollment incomplete": "Incomplete enrollment delays the provider's revenue start.",
    "aging onboarding task": "Aging onboarding tasks delay go-live and revenue.",
    "review required": "Review-state items can age into blockers if not worked.",
    "eligibility mismatch": "Eligibility issues are a leading driver of claim rework.",
    "missing prior authorization": "Missing prior auth commonly blocks clean submission.",
    "procedure / diagnosis mismatch": "Coding mismatches drive avoidable claim rework.",
    "payer-specific rule failed": "Payer-rule failures must be resolved before submission.",
    "timely filing risk": "Timely filing windows close — aged claims risk lost revenue (synthetic).",
    "eligibility unverified": "Unverified eligibility should be confirmed before submission.",
    "payer documentation incomplete": "Documentation gaps slow payer acceptance.",
    "modifier required": "Missing/invalid modifiers cause claim rework.",
    "payer rule needs review": "Flagged payer rules need a human check.",
    "timely filing at risk": "Claims near the filing window need prompt attention.",
}


def summarize_top_actions(work_queue: pd.DataFrame, limit: int = 6) -> list[dict[str, Any]]:
    """Prioritized 'top actions for today' grouped by module + blocker category."""
    if work_queue.empty:
        return []

    actionable = work_queue[work_queue["severity"].isin(["High", "Medium"])].copy()
    if actionable.empty:
        actionable = work_queue.copy()

    actions: list[dict[str, Any]] = []
    grouped = actionable.groupby(["module", "blocker_category"], dropna=False)
    for (module, category), group in grouped:
        high = int((group["severity"] == "High").sum())
        actions.append(
            {
                "module": module,
                "issue": category,
                "why": _WHY.get(str(category), "Affects submission readiness and operational throughput."),
                "recommended_action": group["recommended_action"].mode().iloc[0]
                if not group["recommended_action"].mode().empty
                else group["recommended_action"].iloc[0],
                "affected_records": int(len(group)),
                "high_severity": high,
                "synthetic_impact": round(float(group["synthetic_impact"].sum()), 2),
            }
        )

    actions.sort(
        key=lambda a: (a["high_severity"], a["synthetic_impact"], a["affected_records"]),
        reverse=True,
    )
    return actions[:limit]
