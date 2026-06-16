"""Shared pytest fixtures and path setup for the Plenara test suite."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure `import plenara` (from src/) and `import streamlit_app` (from root)
# both work without requiring PYTHONPATH to be set.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (SRC, ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from plenara import sample_data  # noqa: E402


@pytest.fixture(scope="session")
def pa_df():
    return sample_data.load_authorization_cases()


@pytest.fixture(scope="session")
def onboarding_df():
    return sample_data.load_provider_onboarding()


@pytest.fixture(scope="session")
def claims_df():
    return sample_data.load_claim_readiness()
