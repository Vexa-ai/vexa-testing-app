from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import codecs
import logging
import base64
from haralyzer import HarParser, HarEntry

logger = logging.getLogger(__name__)

class ApiCall(BaseModel):
    """Base model for API calls from the HAR file."""
    method: str
    url: str
    headers: Dict[str, str]
    query_params: Dict[str, str]
    body: Optional[bytes] = None
    timestamp: datetime
    
    @classmethod
    def from_har_entry(cls, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Create base data from HAR entry."""
        request = entry['request']
        headers = {h['name']: h['value'] for h in request['headers']}
        query = {q['name']: q['value'] for q in request['queryString']}
        
        # Get body data if present
        body = None
        if 'postData' in request:
            try:
                # Try to get raw binary data first
                if 'text' in request['postData']:
                    # The data in HAR is raw bytes represented as a string
                    # We need to encode it as latin1 to get the raw bytes back
                    body = request['postData']['text'].encode('latin1')
                    logger.debug(f"Successfully decoded binary data, size: {len(body)} bytes")
            except Exception as e:
                logger.error(f"Failed to decode binary data: {str(e)}")
                body = None
        
        return {
            'method': request['method'],
            'url': request['url'],
            'headers': headers,
            'query_params': query,
            'body': body,
            'timestamp': datetime.fromisoformat(entry['startedDateTime'].replace('Z', '+00:00'))
        }
    
class AudioCall(ApiCall):
    """Model for audio endpoint calls."""
    chunk_index: int
    connection_id: str
    meeting_id: str
    
    @classmethod
    def from_har_entry(cls, entry: Dict[str, Any]) -> 'AudioCall':
        """Create AudioCall from HAR entry."""
        base_data = ApiCall.from_har_entry(entry)
        query = {q['name']: q['value'] for q in entry['request']['queryString']}
        
        return cls(
            **base_data,
            chunk_index=int(query['i']),
            connection_id=query['connection_id'],
            meeting_id=query['meeting_id']
        )

class SpeakersCall(ApiCall):
    """Model for speakers endpoint calls."""
    connection_id: Optional[str]  # Now optional
    meeting_id: str
    call_name: Optional[str] = None  # Now optional
    
    @classmethod
    def from_har_entry(cls, entry: Dict[str, Any]) -> Optional['SpeakersCall']:
        """Create SpeakersCall from HAR entry."""
        base_data = ApiCall.from_har_entry(entry)
        query = {q['name']: q['value'] for q in entry['request']['queryString']}
        
        # Log the query parameters for debugging
        logger.debug(f"Speaker call query parameters: {query}")
        
        try:
            connection_id = query.get('connection_id')
            meeting_id = query.get('meeting_id')
            
            if not meeting_id:
                logger.warning(f"Missing meeting_id in speakers call. URL: {entry['request']['url']}")
                return None
            
            return cls(
                **base_data,
                connection_id=connection_id,  # Can be None
                meeting_id=meeting_id,
                call_name=query.get('call_name', '')  # Optional
            )
        except Exception as e:
            logger.warning(f"Failed to create SpeakersCall from entry: {str(e)}")
            logger.warning(f"Request URL: {entry['request']['url']}")
            logger.warning(f"Query parameters: {query}")
            return None

class HarProcessor:
    """Class for processing HAR files."""
    def __init__(self, har_data: Dict[str, Any]):
        self.parser = HarParser(har_data)
        
    def get_audio_calls(self) -> List[AudioCall]:
        """Extract all audio calls from HAR file."""
        return [
            AudioCall.from_har_entry(entry.raw_entry)
            for page in self.parser.pages
            for entry in page.entries
            if '/extension/audio' in entry.url
        ]
    
    def get_speaker_calls(self) -> List[SpeakersCall]:
        """Extract all speaker calls from HAR file."""
        valid_calls = []
        for page in self.parser.pages:
            for entry in page.entries:
                if '/extension/speakers' in entry.url:
                    try:
                        call = SpeakersCall.from_har_entry(entry.raw_entry)
                        if call:  # Only add valid calls
                            valid_calls.append(call)
                    except Exception as e:
                        logger.warning(f"Skipping invalid speakers call: {str(e)}")
        return valid_calls 