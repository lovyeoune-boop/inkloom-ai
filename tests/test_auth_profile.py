import unittest

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import User
from app.routes.auth import change_password, update_profile
from app.schemas import PasswordChangeIn, ProfileUpdateIn
from app.security import hash_password, verify_password


class AuthProfileTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.user = User(
            email="user@example.com",
            password_hash=hash_password("current-password"),
            role="creator",
        )
        self.session.add(self.user)
        self.session.add(User(
            email="taken@example.com",
            password_hash=hash_password("another-password"),
            role="manager",
        ))
        self.session.commit()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def test_profile_email_updates_without_changing_role(self):
        result = update_profile(
            ProfileUpdateIn(email="Updated@Example.com"),
            self.session,
            self.user,
        )

        self.assertEqual(result["email"], "updated@example.com")
        self.assertEqual(result["role"], "creator")

    def test_profile_rejects_email_used_by_another_account(self):
        with self.assertRaises(HTTPException) as error:
            update_profile(
                ProfileUpdateIn(email="taken@example.com"),
                self.session,
                self.user,
            )

        self.assertEqual(error.exception.status_code, 409)

    def test_password_change_requires_current_password(self):
        with self.assertRaises(HTTPException) as error:
            change_password(
                PasswordChangeIn(
                    current_password="incorrect-password",
                    new_password="new-password",
                ),
                self.session,
                self.user,
            )

        self.assertEqual(error.exception.status_code, 400)
        self.assertTrue(verify_password("current-password", self.user.password_hash))

    def test_password_change_hashes_new_password(self):
        change_password(
            PasswordChangeIn(
                current_password="current-password",
                new_password="new-password",
            ),
            self.session,
            self.user,
        )

        self.assertTrue(verify_password("new-password", self.user.password_hash))
        self.assertFalse(verify_password("current-password", self.user.password_hash))


if __name__ == "__main__":
    unittest.main()
