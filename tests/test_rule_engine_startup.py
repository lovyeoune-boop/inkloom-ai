import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.services import rule_engine


class RuleEngineStartupTests(unittest.TestCase):
    def test_empty_rule_book_is_skipped(self):
        with tempfile.TemporaryDirectory() as directory:
            rule_book_directory = Path(directory)
            (rule_book_directory / "empty.json").write_text("", encoding="utf-8")
            (rule_book_directory / "valid.json").write_text(
                json.dumps({"rules": []}), encoding="utf-8"
            )

            with patch.object(rule_engine, "RULE_BOOK_DIRECTORY", rule_book_directory):
                with self.assertLogs(rule_engine.logger, level="WARNING") as logs:
                    books = rule_engine._load_rule_books()

        self.assertEqual([book["name"] for book in books], ["valid"])
        self.assertIn("Skipping empty rule book", logs.output[0])


if __name__ == "__main__":
    unittest.main()
