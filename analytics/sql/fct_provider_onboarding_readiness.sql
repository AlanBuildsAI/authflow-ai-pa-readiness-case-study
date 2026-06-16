-- fct_provider_onboarding_readiness
-- Fact model: one row per synthetic provider onboarding record with derived
-- readiness. Mirrors plenara.provider_onboarding.
--
-- BLOCKED      : a critical onboarding status is missing/expired/mismatched or
--                the payer contract is not active / directory not updated /
--                enrollment incomplete.
-- NEEDS REVIEW : stale CAQH, incomplete documentation, aging stage (>30 days),
--                unassigned owner, in-progress credential/contract/enrollment,
--                or mid-band readiness score.
-- READY        : everything critical complete and current.

with staged as (

    select * from {{ ref('stg_provider_onboarding') }}

),

flags as (

    select
        *,
        (
            credentialing_status = 'missing'
            or contract_status = 'not_active'
            or license_status in ('missing', 'expired')
            or npi_status in ('missing', 'mismatch')
            or effective_date_status = 'missing'
            or directory_status = 'not_updated'
            or enrollment_status = 'not_enrolled'
        )                                                   as has_blocker,
        (
            caqh_status = 'stale'
            or documentation_status = 'incomplete'
            or days_in_stage > 30
            or owner_team in ('', 'unassigned', 'none', 'n/a')
            or credentialing_status in ('in_progress', 'pending')
            or contract_status = 'pending'
            or enrollment_status = 'pending'
            or (readiness_score >= 0.5 and readiness_score < 0.8)
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
        end as derived_readiness_status,
        (days_in_stage > 30) as is_aging
    from flags

)

select
    provider_id,
    specialty,
    clinic_id,
    clinic_region,
    payer_name_mock,
    insurance_plan_type,
    onboarding_stage,
    blocker_category,
    owner_team,
    days_in_stage,
    is_aging,
    readiness_score,
    readiness_status,
    derived_readiness_status,
    (readiness_status = derived_readiness_status) as readiness_status_consistent,
    synthetic_only_flag
from scored
