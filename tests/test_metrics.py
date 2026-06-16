"""Tests for client-reporting metrics."""

import pandas as pd

from plenara import metrics


def test_readiness_rate_simple():
    df = pd.DataFrame({"readiness_status": ["READY", "READY", "BLOCKED", "NEEDS REVIEW"]})
    assert metrics.readiness_rate(df) == 0.5
    assert metrics.blocked_rate(df) == 0.25
    assert metrics.needs_review_rate(df) == 0.25


def test_rates_sum_to_one(pa_df):
    total = metrics.readiness_rate(pa_df) + metrics.blocked_rate(pa_df) + metrics.needs_review_rate(pa_df)
    assert abs(total - 1.0) < 1e-9


def test_status_distribution_counts(pa_df):
    dist = metrics.status_distribution(pa_df)
    assert sum(dist.values()) == len(pa_df)


def test_clean_claim_rate_matches_distribution(claims_df):
    dist = metrics.status_distribution(claims_df, "claim_readiness_status")
    expected = dist["READY"] / len(claims_df)
    assert abs(metrics.clean_claim_readiness_rate(claims_df) - expected) < 1e-9


def test_revenue_at_risk_non_negative(claims_df):
    assert metrics.revenue_at_risk_synthetic(claims_df) >= 0


def test_revenue_at_risk_matches_sum(claims_df):
    expected = round(float(claims_df["estimated_revenue_at_risk_synthetic"].sum()), 2)
    assert metrics.revenue_at_risk_synthetic(claims_df) == expected


def test_denial_risk_distribution_keys(claims_df):
    dist = metrics.denial_risk_distribution(claims_df)
    assert set(dist).issubset({"low", "medium", "high"})
    assert sum(dist.values()) == len(claims_df)


def test_aging_bucket_distribution_order(claims_df):
    dist = metrics.aging_bucket_distribution(claims_df)
    assert list(dist.keys()) == ["0-30", "31-60", "61-90", "90+"]
    assert sum(dist.values()) == len(claims_df)


def test_workqueue_excludes_ready(claims_df):
    wq = metrics.workqueue_by_owner_team(claims_df)
    ready = claims_df[claims_df["claim_readiness_status"] == "READY"]
    not_ready = len(claims_df) - len(ready)
    assert sum(wq.values()) == not_ready


def test_payer_clinic_matrix_shape(onboarding_df):
    matrix = metrics.payer_clinic_ready_rate(onboarding_df)
    assert not matrix.empty
    # Values are rates in [0, 1].
    assert matrix.fillna(0).to_numpy().max() <= 1.0


def test_empty_df_safe():
    empty = pd.DataFrame()
    assert metrics.readiness_rate(empty) == 0.0
    assert metrics.revenue_at_risk_synthetic(empty) == 0.0
    assert metrics.denial_risk_distribution(empty) == {}
