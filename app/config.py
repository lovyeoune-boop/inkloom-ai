import os
from pathlib import Path

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./brandguard.db")
SECRET_KEY = os.getenv("SECRET_KEY", "local-demo-secret-change-this")
ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 60 * 8
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "25"))
MODERATION_API_URL = os.getenv("MODERATION_API_URL", "").strip()
MODERATION_API_KEY = os.getenv("MODERATION_API_KEY", "")
MODERATION_TIMEOUT_SECONDS = float(os.getenv("MODERATION_TIMEOUT_SECONDS", "20"))
MANAGER_EMAIL = os.getenv("MANAGER_EMAIL", "").strip().lower()
MANAGER_PASSWORD = os.getenv("MANAGER_PASSWORD", "")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
