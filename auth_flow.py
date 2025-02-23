import httpx
import logging
import uuid
from typing import Dict, Optional
import json
import os

logger = logging.getLogger(__name__)

class AuthFlow:
    def __init__(self, credentials_file: str = "user_credentials.json"):
        self.credentials_file = credentials_file
        
    async def register_user(self, engine_url: str, engine_token: str) -> Dict:
        """Register a new user and return credentials"""
        try:
            # Generate random email
            random_id = uuid.uuid4().hex[:10]
            email = f"test_{random_id}@example.com"
            
            # Make API call to register
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{engine_url}/auth/default",
                    headers={"Authorization": f"Bearer {engine_token}"},
                    json={"email": email}
                )
                response.raise_for_status()
                credentials = response.json()
                
                # Validate credentials format
                if not self._validate_credentials(credentials):
                    raise ValueError("Invalid credentials format received from server")
                    
                return credentials
                
        except Exception as e:
            logger.error(f"Failed to register user: {str(e)}")
            raise
            
    def _validate_credentials(self, credentials: Dict) -> bool:
        """Validate that credentials have the correct format"""
        required_fields = ["user_id", "token", "email"]
        
        # Check all required fields exist
        if not all(field in credentials for field in required_fields):
            return False
            
        # Validate UUID format
        try:
            uuid.UUID(credentials["user_id"])
            uuid.UUID(credentials["token"])
        except ValueError:
            return False
            
        return True
        
    def load_credentials(self) -> Optional[Dict]:
        """Load existing credentials if they exist"""
        try:
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'r') as f:
                    credentials = json.load(f)
                    if self._validate_credentials(credentials):
                        return credentials
                    logger.warning("Found invalid credentials file, will create new credentials")
            return None
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            return None
            
    def save_credentials(self, credentials: Dict) -> None:
        """Save credentials to file"""
        try:
            if not self._validate_credentials(credentials):
                raise ValueError("Cannot save invalid credentials")
                
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
            raise 