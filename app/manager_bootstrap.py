import logging

from sqlalchemy.orm import Session

from .config import MANAGER_EMAIL, MANAGER_PASSWORD
from .database import SessionLocal
from .models import User
from .security import hash_password

logger = logging.getLogger(__name__)


def create_manager_account(db: Session, email: str, password: str) -> bool:
    normalized_email = email.strip().lower()
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        if existing_user.role != "manager":
            raise RuntimeError(
                f"Configured manager email {normalized_email!r} belongs to a "
                f"{existing_user.role!r} account; no role or password was changed."
            )
        return False

    user = User(
        email=normalized_email,
        password_hash=hash_password(password),
        role="manager",
    )
    db.add(user)
    db.commit()
    return True


def bootstrap_manager() -> None:
    if not MANAGER_EMAIL and not MANAGER_PASSWORD:
        return
    if not MANAGER_EMAIL or not MANAGER_PASSWORD:
        raise RuntimeError(
            "Set both MANAGER_EMAIL and MANAGER_PASSWORD to enable manager account bootstrap."
        )
    if len(MANAGER_PASSWORD) < 12:
        raise RuntimeError("MANAGER_PASSWORD must be at least 12 characters.")
    if len(MANAGER_PASSWORD.encode("utf-8")) > 72:
        raise RuntimeError("MANAGER_PASSWORD must be no more than 72 UTF-8 bytes.")

    db = SessionLocal()
    try:
        created = create_manager_account(db, MANAGER_EMAIL, MANAGER_PASSWORD)
        if created:
            logger.info("Bootstrapped manager account for %s", MANAGER_EMAIL)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
