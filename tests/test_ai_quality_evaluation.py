from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "ai_quality_evaluation" / "evaluate.py"
spec = importlib.util.spec_from_file_location("quality_eval", MODULE_PATH)
quality_eval = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(quality_eval)


def test_expected_record_counts():
    rows = quality_eval.evaluate()
    assert len(rows) == 10
    assert len({row["case_id"] for row in rows}) == 5


def test_acceptable_variants_pass_with_complete_coverage():
    rows = quality_eval.evaluate()
    acceptable = [row for row in rows if row["variant"] == "acceptable"]
    assert all(row["decision"] == "PASS" for row in acceptable)
    assert all(row["defect_types"] == "none" for row in acceptable)
    assert all(len(set(row["required_fact_coverage"].split("/"))) == 1 for row in acceptable)


def test_flawed_variants_fail():
    rows = quality_eval.evaluate()
    assert all(row["decision"] == "FAIL" for row in rows if row["variant"] == "flawed")


def test_critical_case_requires_escalation():
    rows = quality_eval.evaluate()
    good = next(row for row in rows if row["output_id"] == "CITY-EMR-004-A")
    bad = next(row for row in rows if row["output_id"] == "CITY-EMR-004-B")
    assert good["escalation_ok"] is True
    assert bad["escalation_ok"] is False


def test_source_conflict_requires_human_confirmation():
    rows = quality_eval.evaluate()
    good = next(row for row in rows if row["output_id"] == "CITY-SRC-005-A")
    bad = next(row for row in rows if row["output_id"] == "CITY-SRC-005-B")
    assert good["human_review_ok"] is True
    assert bad["human_review_ok"] is False
    assert "unsupported_or_forbidden_claim" in bad["defect_types"]


def test_rubric_threshold_controls_decision(tmp_path):
    rubric = quality_eval.load_rubric()
    rubric["release_guidance"]["minimum_average_score"] = 5.1
    rubric_path = tmp_path / "rubric.yaml"
    rubric_path.write_text(__import__("yaml").safe_dump(rubric), encoding="utf-8")
    rows = quality_eval.evaluate(rubric_path=rubric_path)
    assert all(row["decision"] == "FAIL" for row in rows)


def test_checked_in_outputs_are_reproducible(tmp_path):
    rows = quality_eval.evaluate()
    quality_eval.write_outputs(rows, output_dir=tmp_path)
    assert (tmp_path / "evaluation_results.csv").read_bytes() == (ROOT / "ai_quality_evaluation" / "evaluation_results.csv").read_bytes()
    assert (tmp_path / "quality_report.md").read_bytes() == (ROOT / "ai_quality_evaluation" / "quality_report.md").read_bytes()
