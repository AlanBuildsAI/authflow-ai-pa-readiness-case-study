"""
Prior Authorization readiness engine (synthetic).

Turns a structured (synthetic) prior authorization case into a readiness state:
READY / NEEDS REVIEW / BLOCKED, plus the reasons behind that state.

Safety:
- Synthetic/mock data only. No PHI, no real patient/payer data.
- This does NOT predict payer approvals or denials. It evaluates whether a
  synthetic packet looks complete enough for a human to review before submission.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Canonical readiness labels used across every module and dataset.
READY = "READY"
NEEDS_REVIEW = "NEEDS REVIEW"
BLOCKED = "BLOCKED"

READINESS_STATES = (READY, NEEDS_REVIEW, BLOCKED)

# Fields whose absence should block a packet rather than merely flag it.
CRITICAL_MISSING_FIELDS = frozenset(
    {
        "diagnosis",
        "medication",
        "authorization_type",
        "disease_activity_evidence",
        "provider_specialty",
    }
)

# Confidence bands that route a packet to human review.
REVIEW_CONFIDENCE_BANDS = frozenset({"low", "medium"})

# Minimum completeness before a packet is considered review-free.
COMPLETENESS_REVIEW_THRESHOLD = 0.85


@dataclass
class ReadinessResult:
    """Outcome of evaluating one synthetic PA case."""

    status: str
    blockers: list[str] = field(default_factory=list)
    review_reasons: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "readiness_status": self.status,
            "blockers": list(self.blockers),
            "review_reasons": list(self.review_reasons),
            "missing_fields": list(self.missing_fields),
        }


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


def evaluate_pa_case(case: dict[str, Any]) -> ReadinessResult:
    """
    Evaluate a single synthetic prior authorization case.

    Expected (synthetic) input keys:
        failed_blocker_count, missing_field_count, top_missing_field,
        confidence_band, review_required_count, data_completeness_score

    Rules (deterministic, human-readable):
        * BLOCKED   if any blocker failed, or a critical field is missing.
        * NEEDS REVIEW if confidence is low/medium, a field needs review, or
                       data completeness is below threshold.
        * READY     otherwise.
    """
    failed_blockers = _to_int(case.get("failed_blocker_count"))
    missing_count = _to_int(case.get("missing_field_count"))
    top_missing = str(case.get("top_missing_field") or "").strip()
    confidence_band = str(case.get("confidence_band") or "").strip().lower()
    review_required = _to_int(case.get("review_required_count"))
    completeness = _to_float(case.get("data_completeness_score"))

    blockers: list[str] = []
    review_reasons: list[str] = []
    missing_fields: list[str] = []

    if missing_count > 0 and top_missing:
        missing_fields.append(top_missing)

    # --- Blocking conditions ------------------------------------------------
    if failed_blockers > 0:
        blockers.append(f"{failed_blockers} payer-style blocker(s) failed")
    if missing_count > 0 and top_missing in CRITICAL_MISSING_FIELDS:
        blockers.append(f"critical field missing: {top_missing}")

    if blockers:
        return ReadinessResult(BLOCKED, blockers, review_reasons, missing_fields)

    # --- Review conditions --------------------------------------------------
    if confidence_band in REVIEW_CONFIDENCE_BANDS:
        review_reasons.append(f"{confidence_band} extraction confidence")
    if review_required > 0:
        review_reasons.append(f"{review_required} field(s) flagged for review")
    if completeness < COMPLETENESS_REVIEW_THRESHOLD:
        review_reasons.append(
            f"data completeness {completeness:.0%} below "
            f"{COMPLETENESS_REVIEW_THRESHOLD:.0%}"
        )

    if review_reasons:
        return ReadinessResult(NEEDS_REVIEW, blockers, review_reasons, missing_fields)

    return ReadinessResult(READY, blockers, review_reasons, missing_fields)


def evaluate_pa_status(case: dict[str, Any]) -> str:
    """Convenience wrapper returning just the readiness label."""
    return evaluate_pa_case(case).status
