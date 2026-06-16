"""
Plenara — Healthcare Operations Readiness Lab (Streamlit demo).

A synthetic healthcare operations analytics demo covering three readiness
modules: prior authorization, provider onboarding, and diagnostic/lab revenue
cycle. All data is synthetic/mock. No PHI, no live integrations, no network
calls at runtime.

Run:
    PYTHONPATH=src streamlit run streamlit_app.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Make the `plenara` package importable whether or not PYTHONPATH=src is set.
_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import pandas as pd
import streamlit as st

from plenara import metrics, reporting
from plenara.claims_readiness import evaluate_claim_readiness
from plenara.data_quality import (
    run_authorization_checks,
    run_claim_checks,
    run_onboarding_checks,
)
from plenara.provider_onboarding import evaluate_provider_onboarding
from plenara.readiness import BLOCKED, NEEDS_REVIEW, READY, evaluate_pa_case
from plenara.sample_data import (
    load_authorization_cases,
    load_claim_readiness,
    load_provider_onboarding,
)

SAFETY_BANNER = (
    "Synthetic/mock data only. No PHI, no real patient data, no payer "
    "integrations, no clinical decisions, and no production use."
)
ANALYTICS_DIR = Path(__file__).resolve().parent / "analytics"


# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------
def _load_data():
    return (
        load_authorization_cases(),
        load_provider_onboarding(),
        load_claim_readiness(),
    )


def get_data():
    """Load datasets, using Streamlit cache when available."""
    cache = getattr(st, "cache_data", None)
    if cache is not None:
        return cache(_load_data)()
    return _load_data()


def _pct(value: float) -> str:
    return f"{value * 100:.0f}%"


def _money(value: float) -> str:
    return f"${value:,.0f}"


def _filter_df(df: pd.DataFrame, column: str, selected: list[str]) -> pd.DataFrame:
    if not selected or column not in df.columns:
        return df
    return df[df[column].isin(selected)]


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
def render_executive(pa_df, onb_df, claims_df):
    st.subheader("Executive HealthOps overview")
    summary = reporting.executive_summary(pa_df, onb_df, claims_df)

    st.markdown("**Prior authorization**")
    c = st.columns(4)
    c[0].metric("PA ready rate", _pct(summary["prior_authorization"]["ready_rate"]))
    c[1].metric("PA blocked rate", _pct(summary["prior_authorization"]["blocked_rate"]))
    c[2].metric("Avg data completeness", _pct(summary["prior_authorization"]["avg_data_completeness"]))
    c[3].metric("Review workload", summary["prior_authorization"]["review_workload"])

    st.markdown("**Provider onboarding**")
    c = st.columns(4)
    c[0].metric("Onboarding ready rate", _pct(summary["provider_onboarding"]["ready_rate"]))
    c[1].metric("Blocked rate", _pct(summary["provider_onboarding"]["blocked_rate"]))
    c[2].metric("Avg days in stage", f"{summary['provider_onboarding']['avg_days_in_stage']:.0f}")
    c[3].metric("Aging task rate", _pct(summary["provider_onboarding"]["aging_task_rate"]))

    st.markdown("**Diagnostic / lab revenue cycle**")
    c = st.columns(4)
    c[0].metric("Clean claim readiness", _pct(summary["revenue_cycle"]["clean_claim_readiness_rate"]))
    c[1].metric("Synthetic revenue at risk", _money(summary["revenue_cycle"]["revenue_at_risk_synthetic"]))
    c[2].metric("Top denial-risk category", summary["revenue_cycle"]["top_denial_risk_category"])
    c[3].metric("Aging claims (60d+)", summary["revenue_cycle"]["aging_claims_count"])

    st.divider()
    left, right = st.columns(2)
    with left:
        st.caption("PA readiness distribution")
        st.bar_chart(pd.Series(metrics.status_distribution(pa_df)))
        st.caption("Onboarding readiness by clinic (READY rate)")
        by_clinic = onb_df.assign(ready=(onb_df["readiness_status"] == READY).astype(float)).groupby("clinic_id")["ready"].mean()
        st.bar_chart(by_clinic)
    with right:
        st.caption("Claim readiness distribution")
        st.bar_chart(pd.Series(metrics.status_distribution(claims_df, "claim_readiness_status")))
        st.caption("Aging tasks by owner team (onboarding + claims, non-ready)")
        owners = pd.Series(metrics.workqueue_by_owner_team(claims_df))
        if not owners.empty:
            st.bar_chart(owners)

    st.info(summary["safety_notice"])


def render_prior_auth(pa_df):
    st.subheader("Prior authorization readiness")
    if pa_df.empty:
        st.warning("No PA cases match the current filters.")
        return

    case_id = st.selectbox("Select a synthetic case", pa_df["case_id"].tolist())
    row = pa_df[pa_df["case_id"] == case_id].iloc[0].to_dict()
    result = evaluate_pa_case(row)

    status_color = {READY: "🟢", NEEDS_REVIEW: "🟡", BLOCKED: "🔴"}[result.status]
    st.markdown(f"### {status_color} {result.status}")
    st.write(reporting.pa_case_explanation(row))

    c = st.columns(4)
    c[0].metric("Failed blockers", int(row.get("failed_blocker_count", 0)))
    c[1].metric("Missing fields", int(row.get("missing_field_count", 0)))
    c[2].metric("Review-required", int(row.get("review_required_count", 0)))
    c[3].metric("Data completeness", _pct(float(row.get("data_completeness_score", 0))))

    st.json(
        {
            "case_id": row.get("case_id"),
            "readiness_status": result.status,
            "blockers": result.blockers,
            "review_reasons": result.review_reasons,
            "missing_fields": result.missing_fields,
            "confidence_band": row.get("confidence_band"),
            "safety_notice": reporting.SYNTHETIC_NOTICE,
        }
    )


def render_onboarding(onb_df):
    st.subheader("Provider onboarding matrix")
    if onb_df.empty:
        st.warning("No onboarding records match the current filters.")
        return

    st.caption("Clinic × payer onboarding READY rate")
    matrix = metrics.payer_clinic_ready_rate(onb_df)
    if not matrix.empty:
        st.dataframe(matrix.style.format("{:.0%}"), use_container_width=True)

    c = st.columns(3)
    c[0].metric("Ready rate", _pct(metrics.onboarding_ready_rate(onb_df)))
    c[1].metric("Aging task rate", _pct(metrics.aging_task_rate(onb_df)))
    c[2].metric("Avg days in stage", f"{metrics.average_days_in_stage(onb_df):.0f}")

    st.caption("Top blocker categories")
    st.bar_chart(pd.Series(metrics.blocker_category_distribution(onb_df)))

    st.caption("Onboarding work queue (blocked + needs review)")
    st.dataframe(reporting.onboarding_work_queue(onb_df), use_container_width=True)


def render_revenue_cycle(claims_df):
    st.subheader("Revenue cycle readiness — diagnostic / lab")
    if claims_df.empty:
        st.warning("No claims match the current filters.")
        return

    c = st.columns(4)
    c[0].metric("Clean claim readiness", _pct(metrics.clean_claim_readiness_rate(claims_df)))
    c[1].metric("Blocked claim rate", _pct(metrics.blocked_claim_rate(claims_df)))
    c[2].metric("Needs-review rate", _pct(metrics.needs_review_claim_rate(claims_df)))
    c[3].metric("Synthetic revenue at risk", _money(metrics.revenue_at_risk_synthetic(claims_df)))

    left, right = st.columns(2)
    with left:
        st.caption("Aging bucket distribution")
        st.bar_chart(pd.Series(metrics.aging_bucket_distribution(claims_df)))
        st.caption("Denial-risk category (synthetic operational signal)")
        st.bar_chart(pd.Series(metrics.denial_risk_distribution(claims_df)))
    with right:
        st.caption("Work queue by owner team (non-ready claims)")
        st.bar_chart(pd.Series(metrics.workqueue_by_owner_team(claims_df)))
        st.caption("Synthetic revenue at risk by payer")
        st.bar_chart(pd.Series(metrics.revenue_at_risk_by_payer(claims_df)))

    st.divider()
    claim_id = st.selectbox("Inspect a synthetic claim", claims_df["claim_id"].tolist())
    row = claims_df[claims_df["claim_id"] == claim_id].iloc[0].to_dict()
    result = evaluate_claim_readiness(row)
    status_color = {READY: "🟢", NEEDS_REVIEW: "🟡", BLOCKED: "🔴"}[result.status]
    st.markdown(f"### {status_color} {result.status} — denial risk: {result.denial_risk_category}")
    st.write(reporting.claim_explanation(row))

    st.caption("RCM work queue (highest synthetic revenue at risk first)")
    st.dataframe(reporting.rcm_work_queue(claims_df), use_container_width=True)
    st.caption("Denial-risk category is a synthetic operational signal — not a denial prediction.")


def _render_checks(title, results):
    st.markdown(f"**{title}**")
    df = pd.DataFrame([r.as_dict() for r in results])
    st.dataframe(df, use_container_width=True)
    if df["passed"].all():
        st.success("All data-quality checks passed.")
    else:
        st.error("One or more data-quality checks failed.")


def render_data_quality(pa_df, onb_df, claims_df):
    st.subheader("Data quality & synthetic safety")
    st.write(
        "Every dataset is validated for structural integrity and screened for "
        "PHI-like columns. These are the same checks the test suite asserts."
    )
    _render_checks("Prior authorization", run_authorization_checks(pa_df))
    _render_checks("Provider onboarding", run_onboarding_checks(onb_df))
    _render_checks("Diagnostic / lab claims", run_claim_checks(claims_df))


def render_metrics_tab():
    st.subheader("Client reporting metrics")
    st.write(
        "Metric definitions are documented in `analytics/metric_definitions.yml` "
        "so analysts, engineers, and stakeholders share one source of truth."
    )
    yml = ANALYTICS_DIR / "metric_definitions.yml"
    try:
        import yaml

        defs = yaml.safe_load(yml.read_text())
        rows = [
            {"metric": m["name"], "module": m.get("module", ""), "definition": m.get("definition", "")}
            for m in defs.get("metrics", [])
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    except Exception:
        st.code(yml.read_text() if yml.exists() else "metric_definitions.yml not found")


def render_sql_tab():
    st.subheader("SQL / modeling layer")
    st.write(
        "A dbt-style modeling layer maps the synthetic CSVs into staging, fact, "
        "and reporting-mart models. This mirrors a real analytics-engineering "
        "workflow without connecting to a warehouse."
    )
    st.markdown(
        "- **Staging** — `stg_authorization_cases`, `stg_provider_onboarding`, "
        "`stg_claim_readiness` (type-cast / standardize)\n"
        "- **Fact** — `fct_authorization_readiness`, "
        "`fct_provider_onboarding_readiness`, `fct_claim_readiness` "
        "(derive readiness; assert SQL/Python agree)\n"
        "- **Marts** — `mart_healthops_client_reporting`, "
        "`mart_rcm_client_reporting` (client-facing summaries)"
    )
    sql_dir = ANALYTICS_DIR / "sql"
    files = sorted(sql_dir.glob("*.sql")) if sql_dir.exists() else []
    if files:
        choice = st.selectbox("View a model", [f.name for f in files])
        st.code((sql_dir / choice).read_text(), language="sql")


def render_methodology():
    st.subheader("Methodology & safety")
    st.markdown(
        """
**Synthetic data only.** Every record is fabricated and flagged
`synthetic_only_flag = True`. There is no PHI, no real patient/provider/payer
data, and no real claims or reimbursement figures.

**How readiness is decided.** Each module uses deterministic, human-readable
rules (see the `plenara` package). A record is **BLOCKED** when a critical
requirement fails, **NEEDS REVIEW** when a softer signal needs a human, and
**READY** when checks pass.

**What this is not.**
- Not a clinical decision support tool and not medical advice.
- Not an approval/denial prediction. The `denial_risk_category` is a synthetic
  operational signal derived from data-quality and payer-rule fields.
- Not production billing software and not connected to any EHR, payer, or
  claims system. No network calls happen at runtime.

**What production would require.** Secure infrastructure under regulatory
review, BAAs, encryption in transit and at rest, role-based access control,
audit logging, data retention controls, monitoring, clinical/legal review, and
human oversight.

*Any ROI or revenue-at-risk figure shown here is a synthetic operations
simulation — not observed business impact.*
        """
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    st.set_page_config(page_title="Plenara — Healthcare Operations Readiness Lab", layout="wide")

    st.title("Plenara — Healthcare Operations Readiness Lab")
    st.caption(
        "Synthetic healthcare operations analytics for prior authorization "
        "readiness, provider onboarding, diagnostic/lab revenue cycle, data "
        "quality, and stakeholder reporting."
    )
    st.warning(SAFETY_BANNER)

    pa_df, onb_df, claims_df = get_data()

    # --- Sidebar ---------------------------------------------------------
    st.sidebar.header("Controls")
    st.sidebar.subheader("Data source")
    st.sidebar.write("Using bundled synthetic data.")

    st.sidebar.subheader("Filters")
    clinics = sorted(set(pa_df["clinic_id"]) | set(onb_df["clinic_id"]) | set(claims_df["clinic_id"]))
    payers = sorted(set(onb_df["payer_name_mock"]) | set(claims_df["payer_name_mock"]))
    specialties = sorted(set(onb_df["specialty"]))
    owner_teams = sorted(set(claims_df["owner_team"]) | set(onb_df["owner_team"]))

    sel_clinics = st.sidebar.multiselect("Clinic", clinics)
    sel_payers = st.sidebar.multiselect("Payer", payers)
    sel_specialties = st.sidebar.multiselect("Specialty", specialties)
    sel_owners = st.sidebar.multiselect("Owner team", owner_teams)

    # Apply filters per dataset (only columns that exist).
    pa_f = _filter_df(pa_df, "clinic_id", sel_clinics)
    onb_f = _filter_df(_filter_df(_filter_df(_filter_df(onb_df, "clinic_id", sel_clinics), "payer_name_mock", sel_payers), "specialty", sel_specialties), "owner_team", sel_owners)
    claims_f = _filter_df(_filter_df(_filter_df(claims_df, "clinic_id", sel_clinics), "payer_name_mock", sel_payers), "owner_team", sel_owners)

    st.sidebar.subheader("About")
    st.sidebar.info(
        "Three modules: prior authorization, provider onboarding, and "
        "diagnostic/lab revenue cycle readiness. Synthetic data only."
    )

    tabs = st.tabs(
        [
            "Executive overview",
            "Prior authorization",
            "Provider onboarding",
            "Revenue cycle readiness",
            "Data quality",
            "Client reporting metrics",
            "SQL / modeling",
            "Methodology & safety",
        ]
    )
    with tabs[0]:
        render_executive(pa_f, onb_f, claims_f)
    with tabs[1]:
        render_prior_auth(pa_f)
    with tabs[2]:
        render_onboarding(onb_f)
    with tabs[3]:
        render_revenue_cycle(claims_f)
    with tabs[4]:
        render_data_quality(pa_f, onb_f, claims_f)
    with tabs[5]:
        render_metrics_tab()
    with tabs[6]:
        render_sql_tab()
    with tabs[7]:
        render_methodology()


if __name__ == "__main__":
    main()
