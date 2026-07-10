# Product Strategy — Plenara

> Synthetic prototype stage. No PHI, no integrations, no production deployment.
> This document is product thinking, not a commitment to build a regulated system.

## Product thesis

Healthcare operations readiness is a workflow-intelligence problem, not a form
problem. If a clinic can see — in one place — what is blocked, why, who owns it,
and what to do next across prior authorization, provider onboarding, and lab
revenue cycle, it can prevent rework and aging before work moves forward. Plenara
demonstrates that picture on synthetic data, with explainable logic and clear
safety boundaries.

## Target users

Prior authorization managers · revenue cycle / billing managers · clinic
operations managers · provider onboarding teams · healthcare data / operations
analysts.

## Core pain points

- Fragmented tools: PA, onboarding, and claims live in separate systems.
- No shared definition of "ready," so prioritization is manual and inconsistent.
- Blocked and aging work is discovered late, causing rework and lost time.
- Unclear ownership of blocked items.
- Leaders lack a fast, trustworthy operational read.

## Why clinics would care

Less rework, earlier detection of missing documentation and blockers, clearer
ownership, and a consistent readiness language across teams — without adding
another opaque tool. Explainability builds trust with operators.

## MVP scope (synthetic)

Three readiness workflows · shared READY/NEEDS REVIEW/BLOCKED states · unified
work queue with severity and recommended actions · executive KPIs and insights ·
data-quality checks · SQL analytics layer · scenario selector.

## Demo-only scope (explicitly out of scope now)

No PHI, no EHR/payer integrations, no claim submission, no production auth or
database, no user accounts, no approval/denial prediction, no autonomous
decisions.

## Differentiation

- **Explainable, deterministic** readiness rather than opaque scoring.
- **Cross-workflow** view (PA + onboarding + RCM) in one readiness language.
- **Analyst-grade proof**: metric definitions, dbt-style models, and a runnable
  DuckDB SQL portfolio with a consistency check.
- **Safety-first**: synthetic-only with explicit boundaries and honest framing.

## Design-partner discovery plan

Use the synthetic demo and [`clinic_demo_script.md`](clinic_demo_script.md) to run
discovery conversations with clinics and operators — no PHI. Map real workflows,
validate the readiness picture, and identify the highest-friction workflow before
any pilot.

## Success metrics — synthetic demo

- A reviewer understands the product in under two minutes.
- Operators agree the readiness picture matches how they work.
- Clear identification of the highest-friction workflow to target first.
- Positive signal to continue to a scoped, no-PHI workflow-mapping engagement.

## Success metrics — future clinic pilot

Defined with a design partner; would center on reduced rework, earlier blocker
detection, clearer ownership, and time-to-ready — measured under proper agreements
and controls, never claimed from synthetic data.

## Risks and constraints

- Regulated domain: real PHI requires legal, security, and compliance work.
- Over-claiming risk: avoid prediction, ROI, or compliance claims.
- Integration complexity if/when real systems are involved.
- Scope creep: keep the demo focused and honest.

## What not to build yet

Authentication, production database, EHR/payer integrations, claim submission,
approval/denial prediction, autonomous decisions, or any real-PHI path — none of
these until a proper legal, security, and compliance foundation exists.
