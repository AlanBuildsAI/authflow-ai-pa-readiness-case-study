# Recruiter / Reviewer Review Guide — Plenara

A fast path to evaluate this project in ~10 minutes. Plenara is a professional
**synthetic** healthcare operations SaaS prototype for prior authorization,
provider onboarding, and revenue-cycle readiness.

> Synthetic / mock data only — no PHI, no integrations, no production deployment.

## How to review, in order

1. **Read the Professional SaaS Prototype Snapshot** at the top of [`README.md`](../README.md).
2. **Open the live Streamlit demo** (link in the README) — or run locally
   (`PYTHONPATH=src streamlit run streamlit_app.py`).
3. **Product demo tab** — positioning, users, three workflows, and what
   READY / NEEDS REVIEW / BLOCKED mean.
4. **Executive insights** — five data-derived insights and five KPI cards.
5. **SQL Portfolio** — [`docs/sql_portfolio.md`](sql_portfolio.md) and
   `python scripts/run_sql_portfolio.py` (outputs in [`sample_outputs/sql/`](../sample_outputs/sql)).
6. **Implementation case study** — [`docs/implementation_case_study.md`](implementation_case_study.md),
   including the 60-second interview explanation.
7. **Data-quality checks** — [`src/plenara/data_quality.py`](../src/plenara/data_quality.py).
8. **Tests** — `python -m pytest tests/ -q`.
9. **Safety boundaries** — the app's Safety tab and the README safety section.

## Roles this project supports

Data Analyst · Operations Analyst · Data Quality Analyst · Business Analyst ·
Healthcare Operations Analyst · Implementation Analyst · Client Reporting Analyst.

## Skills demonstrated

Python · pandas · SQL · DuckDB · Streamlit · data-quality checks · metric
definitions · workflow rules · work queues · executive reporting ·
synthetic-data safety · testing.

## Best files to inspect

- Readiness logic: [`src/plenara/readiness.py`](../src/plenara/readiness.py),
  [`provider_onboarding.py`](../src/plenara/provider_onboarding.py),
  [`claims_readiness.py`](../src/plenara/claims_readiness.py)
- Work queue: [`src/plenara/workqueue.py`](../src/plenara/workqueue.py)
- Insights: [`src/plenara/executive_insights.py`](../src/plenara/executive_insights.py)
- SQL portfolio: [`scripts/run_sql_portfolio.py`](../scripts/run_sql_portfolio.py)
- Data quality: [`src/plenara/data_quality.py`](../src/plenara/data_quality.py)
- App (presentation only): [`streamlit_app.py`](../streamlit_app.py)
- Tests: [`tests/`](../tests)

## Suggested interview talking points

- Clean architecture: Streamlit is presentation-only; all logic is in reusable,
  tested `plenara` modules.
- Deterministic, explainable readiness rules across three workflows — no opaque
  scoring, no prediction.
- A DuckDB SQL portfolio with a **consistency check** proving SQL and Python agree.
- Designed-realistic synthetic data (clinic/payer friction, aging correlated with
  status, revenue concentrated in aged blocked claims) — with honest labeling.
- Regulated-domain discipline: explicit synthetic-only safety boundaries and a
  phased path to a real product.
