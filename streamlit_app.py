"""
Plenara — Healthcare Operations Readiness Lab (Streamlit command center).

A synthetic healthcare operations readiness product demo across three modules:
prior authorization, provider onboarding, and diagnostic/lab revenue cycle.
The app is organized as an operations command center: what is blocked, why, who
owns it, what to do next, what is aging, and where the friction is.

All data is synthetic/mock. No PHI, no live integrations, no network calls at
runtime, and no approval/denial prediction.

Run:
    PYTHONPATH=src streamlit run streamlit_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

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
    generate_all,
    load_authorization_cases,
    load_claim_readiness,
    load_provider_onboarding,
)
from plenara.scenarios import DEFAULT_SCENARIO, SCENARIOS
from plenara.workqueue import build_unified_work_queue, summarize_top_actions

SAFETY_BANNER = (
    "Synthetic / mock data only. No PHI, no real patient/provider/payer/claims "
    "data, no live integrations, no network calls, and no approval/denial prediction."
)
ANALYTICS_DIR = Path(__file__).resolve().parent / "analytics"
STATUS_ICON = {READY: "🟢", NEEDS_REVIEW: "🟡", BLOCKED: "🔴"}
SEVERITY_ICON = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}

BUNDLED_LABEL = "Bundled data (moderate backlog)"


# ---------------------------------------------------------------------------
# Data loading (cached per scenario)
# ---------------------------------------------------------------------------
def _load_bundled():
    return load_authorization_cases(), load_provider_onboarding(), load_claim_readiness()


def _generate(scenario_key: str):
    frames = generate_all(scenario_key)
    return frames["authorization"], frames["provider_onboarding"], frames["claim_readiness"]


def _maybe_cache(fn):
    cache = getattr(st, "cache_data", None)
    return cache(fn) if cache is not None else fn


_load_bundled_cached = _maybe_cache(_load_bundled)
_generate_cached = _maybe_cache(_generate)


def get_data(scenario_label: str):
    if scenario_label == BUNDLED_LABEL:
        return _load_bundled_cached()
    return _generate_cached(scenario_label)


def _pct(value: float) -> str:
    return f"{value * 100:.0f}%"


def _money(value: float) -> str:
    return f"${value:,.0f}"


def _filter(df: pd.DataFrame, column: str, selected: list[str]) -> pd.DataFrame:
    if not selected or column not in df.columns:
        return df
    return df[df[column].isin(selected)]


# ---------------------------------------------------------------------------
# Command center
# ---------------------------------------------------------------------------
def render_command_center(pa_df, onb_df, claims_df, work_queue):
    st.subheader("Command center")
    st.caption("What is blocked, what is aging, who owns it, and what to prioritize today.")

    kpis = reporting.command_center_kpis(pa_df, onb_df, claims_df)
    c = st.columns(5)
    c[0].metric("Critical blockers", kpis["critical_blockers"])
    c[1].metric("Aging claims 60+", kpis["aging_claims_60_plus"])
    c[2].metric("Unassigned work items", kpis["unassigned_work_items"])
    c[3].metric("Synthetic revenue at risk", _money(kpis["revenue_at_risk_synthetic"]))
    c[4].metric("Overall readiness rate", _pct(kpis["overall_readiness_rate"]))

    st.divider()
    st.markdown("### Top actions for today")
    actions = summarize_top_actions(work_queue)
    if not actions:
        st.success("No high-priority actions in the current view.")
    for a in actions:
        impact = f" · synthetic impact {_money(a['synthetic_impact'])}" if a["synthetic_impact"] else ""
        with st.container(border=True):
            st.markdown(f"**[{a['module']}] {a['issue']}** — {a['affected_records']} record(s){impact}")
            st.caption(f"Why it matters: {a['why']}")
            st.markdown(f"➡️ **Recommended next action:** {a['recommended_action']}")

    st.divider()
    left, right = st.columns(2)
    with left:
        st.caption("Readiness by workflow")
        frame = pd.DataFrame(
            {
                "Prior auth": metrics.status_distribution(pa_df),
                "Onboarding": metrics.status_distribution(onb_df),
                "Revenue cycle": metrics.status_distribution(claims_df, "claim_readiness_status"),
            }
        )
        st.bar_chart(frame)
    with right:
        st.caption("Synthetic revenue at risk by payer")
        rev = pd.Series(metrics.revenue_at_risk_by_payer(claims_df))
        if not rev.empty:
            st.bar_chart(rev)

    st.info(kpis["safety_notice"])


# ---------------------------------------------------------------------------
# Unified work queue
# ---------------------------------------------------------------------------
def render_work_queue(work_queue):
    st.subheader("Work queue")
    st.caption("One prioritized queue across all three workflows. Severity drives the order.")

    cols = st.columns(3)
    modules = cols[0].multiselect("Module", sorted(work_queue["module"].unique()))
    severities = cols[1].multiselect("Severity", ["High", "Medium", "Low"])
    owners = cols[2].multiselect("Owner team", sorted(work_queue["owner_team"].astype(str).unique()))

    view = work_queue
    view = _filter(view, "module", modules)
    view = _filter(view, "severity", severities)
    view = _filter(view, "owner_team", owners)

    sev = view["severity"].value_counts().to_dict()
    s = st.columns(3)
    s[0].metric("High", sev.get("High", 0))
    s[1].metric("Medium", sev.get("Medium", 0))
    s[2].metric("Total in queue", len(view))

    display = view.copy()
    display["severity"] = display["severity"].map(lambda x: f"{SEVERITY_ICON.get(x, '')} {x}")
    display["synthetic_impact"] = display["synthetic_impact"].map(lambda v: _money(v) if v else "—")
    display["age_days"] = display["age_days"].astype(int)
    st.dataframe(display, use_container_width=True, hide_index=True)
    st.caption(
        "Severity — High: blocked + aging beyond internal SLA / high synthetic impact / "
        "unassigned owner. Medium: other blocked or needs-review. Low: ready / informational."
    )


# ---------------------------------------------------------------------------
# Module tabs
# ---------------------------------------------------------------------------
def render_prior_auth(pa_df):
    st.subheader("Prior auth — submission readiness")
    if pa_df.empty:
        st.warning("No prior authorization cases match the current filters.")
        return

    case_id = st.selectbox("Select a synthetic case", pa_df["case_id"].tolist())
    row = pa_df[pa_df["case_id"] == case_id].iloc[0].to_dict()
    result = evaluate_pa_case(row)

    st.markdown(f"### {STATUS_ICON[result.status]} {result.status}")
    c = st.columns(4)
    c[0].metric("Failed blockers", int(row.get("failed_blocker_count", 0)))
    c[1].metric("Missing fields", int(row.get("missing_field_count", 0)))
    c[2].metric("Needs review", int(row.get("review_required_count", 0)))
    c[3].metric("Data completeness", _pct(float(row.get("data_completeness_score", 0))))

    st.markdown("**Readiness blockers**")
    if result.blockers:
        for b in result.blockers:
            st.markdown(f"- 🔴 {b}")
    elif result.review_reasons:
        for r in result.review_reasons:
            st.markdown(f"- 🟡 {r}")
    else:
        st.markdown("- 🟢 No blockers — ready for submission.")

    st.markdown(f"**Recommended next action:** {reporting.pa_case_explanation(row)}")
    st.markdown("**What would make it READY**")
    for step in reporting.pa_path_to_ready(row):
        st.markdown(f"- {step}")


def render_onboarding(onb_df):
    st.subheader("Provider onboarding — readiness matrix")
    if onb_df.empty:
        st.warning("No onboarding records match the current filters.")
        return

    c = st.columns(3)
    c[0].metric("Ready for go-live", _pct(metrics.onboarding_ready_rate(onb_df)))
    c[1].metric("Aging beyond SLA", _pct(metrics.aging_task_rate(onb_df)))
    c[2].metric("Avg days in stage", f"{metrics.average_days_in_stage(onb_df):.0f}")

    st.caption("Clinic × payer onboarding READY rate")
    matrix = metrics.payer_clinic_ready_rate(onb_df)
    if not matrix.empty:
        st.dataframe(matrix.style.format("{:.0%}"), use_container_width=True)

    st.caption("Top blocker categories")
    st.bar_chart(pd.Series(metrics.blocker_category_distribution(onb_df)))

    st.markdown(
        "**Aging / ownership:** records past the internal SLA or without an owner team are the "
        "first that age into blockers. The queue below is sorted by days in stage."
    )
    st.caption("Blocked + needs-review onboarding queue")
    st.dataframe(reporting.onboarding_work_queue(onb_df), use_container_width=True, hide_index=True)


def render_revenue_cycle(claims_df):
    st.subheader("Revenue cycle — clean-claim readiness")
    if claims_df.empty:
        st.warning("No claims match the current filters.")
        return

    c = st.columns(4)
    c[0].metric("Clean claim readiness", _pct(metrics.clean_claim_readiness_rate(claims_df)))
    c[1].metric("Blocked", _pct(metrics.blocked_claim_rate(claims_df)))
    c[2].metric("Needs review", _pct(metrics.needs_review_claim_rate(claims_df)))
    c[3].metric("Synthetic revenue at risk", _money(metrics.revenue_at_risk_synthetic(claims_df)))

    left, right = st.columns(2)
    with left:
        st.caption("Aging bucket distribution")
        st.bar_chart(pd.Series(metrics.aging_bucket_distribution(claims_df)))
    with right:
        st.caption("Denial-risk category — synthetic operational signal, not a prediction")
        st.bar_chart(pd.Series(metrics.denial_risk_distribution(claims_df)))

    st.divider()
    claim_id = st.selectbox("Inspect a synthetic claim", claims_df["claim_id"].tolist())
    row = claims_df[claims_df["claim_id"] == claim_id].iloc[0].to_dict()
    result = evaluate_claim_readiness(row)
    st.markdown(f"### {STATUS_ICON[result.status]} {result.status} · denial risk: {result.denial_risk_category}")
    st.markdown(f"**Recommended next action:** {reporting.claim_explanation(row)}")
    st.caption("Denial-risk category is a synthetic operational signal derived from data-quality and payer-rule fields — not a denial prediction.")

    st.caption("RCM work queue (highest synthetic revenue at risk first)")
    st.dataframe(reporting.rcm_work_queue(claims_df), use_container_width=True, hide_index=True)


def _render_checks(title, results):
    st.markdown(f"**{title}**")
    df = pd.DataFrame([r.as_dict() for r in results])
    st.dataframe(df, use_container_width=True, hide_index=True)
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


def render_analytics_layer():
    st.subheader("Analytics layer")
    st.write(
        "The technical proof behind the dashboards: documented metric definitions, "
        "a dbt-style SQL modeling layer, and a data-model summary."
    )

    with st.expander("Metric definitions", expanded=True):
        yml = ANALYTICS_DIR / "metric_definitions.yml"
        try:
            import yaml

            defs = yaml.safe_load(yml.read_text())
            rows = [
                {"metric": m["name"], "module": m.get("module", ""), "definition": m.get("definition", "")}
                for m in defs.get("metrics", [])
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        except Exception:
            st.code(yml.read_text() if yml.exists() else "metric_definitions.yml not found")

    with st.expander("SQL / dbt-style models"):
        st.markdown(
            "- **Staging** — `stg_authorization_cases`, `stg_provider_onboarding`, `stg_claim_readiness`\n"
            "- **Fact** — `fct_authorization_readiness`, `fct_provider_onboarding_readiness`, "
            "`fct_claim_readiness` (each asserts SQL/Python parity)\n"
            "- **Marts** — `mart_healthops_client_reporting`, `mart_rcm_client_reporting`"
        )
        sql_dir = ANALYTICS_DIR / "sql"
        files = sorted(sql_dir.glob("*.sql")) if sql_dir.exists() else []
        if files:
            choice = st.selectbox("View a model", [f.name for f in files])
            st.code((sql_dir / choice).read_text(), language="sql")

    with st.expander("Data model summary"):
        st.markdown(
            "- **synthetic_authorization_cases** — one synthetic PA case (90 rows)\n"
            "- **synthetic_provider_onboarding** — one synthetic provider-clinic-payer record (120 rows)\n"
            "- **synthetic_claim_readiness** — one synthetic diagnostic/lab claim (150 rows)\n\n"
            "Every row carries `synthetic_only_flag = true` and no PHI-like columns. "
            "Readiness columns are reproducible from the `plenara` engines."
        )


def render_safety():
    st.subheader("Safety & methodology")
    st.markdown(
        """
**Synthetic data only.** Every record is fabricated and flagged
`synthetic_only_flag = true`. There is no PHI and no real patient, provider,
payer, claims, or reimbursement data.

**Numbers are designed, not benchmarked.** Scenarios are tuned to be
operationally plausible so the dashboards tell a coherent story. They are
**not** industry benchmarks and **not** observed business impact. See
`docs/domain_calibration.md`.

**How readiness is decided.** Each module uses deterministic, human-readable
rules (the `plenara` package). BLOCKED = a critical requirement fails; NEEDS
REVIEW = a softer signal needs a human; READY = checks pass.

**What this is not.**
- Not clinical decision support and not medical advice.
- Not an approval/denial prediction — `denial_risk_category` is a synthetic
  operational signal from data-quality and payer-rule fields.
- Not production billing software; no EHR/payer integrations and no network
  calls at runtime.

**What production would require.** Secure infrastructure under regulatory
review, BAAs, encryption in transit and at rest, role-based access control,
audit logging, data retention controls, monitoring, clinical/legal review, and
human oversight.

*Any revenue-at-risk figure is a synthetic operations simulation — not observed
business impact.*
        """
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    st.set_page_config(page_title="Plenara — Healthcare Operations Readiness Lab", layout="wide")
    st.title("Plenara — Healthcare Operations Readiness Lab")
    st.caption(
        "Synthetic operations command center for prior authorization, provider "
        "onboarding, and diagnostic/lab revenue cycle readiness."
    )
    st.warning(SAFETY_BANNER)

    # --- Sidebar ---------------------------------------------------------
    st.sidebar.header("Controls")
    st.sidebar.subheader("Scenario")
    scenario_options = [BUNDLED_LABEL] + list(SCENARIOS.keys())
    scenario_label = st.sidebar.selectbox(
        "Operating posture", scenario_options, index=0,
        format_func=lambda k: BUNDLED_LABEL if k == BUNDLED_LABEL else SCENARIOS[k].label,
    )
    if scenario_label != BUNDLED_LABEL:
        st.sidebar.caption(SCENARIOS[scenario_label].ui_copy)
        st.sidebar.caption("Synthetic scenario design — not a real benchmark.")

    pa_df, onb_df, claims_df = get_data(scenario_label)

    st.sidebar.subheader("Filters")
    clinics = sorted(set(pa_df["clinic_id"]) | set(onb_df["clinic_id"]) | set(claims_df["clinic_id"]))
    payers = sorted(set(onb_df["payer_name_mock"]) | set(claims_df["payer_name_mock"]))
    specialties = sorted(set(onb_df["specialty"]))
    owners = sorted(set(claims_df["owner_team"].astype(str)) | set(onb_df["owner_team"].astype(str)))

    sel_clinics = st.sidebar.multiselect("Clinic", clinics)
    sel_payers = st.sidebar.multiselect("Payer", payers)
    sel_specialties = st.sidebar.multiselect("Specialty", specialties)
    sel_owners = st.sidebar.multiselect("Owner team", owners)

    pa_f = _filter(pa_df, "clinic_id", sel_clinics)
    onb_f = _filter(_filter(_filter(_filter(onb_df, "clinic_id", sel_clinics), "payer_name_mock", sel_payers), "specialty", sel_specialties), "owner_team", sel_owners)
    claims_f = _filter(_filter(_filter(claims_df, "clinic_id", sel_clinics), "payer_name_mock", sel_payers), "owner_team", sel_owners)

    work_queue = build_unified_work_queue(pa_f, onb_f, claims_f)

    st.sidebar.subheader("About")
    st.sidebar.info(
        "Synthetic operations readiness across prior authorization, provider "
        "onboarding, and diagnostic/lab revenue cycle. No PHI, no integrations."
    )

    tabs = st.tabs(
        [
            "Command center",
            "Work queue",
            "Prior auth",
            "Provider onboarding",
            "Revenue cycle",
            "Data quality",
            "Analytics layer",
            "Safety",
        ]
    )
    with tabs[0]:
        render_command_center(pa_f, onb_f, claims_f, work_queue)
    with tabs[1]:
        render_work_queue(work_queue)
    with tabs[2]:
        render_prior_auth(pa_f)
    with tabs[3]:
        render_onboarding(onb_f)
    with tabs[4]:
        render_revenue_cycle(claims_f)
    with tabs[5]:
        render_data_quality(pa_f, onb_f, claims_f)
    with tabs[6]:
        render_analytics_layer()
    with tabs[7]:
        render_safety()


if __name__ == "__main__":
    main()
