import requests, os, logging

URL = "https://9uc4obe1q1.execute-api.us-east-2.amazonaws.com/dev/responses"
_session = requests.Session()                # ← keeps TLS socket open

def post_response(email_id: str, body: str):
    payload = {
        "email_id": email_id,
        "response_body": body,
        "api_key": os.getenv("EMAIL_API_KEY")
    }
    if os.getenv("TEST_MODE") == "true":
        payload["test_mode"] = "true"

    r = _session.post(URL, json=payload, timeout=5)
    if not r.ok:
        logging.warning("POST %s failed %s %s", email_id, r.status_code, r.text)
