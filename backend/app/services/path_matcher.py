import re
from dataclasses import dataclass

_PARAM_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


@dataclass(frozen=True)
class PathMatch:
    matched: bool
    params: dict[str, str]


def normalize_path(path: str) -> str:
    path = (path or "").strip()
    if not path:
        return "/"
    if not path.startswith("/"):
        path = f"/{path}"
    return path.rstrip("/") or "/"


def pattern_to_regex(pattern: str) -> re.Pattern[str]:
    normalized = normalize_path(pattern)
    cursor = 0
    regex = "^"
    for match in _PARAM_RE.finditer(normalized):
        regex += re.escape(normalized[cursor:match.start()])
        regex += f"(?P<{match.group(1)}>[^/]+)"
        cursor = match.end()
    regex += re.escape(normalized[cursor:])
    regex += "$"
    return re.compile(regex)


def match_path(pattern: str, actual_path: str) -> PathMatch:
    compiled = pattern_to_regex(pattern)
    match = compiled.match(normalize_path(actual_path))
    if not match:
        return PathMatch(False, {})
    return PathMatch(True, match.groupdict())
