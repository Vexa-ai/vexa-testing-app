from typing import Optional, Dict
import re
import json
import logging

logger = logging.getLogger(__name__)

class SpeakersCall(ApiCall):
    """Represents a call to the speakers endpoint"""
    def __init__(self, meeting_id: str, call_name: Optional[str] = None, connection_id: Optional[str] = None, body: Optional[bytes] = None):
        super().__init__(call_name or "speakers")
        self.meeting_id = meeting_id
        self.connection_id = connection_id
        self.body = body

    @classmethod
    def from_har_entry(cls, entry: Dict) -> Optional['SpeakersCall']:
        """Create a SpeakersCall from a HAR entry"""
        try:
            url = entry.get('request', {}).get('url', '')
            if not url:
                logger.warning("No URL found in HAR entry")
                return None

            # Extract meeting_id from URL
            meeting_id_match = re.search(r'meeting_id=([^&]+)', url)
            if not meeting_id_match:
                logger.warning("No meeting_id found in URL")
                return None
            meeting_id = meeting_id_match.group(1)

            # Extract connection_id from URL if present
            connection_id_match = re.search(r'connection_id=([^&]+)', url)
            connection_id = connection_id_match.group(1) if connection_id_match else None

            # Get response body if present
            response = entry.get('response', {})
            content = response.get('content', {})
            if content and content.get('text'):
                try:
                    # Parse speaker data to validate format
                    speaker_data = json.loads(content['text'])
                    if not isinstance(speaker_data, list):
                        logger.warning("Invalid speaker data format - expected list")
                        return None
                        
                    # Validate each speaker entry
                    for speaker_entry in speaker_data:
                        if not isinstance(speaker_entry, list) or len(speaker_entry) < 2:
                            logger.warning("Invalid speaker entry format")
                            continue
                            
                        speaker_name, meta_bits = speaker_entry[0:2]
                        if not isinstance(speaker_name, str) or not isinstance(meta_bits, str):
                            logger.warning("Invalid speaker name or meta bits type")
                            continue
                            
                    # If we get here, format is valid
                    body = content['text'].encode('utf-8')
                except json.JSONDecodeError:
                    logger.warning("Failed to parse speaker data JSON")
                    return None
            else:
                body = None

            return cls(
                meeting_id=meeting_id,
                connection_id=connection_id,
                body=body
            )
        except Exception as e:
            logger.warning(f"Failed to create SpeakersCall from HAR entry: {e}")
            return None

    def to_request(self, base_url: str) -> Dict:
        """Convert to a request that can be sent to the API"""
        url = f"{base_url}/api/v1/extension/speakers"
        params = {'meeting_id': self.meeting_id}
        if self.connection_id:
            params['connection_id'] = self.connection_id

        return {
            'url': url,
            'method': 'GET',
            'params': params,
            'body': self.body.decode('utf-8') if self.body else None
        }

    def __str__(self) -> str:
        return f"SpeakersCall(meeting_id={self.meeting_id}, connection_id={self.connection_id})" 