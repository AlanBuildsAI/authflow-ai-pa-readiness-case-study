"""
Stakeholder-friendly reporting helpers for the HealthOps Readiness Lab.

Turns the raw metrics into KPI dictionaries, plain-language explanations, and a
compact RCM work queue. All figures are synthetic.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from . import metrics
from .claims_readiness import evaluate_claim_readiness
from .provider_onboarding import evaluate_provider_onboarding
from .readiness import evaluate_pa_case

SYNTHETIC_NOTICE = (
    "Synthetic/mock data only. No PHI, no real patient/provider/payer data, "
    "no real claims or reimbursement. Readiness states support human review; "
    "they are not approval/denial predictions and not production billing software."
)


def executive_summary(
    pa_df: pd.DataFrame,
    onboarding_df: pd.DataFrame,
    claims_df: pd.DataFrame,
) -> dict[str, Any]:
    """Cross-module KPI dictionary for the executive overview."""
    pa_dist = metrics.status_distribution(pa_df)
    onb_dist = metrics.status_distribution(onboarding_df)
    claim_dist = metrics.status_distribution(claims_df, "claim_readiness_status")
    denial = metrics.denial_risk_distribution(claims_df)
    top_denial = max(denial, key=denial.get) if denial else "n/a"

    return {
        "prior_authorization": {
            "ready_rate": metrics.readiness_rate(pa_df),
            "blocked_rate": metrics.blocked_rate(pa_df),
            "needs_review_rate": metrics.needs_review_rate(pa_df),
            "avg_data_completeness": metrics.data_completeness_score(pa_df),
            "avg_days_to_ready": metrics.average_days_to_ready(pa_df),
            "status_distribution": pa_dist,
            "review_workload": pa_dist["NEEDS REVIEW"] + pa_dist["BLOCKED"],
        },
        "provider_onboarding": {
            "ready_rate": metrics.onboarding_ready_rate(onboarding_df),
            "blocked_rate": metrics.blocked_rate(onboarding_df),
            "needs_review_rate": metrics.needs_review_rate(onboarding_df),
            "avg_days_in_stage": metrics.average_days_in_stage(onboarding_df),
            "aging_task_rate": metrics.aging_task_rate(onboarding_df),
            "status_distribution": onb_dist,
        },
        "revenue_cycle": {
            "clean_claim_readiness_rate": metrics.clean_claim_readiness_rate(claims_df),
            "blocked_claim_rate": metrics.blocked_claim_rate(claims_df),
            "needs_review_claim_rate": metrics.needs_review_claim_rate(claims_df),
            "revenue_at_risk_synthetic": metrics.revenue_at_risk_synthetic(claims_df),
            "top_denial_risk_category": top_denial,
            "aging_claims_count": int(
                metrics.aging_bucket_distribution(claims_df).get("61-90", 0)
                + metrics.aging_bucket_distribution(claims_df).get("90+", 0)
            ),
            "status_distribution": claim_dist,
        },
        "safety_notice": SYNTHETIC_NOTICE,
    }


def pa_case_explanation(case: dict[str, Any]) -> str:
    result = evaluate_pa_case(case)
    if result.status == "READY":
        return "READY — synthetic blocker checks pass and completeness/confidence are sufficient."
    if result.status == "BLOCKED":
        return "BLOCKED — " + "; ".join(result.blockers)
    return "NEEDS REVIEW — " + "; ".join(result.review_reasons)


def onboarding_explanation(record: dict[str, Any]) -> str:
    result = evaluate_provider_onboarding(record)
    if result.status == "READY":
        return "READY — all critical credentialing/contract/license statuses are current."
    if result.status == "BLOCKED":
        return "BLOCKED — " + "; ".join(result.blockers)
    return "NEEDS REVIEW — " + "; ".join(result.review_reasons)


def claim_explanation(claim: dict[str, Any]) -> str:
    result = evaluate_claim_readiness(claim)
    if result.status == "READY":
        return "READY — eligibility, coding, documentation, and payer-rule checks pass."
    if result.status == "BLOCKED":
        return "BLOCKED — " + "; ".join(result.blockers)
    return "NEEDS REVIEW — " + "; ".join(result.review_reasons)


def rcm_work_queue(claims_df: pd.DataFrame, include_ready: bool = False) -> pd.DataFrame:
    """Compact, stakeholder-facing RCM work queue."""
    cols = [
        "claim_id", "payer_name_mock", "clinic_id", "test_category",
        "claim_readiness_status", "denial_risk_category", "aging_bucket",
        "owner_team", "estimated_revenue_at_risk_synthetic",
    ]
    present = [c for c in cols if c in claims_df.columns]
    queue = claims_df if include_ready else claims_df[claims_df.get("claim_readiness_status") != "READY"]
    queue = queue[present].copy()
    if "estimated_revenue_at_risk_synthetic" in queue.columns:
        queue = queue.sort_values("estimated_revenue_at_risk_synthetic", ascending=False)
    return queue.reset_index(drop=True)


def onboarding_work_queue(onboarding_df: pd.DataFrame) -> pd.DataFrame:
    """Blocked / review onboarding records for the operations queue."""
    cols = [
        "provider_id", "provider_name_mock", "specialty", "clinic_id",
        "payer_name_mock", "readiness_status", "blocker_category",
        "days_in_stage", "owner_team",
    ]
    present = [c for c in cols if c in onboarding_df.columns]
    queue = onboarding_df[onboarding_df.get("readiness_status") != "READY"][present].copy()
    if "days_in_stage" in queue.columns:
        queue = queue.sort_values("days_in_stage", ascending=False)
    return queue.reset_index(drop=True)
