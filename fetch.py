import os
from session import _session as SESSION

URL = "https://9uc4obe1q1.execute-api.us-east-2.amazonaws.com/dev/emails"

def fetch_emails() -> list[dict]:
    params = {"api_key": os.getenv("EMAIL_API_KEY")}
    if os.getenv("TEST_MODE", "true").lower() == "true":
        params["test_mode"] = "true"          # omit in live mode
    resp = SESSION.get(URL, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()
