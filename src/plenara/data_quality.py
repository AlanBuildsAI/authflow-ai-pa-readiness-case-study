"""
Data-quality and synthetic-safety checks for the HealthOps Readiness Lab.

These checks make two promises explicit and testable:
1. The datasets are internally well-formed (no dup IDs, valid statuses, sane
   numeric ranges, owners present where required).
2. The datasets are synthetic and contain no PHI-like columns.

Every check returns a :class:`CheckResult` so the Streamlit app and the test
suite can render / assert the same results.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Sequence

import pandas as pd

from .readiness import READINESS_STATES, BLOCKED

# Column-name fragments that would suggest real PHI / direct identifiers.
PHI_LIKE_PATTERNS = (
    r"ssn",
    r"social_security",
    r"\bdob\b",
    r"date_of_birth",
    r"birth_date",
    r"\bmrn\b",
    r"medical_record_number",
    r"patient_name",
    r"first_name",
    r"last_name",
    r"phone",
    r"email",
    r"street",
    r"address",
    r"zip_code",
    r"member_id",
    r"subscriber_id",
)
_PHI_RE = re.compile("|".join(PHI_LIKE_PATTERNS), flags=re.IGNORECASE)


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""

    def as_dict(self) -> dict[str, object]:
        return {"check": self.name, "passed": self.passed, "detail": self.detail}


def check_no_phi_like_columns(df: pd.DataFrame) -> CheckResult:
    flagged = [c for c in df.columns if _PHI_RE.search(str(c))]
    # "_mock" columns are explicitly fabricated and exempt.
    flagged = [c for c in flagged if not str(c).endswith("_mock")]
    return CheckResult(
        "no_phi_like_columns",
        passed=not flagged,
        detail="none" if not flagged else f"flagged columns: {flagged}",
    )


def check_synthetic_flag(df: pd.DataFrame, col: str = "synthetic_only_flag") -> CheckResult:
    if col not in df.columns:
        return CheckResult("synthetic_only_flag_present", False, f"missing column {col}")
    all_true = bool(df[col].astype(bool).all()) and len(df) > 0
    return CheckResult(
        "synthetic_only_flag_true",
        passed=all_true,
        detail="all rows flagged synthetic" if all_true else "some rows not flagged synthetic",
    )


def check_required_fields(df: pd.DataFrame, required: Sequence[str]) -> CheckResult:
    missing = [c for c in required if c not in df.columns]
    return CheckResult(
        "required_fields_present",
        passed=not missing,
        detail="all present" if not missing else f"missing: {missing}",
    )


def check_no_duplicate_ids(df: pd.DataFrame, id_col: str) -> CheckResult:
    if id_col not in df.columns:
        return CheckResult(f"no_duplicate_{id_col}", False, f"missing column {id_col}")
    dups = int(df[id_col].duplicated().sum())
    return CheckResult(
        f"no_duplicate_{id_col}",
        passed=dups == 0,
        detail="unique" if dups == 0 else f"{dups} duplicate id(s)",
    )


def check_valid_statuses(df: pd.DataFrame, status_col: str, allowed: Iterable[str] = READINESS_STATES) -> CheckResult:
    if status_col not in df.columns:
        return CheckResult("valid_readiness_status", False, f"missing column {status_col}")
    allowed_set = set(allowed)
    bad = sorted(set(df[status_col].unique()) - allowed_set)
    return CheckResult(
        "valid_readiness_status",
        passed=not bad,
        detail="all valid" if not bad else f"invalid: {bad}",
    )


def check_owner_present_for_blocked(df: pd.DataFrame, status_col: str, owner_col: str = "owner_team") -> CheckResult:
    if status_col not in df.columns or owner_col not in df.columns:
        return CheckResult("owner_present_for_blocked", False, "missing status/owner column")
    blocked = df[df[status_col] == BLOCKED]
    unassigned = blocked[owner_col].astype(str).str.strip().str.lower().isin({"", "unassigned", "none", "n/a", "nan"})
    bad = int(unassigned.sum())
    return CheckResult(
        "owner_present_for_blocked",
        passed=bad == 0,
        detail="all blocked rows owned" if bad == 0 else f"{bad} blocked row(s) without owner",
    )


def check_non_negative(df: pd.DataFrame, cols: Sequence[str]) -> CheckResult:
    present = [c for c in cols if c in df.columns]
    bad = [c for c in present if (df[c] < 0).any()]
    return CheckResult(
        "non_negative_numeric_fields",
        passed=not bad,
        detail="ok" if not bad else f"negative values in: {bad}",
    )


def check_score_range(df: pd.DataFrame, cols: Sequence[str]) -> CheckResult:
    present = [c for c in cols if c in df.columns]
    bad = [c for c in present if ((df[c] < 0) | (df[c] > 1)).any()]
    return CheckResult(
        "score_between_0_and_1",
        passed=not bad,
        detail="ok" if not bad else f"out-of-range scores in: {bad}",
    )


def run_authorization_checks(df: pd.DataFrame) -> list[CheckResult]:
    required = [
        "case_id", "clinic_id", "payer_type", "readiness_status",
        "missing_field_count", "failed_blocker_count", "review_required_count",
        "data_completeness_score", "owner_team", "synthetic_only_flag",
    ]
    return [
        check_required_fields(df, required),
        check_no_duplicate_ids(df, "case_id"),
        check_valid_statuses(df, "readiness_status"),
        check_owner_present_for_blocked(df, "readiness_status"),
        check_non_negative(df, ["missing_field_count", "failed_blocker_count", "review_required_count", "days_to_ready"]),
        check_score_range(df, ["data_completeness_score"]),
        check_synthetic_flag(df),
        check_no_phi_like_columns(df),
    ]


def run_onboarding_checks(df: pd.DataFrame) -> list[CheckResult]:
    required = [
        "provider_id", "clinic_id", "payer_name_mock", "readiness_status",
        "readiness_score", "days_in_stage", "owner_team", "synthetic_only_flag",
    ]
    return [
        check_required_fields(df, required),
        check_no_duplicate_ids(df, "provider_id"),
        check_valid_statuses(df, "readiness_status"),
        check_non_negative(df, ["days_in_stage"]),
        check_score_range(df, ["readiness_score"]),
        check_synthetic_flag(df),
        check_no_phi_like_columns(df),
    ]


def run_claim_checks(df: pd.DataFrame) -> list[CheckResult]:
    required = [
        "claim_id", "accession_id_mock", "clinic_id", "payer_name_mock",
        "claim_readiness_status", "denial_risk_category", "days_since_service",
        "estimated_revenue_at_risk_synthetic", "data_completeness_score",
        "owner_team", "synthetic_only_flag",
    ]
    return [
        check_required_fields(df, required),
        check_no_duplicate_ids(df, "claim_id"),
        check_no_duplicate_ids(df, "accession_id_mock"),
        check_valid_statuses(df, "claim_readiness_status"),
        check_owner_present_for_blocked(df, "claim_readiness_status"),
        check_non_negative(df, ["days_since_service", "missing_field_count", "failed_rule_count", "review_required_count", "estimated_revenue_at_risk_synthetic"]),
        check_score_range(df, ["data_completeness_score"]),
        check_synthetic_flag(df),
        check_no_phi_like_columns(df),
    ]


def all_checks_passed(results: Iterable[CheckResult]) -> bool:
    return all(r.passed for r in results)
