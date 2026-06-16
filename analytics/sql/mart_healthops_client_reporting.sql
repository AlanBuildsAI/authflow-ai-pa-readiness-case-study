-- mart_healthops_client_reporting
-- Client-facing reporting mart combining prior authorization and provider
-- onboarding readiness into one clinic x payer summary grain.
-- Synthetic/mock only — no PHI, no real payer/provider data.

with pa as (

    select
        clinic_id,
        count(*)                                                as pa_cases,
        avg(case when readiness_status = 'READY' then 1.0 else 0.0 end)        as pa_ready_rate,
        avg(case when readiness_status = 'BLOCKED' then 1.0 else 0.0 end)      as pa_blocked_rate,
        avg(case when readiness_status = 'NEEDS REVIEW' then 1.0 else 0.0 end) as pa_needs_review_rate,
        avg(data_completeness_score)                            as pa_avg_completeness
    from {{ ref('fct_authorization_readiness') }}
    group by clinic_id

),

onboarding as (

    select
        clinic_id,
        payer_name_mock,
        count(*)                                                as provider_records,
        avg(case when readiness_status = 'READY' then 1.0 else 0.0 end)   as onboarding_ready_rate,
        avg(case when readiness_status = 'BLOCKED' then 1.0 else 0.0 end)  as onboarding_blocked_rate,
        avg(days_in_stage)                                      as avg_days_in_stage,
        avg(case when is_aging then 1.0 else 0.0 end)           as aging_task_rate
    from {{ ref('fct_provider_onboarding_readiness') }}
    group by clinic_id, payer_name_mock

)

select
    onboarding.clinic_id,
    onboarding.payer_name_mock,
    onboarding.provider_records,
    onboarding.onboarding_ready_rate,
    onboarding.onboarding_blocked_rate,
    onboarding.avg_days_in_stage,
    onboarding.aging_task_rate,
    pa.pa_cases,
    pa.pa_ready_rate,
    pa.pa_blocked_rate,
    pa.pa_needs_review_rate,
    pa.pa_avg_completeness,
    true as synthetic_only_flag
from onboarding
left join pa
    on onboarding.clinic_id = pa.clinic_id
order by onboarding.clinic_id, onboarding.payer_name_mock
