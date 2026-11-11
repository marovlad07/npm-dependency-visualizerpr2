"""Resolve common npm SemVer ranges using only the standard library."""

import re
from dataclasses import dataclass
from functools import total_ordering

from .errors import AppError

VERSION_RE = re.compile(
    r"v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
)


@total_ordering
@dataclass(frozen=True)
class Version:
    """Compare semantic versions, ignoring build metadata."""

    core: tuple
    pre: tuple = ()

    @classmethod
    def parse(cls, text):
        """Parse a complete version and reject invalid identifiers."""
        match = VERSION_RE.fullmatch(text)
        if not match:
            raise AppError(f"Некорректная SemVer-версия: {text}")
        pre = tuple((match[4] or "").split(".")) if match[4] else ()
        if any(x.isdigit() and len(x) > 1 and x[0] == "0" for x in pre):
            raise AppError(f"Нули в prerelease-идентификаторе: {text}")
        return cls(tuple(int(match[i]) for i in (1, 2, 3)), pre)

    def __lt__(self, other):
        """Apply SemVer ordering, including numeric prerelease parts."""
        if self.core != other.core:
            return self.core < other.core
        if not self.pre or not other.pre:
            return bool(self.pre) and not other.pre
        for left, right in zip(self.pre, other.pre):
            if left == right:
                continue
            if left.isdigit() and right.isdigit():
                return int(left) < int(right)
            if left.isdigit() != right.isdigit():
                return left.isdigit()
            return left < right
        return len(self.pre) < len(other.pre)


def partial(text):
    """Return a padded version and the count of specified components."""
    if VERSION_RE.fullmatch(text):
        return Version.parse(text), 3
    parts = text.removeprefix("v").split(".")
    if len(parts) > 3:
        raise AppError(f"Неподдерживаемый диапазон: {text}")
    numbers = []
    wildcard = False
    for part in parts:
        if part in ("x", "X", "*", ""):
            wildcard = True
        elif re.fullmatch(r"0|[1-9]\d*", part) and not wildcard:
            numbers.append(int(part))
        else:
            raise AppError(f"Неподдерживаемый диапазон: {text}")
    return Version(tuple(numbers + [0] * (3 - len(numbers)))), len(numbers)


def next_bound(version, precision):
    """Return the exclusive upper bound for a partial version."""
    core = list(version.core)
    index = max(0, precision - 1)
    core[index] += 1
    core[index + 1:] = [0] * (2 - index)
    return Version(tuple(core))


def expand(token):
    """Expand one npm comparator into primitive comparisons."""
    match = re.fullmatch(r"(\^|~|>=|<=|>|<|=)?(.+)", token)
    if not match:
        raise AppError(f"Некорректный диапазон: {token}")
    operator, text = match[1] or "=", match[2]
    version, count = partial(text)
    if not count:
        return [("<", Version((0, 0, 0)))] if operator in ("<", ">") else []
    if operator in ("^", "~"):
        precision = 1 if count == 1 else 2
        if operator == "^":
            nonzero = next((i + 1 for i, n in enumerate(version.core) if n), 3)
            precision = min(count, nonzero)
        return [(">=", version), ("<", next_bound(version, precision))]
    if count == 3:
        return [(operator, version)]
    if operator == "=":
        return [(">=", version), ("<", next_bound(version, count))]
    if operator == ">":
        return [(">=", next_bound(version, count))]
    if operator == "<=":
        return [("<", next_bound(version, count))]
    return [(operator, version)]


def comparator_set(text):
    """Parse an AND group, including inclusive hyphen ranges."""
    hyphen = re.fullmatch(r"(\S+)\s+-\s+(\S+)", text.strip())
    if hyphen:
        lower, _ = partial(hyphen[1])
        upper, count = partial(hyphen[2])
        result = [(">=", lower)]
        if count:
            result.append(("<=", upper) if count == 3 else (
                "<", next_bound(upper, count)
            ))
        return result
    normalized = re.sub(r"(>=|<=|>|<|=|\^|~)\s+", r"\1", text)
    return [item for token in normalized.split() for item in expand(token)]


def compare(version, operator, target):
    """Evaluate one comparison without dynamic code evaluation."""
    comparisons = {
        "=": version == target, ">": version > target,
        ">=": version >= target, "<": version < target,
        "<=": version <= target,
    }
    return comparisons[operator]


def satisfies(version, groups):
    """Accept a candidate only if an OR group and prerelease rule hold."""
    for group in groups:
        allowed = not version.pre or any(
            target.pre and target.core == version.core for _, target in group
        )
        if allowed and all(compare(version, op, target) for op, target in group):
            return True
    return False


def select_version(versions, specification, tags=None):
    """Choose the highest matching published version or an explicit tag."""
    tags = tags or {}
    specification = tags.get(specification, specification)
    if specification in versions:
        return specification
    groups = [comparator_set(x) for x in specification.split("||")]
    candidates = []
    for text in versions:
        try:
            version = Version.parse(text)
        except AppError:
            continue
        if satisfies(version, groups):
            candidates.append((version, text))
    if not candidates:
        raise AppError(f"Не найдена версия для диапазона {specification!r}")
    return max(candidates)[1]
