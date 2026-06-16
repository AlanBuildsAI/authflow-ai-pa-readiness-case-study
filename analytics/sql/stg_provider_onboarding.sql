-- stg_provider_onboarding
-- Staging model for synthetic provider / clinic / payer onboarding records.
-- Source: data/synthetic_provider_onboarding.csv (synthetic/mock only — no PHI).

with source as (

    select * from {{ ref('raw_provider_onboarding') }}

),

renamed as (

    select
        cast(provider_id as varchar)              as provider_id,
        cast(provider_name_mock as varchar)       as provider_name_mock,
        cast(specialty as varchar)                as specialty,
        cast(clinic_id as varchar)                as clinic_id,
        cast(clinic_region as varchar)            as clinic_region,
        cast(payer_name_mock as varchar)          as payer_name_mock,
        cast(insurance_plan_type as varchar)      as insurance_plan_type,
        lower(cast(credentialing_status as varchar))  as credentialing_status,
        lower(cast(contract_status as varchar))       as contract_status,
        lower(cast(directory_status as varchar))      as directory_status,
        lower(cast(enrollment_status as varchar))     as enrollment_status,
        lower(cast(documentation_status as varchar))  as documentation_status,
        lower(cast(caqh_status as varchar))           as caqh_status,
        lower(cast(npi_status as varchar))            as npi_status,
        lower(cast(license_status as varchar))        as license_status,
        lower(cast(effective_date_status as varchar)) as effective_date_status,
        lower(cast(onboarding_stage as varchar))      as onboarding_stage,
        lower(cast(blocker_category as varchar))      as blocker_category,
        cast(days_in_stage as integer)            as days_in_stage,
        lower(cast(owner_team as varchar))        as owner_team,
        upper(cast(readiness_status as varchar))  as readiness_status,
        cast(readiness_score as double)           as readiness_score,
        cast(synthetic_only_flag as boolean)      as synthetic_only_flag

    from source

)

select * from renamed
