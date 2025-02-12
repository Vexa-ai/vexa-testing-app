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
    connection_id: str
    meeting_id: str
    call_name: str
    
    @classmethod
    def from_har_entry(cls, entry: Dict[str, Any]) -> 'SpeakersCall':
        """Create SpeakersCall from HAR entry."""
        base_data = ApiCall.from_har_entry(entry)
        query = {q['name']: q['value'] for q in entry['request']['queryString']}
        
        return cls(
            **base_data,
            connection_id=query['connection_id'],
            meeting_id=query['meeting_id'],
            call_name=query.get('call_name', '')
        )

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
        return [
            SpeakersCall.from_har_entry(entry.raw_entry)
            for page in self.parser.pages
            for entry in page.entries
            if '/extension/speakers' in entry.url
        ] 