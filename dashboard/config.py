"""Single API URL setting; change this value for IBM Z."""
import os
API_BASE_URL = os.getenv("ZSHIELD_API_URL", "http://127.0.0.1:8000").rstrip("/")
