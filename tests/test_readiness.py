"""Tests for the prior authorization readiness engine."""

from plenara.readiness import BLOCKED, NEEDS_REVIEW, READY, evaluate_pa_case, evaluate_pa_status


def _base():
    return {
        "failed_blocker_count": 0,
        "missing_field_count": 0,
        "top_missing_field": "none",
        "confidence_band": "high",
        "review_required_count": 0,
        "data_completeness_score": 0.98,
    }


def test_ready_case():
    assert evaluate_pa_status(_base()) == READY


def test_blocked_on_failed_blocker():
    case = _base()
    case["failed_blocker_count"] = 1
    result = evaluate_pa_case(case)
    assert result.status == BLOCKED
    assert result.blockers


def test_blocked_on_critical_missing_field():
    case = _base()
    case["missing_field_count"] = 1
    case["top_missing_field"] = "diagnosis"
    assert evaluate_pa_status(case) == BLOCKED


def test_needs_review_on_low_confidence():
    case = _base()
    case["confidence_band"] = "low"
    assert evaluate_pa_status(case) == NEEDS_REVIEW


def test_needs_review_on_review_required():
    case = _base()
    case["review_required_count"] = 2
    assert evaluate_pa_status(case) == NEEDS_REVIEW


def test_needs_review_on_low_completeness():
    case = _base()
    case["data_completeness_score"] = 0.7
    assert evaluate_pa_status(case) == NEEDS_REVIEW


def test_noncritical_missing_is_not_blocking():
    case = _base()
    case["missing_field_count"] = 1
    case["top_missing_field"] = "clinical_note_completeness"
    # Not a critical field -> should not block (high confidence/completeness).
    assert evaluate_pa_status(case) == READY


def test_blocker_precedence_over_review():
    case = _base()
    case["failed_blocker_count"] = 1
    case["confidence_band"] = "low"
    assert evaluate_pa_status(case) == BLOCKED


def test_dataset_matches_engine(pa_df):
    """Every bundled row must match the engine's recomputed status."""
    recomputed = pa_df.apply(lambda r: evaluate_pa_status(r.to_dict()), axis=1)
    assert (recomputed == pa_df["readiness_status"]).all()


def test_dataset_has_all_three_states(pa_df):
    states = set(pa_df["readiness_status"].unique())
    assert states == {READY, NEEDS_REVIEW, BLOCKED}
