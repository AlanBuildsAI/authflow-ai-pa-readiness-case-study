"""
Dataset-realism (calibration) tests.

These assert the *designed* operational patterns hold in the bundled synthetic
data: blocked records carry stronger signals than ready ones, aging correlates
with non-ready states, and synthetic revenue at risk concentrates in non-ready
claims. These are synthetic-design guarantees, not real-world benchmarks.
"""

from plenara.readiness import BLOCKED, NEEDS_REVIEW, READY


def test_blocked_pa_has_stronger_signals_than_ready(pa_df):
    blocked = pa_df[pa_df["readiness_status"] == BLOCKED]
    ready = pa_df[pa_df["readiness_status"] == READY]
    assert blocked["failed_blocker_count"].mean() > ready["failed_blocker_count"].mean()
    assert ready["data_completeness_score"].mean() >= blocked["data_completeness_score"].mean()


def test_ready_pa_has_low_blockers(pa_df):
    ready = pa_df[pa_df["readiness_status"] == READY]
    assert (ready["failed_blocker_count"] == 0).all()


def test_claim_aging_correlates_with_status(claims_df):
    mean_age = claims_df.groupby("claim_readiness_status")["days_since_service"].mean()
    assert mean_age[BLOCKED] > mean_age[READY]
    assert mean_age[NEEDS_REVIEW] > mean_age[READY]


def test_onboarding_aging_correlates_with_status(onboarding_df):
    mean_age = onboarding_df.groupby("readiness_status")["days_in_stage"].mean()
    assert mean_age[BLOCKED] > mean_age[READY]


def test_revenue_at_risk_non_negative(claims_df):
    assert (claims_df["estimated_revenue_at_risk_synthetic"] >= 0).all()


def test_revenue_concentrated_in_non_ready(claims_df):
    ready = claims_df[claims_df["claim_readiness_status"] == READY]
    non_ready = claims_df[claims_df["claim_readiness_status"] != READY]
    assert ready["estimated_revenue_at_risk_synthetic"].sum() == 0
    assert non_ready["estimated_revenue_at_risk_synthetic"].sum() > 0


def test_blocked_claims_carry_more_revenue_than_review(claims_df):
    blocked = claims_df[claims_df["claim_readiness_status"] == BLOCKED]
    review = claims_df[claims_df["claim_readiness_status"] == NEEDS_REVIEW]
    assert blocked["estimated_revenue_at_risk_synthetic"].mean() > review["estimated_revenue_at_risk_synthetic"].mean()


def test_clinic_friction_varies_blocked_rate(claims_df):
    """Designed friction means blocked rate is not uniform across clinics."""
    rate = claims_df.assign(b=(claims_df["claim_readiness_status"] == BLOCKED)).groupby("clinic_id")["b"].mean()
    assert rate.max() - rate.min() > 0.05


def test_blocked_records_are_owned(pa_df, onboarding_df, claims_df):
    def unowned(df, status_col):
        blocked = df[df[status_col] == BLOCKED]
        owner = blocked["owner_team"].astype(str).str.strip().str.lower()
        return owner.isin({"", "unassigned", "none", "n/a", "nan"}).any()

    assert not unowned(pa_df, "readiness_status")
    assert not unowned(onboarding_df, "readiness_status")
    assert not unowned(claims_df, "claim_readiness_status")
