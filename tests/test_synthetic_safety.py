"""
Repository-level safety tests.

These assert the project keeps its public-demo guarantees: synthetic flags,
no PHI-like columns, README safety language, and no obvious runtime network
calls in the app/package source.
"""

from pathlib import Path

import pytest

from plenara.data_quality import PHI_LIKE_PATTERNS, check_no_phi_like_columns

ROOT = Path(__file__).resolve().parents[1]


def test_all_datasets_flagged_synthetic(pa_df, onboarding_df, claims_df):
    for df in (pa_df, onboarding_df, claims_df):
        assert "synthetic_only_flag" in df.columns
        assert df["synthetic_only_flag"].all()


def test_no_phi_like_columns(pa_df, onboarding_df, claims_df):
    for df in (pa_df, onboarding_df, claims_df):
        assert check_no_phi_like_columns(df).passed


def test_readme_has_safety_language():
    readme = (ROOT / "README.md").read_text().lower()
    assert "synthetic" in readme
    assert "no phi" in readme
    for phrase in ("not production", "no real"):
        assert phrase in readme


def test_readme_avoids_overclaiming():
    readme = (ROOT / "README.md").read_text().lower()
    # Must not make affirmative prediction / compliance claims. (Disclaiming
    # that the project does NOT predict is expected and allowed.)
    overclaims = (
        "predicts approvals",
        "predicts denials",
        "approval probability",
        "denial probability",
        "guaranteed approval",
        "hipaa compliant",
        "hipaa-compliant",
    )
    for phrase in overclaims:
        assert phrase not in readme, f"overclaim found: {phrase}"
    # And the explicit safety disclaimer must be present.
    assert "not approval/denial predictions" in readme


@pytest.mark.parametrize("phrase", ["recruiter", "resume", "hiring"])
def test_readme_omits_non_product_terms(phrase):
    readme = (ROOT / "README.md").read_text().lower()
    assert phrase not in readme


def test_no_runtime_network_calls_in_source():
    """Guard against obvious network usage in the package and app."""
    suspect = ("requests.get", "requests.post", "urllib.request.urlopen", "httpx.")
    files = list((ROOT / "src" / "plenara").glob("*.py")) + [ROOT / "streamlit_app.py"]
    for path in files:
        text = path.read_text()
        for token in suspect:
            assert token not in text, f"{token} found in {path.name}"
