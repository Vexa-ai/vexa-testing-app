import json
import os
import random
import string
import httpx
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class UserCredentialsManager:
    def __init__(self, credentials_file: str = "user_credentials.json"):
        self.credentials_file = credentials_file
        self.credentials: Optional[Dict] = None

    def _generate_random_email(self) -> str:
        """Generate a random email for testing purposes."""
        random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        return f"test_{random_string}@example.com"

    def load_credentials(self) -> Optional[Dict]:
        """Load credentials from file if they exist."""
        try:
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'r') as f:
                    self.credentials = json.load(f)
                return self.credentials
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
        return None

    def save_credentials(self, credentials: Dict) -> None:
        """Save credentials to file."""
        try:
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials, f, indent=4)
            self.credentials = credentials
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
            raise

    async def get_or_create_credentials(self, engine_url: str, engine_token: str) -> Dict:
        """Get existing credentials or create new ones."""
        # Try to load existing credentials
        existing_credentials = self.load_credentials()
        if existing_credentials:
            return existing_credentials

        # Create new user credentials
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{engine_url}/auth/default",
                    headers={"Authorization": f"Bearer {engine_token}"},
                    json={"email": self._generate_random_email()}
                )
                response.raise_for_status()
                credentials = response.json()
                self.save_credentials(credentials)
                return credentials
        except Exception as e:
            logger.error(f"Error creating new user: {e}")
            raise 