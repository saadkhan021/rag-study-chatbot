"""
Automated test script — no manual /docs clicking, no re-authorizing after
every restart. Run this instead of testing through the browser.

Usage:
    python test_api.py
"""

import requests

BASE_URL = "http://127.0.0.1:8000"
EMAIL = "test@example.com"       # change if you want a fresh account
PASSWORD = "testpassword123"

COURSES_TO_TEST = [
    "AI",
    "Agentic AI",
    "BBA",
    "Computer Science",
    "Software Engineering",
]

# One real question per subject — edit these to things you actually know
# the answer to, so you can judge correctness yourself.
TEST_QUESTIONS = {
    "AI": "What are the properties of an environment in AI?",
    "Agentic AI": "What is an AI agent?",
    "BBA": "What are the four functions of management?",
    "Computer Science": "What is a data flow diagram?",
    "Software Engineering": "What is the waterfall model?",
}


def get_token() -> str:
    """Logs in if the account exists, signs up if it doesn't. Either way,
    returns a fresh token — no manual copy-pasting required."""
    login_resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
    )
    if login_resp.status_code == 200:
        print(f"Logged in as {EMAIL}")
        return login_resp.json()["access_token"]

    print(f"Login failed ({login_resp.status_code}), trying signup...")
    signup_resp = requests.post(
        f"{BASE_URL}/auth/signup",
        json={"email": EMAIL, "password": PASSWORD},
    )
    signup_resp.raise_for_status()
    print(f"Signed up as {EMAIL}")
    return signup_resp.json()["access_token"]


def main():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    print(f"\n{'='*60}")
    print("Adding courses...")
    print(f"{'='*60}")
    for course in COURSES_TO_TEST:
        resp = requests.post(
            f"{BASE_URL}/me/courses",
            json={"course_name": course},
            headers=headers,
        )
        status = "OK" if resp.status_code == 200 else f"FAILED ({resp.status_code})"
        print(f"  {course:25s} [{status}] {resp.json()}")

    print(f"\n{'='*60}")
    print("Confirming course list...")
    print(f"{'='*60}")
    resp = requests.get(f"{BASE_URL}/me/courses", headers=headers)
    print(f"  Courses on account: {resp.json()}")

    print(f"\n{'='*60}")
    print("Testing chat per subject...")
    print(f"{'='*60}")
    for course, question in TEST_QUESTIONS.items():
        print(f"\n--- {course} ---")
        print(f"Q: {question}")
        resp = requests.post(
            f"{BASE_URL}/conversations/{course}/messages",
            json={"content": question},
            headers=headers,
        )
        if resp.status_code == 200:
            answer = resp.json()["content"]
            print(f"A: {answer[:500]}{'...' if len(answer) > 500 else ''}")
        else:
            print(f"FAILED ({resp.status_code}): {resp.text}")

    print(f"\n{'='*60}")
    print("Testing refusal behavior (question NOT in the material)...")
    print(f"{'='*60}")
    resp = requests.post(
        f"{BASE_URL}/conversations/AI/messages",
        json={"content": "What is the capital of France?"},
        headers=headers,
    )
    print(f"A: {resp.json().get('content', resp.text)}")
    print("(Should say something like 'not covered' — if it actually answers, that's a hallucination bug)")


if __name__ == "__main__":
    main()