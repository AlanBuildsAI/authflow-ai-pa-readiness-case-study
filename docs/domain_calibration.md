# Domain Calibration — Plenara HealthOps Readiness Lab

This document explains how the synthetic demo is calibrated to *feel* credible to
real healthcare operations staff, and — just as importantly — how it stays
honest. Everything here describes **synthetic scenario design**, not industry
benchmarks and not observed real-world rates.

---

## Target users

The demo is written for the people who actually work these queues:

- **Prior authorization manager / coordinator** — owns submission readiness, payer criteria, and the review queue.
- **RCM / billing manager** — owns clean-claim rate, denials/rework, aging A/R, and timely filing.
- **Clinic operations manager** — owns throughput, owner assignment, and aging tasks across workflows.
- **Healthcare data analyst** — owns metric definitions, data quality, and reporting.

The product question for all four: *what is blocked, why, who owns it, what is
aging, and what should we do next?*

## Workflow assumptions

- Work flows through readiness states: **READY → submit**, **NEEDS REVIEW → human check**, **BLOCKED → fix before submission**.
- Every item should have an **owner team**; unassigned non-ready work is itself a problem to surface.
- Items **age**. Aging correlates with review/blocked states, and aged blocked items are the most urgent.
- Friction is **not uniform** — some clinics and some payers generate more issues than others.
- Readiness is decided by **deterministic, explainable rules**, not opaque scores or predictions.

## Terminology

### Prior authorization
missing clinical documentation · eligibility verification · payer-specific
criteria · medical necessity evidence · diagnosis support · step therapy
documentation · authorization status · submission readiness · review queue ·
internal SLA.

### Provider / clinic / insurance onboarding
credentialing packet · payer enrollment · contract status · CAQH attestation ·
directory update · NPI verification · license verification · effective date ·
owner team · aging task.

### Diagnostic / lab revenue cycle (RCM)
clean claim readiness · eligibility mismatch · coding mismatch · modifier
required · documentation gap · timely filing risk · payer rule failure · claim
aging · denial risk category · work queue · synthetic revenue at risk.

## Synthetic scenario assumptions

The lab ships five scenario profiles (see [`src/plenara/scenarios.py`](../src/plenara/scenarios.py)):

| Scenario | Posture | Emphasis |
|---|---|---|
| `stable_operations` | Calm week, mostly ready | small, well-owned review queue |
| `moderate_backlog` (default) | Balanced mixed week | steady blockers across all three |
| `high_friction_payer_environment` | Elevated friction | payer-rule, documentation, eligibility |
| `onboarding_surge` | Onboarding wave | aging credentialing / enrollment |
| `rcm_cleanup_queue` | Revenue cleanup push | aged claims, revenue at risk |

Each profile defines a `(clean, minor, major)` record mix and a synthetic
distribution **guidance** range. Clinic and payer friction then shift that mix
per record, so the same scenario produces a clinic with a heavy queue and
another that is mostly clean — as operators would expect.

## KPI interpretation guide

| KPI | Reading |
|---|---|
| Critical blockers | Count of BLOCKED records across all modules; the must-fix pile. |
| Aging claims 60+ | Claims past 60 days since service (buckets 61-90, 90+); timely-filing risk grows here. |
| Unassigned work items | Non-ready items without an owner team; assign before handoff. |
| Synthetic revenue at risk | Sum of mock revenue on non-clean claims; concentrated in aged, blocked claims. Not real money. |
| Overall readiness rate | Share of all records that are READY across the three modules. |
| Clean claim readiness rate | Share of claims READY for clean submission. |

## What would look suspicious to a real operator

These are the "tells" the calibration deliberately avoids:

- **100% blocked or 100% ready** — real queues are mixed; we keep all three states present.
- **Uniform friction** — every clinic/payer identical is unrealistic; we vary it.
- **Aging uncorrelated with status** — fresh blockers and ancient clean items look fake; aging tracks status here.
- **Revenue at risk on clean claims** — clean claims carry $0 risk here.
- **Blocked items with no owner everywhere** — blocked work is always owned; only some non-blocked work is unassigned.
- **Opaque scores with no explanation** — every state traces to named blockers/review reasons.
- **Approval/denial prediction language** — we never claim to predict payer decisions.

## How to keep the demo honest

- Label everything synthetic; keep the safety banner and the Safety tab visible.
- Never imply real benchmarks, observed ROI, or real reimbursement.
- Keep `denial_risk_category` framed as a synthetic operational signal, not a prediction.
- Keep readiness rules deterministic and inspectable; no hidden model.
- No network calls, no real data, no integrations at runtime.

## Recommended synthetic ranges (scenario design, not benchmarks)

> These describe how the **demo data is designed to behave**, so dashboards read
> coherently. They are **not** industry figures.

| Scenario | READY | NEEDS REVIEW | BLOCKED |
|---|---|---|---|
| stable_operations | 0.60–0.80 | 0.10–0.25 | 0.05–0.18 |
| moderate_backlog | 0.40–0.58 | 0.25–0.40 | 0.15–0.32 |
| high_friction_payer_environment | 0.22–0.42 | 0.22–0.40 | 0.30–0.50 |
| onboarding_surge | 0.30–0.52 | 0.28–0.45 | 0.15–0.34 |
| rcm_cleanup_queue | 0.25–0.45 | 0.18–0.35 | 0.30–0.52 |

Other designed relationships: aged claims (60+ days) skew blocked/review; synthetic
revenue at risk is highest for aged blocked claims and $0 for clean claims;
high-friction clinics/payers produce more blockers than low-friction ones.
