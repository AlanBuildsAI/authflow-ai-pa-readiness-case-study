from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent
BENCHMARK = ROOT / "data" / "benchmark.json"
RUBRIC = ROOT / "evaluation_rubric.yaml"
DIMENSIONS = ("correctness", "completeness", "groundedness", "safety", "actionability")


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not payload.get("cases"):
        raise ValueError("Benchmark contains no cases.")
    return payload


def load_rubric(path: Path = RUBRIC) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    missing = [dimension for dimension in DIMENSIONS if dimension not in payload.get("dimensions", {})]
    if missing:
        raise ValueError(f"Rubric is missing dimensions: {missing}")
    return payload


def phrase_hits(text: str, phrases: list[str]) -> list[str]:
    normalized = text.casefold()
    return [phrase for phrase in phrases if phrase.casefold() in normalized]


def all_phrases_present(text: str, phrases: list[str]) -> bool:
    return len(phrase_hits(text, phrases)) == len(phrases)


def evaluate(benchmark_path: Path = BENCHMARK, rubric_path: Path = RUBRIC) -> list[dict[str, Any]]:
    benchmark = load_json(benchmark_path)
    rubric = load_rubric(rubric_path)
    threshold = float(rubric["release_guidance"]["minimum_average_score"])
    results: list[dict[str, Any]] = []
    seen_output_ids: set[str] = set()

    for case in benchmark["cases"]:
        required = case.get("required_facts", [])
        forbidden = case.get("forbidden_claims", [])
        escalation_phrases = case.get("required_escalation_phrases", [])
        human_review_phrases = case.get("required_human_review_phrases", [])

        for output in case["outputs"]:
            output_id = output["output_id"]
            if output_id in seen_output_ids:
                raise ValueError(f"Duplicate output_id: {output_id}")
            seen_output_ids.add(output_id)

            response = output["response"]
            required_hits = phrase_hits(response, required)
            forbidden_hits = phrase_hits(response, forbidden)
            escalation_ok = all_phrases_present(response, escalation_phrases)
            human_review_ok = all_phrases_present(response, human_review_phrases)

            scores = output["scores"]
            missing_scores = [dimension for dimension in DIMENSIONS if dimension not in scores]
            if missing_scores:
                raise ValueError(f"Missing scores for {output_id}: {missing_scores}")
            out_of_range = [dimension for dimension in DIMENSIONS if not 1 <= float(scores[dimension]) <= 5]
            if out_of_range:
                raise ValueError(f"Scores outside 1-5 for {output_id}: {out_of_range}")
            average_score = round(sum(float(scores[d]) for d in DIMENSIONS) / len(DIMENSIONS), 2)

            defect_types: list[str] = []
            if forbidden_hits:
                defect_types.append("unsupported_or_forbidden_claim")
            if len(required_hits) < len(required):
                defect_types.append("omission")
            if not escalation_ok:
                defect_types.append("missing_emergency_escalation")
            if not human_review_ok:
                defect_types.append("missing_human_review")

            automatic_failure = bool(forbidden_hits) or not escalation_ok or not human_review_ok
            decision = "FAIL" if automatic_failure or average_score < threshold else "PASS"

            results.append({
                "output_id": output_id,
                "case_id": case["case_id"],
                "variant": output["variant"],
                "risk_level": case["risk_level"],
                "required_fact_coverage": f"{len(required_hits)}/{len(required)}",
                "forbidden_claim_count": len(forbidden_hits),
                "human_review_ok": human_review_ok,
                "escalation_ok": escalation_ok,
                **{dimension: float(scores[dimension]) for dimension in DIMENSIONS},
                "average_score": average_score,
                "decision": decision,
                "defect_types": ";".join(defect_types) if defect_types else "none",
                "reviewer_rationale": output["rationale"],
            })
    return results


def render_csv(results: list[dict[str, Any]]) -> str:
    from io import StringIO
    buffer = StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(results[0].keys()), lineterminator="\n")
    writer.writeheader()
    writer.writerows(results)
    return buffer.getvalue()


def render_report(results: list[dict[str, Any]]) -> str:
    passed = sum(row["decision"] == "PASS" for row in results)
    acceptable = [row for row in results if row["variant"] == "acceptable"]
    flawed = [row for row in results if row["variant"] == "flawed"]
    defects: Counter[str] = Counter()
    for row in results:
        if row["defect_types"] != "none":
            defects.update(row["defect_types"].split(";"))
    defect_lines = "\n".join(f"- **{name.replace('_', ' ')}:** {count}" for name, count in defects.most_common()) or "- None"
    return f"""# AI Quality Evaluation Report

> Synthetic portfolio evaluation only. All agencies, policies, prompts, source passages, and responses are fictional.

## Executive summary

- **Cases:** {len({row['case_id'] for row in results})}
- **Candidate responses:** {len(results)}
- **Passed:** {passed}
- **Failed:** {len(results) - passed}
- **Overall pass rate:** {passed / len(results):.0%}
- **Acceptable-variant pass rate:** {sum(row['decision'] == 'PASS' for row in acceptable) / len(acceptable):.0%}
- **Intentionally flawed-variant fail rate:** {sum(row['decision'] == 'FAIL' for row in flawed) / len(flawed):.0%}

The transparent checks and example human annotations separate acceptable responses from intentionally flawed responses. This demonstrates evaluation design and reproducibility; it is not a claim of production model performance.

## Defect themes

{defect_lines}

## Release logic

A response fails when it contains a listed forbidden claim, misses required escalation or human-review language, or receives an average human score below the threshold in `evaluation_rubric.yaml`. Automated checks support review; a human reviewer owns the final decision.

## Coverage

The prompt bank spans low-, medium-, high-, and critical-risk fictional interactions, including conflicting-source handling.

## Limitations

- Candidate responses are authored synthetic examples, not sampled from a deployed model.
- Phrase checks are intentionally simple and inspectable; they are not semantic evaluation.
- Human annotations are example labels from the project author, not calibrated production judgments.
- No inter-rater reliability, drift monitoring, model/version comparison, privacy review, or customer outcome measurement is claimed.
- Production use would require independent reviewers, adjudication, approved sources, privacy controls, regression history, and stakeholder-approved thresholds.

## Reproduce

```bash
python ai_quality_evaluation/evaluate.py
python -m pytest tests/test_ai_quality_evaluation.py -q
```

Detailed row-level results are in [`evaluation_results.csv`](evaluation_results.csv).
"""


def write_outputs(results: list[dict[str, Any]], output_dir: Path = ROOT) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "evaluation_results.csv").write_text(render_csv(results), encoding="utf-8")
    (output_dir / "quality_report.md").write_text(render_report(results), encoding="utf-8")


if __name__ == "__main__":
    rows = evaluate()
    write_outputs(rows)
    print(f"Wrote {len(rows)} evaluation rows.")
