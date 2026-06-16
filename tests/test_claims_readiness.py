"""Tests for the diagnostic / lab revenue cycle claim readiness engine."""

from plenara.claims_readiness import (
    BLOCKED,
    NEEDS_REVIEW,
    READY,
    aging_bucket,
    evaluate_claim_readiness,
    evaluate_claim_status,
)


def _clean():
    return {
        "eligibility_status": "verified",
        "prior_auth_status": "obtained",
        "documentation_status": "complete",
        "coding_status": "valid",
        "modifier_status": "correct",
        "payer_rule_status": "pass",
        "timely_filing_status": "within_window",
        "failed_rule_count": 0,
        "review_required_count": 0,
        "data_completeness_score": 0.97,
        "days_since_service": 10,
    }


def test_ready_claim():
    result = evaluate_claim_readiness(_clean())
    assert result.status == READY
    assert result.denial_risk_category == "low"


def test_blocked_on_eligibility_mismatch():
    claim = _clean()
    claim["eligibility_status"] = "mismatch"
    result = evaluate_claim_readiness(claim)
    assert result.status == BLOCKED
    assert result.denial_risk_category == "high"


def test_blocked_on_missing_prior_auth():
    claim = _clean()
    claim["prior_auth_status"] = "missing"
    assert evaluate_claim_status(claim) == BLOCKED


def test_blocked_on_coding_mismatch():
    claim = _clean()
    claim["coding_status"] = "mismatch"
    assert evaluate_claim_status(claim) == BLOCKED


def test_blocked_on_timely_filing_expired():
    claim = _clean()
    claim["timely_filing_status"] = "expired"
    assert evaluate_claim_status(claim) == BLOCKED


def test_blocked_on_payer_rule_fail():
    claim = _clean()
    claim["payer_rule_status"] = "fail"
    assert evaluate_claim_status(claim) == BLOCKED


def test_review_on_missing_modifier():
    claim = _clean()
    claim["modifier_status"] = "missing"
    result = evaluate_claim_readiness(claim)
    assert result.status == NEEDS_REVIEW
    assert result.denial_risk_category == "medium"


def test_review_on_unverified_eligibility():
    claim = _clean()
    claim["eligibility_status"] = "unverified"
    assert evaluate_claim_status(claim) == NEEDS_REVIEW


def test_review_on_aging_claim():
    claim = _clean()
    claim["days_since_service"] = 60
    assert evaluate_claim_status(claim) == NEEDS_REVIEW


def test_aging_bucket_boundaries():
    assert aging_bucket(0) == "0-30"
    assert aging_bucket(30) == "0-30"
    assert aging_bucket(31) == "31-60"
    assert aging_bucket(75) == "61-90"
    assert aging_bucket(200) == "90+"


def test_dataset_matches_engine(claims_df):
    recomputed = claims_df.apply(lambda r: evaluate_claim_status(r.to_dict()), axis=1)
    assert (recomputed == claims_df["claim_readiness_status"]).all()


def test_dataset_has_all_three_states(claims_df):
    assert set(claims_df["claim_readiness_status"].unique()) == {READY, NEEDS_REVIEW, BLOCKED}
