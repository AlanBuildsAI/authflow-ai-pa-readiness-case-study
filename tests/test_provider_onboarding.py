"""Tests for the provider onboarding readiness engine."""

from plenara.provider_onboarding import (
    BLOCKED,
    NEEDS_REVIEW,
    READY,
    evaluate_onboarding_status,
    evaluate_provider_onboarding,
)


def _clean():
    return {
        "credentialing_status": "complete",
        "contract_status": "active",
        "directory_status": "updated",
        "enrollment_status": "enrolled",
        "documentation_status": "complete",
        "caqh_status": "current",
        "npi_status": "verified",
        "license_status": "verified",
        "effective_date_status": "set",
        "days_in_stage": 5,
        "owner_team": "Credentialing",
        "readiness_score": 0.95,
    }


def test_ready_record():
    assert evaluate_onboarding_status(_clean()) == READY


def test_blocked_on_missing_credentialing():
    rec = _clean()
    rec["credentialing_status"] = "missing"
    result = evaluate_provider_onboarding(rec)
    assert result.status == BLOCKED
    assert result.blocker_category == "missing credentialing packet"


def test_blocked_on_inactive_contract():
    rec = _clean()
    rec["contract_status"] = "not_active"
    assert evaluate_onboarding_status(rec) == BLOCKED


def test_blocked_on_expired_license():
    rec = _clean()
    rec["license_status"] = "expired"
    assert evaluate_onboarding_status(rec) == BLOCKED


def test_blocked_on_npi_mismatch():
    rec = _clean()
    rec["npi_status"] = "mismatch"
    assert evaluate_onboarding_status(rec) == BLOCKED


def test_review_on_stale_caqh():
    rec = _clean()
    rec["caqh_status"] = "stale"
    assert evaluate_onboarding_status(rec) == NEEDS_REVIEW


def test_review_on_aging_stage():
    rec = _clean()
    rec["days_in_stage"] = 45
    assert evaluate_onboarding_status(rec) == NEEDS_REVIEW


def test_review_on_unassigned_owner():
    rec = _clean()
    rec["owner_team"] = "unassigned"
    assert evaluate_onboarding_status(rec) == NEEDS_REVIEW


def test_dataset_matches_engine(onboarding_df):
    recomputed = onboarding_df.apply(lambda r: evaluate_onboarding_status(r.to_dict()), axis=1)
    assert (recomputed == onboarding_df["readiness_status"]).all()


def test_dataset_has_all_three_states(onboarding_df):
    assert set(onboarding_df["readiness_status"].unique()) == {READY, NEEDS_REVIEW, BLOCKED}
