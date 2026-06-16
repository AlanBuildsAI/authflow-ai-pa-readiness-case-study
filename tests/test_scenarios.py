"""Tests for synthetic scenario profiles and their effect on generated data."""

import pytest

from plenara import sample_data as sd
from plenara.metrics import blocked_rate, readiness_rate
from plenara.scenarios import DEFAULT_SCENARIO, SCENARIOS, get_scenario

EXPECTED_SCENARIOS = {
    "stable_operations",
    "moderate_backlog",
    "high_friction_payer_environment",
    "onboarding_surge",
    "rcm_cleanup_queue",
}


def test_expected_scenarios_exist():
    assert EXPECTED_SCENARIOS.issubset(set(SCENARIOS))


@pytest.mark.parametrize("key", sorted(EXPECTED_SCENARIOS))
def test_scenario_profile_shape(key):
    p = SCENARIOS[key]
    assert p.label and p.description and p.intended_use and p.ui_copy
    assert len(p.profile_mix) == 3
    assert abs(sum(p.mix()) - 1.0) < 1e-9
    assert p.blocker_emphasis  # non-empty


def test_default_scenario_resolves():
    assert get_scenario(DEFAULT_SCENARIO).key == DEFAULT_SCENARIO
    assert get_scenario("does_not_exist").key == DEFAULT_SCENARIO


def test_each_scenario_produces_all_three_states():
    for key in EXPECTED_SCENARIOS:
        claims = sd.generate_claim_readiness(scenario=key)
        states = set(claims["claim_readiness_status"].unique())
        assert states == {"READY", "NEEDS REVIEW", "BLOCKED"}, f"{key}: {states}"


def test_stable_is_cleaner_than_high_friction():
    stable = sd.generate_claim_readiness(scenario="stable_operations")
    high = sd.generate_claim_readiness(scenario="high_friction_payer_environment")
    assert readiness_rate(stable, "claim_readiness_status") > readiness_rate(high, "claim_readiness_status")
    assert blocked_rate(high, "claim_readiness_status") > blocked_rate(stable, "claim_readiness_status")


def test_rcm_cleanup_has_more_blocked_than_stable():
    stable = sd.generate_claim_readiness(scenario="stable_operations")
    cleanup = sd.generate_claim_readiness(scenario="rcm_cleanup_queue")
    assert blocked_rate(cleanup, "claim_readiness_status") > blocked_rate(stable, "claim_readiness_status")
