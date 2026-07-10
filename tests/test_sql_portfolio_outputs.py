"""Tests for the DuckDB SQL portfolio script and its CSV outputs."""

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

pytest.importorskip("duckdb")

import run_sql_portfolio as portfolio  # noqa: E402

REQUIRED_FILES = [
    "payer_blocked_rate.csv",
    "clinic_readiness_summary.csv",
    "owner_workqueue_summary.csv",
    "top_blocker_categories.csv",
    "synthetic_revenue_at_risk_by_payer.csv",
    "readiness_status_consistency.csv",
    "executive_kpi_summary.csv",
    "aging_work_summary.csv",
]


@pytest.fixture(scope="module")
def outputs(tmp_path_factory):
    out_dir = tmp_path_factory.mktemp("sql_out")
    written = portfolio.run_portfolio(out_dir=out_dir)
    return out_dir, written


def test_all_required_files_created(outputs):
    out_dir, written = outputs
    for name in REQUIRED_FILES:
        assert (out_dir / name).exists(), f"missing {name}"
        assert name in written


def test_all_outputs_non_empty(outputs):
    out_dir, _ = outputs
    for name in REQUIRED_FILES:
        df = pd.read_csv(out_dir / name)
        assert len(df) > 0, f"{name} is empty"


def test_consistency_has_flag_and_is_consistent(outputs):
    out_dir, _ = outputs
    df = pd.read_csv(out_dir / "readiness_status_consistency.csv")
    assert "is_consistent" in df.columns
    # SQL-derived readiness must match the stored (engine-generated) labels.
    assert bool(df["is_consistent"].all())
    assert int(df["inconsistent_records"].sum()) == 0


def test_executive_kpis_have_expected_metrics(outputs):
    out_dir, _ = outputs
    df = pd.read_csv(out_dir / "executive_kpi_summary.csv")
    metrics = set(df["metric"])
    for expected in (
        "critical_blockers",
        "aging_claims_60_plus",
        "unassigned_work_items",
        "synthetic_revenue_at_risk",
        "overall_readiness_rate",
    ):
        assert expected in metrics


def test_payer_blocked_rate_is_a_rate(outputs):
    out_dir, _ = outputs
    df = pd.read_csv(out_dir / "payer_blocked_rate.csv")
    assert (df["blocked_rate"] >= 0).all() and (df["blocked_rate"] <= 1).all()


def test_revenue_at_risk_non_negative(outputs):
    out_dir, _ = outputs
    df = pd.read_csv(out_dir / "synthetic_revenue_at_risk_by_payer.csv")
    assert (df["revenue_at_risk_synthetic"] >= 0).all()
