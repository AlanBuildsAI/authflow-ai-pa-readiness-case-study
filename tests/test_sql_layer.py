"""Tests that the SQL/dbt-style modeling layer exists and is well-formed."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "analytics" / "sql"

EXPECTED_MODELS = [
    "stg_authorization_cases",
    "stg_provider_onboarding",
    "stg_claim_readiness",
    "fct_authorization_readiness",
    "fct_provider_onboarding_readiness",
    "fct_claim_readiness",
    "mart_healthops_client_reporting",
    "mart_rcm_client_reporting",
]


@pytest.mark.parametrize("model", EXPECTED_MODELS)
def test_sql_model_file_exists(model):
    path = SQL_DIR / f"{model}.sql"
    assert path.exists(), f"missing SQL model: {model}.sql"
    text = path.read_text().lower()
    assert "select" in text
    assert model.lower() in text  # the model name is referenced in its header


def test_metric_definitions_exist_and_parse():
    yaml = pytest.importorskip("yaml")
    defs_path = ROOT / "analytics" / "metric_definitions.yml"
    assert defs_path.exists()
    defs = yaml.safe_load(defs_path.read_text())
    names = {m["name"] for m in defs["metrics"]}
    for expected in (
        "readiness_rate",
        "onboarding_ready_rate",
        "clean_claim_readiness_rate",
        "revenue_at_risk_synthetic",
    ):
        assert expected in names


def test_fact_models_assert_consistency():
    """Fact models should compare derived vs stored status (SQL/Python parity)."""
    for model in ("fct_authorization_readiness", "fct_claim_readiness", "fct_provider_onboarding_readiness"):
        text = (SQL_DIR / f"{model}.sql").read_text().lower()
        assert "consistent" in text
