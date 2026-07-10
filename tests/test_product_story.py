"""Tests for the product story module (consistent, safe product copy)."""

from plenara import product_story as ps


def test_core_copy_present():
    assert ps.ONE_LINER and "synthetic" in ps.POSITIONING.lower()
    assert ps.VALUE_PROPOSITION
    assert ps.HUMAN_IN_THE_LOOP


def test_synthetic_safety_language():
    note = ps.SYNTHETIC_SAFETY_NOTE.lower()
    assert "synthetic" in note
    assert "no phi" in note


def test_three_workflows():
    names = ps.workflow_names()
    assert len(names) == 3
    joined = " ".join(names).lower()
    assert "prior authorization" in joined
    assert "onboarding" in joined
    assert "revenue cycle" in joined


def test_readiness_definitions_cover_all_states():
    assert set(ps.READINESS_DEFINITIONS) == {"READY", "NEEDS REVIEW", "BLOCKED"}
    assert "READY" in ps.readiness_legend()


def test_target_roles_and_users_nonempty():
    assert len(ps.TARGET_JOB_ROLES) >= 5
    assert len(ps.TARGET_USERS) >= 4
    assert "Data Analyst" in ps.TARGET_JOB_ROLES


def test_does_not_claim_guardrails():
    joined = " ".join(ps.DOES_NOT_CLAIM).lower()
    for phrase in ("hipaa", "clinical decision support", "predicts"):
        assert phrase in joined


def test_design_partner_questions_present():
    assert len(ps.DESIGN_PARTNER_QUESTIONS) >= 5
