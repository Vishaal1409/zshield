import pytest


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    """Every test starts on the template provider with no provider env vars."""
    for k in ("GENAI_BASE_URL", "GENAI_MODEL", "GENAI_API_KEY", "GENAI_TIMEOUT_S", "GENAI_CURRENCY",
              "WATSONX_URL", "WATSONX_APIKEY", "WATSONX_PROJECT_ID", "WATSONX_MODEL_ID"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("GENAI_PROVIDER", "template")
