from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Config(BaseModel):
    """Configuration settings for the mock extension."""
    STREAMQUEUE_URL: str = os.getenv('STREAMQUEUE_URL', '')
    USER_TOKEN: str = os.getenv('USER_TOKEN', '')  # Will be required
    SERVICE_TOKEN: str = os.getenv('SERVICE_TOKEN', '')  # Will be required
    DEFAULT_MEETING_ID: str = os.getenv('DEFAULT_MEETING_ID', 'mock-meeting')
    DEFAULT_CONNECTION_ID: str = os.getenv('DEFAULT_CONNECTION_ID', '')  # Will be auto-generated if not provided
    
    # API endpoints
    AUDIO_ENDPOINT: str = '/api/v1/extension/audio'
    SPEAKERS_ENDPOINT: str = '/api/v1/extension/speakers'
    
    # Replay settings
    PRESERVE_TIMING: bool = os.getenv('PRESERVE_TIMING', 'true').lower() == 'true'
    TIME_SCALE: float = float(os.getenv('TIME_SCALE', '1.0'))  # Can speed up or slow down replay
    
    class Config:
        frozen = True

config = Config() 