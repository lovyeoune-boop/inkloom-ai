import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.manager_bootstrap import create_manager_account
from app.models import User
from app.security import verify_password


class ManagerBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.session = sessionmaker(bind=self.engine)()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def test_creates_manager_with_hashed_password(self):
        created = create_manager_account(
            self.session, "Manager@Example.com", "a-strong-test-password"
        )
        user = self.session.query(User).filter_by(email="manager@example.com").one()

        self.assertTrue(created)
        self.assertEqual(user.role, "manager")
        self.assertNotEqual(user.password_hash, "a-strong-test-password")
        self.assertTrue(verify_password("a-strong-test-password", user.password_hash))

    def test_existing_manager_is_not_reset(self):
        user = User(
            email="manager@example.com",
            password_hash="existing-hash",
            role="manager",
        )
        self.session.add(user)
        self.session.commit()

        created = create_manager_account(
            self.session, "manager@example.com", "a-new-password"
        )

        self.assertFalse(created)
        self.assertEqual(user.password_hash, "existing-hash")

    def test_existing_non_manager_is_not_promoted(self):
        creator = User(
            email="creator@example.com",
            password_hash="existing-hash",
            role="creator",
        )
        self.session.add(creator)
        self.session.commit()

        with self.assertRaises(RuntimeError):
            create_manager_account(
                self.session, "creator@example.com", "a-strong-test-password"
            )

        self.assertEqual(creator.role, "creator")


if __name__ == "__main__":
    unittest.main()
