import json
import unittest
from io import BytesIO
from unittest.mock import patch
from urllib.error import URLError

from app.services import rule_engine
from app.services.rule_engine import AGE_POLICY, apply_age_policy
from app.services import moderation


class TextModerationTests(unittest.TestCase):
    def test_age_policy_matches_requested_matrix(self):
        self.assertEqual(AGE_POLICY, {
            "low": {
                "under_5": "block",
                "5_8": "review",
                "9_12": "allow",
                "13_17": "allow",
            },
            "medium": {
                "under_5": "block",
                "5_8": "block",
                "9_12": "review",
                "13_17": "review",
            },
            "high": {
                "under_5": "block",
                "5_8": "block",
                "9_12": "block",
                "13_17": "block",
            },
        })

    def test_policy_actions_determine_recommendation(self):
        finding = {
            "category": "Inappropriate language",
            "severity": "low",
            "explanation": "Rule match.",
            "evidence": "idiot",
            "recommendation": "Review this wording.",
        }

        blocked = apply_age_policy(
            {"recommendation": "review_required", "findings": [finding.copy()]},
            "under_5",
        )
        allowed = apply_age_policy(
            {"recommendation": "not_recommended", "findings": [finding.copy()]},
            "9_12",
        )

        self.assertEqual(blocked["recommendation"], "not_recommended")
        self.assertEqual(blocked["findings"][0]["policy_action"], "block")
        self.assertEqual(allowed["recommendation"], "age_appropriate")
        self.assertEqual(allowed["findings"][0]["policy_action"], "allow")

    def test_medium_severity_requires_review_for_older_age_bands(self):
        finding = {
            "category": "Inappropriate language",
            "severity": "medium",
            "explanation": "Rule match.",
            "evidence": "worthless",
            "recommendation": "Review this wording.",
        }
        result = apply_age_policy(
            {"recommendation": "age_appropriate", "findings": [finding]},
            "13_17",
        )

        self.assertEqual(result["recommendation"], "review_required")
        self.assertEqual(result["findings"][0]["policy_action"], "review")

    def test_critical_severity_uses_conservative_high_policy(self):
        finding = {
            "category": "Risk",
            "severity": "critical",
            "explanation": "High risk.",
            "evidence": None,
            "recommendation": "Escalate.",
        }
        result = apply_age_policy(
            {"recommendation": "review_required", "findings": [finding]},
            "13_17",
        )

        self.assertEqual(result["recommendation"], "not_recommended")
        self.assertEqual(result["findings"][0]["policy_action"], "block")

    def test_uses_demo_rules_when_no_provider_is_configured(self):
        with patch.object(moderation, "MODERATION_API_URL", ""):
            result = moderation.moderate_text("A friendly story.", "9_12")

        self.assertEqual(result["recommendation"], "review_required")
        self.assertTrue(result["human_review_required"])
        self.assertEqual(result["findings"][0]["category"], "Coverage limitation")

    def test_bad_word_rules_match_terms_without_matching_substrings(self):
        with patch.object(moderation, "MODERATION_API_URL", ""):
            result = moderation.moderate_text(
                "That worthless person is here, but worthlessness is a different word.", "9_12"
            )

        flagged = [
            finding for finding in result["findings"]
            if finding["category"] == "Inappropriate language"
        ]
        self.assertEqual(len(flagged), 1)
        self.assertEqual(flagged[0]["severity"], "medium")
        self.assertEqual(flagged[0]["policy_action"], "review")
        self.assertIn("worthless", flagged[0]["evidence"].lower())

    def test_json_risk_patterns_are_integrated(self):
        with patch.object(moderation, "MODERATION_API_URL", ""):
            result = moderation.moderate_text(
                "The bully says everyone hates you.", "9_12"
            )

        finding = next(
            finding for finding in result["findings"]
            if finding["category"] == "bullying"
        )
        self.assertEqual(finding["severity"], "medium")
        self.assertEqual(finding["policy_action"], "review")

    def test_rule_books_load_phrase_and_nested_pattern_rules(self):
        expected_books = {
            "bad_words",
            "Cyberbullying",
            "Insulting",
            "nation",
            "Online_Scams",
            "Sexual_con",
            "Sexual_Harass",
            "Threats",
        }
        self.assertEqual({book["name"] for book in rule_engine.RULE_BOOKS}, expected_books)
        loaded_books = {book["name"]: book for book in rule_engine.RULE_BOOKS}
        self.assertEqual(
            len(list(rule_engine._iter_rules(loaded_books["Insulting"]["risk_rules"]))),
            15,
        )
        self.assertEqual(
            len(list(rule_engine._iter_rules(loaded_books["Sexual_Harass"]["risk_rules"]))),
            50,
        )

        findings = rule_engine.find_rule_matches(
            "Someone sent unwanted sexual advances.", "9_12"
        )
        self.assertTrue(any(finding["category"] == "sexual_harassment" for finding in findings))

    def test_bad_word_rules_match_kannada_and_hindi(self):
        unicode_rules = [
            {"id": "TEST001", "term": "ಮೂರ್ಖ", "language": "kn", "severity": "LOW", "match_type": "exact", "enabled": True},
            {"id": "TEST002", "term": "मूर्ख", "language": "hi", "severity": "LOW", "match_type": "exact", "enabled": True},
        ]
        with (
            patch.object(moderation, "MODERATION_API_URL", ""),
            patch.object(rule_engine, "RULE_BOOKS", [{
                "name": "test",
                "finding_category": "Inappropriate language",
                "match_context": "Rule {id} detected configured {language} {match_type} language that may be unsuitable for {age_label}.",
                "match_recommendation": "Review this wording in context.",
                "rules": unicode_rules,
                "risk_rules": [],
            }]),
        ):
            kn_result = moderation.moderate_text("ನೀನು ಮೂರ್ಖ", "9_12")
            hi_result = moderation.moderate_text("तुम मूर्ख हो", "9_12")

        for result in (kn_result, hi_result):
            self.assertTrue(any(
                finding["category"] == "Inappropriate language"
                for finding in result["findings"]
            ))

    def test_nation_rule_is_integrated_and_uses_its_category_and_age_policy(self):
        with patch.object(moderation, "MODERATION_API_URL", ""):
            result = moderation.moderate_text(
                "Promote hatred between communities.", "9_12"
            )

        finding = next(
            finding for finding in result["findings"]
            if finding["category"] == "Social Harmony"
        )
        self.assertEqual(finding["severity"], "high")
        self.assertEqual(finding["policy_action"], "block")
        self.assertEqual(result["recommendation"], "not_recommended")

    def test_nation_phrase_rule_does_not_match_unrelated_substrings(self):
        with patch.object(moderation, "MODERATION_API_URL", ""):
            result = moderation.moderate_text(
                "This lesson discusses harmony between communities.", "9_12"
            )

        self.assertFalse(any(
            finding["category"] == "Social Harmony"
            for finding in result["findings"]
        ))

    def test_validates_provider_result_and_requires_human_review(self):
        response = {
            "recommendation": "age_appropriate",
            "risk_level": "low",
            "findings": [],
            "human_review_required": False,
        }
        with (
            patch.object(moderation, "MODERATION_API_URL", "https://moderator.example/review"),
            patch.object(moderation, "MODERATION_API_KEY", "test-key"),
            patch.object(moderation, "urlopen", return_value=BytesIO(json.dumps(response).encode())) as open_url,
        ):
            result = moderation.moderate_text("A friendly story.", "9_12")

        request = open_url.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key")
        self.assertEqual(json.loads(request.data)["age_band"], "9_12")
        self.assertEqual(result["recommendation"], "age_appropriate")
        self.assertTrue(result["human_review_required"])

    def test_local_nation_rule_also_runs_when_provider_is_configured(self):
        response = {
            "recommendation": "age_appropriate",
            "risk_level": "low",
            "findings": [],
            "human_review_required": False,
        }
        with (
            patch.object(moderation, "MODERATION_API_URL", "https://moderator.example/review"),
            patch.object(moderation, "urlopen", return_value=BytesIO(json.dumps(response).encode())),
        ):
            result = moderation.moderate_text(
                "Promote hatred between communities.", "9_12"
            )

        self.assertEqual(result["risk_level"], "high")
        self.assertEqual(result["recommendation"], "not_recommended")
        self.assertTrue(any(
            finding["category"] == "Social Harmony"
            for finding in result["findings"]
        ))

    def test_rejects_malformed_provider_results(self):
        with (
            patch.object(moderation, "MODERATION_API_URL", "https://moderator.example/review"),
            patch.object(moderation, "urlopen", return_value=BytesIO(b'{"recommendation":"safe"}')),
        ):
            with self.assertRaises(moderation.ModerationProviderError):
                moderation.moderate_text("A friendly story.", "9_12")

    def test_does_not_fall_back_when_configured_provider_fails(self):
        with (
            patch.object(moderation, "MODERATION_API_URL", "https://moderator.example/review"),
            patch.object(moderation, "urlopen", side_effect=URLError("offline")),
        ):
            with self.assertRaises(moderation.ModerationProviderError):
                moderation.moderate_text("A friendly story.", "9_12")


if __name__ == "__main__":
    unittest.main()
