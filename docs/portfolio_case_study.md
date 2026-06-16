# AuthFlow AI / Plenara — Public Case Study

## One-line Summary

AuthFlow AI, externally positioned as Plenara, is a synthetic-data healthcare workflow prototype that turns unstructured prior authorization inputs into structured, readiness-aware outputs using Python, JSON-style contracts, validation rules, and explainable review states.

> This project is a public case study and design-partner research prototype only. It uses synthetic/mock data. It does not process real PHI or real patient data.

---

## Problem

Prior authorization workflows in specialty clinics are often slowed down by incomplete documentation, payer-specific criteria, unclear evidence requirements, and repeated rework before a packet is ready for submission.

The goal of this prototype is not to predict approvals. The goal is to help structure information and identify whether a packet appears complete enough for human review.

---

## What I Built

I built a modular workflow prototype that can:

1. Accept synthetic clinical/admin inputs
2. Extract structured fields into JSON
3. Normalize data into a canonical case model
4. Apply payer-style readiness rules
5. Return a readiness state
6. Identify blockers, missing fields, and review-required fields
7. Generate a clinic-facing readiness report

Current readiness states:

- `ready_for_submission`
- `needs_review`
- `blocked_missing_requirements`

---

## Technical Components Represented

- Python workflow logic
- JSON-style schemas and contract definitions
- Canonical case mapping
- Rule-based readiness evaluation
- Confidence-aware review routing
- Synthetic fixtures and sample outputs
- Documentation-first development process

---

## What This Demonstrates

This workflow analytics demo shows practical capabilities across data structuring, data quality, healthcare operations, and workflow automation:

- Structuring messy information into reliable data models
- Building validation logic and readiness checks
- Designing explainable workflow states
- Documenting assumptions, limitations, and safety rules
- Working with API-style JSON outputs
- Translating an operational problem into a measurable workflow
- Handling regulated-domain thinking without using sensitive data

---

## Safety and Scope

This project intentionally avoids:

- Real patient data
- PHI
- Autonomous payer submission
- Approval prediction
- Clinical decision-making
- Production healthcare claims

Production use would require HIPAA-compliant infrastructure, BAAs, audit logging, encryption, access controls, clinical validation, legal review, and human oversight.

---

## Current Status

Public-safe case study. Built to explain the project clearly without exposing private development code, internal artifacts, or sensitive information.

---

## Next Improvements

- Public demo walkthrough
- Sample screenshots and visual workflow diagram
- Lightweight mock UI or dashboard
- More synthetic payer/ruleset examples
- Expanded data quality metrics
