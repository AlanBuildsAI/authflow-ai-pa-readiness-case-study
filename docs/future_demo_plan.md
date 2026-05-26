# Future Demo Plan

This document outlines how the public AuthFlow AI / Plenara case study can become a polished recruiter-facing demo.

## Goal

Create a short, professional demo that shows the workflow clearly without using real patient data, PHI, payer credentials, or production infrastructure.

## Demo Storyline

1. Start with a synthetic clinic note or administrative input.
2. Show how key fields are structured into a canonical case format.
3. Run readiness checks against synthetic payer-style requirements.
4. Display the readiness state.
5. Highlight blockers, missing documentation, and review-required fields.
6. Show a clinic-facing report preview.

## Recommended Demo Assets

- Workflow diagram
- Screenshot of sample JSON output
- Screenshot of synthetic readiness report
- Short screen recording, 60 to 90 seconds
- Optional mock dashboard or lightweight UI

## Demo Safety Rules

- Use synthetic data only
- No PHI
- No real payer data
- No real patient documents
- No autonomous submission claims
- No approval prediction claims
- Include safety notice in screenshots and demo copy

## Suggested Demo Sections

### 1. Problem

Specialty clinics lose time when prior authorization packets are incomplete or difficult to match against payer documentation requirements.

### 2. Workflow

Input → extraction → canonical case → readiness rules → status/report.

### 3. Output

Show a synthetic response with `needs_review`, missing fields, blocker counts, and confidence summary.

### 4. Value

The system demonstrates data structuring, workflow automation, validation logic, and operational thinking.

## Future Enhancement Ideas

- Add a mock UI built with Streamlit or FastAPI templates
- Add multiple synthetic cases
- Add readiness comparison table
- Add audit log example
- Add data quality metrics
- Add a short LinkedIn demo video
