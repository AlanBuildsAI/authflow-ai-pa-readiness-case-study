#!/usr/bin/env python3
"""
SQL portfolio for Plenara — Healthcare Operations Readiness Lab (DuckDB).

Loads the three bundled synthetic CSVs, registers them as raw DuckDB tables, and
runs a set of analyst-style SQL queries that answer real operations questions.
Outputs are written as CSVs to ``sample_outputs/sql/``.

Everything runs locally on bundled synthetic data — no PHI, no real
patient/provider/payer/claims data, and no external database.

Run:
    python scripts/run_sql_portfolio.py
"""

from __future__ import annotations

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "sample_outputs" / "sql"

# Aging thresholds (synthetic internal-SLA design, not benchmarks).
CLAIM_AGING_DAYS = 60
ONBOARDING_AGING_DAYS = 30
COMPLETENESS_THRESHOLD = 0.85

# Derived-readiness CASE expressions that mirror the plenara engines / fct models.
PA_DERIVED = f"""
CASE
  WHEN failed_blocker_count > 0
    OR (missing_field_count > 0 AND lower(top_missing_field) IN
        ('diagnosis','medication','authorization_type','disease_activity_evidence','provider_specialty'))
    THEN 'BLOCKED'
  WHEN lower(confidence_band) IN ('low','medium')
    OR review_required_count > 0
    OR data_completeness_score < {COMPLETENESS_THRESHOLD}
    THEN 'NEEDS REVIEW'
  ELSE 'READY'
END
"""

CLAIM_DERIVED = f"""
CASE
  WHEN eligibility_status IN ('inactive','mismatch')
    OR prior_auth_status = 'missing'
    OR coding_status IN ('missing','mismatch')
    OR payer_rule_status = 'fail'
    OR timely_filing_status = 'expired'
    OR failed_rule_count > 0
    THEN 'BLOCKED'
  WHEN eligibility_status = 'unverified'
    OR documentation_status IN ('incomplete','stale')
    OR modifier_status IN ('missing','invalid')
    OR payer_rule_status = 'review'
    OR timely_filing_status = 'at_risk'
    OR review_required_count > 0
    OR data_completeness_score < {COMPLETENESS_THRESHOLD}
    OR days_since_service > 45
    THEN 'NEEDS REVIEW'
  ELSE 'READY'
END
"""

ONB_DERIVED = """
CASE
  WHEN credentialing_status = 'missing'
    OR contract_status = 'not_active'
    OR license_status IN ('missing','expired')
    OR npi_status IN ('missing','mismatch')
    OR effective_date_status = 'missing'
    OR directory_status = 'not_updated'
    OR enrollment_status = 'not_enrolled'
    THEN 'BLOCKED'
  WHEN caqh_status = 'stale'
    OR documentation_status = 'incomplete'
    OR days_in_stage > 30
    OR lower(trim(owner_team)) IN ('','unassigned','none','n/a')
    OR credentialing_status = 'in_progress'
    OR contract_status = 'pending'
    OR enrollment_status = 'pending'
    OR (readiness_score >= 0.5 AND readiness_score < 0.8)
    THEN 'NEEDS REVIEW'
  ELSE 'READY'
END
"""


def _connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute(
        f"CREATE VIEW raw_authorization AS "
        f"SELECT * FROM read_csv_auto('{DATA / 'synthetic_authorization_cases.csv'}')"
    )
    con.execute(
        f"CREATE VIEW raw_onboarding AS "
        f"SELECT * FROM read_csv_auto('{DATA / 'synthetic_provider_onboarding.csv'}')"
    )
    con.execute(
        f"CREATE VIEW raw_claims AS "
        f"SELECT * FROM read_csv_auto('{DATA / 'synthetic_claim_readiness.csv'}')"
    )
    # Unified readiness view across the three modules (stored labels).
    con.execute(
        """
        CREATE VIEW unified_readiness AS
        SELECT 'Prior auth' AS module, case_id AS record_id, clinic_id,
               CAST(NULL AS VARCHAR) AS payer_name_mock, owner_team,
               readiness_status AS status, days_to_ready AS age_days,
               0.0 AS revenue_at_risk
        FROM raw_authorization
        UNION ALL
        SELECT 'Provider onboarding', provider_id, clinic_id, payer_name_mock,
               owner_team, readiness_status, days_in_stage, 0.0
        FROM raw_onboarding
        UNION ALL
        SELECT 'Revenue cycle', claim_id, clinic_id, payer_name_mock, owner_team,
               claim_readiness_status, days_since_service,
               estimated_revenue_at_risk_synthetic
        FROM raw_claims
        """
    )
    return con


# --- Query 1: payer blocked rate (onboarding + claims) ----------------------
Q_PAYER_BLOCKED_RATE = """
WITH payer_status AS (
    SELECT payer_name_mock, readiness_status AS status FROM raw_onboarding
    UNION ALL
    SELECT payer_name_mock, claim_readiness_status FROM raw_claims
)
SELECT
    payer_name_mock AS payer,
    COUNT(*) AS total_records,
    SUM(CASE WHEN status = 'BLOCKED' THEN 1 ELSE 0 END) AS blocked_records,
    ROUND(AVG(CASE WHEN status = 'BLOCKED' THEN 1.0 ELSE 0.0 END), 4) AS blocked_rate
FROM payer_status
GROUP BY payer_name_mock
ORDER BY blocked_rate DESC, total_records DESC
"""

# --- Query 2: clinic readiness summary (all three modules) ------------------
Q_CLINIC_READINESS = """
SELECT
    clinic_id,
    COUNT(*) AS total_records,
    SUM(CASE WHEN status = 'READY' THEN 1 ELSE 0 END) AS ready_records,
    SUM(CASE WHEN status = 'NEEDS REVIEW' THEN 1 ELSE 0 END) AS needs_review_records,
    SUM(CASE WHEN status = 'BLOCKED' THEN 1 ELSE 0 END) AS blocked_records,
    ROUND(AVG(CASE WHEN status = 'READY' THEN 1.0 ELSE 0.0 END), 4) AS ready_rate,
    ROUND(AVG(CASE WHEN status = 'BLOCKED' THEN 1.0 ELSE 0.0 END), 4) AS blocked_rate
FROM unified_readiness
GROUP BY clinic_id
ORDER BY ready_rate ASC
"""

# --- Query 3: owner team work queue (non-ready workload) --------------------
Q_OWNER_WORKQUEUE = """
SELECT
    owner_team,
    COUNT(*) FILTER (WHERE status <> 'READY') AS non_ready_items,
    COUNT(*) FILTER (WHERE status = 'BLOCKED') AS blocked_items,
    COUNT(*) FILTER (WHERE status = 'NEEDS REVIEW') AS needs_review_items,
    COUNT(*) AS total_items
FROM unified_readiness
GROUP BY owner_team
ORDER BY non_ready_items DESC
"""

# --- Query 4: top blocker categories (derived across modules) ---------------
Q_TOP_BLOCKERS = f"""
WITH blockers AS (
    SELECT CASE
        WHEN {PA_DERIVED.strip()} = 'BLOCKED'
             AND missing_field_count > 0
             AND lower(top_missing_field) IN
                 ('diagnosis','medication','authorization_type','disease_activity_evidence','provider_specialty')
             THEN 'missing clinical documentation'
        WHEN {PA_DERIVED.strip()} = 'BLOCKED' THEN 'payer criteria not met'
        ELSE 'none' END AS blocker_category
    FROM raw_authorization
    UNION ALL
    SELECT CASE WHEN readiness_status <> 'READY' THEN blocker_category ELSE 'none' END
    FROM raw_onboarding
    UNION ALL
    SELECT CASE
        WHEN eligibility_status IN ('inactive','mismatch') THEN 'eligibility mismatch'
        WHEN prior_auth_status = 'missing' THEN 'missing prior authorization'
        WHEN coding_status IN ('missing','mismatch') THEN 'procedure / diagnosis mismatch'
        WHEN payer_rule_status = 'fail' THEN 'payer-specific rule failed'
        WHEN timely_filing_status = 'expired' THEN 'timely filing risk'
        WHEN modifier_status IN ('missing','invalid') THEN 'modifier required'
        WHEN documentation_status IN ('incomplete','stale') THEN 'payer documentation incomplete'
        ELSE 'none' END
    FROM raw_claims
)
SELECT blocker_category, COUNT(*) AS record_count
FROM blockers
WHERE blocker_category <> 'none'
GROUP BY blocker_category
ORDER BY record_count DESC
"""

# --- Query 5: synthetic revenue at risk by payer ----------------------------
Q_REVENUE_AT_RISK = f"""
SELECT
    payer_name_mock AS payer,
    COUNT(*) AS claim_count,
    SUM(CASE WHEN claim_readiness_status = 'BLOCKED' THEN 1 ELSE 0 END) AS blocked_claims,
    ROUND(SUM(estimated_revenue_at_risk_synthetic), 2) AS revenue_at_risk_synthetic,
    ROUND(SUM(CASE WHEN days_since_service > {CLAIM_AGING_DAYS}
                   THEN estimated_revenue_at_risk_synthetic ELSE 0 END), 2)
        AS revenue_at_risk_aged_60_plus
FROM raw_claims
GROUP BY payer_name_mock
ORDER BY revenue_at_risk_synthetic DESC
"""

# --- Query 6: readiness status consistency (stored vs derived) --------------
Q_CONSISTENCY = f"""
WITH checks AS (
    SELECT 'Prior auth' AS module, readiness_status AS stored_status,
           {PA_DERIVED.strip()} AS derived_status
    FROM raw_authorization
    UNION ALL
    SELECT 'Provider onboarding', readiness_status, {ONB_DERIVED.strip()}
    FROM raw_onboarding
    UNION ALL
    SELECT 'Revenue cycle', claim_readiness_status, {CLAIM_DERIVED.strip()}
    FROM raw_claims
)
SELECT
    module,
    COUNT(*) AS total_records,
    SUM(CASE WHEN stored_status = derived_status THEN 1 ELSE 0 END) AS consistent_records,
    SUM(CASE WHEN stored_status <> derived_status THEN 1 ELSE 0 END) AS inconsistent_records,
    (SUM(CASE WHEN stored_status <> derived_status THEN 1 ELSE 0 END) = 0) AS is_consistent
FROM checks
GROUP BY module
ORDER BY module
"""

# --- Query 7: executive KPI summary (long format) ---------------------------
Q_EXECUTIVE_KPIS = f"""
WITH agg AS (
    SELECT
        COUNT(*) AS total,
        SUM(CASE WHEN status = 'READY' THEN 1 ELSE 0 END) AS ready,
        SUM(CASE WHEN status = 'BLOCKED' THEN 1 ELSE 0 END) AS blocked,
        SUM(CASE WHEN status <> 'READY'
                 AND lower(trim(owner_team)) IN ('','unassigned','none','n/a')
                 THEN 1 ELSE 0 END) AS unassigned_non_ready
    FROM unified_readiness
),
claims_agg AS (
    SELECT
        SUM(CASE WHEN days_since_service > {CLAIM_AGING_DAYS} THEN 1 ELSE 0 END) AS aging_60_plus,
        ROUND(SUM(estimated_revenue_at_risk_synthetic), 2) AS revenue_at_risk
    FROM raw_claims
)
SELECT 'critical_blockers' AS metric, CAST(blocked AS DOUBLE) AS value FROM agg
UNION ALL SELECT 'aging_claims_60_plus', CAST(aging_60_plus AS DOUBLE) FROM claims_agg
UNION ALL SELECT 'unassigned_work_items', CAST(unassigned_non_ready AS DOUBLE) FROM agg
UNION ALL SELECT 'synthetic_revenue_at_risk', revenue_at_risk FROM claims_agg
UNION ALL SELECT 'overall_readiness_rate', ROUND(CAST(ready AS DOUBLE) / NULLIF(total, 0), 4) FROM agg
"""

# --- Query 8: aging work summary (claims A/R buckets) -----------------------
Q_AGING = """
SELECT
    aging_bucket,
    COUNT(*) AS claim_count,
    SUM(CASE WHEN claim_readiness_status = 'BLOCKED' THEN 1 ELSE 0 END) AS blocked_claims,
    ROUND(SUM(estimated_revenue_at_risk_synthetic), 2) AS revenue_at_risk_synthetic,
    ROUND(AVG(days_since_service), 1) AS avg_days_since_service
FROM raw_claims
GROUP BY aging_bucket
ORDER BY CASE aging_bucket
    WHEN '0-30' THEN 1 WHEN '31-60' THEN 2 WHEN '61-90' THEN 3 WHEN '90+' THEN 4 ELSE 5 END
"""

QUERIES = {
    "payer_blocked_rate.csv": Q_PAYER_BLOCKED_RATE,
    "clinic_readiness_summary.csv": Q_CLINIC_READINESS,
    "owner_workqueue_summary.csv": Q_OWNER_WORKQUEUE,
    "top_blocker_categories.csv": Q_TOP_BLOCKERS,
    "synthetic_revenue_at_risk_by_payer.csv": Q_REVENUE_AT_RISK,
    "readiness_status_consistency.csv": Q_CONSISTENCY,
    "executive_kpi_summary.csv": Q_EXECUTIVE_KPIS,
    "aging_work_summary.csv": Q_AGING,
}


def run_portfolio(out_dir: Path = OUT) -> dict[str, Path]:
    """Run every portfolio query and write each result to a CSV. Returns paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    con = _connect()
    written: dict[str, Path] = {}
    try:
        for filename, sql in QUERIES.items():
            df = con.execute(sql).fetchdf()
            path = out_dir / filename
            df.to_csv(path, index=False)
            written[filename] = path
    finally:
        con.close()
    return written


def main() -> int:
    written = run_portfolio()
    print("Plenara SQL portfolio (DuckDB) — synthetic data only")
    print(f"output dir: {OUT}")
    for name, path in written.items():
        import pandas as pd

        rows = len(pd.read_csv(path))
        print(f"  {name}: {rows} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
