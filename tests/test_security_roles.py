import unittest
from types import SimpleNamespace

from fastapi import HTTPException

from app.models import User
from app.routes.reports import decide
from app.schemas import ReviewDecisionIn
from app.security import require_reviewer


class FakeQuery:
    def __init__(self, report):
        self.report = report

    def filter(self, _condition):
        return self

    def first(self):
        return self.report


class FakeDatabase:
    def __init__(self, report):
        self.report = report

    def query(self, _model):
        return FakeQuery(self.report)


class ReviewerRoleTests(unittest.TestCase):
    def test_manager_can_review_reports(self):
        manager = User(role="manager")

        self.assertIs(require_reviewer(manager), manager)

    def test_creator_cannot_review_reports(self):
        creator = User(role="creator")

        with self.assertRaises(HTTPException) as error:
            require_reviewer(creator)

        self.assertEqual(error.exception.status_code, 403)

    def test_media_report_cannot_be_approved_without_in_app_review(self):
        report = SimpleNamespace(content_type="video")
        db = FakeDatabase(report)

        with self.assertRaises(HTTPException) as error:
            decide(1, ReviewDecisionIn(action="approve"), db, User(role="manager"))

        self.assertEqual(error.exception.status_code, 409)


if __name__ == "__main__":
    unittest.main()
