-- stg_claim_readiness
-- Staging model for synthetic diagnostic / lab revenue cycle claims.
-- Source: data/synthetic_claim_readiness.csv (synthetic/mock only — no PHI,
-- no real claims, no real reimbursement).

with source as (

    select * from {{ ref('raw_claim_readiness') }}

),

renamed as (

    select
        cast(claim_id as varchar)                 as claim_id,
        cast(accession_id_mock as varchar)        as accession_id_mock,
        cast(lab_order_id_mock as varchar)        as lab_order_id_mock,
        cast(clinic_id as varchar)                as clinic_id,
        cast(clinic_region as varchar)            as clinic_region,
        cast(payer_name_mock as varchar)          as payer_name_mock,
        cast(plan_type as varchar)                as plan_type,
        lower(cast(test_category as varchar))     as test_category,
        cast(procedure_code_mock as varchar)      as procedure_code_mock,
        cast(diagnosis_code_mock as varchar)      as diagnosis_code_mock,
        cast(ordering_provider_specialty as varchar) as ordering_provider_specialty,
        lower(cast(eligibility_status as varchar))    as eligibility_status,
        lower(cast(prior_auth_status as varchar))     as prior_auth_status,
        lower(cast(documentation_status as varchar))  as documentation_status,
        lower(cast(coding_status as varchar))         as coding_status,
        lower(cast(modifier_status as varchar))       as modifier_status,
        lower(cast(payer_rule_status as varchar))     as payer_rule_status,
        lower(cast(timely_filing_status as varchar))  as timely_filing_status,
        upper(cast(claim_readiness_status as varchar)) as claim_readiness_status,
        lower(cast(denial_risk_category as varchar))  as denial_risk_category,
        cast(missing_field_count as integer)      as missing_field_count,
        cast(failed_rule_count as integer)        as failed_rule_count,
        cast(review_required_count as integer)    as review_required_count,
        cast(days_since_service as integer)       as days_since_service,
        cast(aging_bucket as varchar)             as aging_bucket,
        cast(owner_team as varchar)               as owner_team,
        cast(estimated_revenue_at_risk_synthetic as double) as estimated_revenue_at_risk_synthetic,
        cast(data_completeness_score as double)   as data_completeness_score,
        cast(synthetic_only_flag as boolean)      as synthetic_only_flag

    from source

)

select * from renamed
