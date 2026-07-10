# Plenara — Healthcare Operations Readiness Lab
# Synthetic data only. No PHI, no integrations, no production deployment.

.PHONY: help test app sql portfolio

help:
	@echo "make test       - run the test suite (pytest)"
	@echo "make app        - launch the Streamlit app"
	@echo "make sql        - run the DuckDB SQL portfolio (writes sample_outputs/sql/)"
	@echo "make portfolio  - run the SQL portfolio, then the tests"

test:
	python -m pytest tests/ -q

app:
	PYTHONPATH=src python -m streamlit run streamlit_app.py

sql:
	python scripts/run_sql_portfolio.py

portfolio: sql test
