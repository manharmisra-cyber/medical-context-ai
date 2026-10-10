
import os
import time

import requests
from dotenv import load_dotenv

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / "icd.env")

TOKEN_URL = "https://icdaccessmanagement.who.int/connect/token"
API_URL = "https://id.who.int"


class ICDClient:
    def __init__(self):
        self.client_id = os.getenv("ICD_CLIENT_ID")
        self.client_secret = os.getenv("ICD_CLIENT_SECRET")

        if not self.client_id or not self.client_secret:
            raise ValueError("ICD-11 credentials missing from .env")

        self.session = requests.Session()
        self.token = None
        self.expires_at = 0

    def authenticate(self):
        response = self.session.post(
            TOKEN_URL,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
                "scope": "icdapi_access",
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            timeout=30,
        )

        if not response.ok:
            print(f"WHO authentication failed: HTTP {response.status_code}")

            try:
                error = response.json()
                print("Error:", error.get("error", "Unknown"))
                print("Description:", error.get("error_description", "Not provided"))
            except ValueError:
                print("WHO returned a non-JSON error response.")

            response.raise_for_status()

        data = response.json()

        self.token = data["access_token"]
        self.expires_at = (
            time.time() + int(data.get("expires_in", 3600)) - 60
        )

        return True

    def get(self, path, params=None):
        if not self.token or time.time() >= self.expires_at:
            self.authenticate()

        response = self.session.get(
            f"{API_URL}/{path.lstrip('/')}",
            headers={
                "Authorization": f"Bearer {self.token}",
                "API-Version": "v2",
                "Accept": "application/json",
                "Accept-Language": "en",
            },
            params=params,
            timeout=30,
        )

        response.raise_for_status()
        return response.json()

    def search(self, query):
        return self.get(
            "icd/entity/search",
            params={
                "q": query,
                "highlightingEnabled": "false",
            },
        )

    def get_entity(self, entity_id):
        if not str(entity_id).isdigit():
            raise ValueError("Expected a numeric ICD Foundation entity ID")

        return self.get(f"icd/entity/{entity_id}")
