"""
Provider adapter for child-facing content review.

The local rules below are intentionally a demo baseline, not an AI safety guarantee.
Connect a vetted moderation provider in this module, preserve evidence, and always
send uncertain/high-risk results to a trained human reviewer.
"""
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import ValidationError

from ..config import MODERATION_API_KEY, MODERATION_API_URL, MODERATION_TIMEOUT_SECONDS
from .rule_engine import apply_age_policy, find_rule_matches
from ..schemas import ModerationResult


def moderate_text_demo(text: str, age_band: str) -> dict[str, Any]:
    findings = find_rule_matches(text, age_band)

    # Age-aware review reminder. This is not a validated age classifier.
    if age_band == "under_5":
        findings.append({
            "category": "Age suitability",
            "severity": "medium",
            "explanation": "For children under 5, check vocabulary, emotional intensity, pacing, and caregiver suitability.",
            "evidence": None,
            "recommendation": "Ask a qualified reviewer to confirm developmental suitability."
        })

    if not findings:
        return {
            "recommendation": "review_required",
            "risk_level": "unknown",
            "findings": [{
                "category": "Coverage limitation",
                "severity": "low",
                "explanation": "The demo rules found no configured keyword match; this does not prove the content is safe.",
                "evidence": None,
                "recommendation": "Complete human review before publication."
            }],
            "human_review_required": True
        }

    levels = [f["severity"] for f in findings]
    risk = (
        "critical" if "critical" in levels else
        "high" if "high" in levels else
        "medium" if "medium" in levels else
        "low"
    )
    return {
        "recommendation": "review_required",
        "risk_level": risk,
        "findings": findings,
        "human_review_required": True
    }


class ModerationProviderError(Exception):
    """Raised when a configured moderation provider cannot return a valid result."""


def moderate_text(text: str, age_band: str) -> dict[str, Any]:
    if not MODERATION_API_URL:
        return apply_age_policy(moderate_text_demo(text, age_band), age_band)

    request_body = {
        "task": "age_appropriate_text_moderation",
        "age_band": age_band,
        "content": text,
        "instructions": (
            "Assess this child-facing text for age suitability, sexual content, "
            "violence, self-harm, dangerous activities, exploitation, bullying, "
            "hateful content, and privacy or unsafe-contact risks. Consider context; "
            "do not infer risk from isolated words alone. Return JSON with "
            "recommendation (age_appropriate, not_recommended, or review_required), "
            "risk_level (low, medium, high, critical, or unknown), and findings "
            "(an array of objects with category, severity, explanation, evidence, "
            "and recommendation). Keep evidence brief and quote only relevant text."
        ),
    }
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if MODERATION_API_KEY:
        headers["Authorization"] = f"Bearer {MODERATION_API_KEY}"

    try:
        request = Request(
            MODERATION_API_URL,
            data=json.dumps(request_body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urlopen(request, timeout=MODERATION_TIMEOUT_SECONDS) as response:
            response_body = response.read(1_000_001)
        if len(response_body) > 1_000_000:
            raise ModerationProviderError("Provider response exceeded the 1 MB limit.")
        provider_result = json.loads(response_body)
        result = ModerationResult.model_validate(provider_result)
    except HTTPError as exc:
        raise ModerationProviderError(
            f"Provider returned HTTP status {exc.code}."
        ) from exc
    except (URLError, OSError, TimeoutError, ValueError) as exc:
        raise ModerationProviderError("Provider request failed or timed out.") from exc
    except (UnicodeDecodeError, json.JSONDecodeError, ValidationError, TypeError) as exc:
        raise ModerationProviderError(
            "Provider returned an invalid moderation response."
        ) from exc

    validated_result = result.model_dump()
    validated_result["human_review_required"] = True
    validated_result["findings"].extend(find_rule_matches(text, age_band))
    return apply_age_policy(validated_result, age_band)


def moderate_media_stub(file_path: str, content_type: str, age_band: str) -> dict[str, Any]:
    # Extension point: send file to approved, privacy-reviewed provider here.
    # Never mark a media upload safe merely because the adapter is not configured.
    return {
        "recommendation": "review_required",
        "risk_level": "unknown",
        "findings": [{
            "category": "Media analysis pending",
            "severity": "medium",
            "explanation": f"{content_type.title()} upload was received, but a vetted {content_type} moderation provider is not configured in this MVP.",
            "evidence": None,
            "recommendation": "Assign to a trained human reviewer and connect the appropriate modality-specific analysis service."
        }],
        "human_review_required": True
    }
