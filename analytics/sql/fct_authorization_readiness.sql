-- fct_authorization_readiness
-- Fact model: one row per synthetic PA case with derived readiness flags.
-- Mirrors the deterministic logic in plenara.readiness so SQL and Python agree.
--
-- READY        : no failed blockers, no critical missing field, sufficient
--                confidence and completeness.
-- BLOCKED      : failed_blocker_count > 0 OR a critical field is missing.
-- NEEDS REVIEW : low/medium confidence, review-required fields, or low
--                completeness.

with staged as (

    select * from {{ ref('stg_authorization_cases') }}

),

flags as (

    select
        *,
        (failed_blocker_count > 0)                          as has_failed_blocker,
        (
            missing_field_count > 0
            and top_missing_field in (
                'diagnosis', 'medication', 'authorization_type',
                'disease_activity_evidence', 'provider_specialty'
            )
        )                                                   as has_critical_missing,
        (confidence_band in ('low', 'medium'))              as low_confidence,
        (review_required_count > 0)                         as has_review_fields,
        (data_completeness_score < 0.85)                    as low_completeness
    from staged

),

scored as (

    select
        *,
        case
            when has_failed_blocker or has_critical_missing then 'BLOCKED'
            when low_confidence or has_review_fields or low_completeness then 'NEEDS REVIEW'
            else 'READY'
        end as derived_readiness_status
    from flags

)

select
    case_id,
    clinic_id,
    payer_type,
    diagnosis,
    medication,
    authorization_type,
    owner_team,
    missing_field_count,
    failed_blocker_count,
    review_required_count,
    confidence_band,
    data_completeness_score,
    days_to_ready,
    readiness_status,
    derived_readiness_status,
    (readiness_status = derived_readiness_status) as readiness_status_consistent,
    synthetic_only_flag
from scored
