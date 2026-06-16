"""
Diagnostic / Lab Revenue Cycle (RCM) claim readiness engine (synthetic).

Models whether a synthetic diagnostic/lab claim or billing packet is ready for
clean submission, needs review, or is blocked due to eligibility, authorization,
coding, documentation, modifier, payer-rule, timely-filing, or work-queue
ownership issues.

Safety / scope:
- Fully synthetic/mock only. No PHI, no real claims, no real payer contracts,
  no real reimbursement rates.
- "denial_risk_category" is a synthetic operational categorization derived from
  data-quality and payer-rule signals. It is NOT a denial prediction and not a
  statement of real reimbursement outcomes.
- This is a readiness diagnostic for workflow analytics, not production billing
  software.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .readiness import BLOCKED, NEEDS_REVIEW, READY

# Days since date of service beyond which a claim is flagged for review (aging).
DAYS_SINCE_SERVICE_REVIEW_THRESHOLD = 45

# Minimum completeness before a claim is considered review-free.
CLAIM_COMPLETENESS_REVIEW_THRESHOLD = 0.85

# Synthetic denial-risk categories (operational signal, not a prediction).
DENIAL_RISK_LOW = "low"
DENIAL_RISK_MEDIUM = "medium"
DENIAL_RISK_HIGH = "high"

# Blocking status values keyed by field; first match becomes the primary blocker.
BLOCKING_RULES: tuple[tuple[str, frozenset[str], str], ...] = (
    ("eligibility_status", frozenset({"inactive", "mismatch"}), "eligibility mismatch"),
    ("prior_auth_status", frozenset({"missing"}), "missing prior authorization"),
    ("coding_status", frozenset({"missing", "mismatch"}), "procedure / diagnosis mismatch"),
    ("payer_rule_status", frozenset({"fail"}), "payer-specific rule failed"),
    ("timely_filing_status", frozenset({"expired"}), "timely filing risk"),
)

# Review-only status values keyed by field.
REVIEW_RULES: tuple[tuple[str, frozenset[str], str], ...] = (
    ("eligibility_status", frozenset({"unverified"}), "eligibility unverified"),
    ("documentation_status", frozenset({"incomplete", "stale"}), "payer documentation incomplete"),
    ("modifier_status", frozenset({"missing", "invalid"}), "modifier required"),
    ("payer_rule_status", frozenset({"review"}), "payer rule needs review"),
    ("timely_filing_status", frozenset({"at_risk"}), "timely filing at risk"),
)


@dataclass
class ClaimReadinessResult:
    """Outcome of evaluating one synthetic diagnostic/lab claim."""

    status: str
    denial_risk_category: str = DENIAL_RISK_LOW
    blocker_category: str | None = None
    blockers: list[str] = field(default_factory=list)
    review_reasons: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "claim_readiness_status": self.status,
            "denial_risk_category": self.denial_risk_category,
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


def evaluate_claim_readiness(claim: dict[str, Any]) -> ClaimReadinessResult:
    """
    Evaluate a single synthetic diagnostic/lab claim for submission readiness.

    Rules:
        * BLOCKED if a critical billing status is failed/missing/mismatched,
          timely filing is expired, or any payer-style rule failed.
        * NEEDS REVIEW if a softer issue is present (unverified eligibility,
          incomplete/stale documentation, missing/invalid modifier, payer rule
          flagged for review, timely-filing at risk, low completeness, aged
          claim, or review_required_count > 0).
        * READY otherwise.

    denial_risk_category is a synthetic operational signal:
        BLOCKED -> high, NEEDS REVIEW -> medium, READY -> low.
    """
    blockers: list[str] = []
    review_reasons: list[str] = []
    blocker_category: str | None = None

    # --- Blocking conditions ------------------------------------------------
    for field_name, bad_values, label in BLOCKING_RULES:
        if _norm(claim.get(field_name)) in bad_values:
            blockers.append(label)
            if blocker_category is None:
                blocker_category = label

    if _to_int(claim.get("failed_rule_count")) > 0 and not blockers:
        blockers.append("payer-style rule failed")
        blocker_category = "payer-specific rule failed"

    if blockers:
        return ClaimReadinessResult(
            BLOCKED, DENIAL_RISK_HIGH, blocker_category, blockers, review_reasons
        )

    # --- Review conditions --------------------------------------------------
    for field_name, flag_values, label in REVIEW_RULES:
        if _norm(claim.get(field_name)) in flag_values:
            review_reasons.append(label)

    if _to_int(claim.get("review_required_count")) > 0:
        review_reasons.append(
            f"{_to_int(claim.get('review_required_count'))} field(s) flagged for review"
        )

    completeness = _to_float(claim.get("data_completeness_score"), default=1.0)
    if completeness < CLAIM_COMPLETENESS_REVIEW_THRESHOLD:
        review_reasons.append(
            f"data completeness {completeness:.0%} below "
            f"{CLAIM_COMPLETENESS_REVIEW_THRESHOLD:.0%}"
        )

    days_since_service = _to_int(claim.get("days_since_service"))
    if days_since_service > DAYS_SINCE_SERVICE_REVIEW_THRESHOLD:
        review_reasons.append(f"claim aging ({days_since_service} days since service)")

    if review_reasons:
        review_category = review_reasons[0]
        return ClaimReadinessResult(
            NEEDS_REVIEW, DENIAL_RISK_MEDIUM, review_category, blockers, review_reasons
        )

    return ClaimReadinessResult(READY, DENIAL_RISK_LOW, None, blockers, review_reasons)


def evaluate_claim_status(claim: dict[str, Any]) -> str:
    """Convenience wrapper returning just the readiness label."""
    return evaluate_claim_readiness(claim).status


def aging_bucket(days_since_service: Any) -> str:
    """Map days-since-service to a standard A/R aging bucket."""
    days = _to_int(days_since_service)
    if days <= 30:
        return "0-30"
    if days <= 60:
        return "31-60"
    if days <= 90:
        return "61-90"
    return "90+"
