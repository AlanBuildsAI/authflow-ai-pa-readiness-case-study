# SQL Portfolio — Plenara (DuckDB)

Eight analyst-style business questions, answered with SQL over the three bundled
**synthetic** datasets using DuckDB. Everything runs locally:

```bash
python scripts/run_sql_portfolio.py
```

Outputs are written to [`sample_outputs/sql/`](../sample_outputs/sql). The SQL
lives in [`scripts/run_sql_portfolio.py`](../scripts/run_sql_portfolio.py) and
mirrors the readiness logic in the `plenara` package, so the analytics layer and
the app agree by construction.

> Synthetic / mock data only — no PHI, no real patient, provider, payer, or
> claims data. Figures are synthetic scenario design, not benchmarks or observed
> impact.

---

## 1. Which payer has the highest blocked rate?

**Why it matters:** Payers that block the most work are where documentation,
eligibility, and payer-rule effort should concentrate.

**SQL used:** union of onboarding + claims into `(payer, status)`, then
`AVG(CASE WHEN status = 'BLOCKED' THEN 1 ELSE 0 END)` grouped by payer.

**Output:** `payer_blocked_rate.csv` (payer, total_records, blocked_records, blocked_rate)

**Interpretation:** The payer at the top of this list is the operational hotspot;
its blocked rate quantifies how often work stalls, guiding where to add payer-rule
or documentation support.

## 2. Which clinics have the weakest readiness profile?

**Why it matters:** Clinic-level variation shows where onboarding, PA, and claim
readiness are healthiest vs. where a site needs help.

**SQL used:** `unified_readiness` view across all three modules, grouped by
`clinic_id` with `READY` / `NEEDS REVIEW` / `BLOCKED` counts and a `ready_rate`.

**Output:** `clinic_readiness_summary.csv`

**Interpretation:** Clinics sorted by ascending `ready_rate` surface the sites
carrying the most non-ready work — a targeting list for operational support.

## 3. Which owner teams have the largest non-ready workload?

**Why it matters:** Work has to be owned. Concentrated backlog on one team signals
a staffing or process bottleneck.

**SQL used:** `unified_readiness` grouped by `owner_team` with
`COUNT(*) FILTER (WHERE status <> 'READY')` and blocked / needs-review splits.

**Output:** `owner_workqueue_summary.csv`

**Interpretation:** The team at the top owns the most non-ready items; the blocked
vs. needs-review split shows whether the load is urgent or reviewable.

## 4. Which blocker categories create the most operational friction?

**Why it matters:** Fixing the most common blocker category removes the most
rework across the operation.

**SQL used:** `CASE` expressions derive a blocker category per module (PA, claims)
and reuse the onboarding `blocker_category`, unioned and counted.

**Output:** `top_blocker_categories.csv`

**Interpretation:** The ranked categories are the friction drivers — the shortlist
for process fixes, templates, or payer-specific playbooks.

## 5. Where is synthetic revenue at risk concentrated?

**Why it matters:** Revenue-cycle attention should follow the dollars at risk
(synthetic here), especially on aged claims.

**SQL used:** claims grouped by payer with `SUM(estimated_revenue_at_risk_synthetic)`
and an aged (>60 days) subtotal.

**Output:** `synthetic_revenue_at_risk_by_payer.csv`

**Interpretation:** Payers with the highest synthetic revenue at risk — and the
aged portion — are where a cleanup queue would protect the most (synthetic) value.

## 6. Are readiness statuses consistent between source labels and derived SQL logic?

**Why it matters:** A metric is only trustworthy if the stored label matches the
rules. This is a data-quality / lineage check.

**SQL used:** `CASE` re-derives readiness from the raw fields for each module and
compares it to the stored status, with an `is_consistent` flag per module.

**Output:** `readiness_status_consistency.csv` (module, total, consistent,
inconsistent, is_consistent)

**Interpretation:** All three modules should show `is_consistent = true` and zero
inconsistent records — proof the SQL analytics layer and the Python engines agree.

## 7. Which work items are aging beyond internal workflow thresholds?

**Why it matters:** Aged claims risk timely-filing windows; aged onboarding delays
go-live. Aging is a leading indicator of avoidable loss.

**SQL used:** claims grouped by A/R `aging_bucket` (0-30, 31-60, 61-90, 90+) with
counts, blocked counts, and synthetic revenue at risk.

**Output:** `aging_work_summary.csv`

**Interpretation:** The 61-90 and 90+ buckets are the priority; their blocked
counts and synthetic revenue at risk quantify the cost of waiting.

## 8. What executive KPIs should a stakeholder review first?

**Why it matters:** Leaders need a five-number read before drilling in.

**SQL used:** aggregates over `unified_readiness` + claims produce a long-format
KPI table: critical blockers, aging claims 60+, unassigned work items, synthetic
revenue at risk, overall readiness rate.

**Output:** `executive_kpi_summary.csv` (metric, value)

**Interpretation:** These five KPIs are the headline for the Command Center and
Executive Insights views — the fastest way to understand the current scenario.

---

### SQL techniques demonstrated
Grouping and aggregation · `CASE` expressions · derived readiness flags · rate
calculations · `FILTER` clauses · multi-table `UNION ALL` views · payer-, clinic-,
and owner-level summaries · consistency/lineage checks · aging thresholds ·
synthetic revenue-at-risk roll-ups.
