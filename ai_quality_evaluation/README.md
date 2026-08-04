# AI Quality Evaluation Lab

A compact, reproducible portfolio artifact demonstrating **human-in-the-loop AI response evaluation** for fictional public-service use cases.

> **Portfolio scope:** All organizations, policies, source passages, prompts, and responses in this lab are synthetic. This is not a production system, not legal or policy guidance, and not evidence of employment as an AI evaluator. The lab demonstrates transferable evaluation design, source validation, rubric use, edge-case coverage, quality reporting, and transparent automation.

## Why this exists

The lab turns ambiguous quality expectations into reviewable artifacts:

- a versioned evaluation rubric;
- a prompt bank and golden set;
- paired strong and flawed candidate responses;
- human review annotations with concise rationale;
- automated checks for omissions, unsupported claims, safety language, and escalation;
- a generated results table and quality report;
- tests that make the evaluation repeatable.

It complements the broader [Plenara Healthcare Operations Readiness Lab](../README.md) without changing Plenara's application code, datasets, or readiness rules.

## 60-second reviewer path

1. Read [`quality_report.md`](quality_report.md).
2. Inspect [`evaluation_rubric.yaml`](evaluation_rubric.yaml).
3. Review the synthetic cases, candidate responses, and human annotations in [`data/benchmark.json`](data/benchmark.json).
4. Inspect row-level outcomes in [`evaluation_results.csv`](evaluation_results.csv).
5. Run `python ai_quality_evaluation/evaluate.py` and `python -m pytest tests/test_ai_quality_evaluation.py -q`.

## Evaluation design

Each synthetic case includes:

- a user prompt written in realistic language;
- a source-of-truth passage;
- expected facts and required safety/escalation behavior;
- forbidden or unsupported claims;
- one acceptable response and one intentionally flawed response;
- human scores for correctness, completeness, groundedness, safety, and actionability;
- concise reviewer rationale.

The evaluator combines two layers:

1. **Transparent automated checks** for required facts, forbidden claims, escalation language, and human-review requirements.
2. **Human rubric scores** with written rationale.

Automation does not replace human judgment. It makes routine checks reproducible and exposes missing evidence or unsafe behavior for review.

## Files

```text
ai_quality_evaluation/
├── README.md
├── evaluation_rubric.yaml
├── evaluate.py
├── quality_report.md
├── evaluation_results.csv
└── data/
    └── benchmark.json
tests/
└── test_ai_quality_evaluation.py
```

## Run locally

```bash
python ai_quality_evaluation/evaluate.py
python -m pytest tests/test_ai_quality_evaluation.py -q
```

The evaluator rewrites `evaluation_results.csv` and `quality_report.md` deterministically from `data/benchmark.json`.

## What the lab demonstrates

- translating stakeholder expectations into measurable criteria;
- defining repeatable scoring guidance;
- validating answers against explicit source material;
- detecting omissions and unsupported claims;
- building a prompt bank and golden set;
- expanding coverage across risk levels and edge cases;
- documenting reviewer rationale;
- producing concise quality metrics and defect themes;
- preserving a human quality gate.

## Limits

- Candidate responses are authored synthetic examples, not outputs from a deployed model.
- Keyword checks are intentionally simple and inspectable; they are not semantic evaluation.
- Human scores are example annotations by the project author, not calibrated production labels.
- The lab does not measure model drift, production latency, user impact, or real customer outcomes.
- A production program would add independent reviewers, adjudication, inter-rater reliability, approved source repositories, privacy controls, model/version metadata, regression history, and client-approved release thresholds.
