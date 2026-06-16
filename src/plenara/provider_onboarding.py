"""
Provider / Clinic / Insurance onboarding readiness engine (synthetic).

Models whether a synthetic provider-clinic-payer relationship is ready for
operational use: READY / NEEDS REVIEW / BLOCKED, with the primary blocker
category and the reasons behind the state.

Safety:
- Synthetic/mock data only. No real provider, clinic, or payer data.
- Names, IDs, and statuses are fabricated for demonstration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .readiness import BLOCKED, NEEDS_REVIEW, READY

# Aging threshold (days in a single onboarding stage) that triggers review.
AGING_STAGE_THRESHOLD_DAYS = 30

# Readiness-score band that routes to review when nothing else blocks.
REVIEW_SCORE_LOW = 0.5
REVIEW_SCORE_HIGH = 0.8

UNASSIGNED_OWNERS = frozenset({"", "unassigned", "none", "n/a"})

# Status values that block onboarding outright, keyed by a human label used as
# the blocker_category. Order matters: the first matching blocker is "primary".
BLOCKING_RULES: tuple[tuple[str, frozenset[str], str], ...] = (
    ("credentialing_status", frozenset({"missing"}), "missing credentialing packet"),
    ("contract_status", frozenset({"not_active"}), "payer contract not active"),
    ("license_status", frozenset({"missing", "expired"}), "missing state license verification"),
    ("npi_status", frozenset({"missing", "mismatch"}), "NPI mismatch"),
    ("effective_date_status", frozenset({"missing"}), "effective date missing"),
    ("directory_status", frozenset({"not_updated"}), "provider directory not updated"),
    ("enrollment_status", frozenset({"not_enrolled"}), "enrollment incomplete"),
)


@dataclass
class OnboardingResult:
    """Outcome of evaluating one synthetic onboarding record."""

    status: str
    blocker_category: str | None = None
    blockers: list[str] = field(default_factory=list)
    review_reasons: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "readiness_status": self.status,
            "blocker_category": self.blocker_category,
            "blockers": list(self.blockers),
            "review_reasons": list(self.review_reasons),
        }


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def evaluate_provider_onboarding(record: dict[str, Any]) -> OnboardingResult:
    """
    Evaluate a single synthetic provider onboarding record.

    Rules:
        * BLOCKED if any critical onboarding status is missing/expired/mismatched
          or the payer contract is not active.
        * NEEDS REVIEW if CAQH attestation is stale, documentation is incomplete,
          the stage is aging, the owner team is unassigned, a credential is still
          in progress, or the readiness score sits in the middle band.
        * READY otherwise.
    """
    blockers: list[str] = []
    review_reasons: list[str] = []
    blocker_category: str | None = None

    # --- Blocking conditions (primary blocker = first match) ----------------
    for field_name, bad_values, label in BLOCKING_RULES:
        if _norm(record.get(field_name)) in bad_values:
            blockers.append(label)
            if blocker_category is None:
                blocker_category = label

    if blockers:
        return OnboardingResult(BLOCKED, blocker_category, blockers, review_reasons)

    # --- Review conditions --------------------------------------------------
    if _norm(record.get("caqh_status")) == "stale":
        review_reasons.append("CAQH attestation stale")
    if _norm(record.get("documentation_status")) == "incomplete":
        review_reasons.append("documentation incomplete")

    days_in_stage = _to_int(record.get("days_in_stage"))
    if days_in_stage > AGING_STAGE_THRESHOLD_DAYS:
        review_reasons.append(f"aging onboarding task ({days_in_stage} days in stage)")

    if _norm(record.get("owner_team")) in UNASSIGNED_OWNERS:
        review_reasons.append("owner/team not assigned")

    for field_name in ("credentialing_status", "contract_status", "enrollment_status"):
        if _norm(record.get(field_name)) in {"in_progress", "pending"}:
            review_reasons.append(f"{field_name.replace('_', ' ')} in progress")

    score = _to_float(record.get("readiness_score"), default=1.0)
    if REVIEW_SCORE_LOW <= score < REVIEW_SCORE_HIGH:
        review_reasons.append(f"medium readiness score ({score:.2f})")

    if review_reasons:
        review_category = "aging onboarding task" if days_in_stage > AGING_STAGE_THRESHOLD_DAYS else "review required"
        return OnboardingResult(NEEDS_REVIEW, review_category, blockers, review_reasons)

    return OnboardingResult(READY, None, blockers, review_reasons)


def evaluate_onboarding_status(record: dict[str, Any]) -> str:
    """Convenience wrapper returning just the readiness label."""
    return evaluate_provider_onboarding(record).status
