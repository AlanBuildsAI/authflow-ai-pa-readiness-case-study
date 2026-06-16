-- fct_claim_readiness
-- Fact model: one row per synthetic diagnostic/lab claim with derived clean-claim
-- readiness. Mirrors plenara.claims_readiness.
--
-- BLOCKED      : eligibility inactive/mismatch, missing prior auth, coding
--                missing/mismatch, payer rule failed, or timely filing expired.
-- NEEDS REVIEW : eligibility unverified, documentation incomplete/stale,
--                modifier missing/invalid, payer rule review, timely filing at
--                risk, low completeness, review-required fields, or aging > 45d.
-- READY        : clean across all critical checks.
--
-- denial_risk_category is a synthetic operational signal, NOT a prediction.

with staged as (

    select * from {{ ref('stg_claim_readiness') }}

),

flags as (

    select
        *,
        (
            eligibility_status in ('inactive', 'mismatch')
            or prior_auth_status = 'missing'
            or coding_status in ('missing', 'mismatch')
            or payer_rule_status = 'fail'
            or timely_filing_status = 'expired'
            or failed_rule_count > 0
        )                                                   as has_blocker,
        (
            eligibility_status = 'unverified'
            or documentation_status in ('incomplete', 'stale')
            or modifier_status in ('missing', 'invalid')
            or payer_rule_status = 'review'
            or timely_filing_status = 'at_risk'
            or review_required_count > 0
            or data_completeness_score < 0.85
            or days_since_service > 45
        )                                                   as has_review_signal
    from staged

),

scored as (

    select
        *,
        case
            when has_blocker then 'BLOCKED'
            when has_review_signal then 'NEEDS REVIEW'
            else 'READY'
        end as derived_claim_readiness_status
    from flags

)

select
    claim_id,
    accession_id_mock,
    clinic_id,
    clinic_region,
    payer_name_mock,
    plan_type,
    test_category,
    owner_team,
    eligibility_status,
    prior_auth_status,
    documentation_status,
    coding_status,
    modifier_status,
    payer_rule_status,
    timely_filing_status,
    denial_risk_category,
    aging_bucket,
    days_since_service,
    data_completeness_score,
    estimated_revenue_at_risk_synthetic,
    claim_readiness_status,
    derived_claim_readiness_status,
    (claim_readiness_status = derived_claim_readiness_status) as claim_status_consistent,
    synthetic_only_flag
from scored
