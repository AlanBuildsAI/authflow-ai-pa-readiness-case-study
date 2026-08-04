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
    assert len(rows) == 8
    assert len({row["case_id"] for row in rows}) == 4


def test_acceptable_variants_pass():
    rows = quality_eval.evaluate()
    assert all(row["decision"] == "PASS" for row in rows if row["variant"] == "acceptable")


def test_flawed_variants_fail():
    rows = quality_eval.evaluate()
    assert all(row["decision"] == "FAIL" for row in rows if row["variant"] == "flawed")


def test_critical_case_requires_escalation():
    rows = quality_eval.evaluate()
    good = next(row for row in rows if row["output_id"] == "CITY-EMR-004-A")
    bad = next(row for row in rows if row["output_id"] == "CITY-EMR-004-B")
    assert good["escalation_ok"] is True
    assert bad["escalation_ok"] is False


def test_outputs_are_reproducible(tmp_path):
    rows = quality_eval.evaluate()
    quality_eval.write_outputs(rows, output_dir=tmp_path)
    assert (tmp_path / "evaluation_results.csv").exists()
    report = (tmp_path / "quality_report.md").read_text(encoding="utf-8")
    assert "**Overall pass rate:** 50%" in report
    assert "not a claim of production model performance" in report
