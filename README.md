# AuthFlow AI / Plenara — Prior Authorization Readiness Case Study

A recruiter-safe portfolio case study for a synthetic-data healthcare workflow prototype that structures prior authorization information and evaluates packet readiness before submission.

> **Portfolio status:** Synthetic/mock data only. No PHI. No real patient data. Not for clinical or production use.

---

## One-line Summary

AuthFlow AI, externally positioned as **Plenara**, is a workflow automation prototype that turns unstructured prior authorization inputs into structured, readiness-aware outputs using Python, JSON-style contracts, validation logic, and explainable review states.

---

## Why This Project Exists

Specialty clinics often lose time before prior authorization submission because documentation requirements can be payer-specific, incomplete, or difficult to match against clinical notes.

This project explores a focused workflow question:

> Can a structured readiness layer help clinic teams catch missing documentation before a packet is submitted?

The goal is not to predict approvals. The goal is to support human review by making packet readiness clearer.

---

## What This Case Study Shows

This public repo is intentionally **not** the full private development repository. It is a recruiter-safe case study that demonstrates:

- Problem framing
- Workflow analysis
- Data structuring
- Readiness states
- Example synthetic output
- Safety boundaries
- Future demo plan

---

## Core Workflow

```text
Synthetic clinical/admin input
        ↓
Field extraction / structuring
        ↓
Canonical case model
        ↓
Payer-style readiness rules
        ↓
Readiness status + blockers + review fields
        ↓
Clinic-facing readiness report
```

---

## Example Readiness States

- `ready_for_submission`
- `needs_review`
- `blocked_missing_requirements`

---

## Skills Demonstrated

This project is designed to demonstrate practical skills relevant to Data Analyst, Data Quality, Operations Analyst, Business Analyst, Healthcare Operations, and Workflow Automation roles:

- Translating messy workflows into structured data models
- Designing validation and completeness checks
- Working with JSON-style outputs and schemas
- Thinking through operational bottlenecks
- Documenting assumptions, risks, and limitations
- Building in a regulated-domain mindset without using sensitive data
- Communicating technical work clearly to non-technical stakeholders

---

## Repository Structure

```text
docs/
  portfolio_case_study.md
  future_demo_plan.md
sample_outputs/
  README.md
  readiness_response_sample.json
.env.example
.gitignore
README.md
```

---

## What Is Intentionally Excluded

This public case study does not include:

- Real patient data
- PHI
- Production clinical workflows
- Private API keys or credentials
- Internal development artifacts
- Autonomous payer submission
- Approval prediction

---

## Sample Output

See:

```text
sample_outputs/readiness_response_sample.json
```

The sample shows a synthetic readiness response with:

- readiness status
- blocker counts
- missing fields
- review-required fields
- confidence summary
- safety notice

---

## Safety Notice

This project is for portfolio and workflow research purposes only. It is not medical advice, legal advice, a clinical decision tool, or production prior authorization software.

Any production healthcare implementation would require HIPAA-compliant infrastructure, BAAs, encryption, access controls, audit logging, clinical/legal review, and human oversight.

---

## Current Status

Recruiter-safe public case study. The private development repo contains additional prototype code and experiments. This public repo is designed to communicate the project clearly without exposing sensitive or unfinished implementation details.

---

## Next Steps

- Add workflow diagram
- Add screenshots of synthetic sample report
- Add short demo walkthrough
- Add a lightweight mock UI
- Add more synthetic readiness scenarios
