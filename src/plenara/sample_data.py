"""
Synthetic dataset generators and loaders for the Plenara HealthOps Readiness Lab.

Everything here is fabricated. Generators are deterministic (seeded) so the
bundled CSV files in ``data/`` are reproducible. Each generated row is passed
through the matching readiness engine, so the readiness columns in the datasets
are always consistent with the rules in :mod:`plenara.readiness`,
:mod:`plenara.provider_onboarding`, and :mod:`plenara.claims_readiness`.

Safety:
- No PHI, no real patients, providers, clinics, payers, claims, or reimbursement.
- All names/IDs are mock and every row carries ``synthetic_only_flag = True``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .claims_readiness import aging_bucket, evaluate_claim_readiness
from .provider_onboarding import evaluate_provider_onboarding
from .readiness import evaluate_pa_case

# Repo-root/data — resolved relative to this file so it works from any CWD.
DATA_DIR = Path(__file__).resolve().parents[2] / "data"

AUTHORIZATION_CSV = DATA_DIR / "synthetic_authorization_cases.csv"
PROVIDER_ONBOARDING_CSV = DATA_DIR / "synthetic_provider_onboarding.csv"
CLAIM_READINESS_CSV = DATA_DIR / "synthetic_claim_readiness.csv"

# --- Shared synthetic vocab -------------------------------------------------
CLINICS = [f"CLINIC_{i:02d}" for i in range(1, 9)]
CLINIC_REGIONS = ["Northeast", "Midwest", "South", "West", "Mountain"]
PAYERS_MOCK = [
    "MockHealth PPO",
    "Synthetic Mutual",
    "Example Care HMO",
    "Demo Health Plan",
    "Sample State Medicaid (mock)",
    "Placeholder Medicare Adv (mock)",
]
PLAN_TYPES = ["PPO", "HMO", "EPO", "POS", "Medicaid (mock)", "Medicare Adv (mock)"]
OWNER_TEAMS = ["Intake", "Credentialing", "Coding", "Billing", "Payer Relations", "QA"]
SPECIALTIES = [
    "Rheumatology",
    "Gastroenterology",
    "Dermatology",
    "Endocrinology",
    "Pathology",
    "Laboratory Medicine",
]


def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


# ===========================================================================
# A. Prior Authorization Readiness
# ===========================================================================
PA_DIAGNOSES = [
    "rheumatoid_arthritis",
    "crohns_disease",
    "psoriasis",
    "ulcerative_colitis",
]
PA_MEDICATIONS = ["adalimumab", "infliximab", "ustekinumab", "etanercept"]
PA_AUTH_TYPES = ["initial_authorization", "reauthorization"]
PA_PAYER_TYPES = ["commercial", "medicaid_mock", "medicare_adv_mock"]
PA_CONFIDENCE_BANDS = ["high", "high", "high", "medium", "low"]
PA_MISSING_FIELDS = [
    "none",
    "disease_activity_evidence",
    "failed_therapy_history",
    "provider_specialty",
    "clinical_note_completeness",
    "diagnosis",
    "medication",
]


PA_CRITICAL_MISSING = ["diagnosis", "medication", "authorization_type", "disease_activity_evidence", "provider_specialty"]
PA_NONCRITICAL_MISSING = ["failed_therapy_history", "clinical_note_completeness"]


def _pa_inputs(rng: np.random.Generator, profile: str) -> dict:
    """Build PA input fields conditioned on a health profile."""
    if profile == "clean":
        return {
            "failed_blocker_count": 0,
            "missing_field_count": 0,
            "top_missing_field": "none",
            "confidence_band": "high",
            "review_required_count": 0,
            "data_completeness_score": round(float(rng.uniform(0.9, 1.0)), 2),
        }
    if profile == "major":  # blocked
        if rng.random() < 0.6:
            return {
                "failed_blocker_count": int(rng.integers(1, 3)),
                "missing_field_count": int(rng.integers(0, 2)),
                "top_missing_field": str(rng.choice(PA_NONCRITICAL_MISSING + ["none"])),
                "confidence_band": str(rng.choice(["high", "medium"])),
                "review_required_count": int(rng.integers(0, 2)),
                "data_completeness_score": round(float(rng.uniform(0.7, 0.95)), 2),
            }
        return {
            "failed_blocker_count": 0,
            "missing_field_count": int(rng.integers(1, 3)),
            "top_missing_field": str(rng.choice(PA_CRITICAL_MISSING)),
            "confidence_band": str(rng.choice(["high", "medium"])),
            "review_required_count": int(rng.integers(0, 2)),
            "data_completeness_score": round(float(rng.uniform(0.7, 0.95)), 2),
        }
    # minor -> needs review (no blockers, at least one review trigger)
    trigger = str(rng.choice(["confidence", "review_required", "completeness", "noncritical_missing"]))
    return {
        "failed_blocker_count": 0,
        "missing_field_count": 1 if trigger == "noncritical_missing" else 0,
        "top_missing_field": str(rng.choice(PA_NONCRITICAL_MISSING)) if trigger == "noncritical_missing" else "none",
        "confidence_band": str(rng.choice(["low", "medium"])) if trigger == "confidence" else "high",
        "review_required_count": int(rng.integers(1, 3)) if trigger == "review_required" else 0,
        "data_completeness_score": round(float(rng.uniform(0.70, 0.84)), 2) if trigger == "completeness" else round(float(rng.uniform(0.88, 1.0)), 2),
    }


def generate_authorization_cases(n: int = 90, seed: int = 20240601) -> pd.DataFrame:
    rng = _rng(seed)
    rows = []
    profiles = rng.choice(["clean", "minor", "major"], size=n, p=[0.4, 0.33, 0.27])
    for i in range(1, n + 1):
        case = _pa_inputs(rng, str(profiles[i - 1]))
        failed_blockers = case["failed_blocker_count"]
        missing_count = case["missing_field_count"]
        top_missing = case["top_missing_field"]
        confidence = case["confidence_band"]
        review_required = case["review_required_count"]
        completeness = case["data_completeness_score"]

        _case = {
            "failed_blocker_count": failed_blockers,
            "missing_field_count": missing_count,
            "top_missing_field": top_missing,
            "confidence_band": confidence,
            "review_required_count": review_required,
            "data_completeness_score": completeness,
        }
        result = evaluate_pa_case(_case)
        days_to_ready = 0 if result.status == "READY" else int(rng.integers(2, 28))

        rows.append(
            {
                "case_id": f"PA_{i:04d}",
                "clinic_id": str(rng.choice(CLINICS)),
                "payer_type": str(rng.choice(PA_PAYER_TYPES)),
                "diagnosis": str(rng.choice(PA_DIAGNOSES)),
                "medication": str(rng.choice(PA_MEDICATIONS)),
                "authorization_type": str(rng.choice(PA_AUTH_TYPES)),
                "readiness_status": result.status,
                "missing_field_count": missing_count,
                "failed_blocker_count": failed_blockers,
                "review_required_count": review_required,
                "confidence_band": confidence,
                "days_to_ready": days_to_ready,
                "data_completeness_score": completeness,
                "top_missing_field": top_missing,
                "owner_team": str(rng.choice(OWNER_TEAMS)),
                "synthetic_only_flag": True,
            }
        )
    return pd.DataFrame(rows)


# ===========================================================================
# B. Provider / Clinic / Insurance Onboarding Readiness
# ===========================================================================
ONBOARDING_STAGES = [
    "intake",
    "credentialing",
    "payer_enrollment",
    "directory_update",
    "go_live",
]


_ONB_GOOD = {
    "credentialing_status": "complete",
    "contract_status": "active",
    "directory_status": "updated",
    "enrollment_status": "enrolled",
    "documentation_status": "complete",
    "caqh_status": "current",
    "npi_status": "verified",
    "license_status": "verified",
    "effective_date_status": "set",
}
# Field -> a blocking bad value (used for "major" profile).
_ONB_BLOCKERS = {
    "credentialing_status": "missing",
    "contract_status": "not_active",
    "directory_status": "not_updated",
    "enrollment_status": "not_enrolled",
    "npi_status": "mismatch",
    "license_status": "expired",
    "effective_date_status": "missing",
}


def _onboarding_statuses(rng: np.random.Generator, profile: str) -> dict[str, str]:
    statuses = dict(_ONB_GOOD)
    if profile == "major":
        field = str(rng.choice(list(_ONB_BLOCKERS)))
        statuses[field] = _ONB_BLOCKERS[field]
    elif profile == "minor":
        # A soft, review-level signal that does not block.
        choice = str(rng.choice(["caqh", "documentation", "credentialing", "contract"]))
        if choice == "caqh":
            statuses["caqh_status"] = "stale"
        elif choice == "documentation":
            statuses["documentation_status"] = "incomplete"
        elif choice == "credentialing":
            statuses["credentialing_status"] = "in_progress"
        else:
            statuses["contract_status"] = "pending"
    return statuses


def generate_provider_onboarding(n: int = 120, seed: int = 20240602) -> pd.DataFrame:
    rng = _rng(seed)
    first = ["Alex", "Jordan", "Casey", "Riley", "Morgan", "Taylor", "Jamie", "Avery", "Quinn", "Drew"]
    last = ["Stone", "Rivers", "Bell", "Hart", "Frost", "Vale", "Reed", "Marsh", "Cole", "Pike"]
    rows = []
    profiles = rng.choice(["clean", "minor", "major"], size=n, p=[0.4, 0.33, 0.27])
    for i in range(1, n + 1):
        profile = str(profiles[i - 1])
        statuses = _onboarding_statuses(rng, profile)
        # Aging: only "minor" rows risk an aging stage; clean rows stay fresh.
        if profile == "clean":
            days_in_stage = int(rng.integers(1, 25))
        elif profile == "minor":
            days_in_stage = int(rng.integers(5, 60))
        else:
            days_in_stage = int(rng.integers(3, 75))
        owner = str(rng.choice(OWNER_TEAMS)) if profile != "minor" else str(
            rng.choice(OWNER_TEAMS + ["unassigned"], p=[0.16, 0.16, 0.16, 0.16, 0.16, 0.1, 0.1])
        )
        # Synthetic readiness score loosely correlated with cleanliness of statuses.
        clean = sum(
            v in {"complete", "active", "updated", "enrolled", "current", "verified", "set"}
            for v in statuses.values()
        )
        score = round(min(1.0, max(0.2, clean / 9 + float(rng.uniform(-0.05, 0.05)))), 2)

        record = {
            **statuses,
            "days_in_stage": days_in_stage,
            "owner_team": owner,
            "readiness_score": score,
        }
        result = evaluate_provider_onboarding(record)

        rows.append(
            {
                "provider_id": f"PRV_{i:04d}",
                "provider_name_mock": f"Dr. {rng.choice(first)} {rng.choice(last)} (mock)",
                "specialty": str(rng.choice(SPECIALTIES)),
                "clinic_id": str(rng.choice(CLINICS)),
                "clinic_region": str(rng.choice(CLINIC_REGIONS)),
                "payer_name_mock": str(rng.choice(PAYERS_MOCK)),
                "insurance_plan_type": str(rng.choice(PLAN_TYPES)),
                **statuses,
                "onboarding_stage": str(rng.choice(ONBOARDING_STAGES)),
                "blocker_category": result.blocker_category or "none",
                "days_in_stage": days_in_stage,
                "owner_team": owner,
                "readiness_status": result.status,
                "readiness_score": score,
                "synthetic_only_flag": True,
            }
        )
    return pd.DataFrame(rows)


# ===========================================================================
# C. Diagnostic / Lab Revenue Cycle Readiness
# ===========================================================================
TEST_CATEGORIES = [
    "molecular_diagnostics",
    "clinical_chemistry",
    "hematology",
    "anatomic_pathology",
    "microbiology",
    "genetic_testing",
]
# Synthetic base "revenue" per category (mock dollars, not real reimbursement).
TEST_BASE_REVENUE = {
    "molecular_diagnostics": 850.0,
    "clinical_chemistry": 120.0,
    "hematology": 95.0,
    "anatomic_pathology": 410.0,
    "microbiology": 180.0,
    "genetic_testing": 1200.0,
}


_CLAIM_GOOD = {
    "eligibility_status": "verified",
    "prior_auth_status": "obtained",
    "documentation_status": "complete",
    "coding_status": "valid",
    "modifier_status": "correct",
    "payer_rule_status": "pass",
    "timely_filing_status": "within_window",
}
_CLAIM_BLOCKERS = {
    "eligibility_status": ["inactive", "mismatch"],
    "prior_auth_status": ["missing"],
    "coding_status": ["mismatch", "missing"],
    "payer_rule_status": ["fail"],
    "timely_filing_status": ["expired"],
}
_CLAIM_REVIEWS = {
    "eligibility_status": ["unverified"],
    "documentation_status": ["incomplete", "stale"],
    "modifier_status": ["missing", "invalid"],
    "payer_rule_status": ["review"],
    "timely_filing_status": ["at_risk"],
}


def _claim_statuses(rng: np.random.Generator, profile: str) -> dict[str, str]:
    statuses = dict(_CLAIM_GOOD)
    if profile == "major":
        field = str(rng.choice(list(_CLAIM_BLOCKERS)))
        statuses[field] = str(rng.choice(_CLAIM_BLOCKERS[field]))
    elif profile == "minor":
        field = str(rng.choice(list(_CLAIM_REVIEWS)))
        statuses[field] = str(rng.choice(_CLAIM_REVIEWS[field]))
    return statuses


def generate_claim_readiness(n: int = 150, seed: int = 20240603) -> pd.DataFrame:
    rng = _rng(seed)
    rows = []
    profiles = rng.choice(["clean", "minor", "major"], size=n, p=[0.45, 0.32, 0.23])
    for i in range(1, n + 1):
        profile = str(profiles[i - 1])
        statuses = _claim_statuses(rng, profile)
        failed_rule = 1 if statuses["payer_rule_status"] == "fail" else 0
        review_required = int(rng.integers(1, 3)) if profile == "minor" and rng.random() < 0.4 else 0
        if profile == "clean":
            completeness = round(float(rng.uniform(0.9, 1.0)), 2)
            days_since_service = int(rng.integers(1, 40))
        elif profile == "minor":
            completeness = round(float(rng.uniform(0.8, 1.0)), 2)
            days_since_service = int(rng.integers(1, 60))
        else:
            completeness = round(float(rng.uniform(0.7, 1.0)), 2)
            days_since_service = int(rng.integers(1, 120))
        test_category = str(rng.choice(TEST_CATEGORIES))

        claim = {
            **statuses,
            "failed_rule_count": failed_rule,
            "review_required_count": review_required,
            "data_completeness_score": completeness,
            "days_since_service": days_since_service,
        }
        result = evaluate_claim_readiness(claim)

        # Synthetic missing-field count derived from blocking/review signals.
        missing_count = sum(
            statuses[k] in bad
            for k, bad in {
                "coding_status": {"missing"},
                "prior_auth_status": {"missing"},
                "modifier_status": {"missing"},
                "documentation_status": {"incomplete"},
            }.items()
        )

        # Synthetic revenue at risk: base revenue weighted by risk, $0 when clean.
        base = TEST_BASE_REVENUE[test_category]
        risk_weight = {"high": 0.9, "medium": 0.4, "low": 0.0}[result.denial_risk_category]
        revenue_at_risk = round(base * risk_weight, 2)

        rows.append(
            {
                "claim_id": f"CLM_{i:05d}",
                "accession_id_mock": f"ACC_{i:06d}",
                "lab_order_id_mock": f"ORD_{rng.integers(100000, 999999)}",
                "clinic_id": str(rng.choice(CLINICS)),
                "clinic_region": str(rng.choice(CLINIC_REGIONS)),
                "payer_name_mock": str(rng.choice(PAYERS_MOCK)),
                "plan_type": str(rng.choice(PLAN_TYPES)),
                "test_category": test_category,
                "procedure_code_mock": f"MOCK-{rng.integers(80000, 89999)}",
                "diagnosis_code_mock": f"MOCK-{chr(65 + int(rng.integers(0, 26)))}{rng.integers(10, 99)}",
                "ordering_provider_specialty": str(rng.choice(SPECIALTIES)),
                **statuses,
                "claim_readiness_status": result.status,
                "denial_risk_category": result.denial_risk_category,
                "missing_field_count": int(missing_count),
                "failed_rule_count": failed_rule,
                "review_required_count": review_required,
                "days_since_service": days_since_service,
                "aging_bucket": aging_bucket(days_since_service),
                "owner_team": str(rng.choice(OWNER_TEAMS)),
                "estimated_revenue_at_risk_synthetic": revenue_at_risk,
                "data_completeness_score": completeness,
                "synthetic_only_flag": True,
            }
        )
    return pd.DataFrame(rows)


# ===========================================================================
# Materialization + loaders
# ===========================================================================
def write_all_datasets() -> dict[str, Path]:
    """(Re)generate all three CSVs into ``data/``. Used to build the repo."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "authorization": (AUTHORIZATION_CSV, generate_authorization_cases()),
        "provider_onboarding": (PROVIDER_ONBOARDING_CSV, generate_provider_onboarding()),
        "claim_readiness": (CLAIM_READINESS_CSV, generate_claim_readiness()),
    }
    paths: dict[str, Path] = {}
    for name, (path, frame) in outputs.items():
        frame.to_csv(path, index=False)
        paths[name] = path
    return paths


def _load_or_generate(path: Path, generator) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    return generator()


def load_authorization_cases() -> pd.DataFrame:
    return _load_or_generate(AUTHORIZATION_CSV, generate_authorization_cases)


def load_provider_onboarding() -> pd.DataFrame:
    return _load_or_generate(PROVIDER_ONBOARDING_CSV, generate_provider_onboarding)


def load_claim_readiness() -> pd.DataFrame:
    return _load_or_generate(CLAIM_READINESS_CSV, generate_claim_readiness)


if __name__ == "__main__":
    written = write_all_datasets()
    for name, path in written.items():
        df = pd.read_csv(path)
        print(f"{name}: {len(df)} rows -> {path}")
