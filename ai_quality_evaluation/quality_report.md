# AI Quality Evaluation Report

> Synthetic portfolio evaluation only. All agencies, policies, prompts, source passages, and responses are fictional.

## Executive summary

- **Cases:** 4
- **Candidate responses:** 8
- **Passed:** 4
- **Failed:** 4
- **Overall pass rate:** 50%
- **Acceptable-variant pass rate:** 100%
- **Intentionally flawed-variant fail rate:** 100%

The transparent checks and example human annotations separate acceptable responses from intentionally flawed responses. This demonstrates evaluation design and reproducibility; it is not a claim of production model performance.

## Defect themes

- **omission:** 4
- **unsupported or forbidden claim:** 4
- **missing human review:** 2
- **missing emergency escalation:** 1

## Release logic

A response fails when it contains a forbidden claim, misses required emergency escalation or human-review language, or receives an average human score below 4.0. Automated checks support review; a human reviewer owns the final decision.

## Coverage

The prompt bank spans low-, medium-, high-, and critical-risk fictional public-service interactions: parking, records, benefits screening, and emergency communication.

## Limitations

- Candidate responses are authored synthetic examples, not sampled from a deployed model.
- Keyword checks are intentionally simple and inspectable; they are not semantic evaluation.
- Human annotations are example labels from the project author, not calibrated production judgments.
- No inter-rater reliability, drift monitoring, model/version comparison, privacy review, or customer outcome measurement is claimed.
- Production use would require independent reviewers, adjudication, approved sources, privacy controls, regression history, and stakeholder-approved thresholds.

## Reproduce

```bash
python ai_quality_evaluation/evaluate.py
python -m pytest tests/test_ai_quality_evaluation.py -q
```

Detailed row-level results are in [`evaluation_results.csv`](evaluation_results.csv).
