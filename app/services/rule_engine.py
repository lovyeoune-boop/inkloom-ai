import json
import logging
import re
from pathlib import Path
from typing import Any, Iterator


RULE_BOOK_DIRECTORY = Path(__file__).resolve().parents[1] / "rule_book"
logger = logging.getLogger(__name__)
_AGE_POLICY_BOOK = json.loads(
    (RULE_BOOK_DIRECTORY / "age_policy.json").read_text(encoding="utf-8")
)
AGE_LABELS = _AGE_POLICY_BOOK["age_labels"]
AGE_POLICY = _AGE_POLICY_BOOK["age_policy"]
_SEVERITY_POLICY_LEVELS = _AGE_POLICY_BOOK["severity_policy_levels"]


def _load_rule_books() -> list[dict[str, Any]]:
    rule_books = []
    for path in sorted(RULE_BOOK_DIRECTORY.glob("*.json")):
        if path.stem == "age_policy":
            continue
        contents = path.read_text(encoding="utf-8")
        if not contents.strip():
            logger.warning("Skipping empty rule book: %s", path)
            continue
        book = json.loads(contents)
        if not isinstance(book, dict):
            raise ValueError(f"Rule book {path.name} must contain a JSON object.")
        if "rules" in book or "risk_rules" in book:
            rule_books.append({"name": path.stem, **book})
    return rule_books


RULE_BOOKS = _load_rule_books()


def _iter_rules(rules: Any) -> Iterator[dict[str, Any]]:
    if isinstance(rules, dict):
        yield rules
    elif isinstance(rules, list):
        for rule in rules:
            yield from _iter_rules(rule)


def find_rule_matches(text: str, age_band: str) -> list[dict[str, Any]]:
    findings = []

    for book in RULE_BOOKS:
        for rule in _iter_rules(book.get("rules", [])):
            if not rule.get("enabled", True):
                continue
            term = rule.get("term")
            if not isinstance(term, str) or not term:
                continue
            pattern = rf"(?<!\w){re.escape(term)}(?!\w)"
            age_label = AGE_LABELS[age_band]
            for match in re.finditer(pattern, text, re.IGNORECASE):
                category = book.get("finding_category") or rule["category"].replace(
                    "_", " "
                ).title()
                findings.append({
                    "category": category,
                    "severity": rule["severity"].lower(),
                    "explanation": book.get(
                        "match_context",
                        "Rule {id} detected a configured phrase for {age_label}.",
                    ).format(
                        id=rule["id"],
                        language=rule.get("language", ""),
                        match_type=rule.get("match_type", ""),
                        age_label=age_label,
                    ),
                    "evidence": text[
                        max(0, match.start() - 45):min(len(text), match.end() + 45)
                    ],
                    "recommendation": book.get(
                        "match_recommendation",
                        "Review this phrase in context; educational or reporting uses may need different treatment.",
                    ),
                })

        for rule in _iter_rules(book.get("risk_rules", [])):
            if not rule.get("enabled", True):
                continue
            pattern = rule.get("pattern")
            if not isinstance(pattern, str) or not pattern:
                continue
            for match in re.finditer(pattern, text, re.IGNORECASE):
                findings.append({
                    "category": rule.get("category", " ".join(book["name"].split("_")).title()),
                    "severity": rule["severity"].lower(),
                    "explanation": book.get(
                        "risk_context",
                        "Rule-based demo detected a phrase that may need context review for {age_label}.",
                    ).format(age_label=AGE_LABELS[age_band]),
                    "evidence": text[
                        max(0, match.start() - 45):min(len(text), match.end() + 45)
                    ],
                    "recommendation": rule.get(
                        "recommendation",
                        book.get(
                            "match_recommendation",
                            "Review this match in context with a qualified human reviewer.",
                        ),
                    ),
                })

    return findings


def apply_age_policy(result: dict[str, Any], age_band: str) -> dict[str, Any]:
    actions = []
    severity_rank = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    finding_severities = []
    for finding in result["findings"]:
        severity = finding["severity"].lower()
        if severity in severity_rank:
            finding_severities.append(severity)
        policy_level = _SEVERITY_POLICY_LEVELS.get(severity, severity)
        if finding["category"] == "Coverage limitation":
            action = "review"
        else:
            try:
                action = AGE_POLICY[policy_level][age_band]
            except KeyError as exc:
                raise ValueError(
                    f"No age policy configured for severity {severity!r} and age band {age_band!r}."
                ) from exc
        finding["policy_action"] = action
        actions.append(action)

    if finding_severities:
        result["risk_level"] = max(finding_severities, key=severity_rank.__getitem__)

    if "block" in actions:
        result["recommendation"] = "not_recommended"
    elif "review" in actions:
        result["recommendation"] = "review_required"
    elif actions:
        result["recommendation"] = "age_appropriate"

    return result
