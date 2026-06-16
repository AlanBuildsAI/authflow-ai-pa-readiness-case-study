"""
Plenara — Healthcare Operations Readiness Lab (synthetic).

A synthetic healthcare operations analytics package covering three readiness
modules:

1. Prior Authorization Readiness        (:mod:`plenara.readiness`)
2. Provider / Clinic / Insurance Onboarding Readiness
                                        (:mod:`plenara.provider_onboarding`)
3. Diagnostic / Lab Revenue Cycle Readiness
                                        (:mod:`plenara.claims_readiness`)

Supporting layers: :mod:`plenara.metrics`, :mod:`plenara.data_quality`,
:mod:`plenara.reporting`, and :mod:`plenara.sample_data`.

Safety: synthetic/mock data only. No PHI, no real patient/provider/payer/claims
data, no live integrations, and no network calls at import time.

This ``__init__`` is intentionally lightweight: it exposes version metadata and
the canonical readiness labels, and re-exports the three evaluator entry points.
It performs no I/O and no eager dataset loading on import.
"""

from __future__ import annotations

__version__ = "0.2.0"

from .readiness import (
    BLOCKED,
    NEEDS_REVIEW,
    READINESS_STATES,
    READY,
    evaluate_pa_case,
)
from .provider_onboarding import evaluate_provider_onboarding
from .claims_readiness import evaluate_claim_readiness

__all__ = [
    "__version__",
    "READY",
    "NEEDS_REVIEW",
    "BLOCKED",
    "READINESS_STATES",
    "evaluate_pa_case",
    "evaluate_provider_onboarding",
    "evaluate_claim_readiness",
]
