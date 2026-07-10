"""Tests for the deterministic executive insights module."""

from plenara import executive_insights as ei
from plenara.executive_insights import Insight


def test_build_returns_five_insights(pa_df, onboarding_df, claims_df):
    insights = ei.build_executive_insights(pa_df, onboarding_df, claims_df)
    assert len(insights) == 5
    for ins in insights:
        assert isinstance(ins, Insight)
        assert isinstance(ins.text, str) and len(ins.text) > 10
        assert ins.text[0].isupper()  # reads like a sentence


def test_individual_insights_return_strings(pa_df, onboarding_df, claims_df):
    assert ei.highest_blocked_rate_payer(onboarding_df, claims_df).text
    assert ei.weakest_readiness_workflow(pa_df, onboarding_df, claims_df).text
    assert ei.largest_owner_workqueue(pa_df, onboarding_df, claims_df).text
    assert ei.highest_revenue_at_risk_payer(claims_df).text
    assert ei.most_common_blocker_category(pa_df, onboarding_df, claims_df).text
    assert ei.aging_work_summary(claims_df).text


def test_insights_carry_supporting_values(pa_df, onboarding_df, claims_df):
    weakest = ei.weakest_readiness_workflow(pa_df, onboarding_df, claims_df)
    assert weakest.value is not None
    assert "workflow" in weakest.value


def test_prioritize_today_is_actionable(pa_df, onboarding_df, claims_df):
    line = ei.prioritize_today(pa_df, onboarding_df, claims_df)
    assert isinstance(line, str) and len(line) > 10


def test_insights_do_not_crash_on_empty():
    import pandas as pd

    empty = pd.DataFrame()
    insights = ei.build_executive_insights(empty, empty, empty)
    assert len(insights) == 5
    for ins in insights:
        assert isinstance(ins.text, str) and ins.text
    assert isinstance(ei.prioritize_today(empty, empty, empty), str)


def test_highest_revenue_payer_matches_data(claims_df):
    from plenara import metrics

    ins = ei.highest_revenue_at_risk_payer(claims_df)
    by_payer = metrics.revenue_at_risk_by_payer(claims_df)
    expected = max(by_payer, key=by_payer.get)
    assert ins.value["payer"] == expected
