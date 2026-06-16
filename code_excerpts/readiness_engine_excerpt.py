"""
Public-safe excerpt from the Plenara readiness engine.

This is not a standalone production module. It is a selected excerpt included to
show implementation style, rule evaluation logic, and readiness-state thinking.

Original private module context:
- Maps extracted cases into a canonical model
- Evaluates payer-style JSON rulesets
- Produces readiness states:
  - ready_for_submission
  - needs_review
  - blocked_missing_requirements

Safety:
- No PHI
- No real patient data
- No credentials
- No production clinical use
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple


RULESET_TO_CANONICAL_PATHS = {
    "clinical.disease_activity.moderate_to_severe": (
        "diagnosis.disease_activity.moderate_to_severe"
    ),
    "clinical.disease_activity.score": "diagnosis.disease_activity.score",
    "history.non_biologic_dmard.trial": "prior_failed_therapies.0",
    "history.non_biologic_dmard.trial.duration_months": (
        "prior_failed_therapies.0.duration_months"
    ),
    "history.non_biologic_dmard.trial.at_maximally_indicated_dose": (
        "prior_failed_therapies.0.at_maximally_indicated_dose"
    ),
    "provider.specialty_consulted": "provider.specialty_consulted",
}


def canonical_path_for_ruleset_path(ruleset_path: str) -> str:
    """Return the canonical model path for a ruleset field path."""
    return RULESET_TO_CANONICAL_PATHS.get(ruleset_path, ruleset_path)


def get_by_path(obj: Any, dot_path: str) -> Tuple[bool, Any]:
    """Return (found, value) from a nested dictionary using dot notation."""
    cur = obj
    for part in dot_path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return False, None
    return True, cur


def op_equals(actual: Any, expected: Any) -> bool:
    return actual == expected


def op_exists(found: bool, actual: Any, expected: Any) -> bool:
    want = bool(expected)
    has = found and actual is not None
    return has if want else (not has)


def op_gte(actual: Any, expected: Any) -> bool:
    try:
        return float(actual) >= float(expected)
    except Exception:
        return False


def op_in(actual: Any, expected_list: Any) -> bool:
    return isinstance(expected_list, list) and actual in expected_list


def op_contains_any(actual: Any, expected_list: Any) -> bool:
    if not isinstance(expected_list, list):
        return False
    if isinstance(actual, list):
        return any(a in expected_list for a in actual)
    if isinstance(actual, str):
        return actual in expected_list
    return False


@dataclass
class EvalResult:
    ok: bool
    missing_fields: set[str]
    unmet: list[str]
    critical_fields: set[str]


@dataclass
class ReadinessEvaluation:
    readiness: str
    passed_blockers: list[str]
    failed_blockers: list[str]
    missing_fields: set[str]
    unmet: list[str]


def eval_node(node: Any, payload: Any) -> EvalResult:
    """
    Evaluate a ruleset node against a structured payload.

    Supports nested require_all / require_any logic and leaf operators such as:
    equals, exists, greater_than_or_equal, in, and contains_any.
    """
    missing: set[str] = set()
    unmet: list[str] = []
    critical_fields: set[str] = set()

    if not isinstance(node, dict):
        return EvalResult(False, set(), ["Invalid logic node"], set())

    if "require_all" in node:
        children = node.get("require_all")
        if not isinstance(children, list):
            return EvalResult(False, set(), ["require_all must be an array"], set())

        all_ok = True
        for child in children:
            result = eval_node(child, payload)
            all_ok = all_ok and result.ok
            missing |= result.missing_fields
            unmet.extend(result.unmet)
            critical_fields |= result.critical_fields

        return EvalResult(all_ok, missing, unmet, critical_fields)

    if "require_any" in node:
        children = node.get("require_any")
        if not isinstance(children, list):
            return EvalResult(False, set(), ["require_any must be an array"], set())

        child_results = [eval_node(child, payload) for child in children]
        if any(result.ok for result in child_results):
            passed_fields: set[str] = set()
            for result in child_results:
                if result.ok:
                    passed_fields |= result.critical_fields
            return EvalResult(True, set(), [], passed_fields)

        for result in child_results:
            missing |= result.missing_fields
            unmet.extend(result.unmet)

        return EvalResult(False, missing, unmet, set())

    field = node.get("field")
    operator = node.get("operator")
    expected = node.get("value", None)

    if not isinstance(field, str) or not isinstance(operator, str):
        return EvalResult(False, set(), ["Leaf node missing field/operator"], set())

    found, actual = get_by_path(payload, field)

    passed = False
    if operator == "equals":
        passed = found and op_equals(actual, expected)
        if not found:
            missing.add(field)
    elif operator == "exists":
        passed = op_exists(found, actual, expected)
        if bool(expected) and (not found or actual is None):
            missing.add(field)
    elif operator == "greater_than_or_equal":
        passed = found and op_gte(actual, expected)
        if not found:
            missing.add(field)
    elif operator == "in":
        passed = found and op_in(actual, expected)
        if not found:
            missing.add(field)
    elif operator == "contains_any":
        passed = found and op_contains_any(actual, expected)
        if not found:
            missing.add(field)
    else:
        return EvalResult(
            False,
            set(),
            [f"Unsupported operator: {operator} (field: {field})"],
            set(),
        )

    if passed:
        return EvalResult(
            True,
            set(),
            [],
            {canonical_path_for_ruleset_path(field)},
        )

    unmet.append(f"{field} {operator} {expected!r} (actual={actual!r})")
    return EvalResult(False, missing, unmet, set())


def evaluate_ruleset(payload: dict[str, Any], ruleset: dict[str, Any]) -> ReadinessEvaluation:
    """Evaluate blockers and return a readiness summary."""
    blockers = ruleset.get("blockers", [])
    if not isinstance(blockers, list):
        raise ValueError("ruleset blockers is not an array")

    passed_blockers: list[str] = []
    failed_blockers: list[str] = []
    missing_fields: set[str] = set()
    unmet: list[str] = []

    for blocker in blockers:
        if not isinstance(blocker, dict):
            continue

        blocker_id = blocker.get("id", "<unknown>")
        logic = blocker.get("logic", {})
        result = eval_node(logic, payload)

        if result.ok:
            passed_blockers.append(blocker_id)
        else:
            failed_blockers.append(blocker_id)
            missing_fields |= result.missing_fields
            unmet.extend([f"{blocker_id}: {item}" for item in result.unmet])

    if failed_blockers:
        readiness = "blocked_missing_requirements"
    else:
        readiness = "ready_for_submission"

    return ReadinessEvaluation(
        readiness=readiness,
        passed_blockers=passed_blockers,
        failed_blockers=failed_blockers,
        missing_fields=missing_fields,
        unmet=unmet,
    )
