"""
Client-reporting metrics for the Plenara HealthOps Readiness Lab (synthetic).

All functions operate on pandas DataFrames produced by :mod:`plenara.sample_data`
and return plain Python numbers / dicts suitable for KPI cards and charts.

Readiness status values are the canonical labels: "READY", "NEEDS REVIEW",
"BLOCKED". All outputs are derived from synthetic data only.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .readiness import BLOCKED, NEEDS_REVIEW, READY


def _safe_div(numerator: float, denominator: float) -> float:
    return float(numerator) / float(denominator) if denominator else 0.0


def _status_rate(df: pd.DataFrame, status_col: str, value: str) -> float:
    if df.empty or status_col not in df.columns:
        return 0.0
    return _safe_div((df[status_col] == value).sum(), len(df))


# ===========================================================================
# Shared readiness rates (work for any module with a status column)
# ===========================================================================
def readiness_rate(df: pd.DataFrame, status_col: str = "readiness_status") -> float:
    """Fraction of records that are READY."""
    return _status_rate(df, status_col, READY)


def ready_rate(df: pd.DataFrame, status_col: str = "readiness_status") -> float:
    return readiness_rate(df, status_col)


def blocked_rate(df: pd.DataFrame, status_col: str = "readiness_status") -> float:
    return _status_rate(df, status_col, BLOCKED)


def needs_review_rate(df: pd.DataFrame, status_col: str = "readiness_status") -> float:
    return _status_rate(df, status_col, NEEDS_REVIEW)


def status_distribution(df: pd.DataFrame, status_col: str = "readiness_status") -> dict[str, int]:
    if df.empty or status_col not in df.columns:
        return {READY: 0, NEEDS_REVIEW: 0, BLOCKED: 0}
    counts = df[status_col].value_counts().to_dict()
    return {state: int(counts.get(state, 0)) for state in (READY, NEEDS_REVIEW, BLOCKED)}


def _mean(df: pd.DataFrame, col: str) -> float:
    if df.empty or col not in df.columns:
        return 0.0
    return float(df[col].mean())


# ===========================================================================
# Prior Authorization metrics
# ===========================================================================
def average_missing_fields(df: pd.DataFrame) -> float:
    return _mean(df, "missing_field_count")


def average_failed_blockers(df: pd.DataFrame) -> float:
    return _mean(df, "failed_blocker_count")


def average_review_required_fields(df: pd.DataFrame) -> float:
    return _mean(df, "review_required_count")


def average_days_to_ready(df: pd.DataFrame) -> float:
    return _mean(df, "days_to_ready")


def data_completeness_score(df: pd.DataFrame) -> float:
    return _mean(df, "data_completeness_score")


# ===========================================================================
# Provider onboarding metrics
# ===========================================================================
def onboarding_ready_rate(df: pd.DataFrame) -> float:
    return readiness_rate(df, "readiness_status")


def average_days_in_stage(df: pd.DataFrame) -> float:
    return _mean(df, "days_in_stage")


def aging_task_rate(df: pd.DataFrame, threshold: int = 30, days_col: str = "days_in_stage") -> float:
    """Fraction of records whose stage age exceeds ``threshold`` days."""
    if df.empty or days_col not in df.columns:
        return 0.0
    return _safe_div((df[days_col] > threshold).sum(), len(df))


def payer_clinic_ready_rate(df: pd.DataFrame) -> pd.DataFrame:
    """Clinic x payer READY-rate matrix (rows=clinic, cols=payer)."""
    needed = {"clinic_id", "payer_name_mock", "readiness_status"}
    if df.empty or not needed.issubset(df.columns):
        return pd.DataFrame()
    ready = df.assign(_ready=(df["readiness_status"] == READY).astype(float))
    return ready.pivot_table(
        index="clinic_id", columns="payer_name_mock", values="_ready", aggfunc="mean"
    )


def blocker_category_distribution(df: pd.DataFrame, col: str = "blocker_category") -> dict[str, int]:
    if df.empty or col not in df.columns:
        return {}
    counts = df[df[col].astype(str) != "none"][col].value_counts().to_dict()
    return {str(k): int(v) for k, v in counts.items()}


def owner_workload_summary(df: pd.DataFrame, owner_col: str = "owner_team", status_col: str = "readiness_status") -> dict[str, dict[str, int]]:
    """Count of non-READY items per owner team (the review/blocked workload)."""
    if df.empty or owner_col not in df.columns or status_col not in df.columns:
        return {}
    work = df[df[status_col] != READY]
    summary: dict[str, dict[str, int]] = {}
    for owner, group in work.groupby(owner_col):
        summary[str(owner)] = {
            BLOCKED: int((group[status_col] == BLOCKED).sum()),
            NEEDS_REVIEW: int((group[status_col] == NEEDS_REVIEW).sum()),
        }
    return summary


# ===========================================================================
# Diagnostic / Lab Revenue Cycle (RCM) metrics
# ===========================================================================
def clean_claim_readiness_rate(df: pd.DataFrame, status_col: str = "claim_readiness_status") -> float:
    """Fraction of claims that are READY for clean submission."""
    return _status_rate(df, status_col, READY)


def blocked_claim_rate(df: pd.DataFrame, status_col: str = "claim_readiness_status") -> float:
    return _status_rate(df, status_col, BLOCKED)


def needs_review_claim_rate(df: pd.DataFrame, status_col: str = "claim_readiness_status") -> float:
    return _status_rate(df, status_col, NEEDS_REVIEW)


def denial_risk_distribution(df: pd.DataFrame, col: str = "denial_risk_category") -> dict[str, int]:
    if df.empty or col not in df.columns:
        return {}
    counts = df[col].value_counts().to_dict()
    return {str(k): int(v) for k, v in counts.items()}


def average_claim_data_completeness(df: pd.DataFrame) -> float:
    return _mean(df, "data_completeness_score")


def average_days_since_service(df: pd.DataFrame) -> float:
    return _mean(df, "days_since_service")


def aging_bucket_distribution(df: pd.DataFrame, col: str = "aging_bucket") -> dict[str, int]:
    if df.empty or col not in df.columns:
        return {}
    order = ["0-30", "31-60", "61-90", "90+"]
    counts = df[col].value_counts().to_dict()
    return {bucket: int(counts.get(bucket, 0)) for bucket in order}


def revenue_at_risk_synthetic(df: pd.DataFrame, col: str = "estimated_revenue_at_risk_synthetic") -> float:
    """Sum of synthetic revenue-at-risk dollars. Mock figure, not real revenue."""
    if df.empty or col not in df.columns:
        return 0.0
    return round(float(df[col].sum()), 2)


def workqueue_by_owner_team(df: pd.DataFrame, owner_col: str = "owner_team", status_col: str = "claim_readiness_status") -> dict[str, int]:
    """Count of claims needing attention (not READY) per owner team."""
    if df.empty or owner_col not in df.columns or status_col not in df.columns:
        return {}
    work = df[df[status_col] != READY]
    return {str(k): int(v) for k, v in work[owner_col].value_counts().to_dict().items()}


def top_claim_blocker_categories(df: pd.DataFrame, top_n: int = 5) -> dict[str, int]:
    """Most common blocking/denial-risk drivers among non-clean claims."""
    if df.empty:
        return {}
    # Prefer an explicit blocker column; otherwise summarize by denial risk.
    if "blocker_category" in df.columns:
        dist = blocker_category_distribution(df, "blocker_category")
    else:
        dist = denial_risk_distribution(df)
    return dict(sorted(dist.items(), key=lambda kv: kv[1], reverse=True)[:top_n])


def revenue_at_risk_by_payer(df: pd.DataFrame) -> dict[str, float]:
    needed = {"payer_name_mock", "estimated_revenue_at_risk_synthetic"}
    if df.empty or not needed.issubset(df.columns):
        return {}
    grouped = df.groupby("payer_name_mock")["estimated_revenue_at_risk_synthetic"].sum()
    return {str(k): round(float(v), 2) for k, v in grouped.items()}
