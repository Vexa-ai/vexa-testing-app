import aiohttp
import asyncio
from typing import Optional, Dict, Any
import json
from datetime import datetime
import logging
import urllib.parse

from .config import config
from .models import AudioCall, SpeakersCall

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StreamqueueClient:
    """Async client for making API calls to Streamqueue."""
    
    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        self.base_url = config.TRANSCRIPTION_SERVICE_API_URL.rstrip('/')  # Remove trailing slash if present
        self.token = config.USER_TOKEN
        logger.info(f"Initialized client with base URL: {self.base_url}")
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Create a new session for each request."""
        return aiohttp.ClientSession()
        
    async def close(self):
        """Nothing to close since we create new sessions per request."""
        pass
        
    def _prepare_headers(self, additional_headers: Dict[str, str] = None) -> Dict[str, str]:
        """Prepare headers for API calls."""
        headers = {
            'Accept': '*/*',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }
        if additional_headers:
            headers.update(additional_headers)
        return headers
        
    async def send_audio(self, call: AudioCall) -> Dict[str, Any]:
        """Send audio chunk to Streamqueue."""
        url = f"{self.base_url}{config.AUDIO_ENDPOINT}"
        params = {
            'meeting_id': call.meeting_id,
            'connection_id': call.connection_id,
            'i': call.chunk_index,
            'ts': int(call.timestamp.timestamp()),
            'l': '1'
        }
        
        logger.info(f"Sending audio chunk {call.chunk_index} to {url}")
        logger.debug(f"Audio params: {params}")
        logger.debug(f"Audio headers: {call.headers}")
        
        try:
            async with await self._get_session() as session:
                async with session.put(
                    url,
                    params=params,
                    headers=self._prepare_headers(call.headers),
                    data=call.body
                ) as response:
                    response.raise_for_status()
                    response_data = await response.json()
                    logger.info(f"Successfully sent audio chunk {call.chunk_index}. Response: {response_data}")
                    return response_data
        except Exception as e:
            logger.error(f"Error sending audio chunk {call.chunk_index}: {str(e)}")
            logger.error(f"Full URL: {url}?{urllib.parse.urlencode(params)}")
            raise
            
    async def send_speakers(self, call: SpeakersCall) -> Dict[str, Any]:
        """Send speakers data to Streamqueue."""
        url = f"{self.base_url}{config.SPEAKERS_ENDPOINT}"
        params = {
            'meeting_id': call.meeting_id,
            'connection_id': call.connection_id,
            'call_name': call.call_name,
            'ts': int(call.timestamp.timestamp()),
            'l': '1'
        }
        
        logger.info(f"Sending speakers data to {url}")
        logger.debug(f"Speakers params: {params}")
        
        try:
            # Parse and validate the data format
            speakers_data = json.loads(call.body) if call.body else None
            logger.info(f"Parsed speakers_data: {speakers_data}")
            
            if not isinstance(speakers_data, list) or not speakers_data:
                raise ValueError("Speakers data must be a non-empty list")
                
            # Validate each speaker entry
            for entry in speakers_data:
                if not isinstance(entry, list) or len(entry) != 2:
                    raise ValueError("Each speaker entry must be a list of exactly 2 elements")
                if not isinstance(entry[0], str) or not isinstance(entry[1], str):
                    raise ValueError("Speaker name and meta must be strings")
            
            # Convert back to JSON string and encode as UTF-8
            data = json.dumps(speakers_data, ensure_ascii=False).encode('utf-8')
            headers = {
                'Accept': '*/*',
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.token}',
                'Content-Length': str(len(data)),
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'en-US,en;q=0.9,ru-RU;q=0.8,ru;q=0.7,pt-PT;q=0.6,pt;q=0.5',
                'Connection': 'close',  # Explicitly close the connection
                'Origin': 'chrome-extension://ihibgadfkbefnclpbhdlpahfiejhfibl',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
            }
            
            logger.info(f"Sending data: {data}")
            
            async with await self._get_session() as session:
                async with session.put(
                    url,
                    params=params,
                    headers=headers,
                    data=data
                ) as response:
                    response.raise_for_status()
                    response_data = await response.json()
                    logger.info(f"Successfully sent speakers data. Response: {response_data}")
                    return response_data
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            logger.error(f"Problematic JSON string: {call.body}")
            raise
        except ValueError as e:
            logger.error(f"Data validation error: {str(e)}")
            logger.error(f"Invalid data: {speakers_data}")
            raise
        except Exception as e:
            logger.error(f"Error sending speakers data: {str(e)}")
            logger.error(f"Full URL: {url}?{urllib.parse.urlencode(params)}")
            raise

class Client(StreamqueueClient):
    """Extended client that supports token injection."""
    
    def __init__(self, user_token: str = None, meeting_id: str = None, connection_id: str = None):
        super().__init__()
        self.user_token = user_token or config.USER_TOKEN
        self.token = self.user_token  # Override parent's token
        self.headers = {'Authorization': f'Bearer {self.user_token}'}
        self.meeting_id = meeting_id
        self.connection_id = connection_id
        logger.info(f"Initialized client with base URL: {self.base_url}")
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Create a new session for each request."""
        return aiohttp.ClientSession()
        
    async def close(self):
        """Nothing to close since we create new sessions per request."""
        pass
        
    def _prepare_headers(self, additional_headers: Dict[str, str] = None) -> Dict[str, str]:
        """Prepare headers for API calls."""
        headers = {
            'Accept': '*/*',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.user_token}'
        }
        if additional_headers:
            headers.update(additional_headers)
        return headers
        
    async def send_audio(self, call: AudioCall) -> Dict[str, Any]:
        """Send audio chunk to Streamqueue."""
        url = f"{self.base_url}{config.AUDIO_ENDPOINT}"
        params = {
            'meeting_id': call.meeting_id,
            'connection_id': call.connection_id,
            'i': call.chunk_index,
            'ts': int(call.timestamp.timestamp()),
            'l': '1'
        }
        
        logger.info(f"Sending audio chunk {call.chunk_index} to {url}")
        logger.debug(f"Audio params: {params}")
        logger.debug(f"Audio headers: {call.headers}")
        
        try:
            async with await self._get_session() as session:
                async with session.put(
                    url,
                    params=params,
                    headers=self._prepare_headers(call.headers),
                    data=call.body
                ) as response:
                    response.raise_for_status()
                    response_data = await response.json()
                    logger.info(f"Successfully sent audio chunk {call.chunk_index}. Response: {response_data}")
                    return response_data
        except Exception as e:
            logger.error(f"Error sending audio chunk {call.chunk_index}: {str(e)}")
            logger.error(f"Full URL: {url}?{urllib.parse.urlencode(params)}")
            raise
            
    async def send_speakers(self, call: SpeakersCall) -> Dict[str, Any]:
        """Send speakers data to Streamqueue."""
        url = f"{self.base_url}{config.SPEAKERS_ENDPOINT}"
        params = {
            'meeting_id': call.meeting_id,
            'connection_id': call.connection_id,
            'call_name': call.call_name,
            'ts': int(call.timestamp.timestamp()),
            'l': '1'
        }
        
        logger.info(f"Sending speakers data to {url}")
        logger.debug(f"Speakers params: {params}")
        
        try:
            # Parse and validate the data format
            speakers_data = json.loads(call.body) if call.body else None
            logger.info(f"Parsed speakers_data: {speakers_data}")
            
            if not isinstance(speakers_data, list) or not speakers_data:
                raise ValueError("Speakers data must be a non-empty list")
                
            # Validate each speaker entry
            for entry in speakers_data:
                if not isinstance(entry, list) or len(entry) != 2:
                    raise ValueError("Each speaker entry must be a list of exactly 2 elements")
                if not isinstance(entry[0], str) or not isinstance(entry[1], str):
                    raise ValueError("Speaker name and meta must be strings")
            
            # Convert back to JSON string and encode as UTF-8
            data = json.dumps(speakers_data, ensure_ascii=False).encode('utf-8')
            headers = {
                'Accept': '*/*',
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.user_token}',
                'Content-Length': str(len(data)),
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'en-US,en;q=0.9,ru-RU;q=0.8,ru;q=0.7,pt-PT;q=0.6,pt;q=0.5',
                'Connection': 'close',  # Explicitly close the connection
                'Origin': 'chrome-extension://ihibgadfkbefnclpbhdlpahfiejhfibl',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
            }
            
            logger.info(f"Sending data: {data}")
            
            async with await self._get_session() as session:
                async with session.put(
                    url,
                    params=params,
                    headers=headers,
                    data=data
                ) as response:
                    response.raise_for_status()
                    response_data = await response.json()
                    logger.info(f"Successfully sent speakers data. Response: {response_data}")
                    return response_data
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            logger.error(f"Problematic JSON string: {call.body}")
            raise
        except ValueError as e:
            logger.error(f"Data validation error: {str(e)}")
            logger.error(f"Invalid data: {speakers_data}")
            raise
        except Exception as e:
            logger.error(f"Error sending speakers data: {str(e)}")
            logger.error(f"Full URL: {url}?{urllib.parse.urlencode(params)}")
            raise 