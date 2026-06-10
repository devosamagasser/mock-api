from typing import Any

SUPPORTED_OPERATORS = {
    "equals", "not_equals", "exists", "missing", "contains", "greater_than", "less_than", "in", "not_in", "starts_with", "ends_with"
}


def get_value(context: dict[str, Any], dotted_path: str) -> tuple[bool, Any]:
    current: Any = context
    for part in dotted_path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return False, None
    return True, current


def compare(operator: str, actual: Any, expected: Any, exists: bool) -> bool:
    if operator == "exists":
        return exists
    if operator == "missing":
        return not exists
    if not exists:
        return False
    if operator == "equals":
        return actual == expected or str(actual) == str(expected)
    if operator == "not_equals":
        return not (actual == expected or str(actual) == str(expected))
    if operator == "contains":
        return str(expected) in str(actual) if not isinstance(actual, (list, tuple, set, dict)) else expected in actual
    if operator == "greater_than":
        return float(actual) > float(expected)
    if operator == "less_than":
        return float(actual) < float(expected)
    if operator == "in":
        return actual in expected if isinstance(expected, (list, tuple, set)) else str(actual) in str(expected)
    if operator == "not_in":
        return actual not in expected if isinstance(expected, (list, tuple, set)) else str(actual) not in str(expected)
    if operator == "starts_with":
        return str(actual).startswith(str(expected))
    if operator == "ends_with":
        return str(actual).endswith(str(expected))
    return False


def matches_conditions(condition_json: Any, context: dict[str, Any]) -> bool:
    if not condition_json:
        return True
    if not isinstance(condition_json, dict):
        return False
    for path, rule in condition_json.items():
        if not isinstance(rule, dict):
            return False
        operator = rule.get("operator", "equals")
        if operator not in SUPPORTED_OPERATORS:
            return False
        exists, actual = get_value(context, path)
        try:
            if not compare(operator, actual, rule.get("value"), exists):
                return False
        except (TypeError, ValueError):
            return False
    return True
