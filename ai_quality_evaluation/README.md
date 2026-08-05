# AI Quality Evaluation Lab

A compact, reproducible portfolio artifact demonstrating **human-in-the-loop AI response evaluation** for fictional public-service use cases.

> **Portfolio scope:** All organizations, policies, source passages, prompts, and responses in this lab are synthetic. This is not a production system, not legal or policy guidance, and not evidence of employment as an AI evaluator. The lab demonstrates transferable evaluation design, source validation, rubric use, edge-case coverage, quality reporting, and transparent automation.

## Why this exists

The lab turns ambiguous quality expectations into reviewable artifacts:

- a versioned evaluation rubric;
- a compact benchmark and golden set;
- paired acceptable and intentionally flawed candidate responses;
- example human scores with concise rationale;
- automated checks for omissions, unsupported claims, safety language, escalation, and source conflict;
- generated results and a quality report;
- tests that verify both evaluation behavior and reproducibility.

It complements the broader [Plenara Healthcare Operations Readiness Lab](../README.md) without changing Plenara's application code, datasets, or readiness rules.

## 60-second reviewer path

1. Read [`quality_report.md`](quality_report.md).
2. Inspect [`evaluation_rubric.yaml`](evaluation_rubric.yaml).
3. Compare source truth, expected behavior, and candidate responses in [`data/benchmark.json`](data/benchmark.json).
4. Review row-level outcomes in [`evaluation_results.csv`](evaluation_results.csv).
5. Run `python ai_quality_evaluation/evaluate.py` and `python -m pytest tests/test_ai_quality_evaluation.py -q`.

## Evaluation design

Each synthetic case includes:

- a realistic user prompt;
- an approved source-of-truth passage;
- expected facts and required safety or escalation behavior;
- forbidden or unsupported claims;
- one acceptable response and one intentionally flawed response;
- example human scores and written rationale.

The evaluator combines two layers:

1. **Transparent automated checks** for required facts, forbidden claims, escalation language, human-review requirements, and source-conflict handling.
2. **Example human rubric scores** for correctness, completeness, groundedness, safety, and actionability.

The automated decision threshold is loaded from the versioned rubric instead of being duplicated in code. Automation does not replace human judgment; it makes routine checks reproducible and exposes missing evidence for review.

## Files

```text
ai_quality_evaluation/
├── README.md
├── evaluation_rubric.yaml
├── evaluate.py
├── evaluation_results.csv
├── quality_report.md
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

The evaluator rewrites `evaluation_results.csv` and `quality_report.md` deterministically from the checked-in rubric and benchmark. The test suite verifies that regenerated files exactly match the committed artifacts.

## What the lab demonstrates

- translating stakeholder expectations into measurable criteria;
- defining repeatable scoring and release guidance;
- validating answers against explicit source material;
- detecting omissions and unsupported claims;
- constructing a small golden set and prompt bank;
- handling low-, medium-, high-, and critical-risk cases;
- handling conflicting or stale sources without inventing certainty;
- documenting reviewer rationale;
- producing concise quality metrics and defect themes;
- preserving human-review and escalation boundaries.

## Transferable role alignment

This artifact is strongest as supporting evidence for:

- AI Quality Analyst;
- AI Evaluator or Model Evaluation Analyst;
- Implementation Quality Analyst;
- Conversational AI QA;
- AI Operations Quality;
- Trust & Safety quality or policy-evaluation roles;
- public-sector or regulated-workflow AI quality roles.

It is adjacent evidence for Data Quality and Business Systems roles, but it is **not sufficient by itself** for software test-automation engineering, data-pipeline QA ownership, clinical validation, or regulated manufacturing quality.

## Limits

- The candidate responses are authored synthetic examples, not outputs from a deployed model.
- Phrase checks are intentionally simple and inspectable; they are not semantic evaluation.
- Human scores are example annotations by the project author, not calibrated production labels.
- The benchmark is intentionally compact; it demonstrates a framework, not production-scale coverage.
- The lab does not measure model drift, production latency, user impact, or real customer outcomes.
- A production program would add independent reviewers, adjudication, inter-rater reliability, approved source repositories, privacy controls, model/version metadata, regression history, and stakeholder-approved release thresholds.
