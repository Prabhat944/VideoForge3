import os
import uuid
import pytest
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load frontend .env so BASE_URL is available when running pytest from shell
load_dotenv(Path(__file__).resolve().parents[2] / 'frontend' / '.env')

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

DEFAULT_TEST_EMAIL = "tester@videoforge.ai"
DEFAULT_TEST_PASSWORD = "TestPass123!"
DEFAULT_TEST_NAME = "Test Creator"


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture(scope="session")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def auth_token(api_client):
    """Login primary test user, create if missing."""
    # Try login first
    r = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": DEFAULT_TEST_EMAIL,
        "password": DEFAULT_TEST_PASSWORD,
    })
    if r.status_code == 200:
        return r.json()["token"]
    # Register otherwise
    r = api_client.post(f"{BASE_URL}/api/auth/register", json={
        "email": DEFAULT_TEST_EMAIL,
        "password": DEFAULT_TEST_PASSWORD,
        "full_name": DEFAULT_TEST_NAME,
    })
    if r.status_code == 200:
        return r.json()["token"]
    pytest.skip(f"Auth bootstrap failed: {r.status_code} {r.text}")


@pytest.fixture(scope="session")
def authed(api_client, auth_token):
    s = requests.Session()
    s.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}",
    })
    return s


@pytest.fixture
def fresh_email():
    return f"TEST_user_{uuid.uuid4().hex[:10]}@videoforge.ai"
