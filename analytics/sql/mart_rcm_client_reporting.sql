-- mart_rcm_client_reporting
-- Client-facing revenue cycle reporting mart at the payer x clinic grain.
-- Surfaces clean-claim readiness, blocker mix, synthetic revenue at risk, and
-- aging — the metrics a diagnostic/lab RCM operations team reviews.
-- Synthetic/mock only — no PHI, no real claims, no real reimbursement.

with claims as (

    select * from {{ ref('fct_claim_readiness') }}

)

select
    payer_name_mock,
    clinic_id,
    count(*)                                                            as claim_count,
    avg(case when claim_readiness_status = 'READY' then 1.0 else 0.0 end)        as clean_claim_readiness_rate,
    avg(case when claim_readiness_status = 'BLOCKED' then 1.0 else 0.0 end)      as blocked_claim_rate,
    avg(case when claim_readiness_status = 'NEEDS REVIEW' then 1.0 else 0.0 end) as needs_review_claim_rate,
    avg(case when denial_risk_category = 'high' then 1.0 else 0.0 end)  as high_denial_risk_rate,
    avg(case when payer_rule_status = 'fail' then 1.0 else 0.0 end)     as payer_rule_failure_rate,
    avg(case when prior_auth_status = 'missing' then 1.0 else 0.0 end)  as authorization_missing_rate,
    avg(case when documentation_status in ('incomplete', 'stale') then 1.0 else 0.0 end) as documentation_missing_rate,
    sum(case when aging_bucket in ('61-90', '90+') then 1 else 0 end)  as aging_claims,
    sum(estimated_revenue_at_risk_synthetic)                           as revenue_at_risk_synthetic,
    avg(data_completeness_score)                                       as avg_data_completeness,
    true                                                               as synthetic_only_flag
from claims
group by payer_name_mock, clinic_id
order by revenue_at_risk_synthetic desc
