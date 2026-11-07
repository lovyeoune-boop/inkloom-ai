import json
import unittest
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse

from app.main import app
from app.routes.rule_book import get_rule_book, router


class RuleBookEndpointTests(unittest.TestCase):
    def test_rule_books_are_available_from_backend_api(self):
        response = get_rule_book("nation")

        self.assertTrue(any(
            getattr(route, "original_router", None) is router
            for route in app.routes
        ))
        self.assertEqual(router.routes[0].path, "/api/rule-book/{book_name}")
        self.assertIsInstance(response, FileResponse)
        self.assertEqual(response.media_type, "application/json")
        payload = json.loads(Path(response.path).read_text(encoding="utf-8"))
        self.assertEqual(len(payload["rules"]), 62)
        self.assertIn("age_labels", payload)

        words_response = get_rule_book("bad_words")
        words = json.loads(Path(words_response.path).read_text(encoding="utf-8"))
        self.assertEqual(len(words["rules"]), 400)
        self.assertEqual(len(words["risk_rules"][0]), 51)

    def test_rejects_unknown_rule_book(self):
        with self.assertRaises(HTTPException) as error:
            get_rule_book("../secrets")
        self.assertEqual(error.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
