"""Smoke test: the Streamlit app imports cleanly without executing the UI."""

import importlib

import pytest


def test_streamlit_app_imports():
    pytest.importorskip("streamlit")
    # Importing must not run main() (guarded by __name__ == "__main__").
    module = importlib.import_module("streamlit_app")
    assert hasattr(module, "main")
    assert callable(module.main)


def test_plenara_package_imports():
    import plenara

    assert hasattr(plenara, "__version__")
    from plenara.metrics import readiness_rate  # noqa: F401
    from plenara.claims_readiness import evaluate_claim_readiness  # noqa: F401
