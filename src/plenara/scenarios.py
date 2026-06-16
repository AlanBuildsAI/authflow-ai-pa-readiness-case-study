"""
Synthetic scenario profiles for the Plenara HealthOps Readiness Lab.

A "scenario" is a synthetic operating posture used to make the demo feel like a
real operations week (a calm week, a backlog week, a payer-friction week, an
onboarding surge, a revenue-cycle cleanup push). Each profile tunes the mix of
clean / minor-issue / major-issue records the generators produce.

IMPORTANT
---------
These are **synthetic scenario design assumptions**, not industry benchmarks and
not observed real-world rates. The distribution guidance ranges describe how the
demo data is *designed* to behave so the dashboards tell a coherent story — they
are not claims about real prior authorization, onboarding, or claims operations.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioProfile:
    key: str
    label: str
    description: str
    intended_use: str
    # (clean, minor, major) base probability mix applied to generated records.
    profile_mix: tuple[float, float, float]
    # Synthetic distribution *guidance* (designed, not benchmarked).
    ready_range: tuple[float, float]
    review_range: tuple[float, float]
    blocked_range: tuple[float, float]
    blocker_emphasis: tuple[str, ...]
    ui_copy: str

    def mix(self) -> list[float]:
        total = sum(self.profile_mix)
        return [p / total for p in self.profile_mix]


SCENARIOS: dict[str, ScenarioProfile] = {
    "stable_operations": ScenarioProfile(
        key="stable_operations",
        label="Stable operations",
        description=(
            "A calm operating week. Most work is ready or moving; only a small "
            "share is blocked or aging."
        ),
        intended_use="Baseline / healthy-state view for stakeholders.",
        profile_mix=(0.70, 0.20, 0.10),
        ready_range=(0.60, 0.80),
        review_range=(0.10, 0.25),
        blocked_range=(0.05, 0.18),
        blocker_emphasis=("missing clinical documentation", "eligibility verification"),
        ui_copy="Operations are stable — focus on a small, well-owned review queue.",
    ),
    "moderate_backlog": ScenarioProfile(
        key="moderate_backlog",
        label="Moderate backlog",
        description=(
            "A realistic mixed week with a meaningful review queue and a steady "
            "stream of blockers across all three workflows."
        ),
        intended_use="Default balanced demo across prior auth, onboarding, and RCM.",
        profile_mix=(0.45, 0.32, 0.23),
        ready_range=(0.40, 0.58),
        review_range=(0.25, 0.40),
        blocked_range=(0.15, 0.32),
        blocker_emphasis=("payer-specific criteria", "missing clinical documentation"),
        ui_copy="A normal backlog — prioritize aging and high-impact blockers first.",
    ),
    "high_friction_payer_environment": ScenarioProfile(
        key="high_friction_payer_environment",
        label="High-friction payer environment",
        description=(
            "Payer-rule failures, documentation gaps, and eligibility issues are "
            "elevated, pushing more work into blocked and review states."
        ),
        intended_use="Stress view emphasizing payer-rule and documentation friction.",
        profile_mix=(0.30, 0.30, 0.40),
        ready_range=(0.22, 0.42),
        review_range=(0.22, 0.40),
        blocked_range=(0.30, 0.50),
        blocker_emphasis=(
            "payer rule failure",
            "documentation gap",
            "eligibility mismatch",
        ),
        ui_copy="Payer friction is high — expect more blockers tied to payer rules and documentation.",
    ),
    "onboarding_surge": ScenarioProfile(
        key="onboarding_surge",
        label="Onboarding surge",
        description=(
            "A wave of provider onboarding with credentialing, enrollment, and "
            "directory work aging in queue."
        ),
        intended_use="Provider/clinic/payer onboarding-focused view with aging tasks.",
        profile_mix=(0.38, 0.37, 0.25),
        ready_range=(0.30, 0.52),
        review_range=(0.28, 0.45),
        blocked_range=(0.15, 0.34),
        blocker_emphasis=(
            "credentialing packet",
            "payer enrollment",
            "aging task",
        ),
        ui_copy="Onboarding volume is high — watch aging credentialing and enrollment tasks.",
    ),
    "rcm_cleanup_queue": ScenarioProfile(
        key="rcm_cleanup_queue",
        label="RCM cleanup queue",
        description=(
            "A revenue-cycle cleanup push: aged claims, payer-rule failures, and "
            "elevated synthetic revenue at risk concentrated in non-clean claims."
        ),
        intended_use="Diagnostic/lab RCM-focused view with aging and revenue at risk.",
        profile_mix=(0.32, 0.26, 0.42),
        ready_range=(0.25, 0.45),
        review_range=(0.18, 0.35),
        blocked_range=(0.30, 0.52),
        blocker_emphasis=(
            "claim aging",
            "payer rule failure",
            "timely filing risk",
        ),
        ui_copy="Revenue-cycle cleanup — clear aged, high-impact claims before timely filing risk grows.",
    ),
}

DEFAULT_SCENARIO = "moderate_backlog"


def get_scenario(key: str) -> ScenarioProfile:
    """Return a scenario profile, falling back to the default if unknown."""
    return SCENARIOS.get(key, SCENARIOS[DEFAULT_SCENARIO])
