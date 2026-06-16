"""Tests for data-quality checks across all three datasets."""

import pandas as pd

from plenara.data_quality import (
    all_checks_passed,
    check_no_phi_like_columns,
    check_synthetic_flag,
    run_authorization_checks,
    run_claim_checks,
    run_onboarding_checks,
)


def test_authorization_checks_pass(pa_df):
    assert all_checks_passed(run_authorization_checks(pa_df))


def test_onboarding_checks_pass(onboarding_df):
    assert all_checks_passed(run_onboarding_checks(onboarding_df))


def test_claim_checks_pass(claims_df):
    assert all_checks_passed(run_claim_checks(claims_df))


def test_phi_like_column_is_detected():
    bad = pd.DataFrame({"patient_name": ["x"], "ssn": ["y"]})
    result = check_no_phi_like_columns(bad)
    assert result.passed is False


def test_mock_columns_are_allowed():
    ok = pd.DataFrame({"provider_name_mock": ["Dr. Mock"], "accession_id_mock": ["ACC_1"]})
    assert check_no_phi_like_columns(ok).passed is True


def test_synthetic_flag_required():
    missing = pd.DataFrame({"x": [1, 2]})
    assert check_synthetic_flag(missing).passed is False
    present = pd.DataFrame({"synthetic_only_flag": [True, True]})
    assert check_synthetic_flag(present).passed is True


def test_no_phi_columns_in_real_datasets(pa_df, onboarding_df, claims_df):
    for df in (pa_df, onboarding_df, claims_df):
        assert check_no_phi_like_columns(df).passed is True


def test_all_synthetic_flags_true(pa_df, onboarding_df, claims_df):
    for df in (pa_df, onboarding_df, claims_df):
        assert df["synthetic_only_flag"].all()
