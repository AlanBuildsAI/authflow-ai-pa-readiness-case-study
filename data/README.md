# Synthetic datasets

Every file in this folder is **fully synthetic / mock data**. There is no PHI,
no real patient, provider, clinic, or payer information, no real claims, and no
real reimbursement figures. Every row carries `synthetic_only_flag = true`.

The datasets are generated deterministically (seeded) by
[`src/plenara/sample_data.py`](../src/plenara/sample_data.py). Each row is passed
through the matching readiness engine, so the readiness columns always agree with
the rules in the `plenara` package. To regenerate:

```bash
PYTHONPATH=src python -m plenara.sample_data
```

## Files

### `synthetic_authorization_cases.csv` (90 rows)
Synthetic prior authorization cases.

| Column | Notes |
|---|---|
| `case_id` | unique synthetic id |
| `clinic_id`, `payer_type`, `diagnosis`, `medication`, `authorization_type` | synthetic attributes |
| `readiness_status` | READY / NEEDS REVIEW / BLOCKED (from the engine) |
| `missing_field_count`, `failed_blocker_count`, `review_required_count` | counts |
| `confidence_band` | high / medium / low (extraction confidence) |
| `days_to_ready`, `data_completeness_score`, `top_missing_field`, `owner_team` | analytics fields |
| `synthetic_only_flag` | always true |

### `synthetic_provider_onboarding.csv` (120 rows)
Synthetic provider / clinic / payer onboarding records.

Key columns: `provider_id`, `provider_name_mock`, `specialty`, `clinic_id`,
`clinic_region`, `payer_name_mock`, `insurance_plan_type`, the credentialing /
contract / directory / enrollment / documentation / CAQH / NPI / license /
effective-date statuses, `onboarding_stage`, `blocker_category`, `days_in_stage`,
`owner_team`, `readiness_status`, `readiness_score`, `synthetic_only_flag`.

### `synthetic_claim_readiness.csv` (150 rows)
Synthetic diagnostic / lab revenue cycle claims.

Key columns: `claim_id`, `accession_id_mock`, `lab_order_id_mock`, `clinic_id`,
`clinic_region`, `payer_name_mock`, `plan_type`, `test_category`,
`procedure_code_mock`, `diagnosis_code_mock`, `ordering_provider_specialty`, the
eligibility / prior-auth / documentation / coding / modifier / payer-rule /
timely-filing statuses, `claim_readiness_status`, `denial_risk_category`,
`missing_field_count`, `failed_rule_count`, `review_required_count`,
`days_since_service`, `aging_bucket`, `owner_team`,
`estimated_revenue_at_risk_synthetic`, `data_completeness_score`,
`synthetic_only_flag`.

> `estimated_revenue_at_risk_synthetic` is a mock dollar figure for demonstration
> only — not observed business impact and not real reimbursement.
> `denial_risk_category` is a synthetic operational signal, not a denial prediction.
