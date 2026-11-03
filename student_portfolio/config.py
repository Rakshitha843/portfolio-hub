"""Central configuration. Values come from environment variables (a .env file is loaded too)."""
import os
import secrets

from dotenv import load_dotenv

load_dotenv()


def _flag(name, default=False):
    fallback = "1" if default else "0"
    return os.getenv(name, fallback).strip().lower() in {"1", "true", "yes", "on"}


# --- Redis -------------------------------------------------------------------------
# Local Docker:  redis://localhost:6379/0
# Redis Cloud:   rediss://default:<password>@<host>:<port>
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
STUDENT_INDEX = "idx:students"

# --- Security ----------------------------------------------------------------------
_secret = os.getenv("SECRET_KEY", "").strip()
SECRET_KEY_IS_RANDOM = not _secret
SECRET_KEY = _secret or secrets.token_hex(32)  # random per start-up if not configured
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "8"))
COOKIE_NAME = "portfolio_token"
COOKIE_SECURE = _flag("COOKIE_SECURE", False)  # set to 1 when served over HTTPS

# --- Admin account + demo data -----------------------------------------------------
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@college.edu").strip().lower()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@123")
AUTO_SEED = _flag("AUTO_SEED", True)
DEMO_STUDENT_PASSWORD = "Student@123"

# --- Domain constants --------------------------------------------------------------
DEPARTMENTS = [
    "CSE", "ISE", "AIML", "Data Science", "ECE", "EEE", "Mechanical", "Civil", "Other",
]
YEARS = [1, 2, 3, 4]

MAX_UPLOAD_BYTES = 3 * 1024 * 1024   # hard cap on any request body
MAX_PHOTO_BYTES = 2 * 1024 * 1024    # profile photo cap
PHOTO_SIZE = 400                     # photos are resized to 400 x 400 JPEG
