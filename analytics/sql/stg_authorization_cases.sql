-- stg_authorization_cases
-- Staging model for synthetic prior authorization cases.
-- Source: data/synthetic_authorization_cases.csv (synthetic/mock only — no PHI).
--
-- Staging responsibilities: type-cast, trim, and standardize raw columns. No
-- business logic here; readiness rules live in the fact model.

with source as (

    select * from {{ ref('raw_authorization_cases') }}

),

renamed as (

    select
        cast(case_id as varchar)                  as case_id,
        cast(clinic_id as varchar)                as clinic_id,
        lower(cast(payer_type as varchar))        as payer_type,
        lower(cast(diagnosis as varchar))         as diagnosis,
        lower(cast(medication as varchar))        as medication,
        lower(cast(authorization_type as varchar)) as authorization_type,
        upper(cast(readiness_status as varchar))  as readiness_status,
        cast(missing_field_count as integer)      as missing_field_count,
        cast(failed_blocker_count as integer)     as failed_blocker_count,
        cast(review_required_count as integer)    as review_required_count,
        lower(cast(confidence_band as varchar))   as confidence_band,
        cast(days_to_ready as integer)            as days_to_ready,
        cast(data_completeness_score as double)   as data_completeness_score,
        lower(cast(top_missing_field as varchar)) as top_missing_field,
        cast(owner_team as varchar)               as owner_team,
        cast(synthetic_only_flag as boolean)      as synthetic_only_flag

    from source

)

select * from renamed
