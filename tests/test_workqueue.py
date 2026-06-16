"""Tests for the unified work queue, severity rules, and top actions."""

from plenara.workqueue import (
    ONBOARDING,
    PRIOR_AUTH,
    REVENUE_CYCLE,
    WORK_QUEUE_COLUMNS,
    build_unified_work_queue,
    recommended_action_from_record,
    severity_from_record,
    summarize_top_actions,
)


# --- severity rules --------------------------------------------------------
def test_severity_unassigned_non_ready_is_high():
    assert severity_from_record(REVENUE_CYCLE, "NEEDS REVIEW", 5, 0.0, "unassigned") == "High"


def test_severity_blocked_aging_is_high():
    assert severity_from_record(REVENUE_CYCLE, "BLOCKED", 90, 0.0, "Billing") == "High"


def test_severity_blocked_high_revenue_is_high():
    assert severity_from_record(REVENUE_CYCLE, "BLOCKED", 5, 1500.0, "Billing") == "High"


def test_severity_blocked_fresh_low_impact_is_medium():
    assert severity_from_record(PRIOR_AUTH, "BLOCKED", 1, 0.0, "Intake") == "Medium"


def test_severity_needs_review_is_medium():
    assert severity_from_record(ONBOARDING, "NEEDS REVIEW", 5, 0.0, "Credentialing") == "Medium"


def test_severity_ready_is_low():
    assert severity_from_record(PRIOR_AUTH, "READY", 0, 0.0, "Intake") == "Low"


# --- recommended actions ---------------------------------------------------
def test_action_ready_needs_nothing():
    assert "no action" in recommended_action_from_record(PRIOR_AUTH, "READY", "none", "Intake").lower()


def test_action_unassigned_assigns_owner():
    msg = recommended_action_from_record(REVENUE_CYCLE, "BLOCKED", "eligibility mismatch", "unassigned")
    assert "assign owner team" in msg.lower()


def test_action_known_category_is_mapped():
    msg = recommended_action_from_record(REVENUE_CYCLE, "BLOCKED", "missing prior authorization", "Billing")
    assert "prior authorization" in msg.lower()


# --- unified queue ---------------------------------------------------------
def test_build_unified_work_queue_columns(pa_df, onboarding_df, claims_df):
    wq = build_unified_work_queue(pa_df, onboarding_df, claims_df)
    assert list(wq.columns) == WORK_QUEUE_COLUMNS
    assert not wq.empty


def test_work_queue_excludes_ready_by_default(pa_df, onboarding_df, claims_df):
    wq = build_unified_work_queue(pa_df, onboarding_df, claims_df)
    assert (wq["readiness_status"] != "READY").all()


def test_work_queue_includes_all_modules(pa_df, onboarding_df, claims_df):
    wq = build_unified_work_queue(pa_df, onboarding_df, claims_df)
    assert set(wq["module"].unique()) == {PRIOR_AUTH, ONBOARDING, REVENUE_CYCLE}


def test_work_queue_sorted_high_first(pa_df, onboarding_df, claims_df):
    wq = build_unified_work_queue(pa_df, onboarding_df, claims_df)
    sev = list(wq["severity"])
    # High block should precede the first Medium.
    if "High" in sev and "Medium" in sev:
        assert sev.index("High") < sev.index("Medium")


def test_top_actions_shape(pa_df, onboarding_df, claims_df):
    wq = build_unified_work_queue(pa_df, onboarding_df, claims_df)
    actions = summarize_top_actions(wq, limit=6)
    assert 0 < len(actions) <= 6
    for a in actions:
        assert {"module", "issue", "why", "recommended_action", "affected_records", "synthetic_impact"} <= set(a)
        assert a["affected_records"] >= 1


def test_top_actions_empty_queue():
    import pandas as pd

    empty = pd.DataFrame(columns=WORK_QUEUE_COLUMNS)
    assert summarize_top_actions(empty) == []
