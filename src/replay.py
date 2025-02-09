import asyncio
import json
import logging
from datetime import datetime
from typing import List, Tuple, Dict, Any
import uuid

from .config import config
from .models import AudioCall, SpeakersCall, HarProcessor
from .client import StreamqueueClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ApiReplay:
    """Class for replaying API calls from HAR file."""
    
    def __init__(self, har_file_path: str):
        self.har_file_path = har_file_path
        self.client = StreamqueueClient()
        
    async def load_har_file(self) -> HarProcessor:
        """Load and parse HAR file."""
        with open(self.har_file_path, 'r') as f:
            data = json.load(f)
            return HarProcessor(data)
            
    def _calculate_delay(self, current: datetime, previous: datetime) -> float:
        """Calculate delay between calls, applying time scale."""
        if not config.PRESERVE_TIMING:
            return 0
        delay = (current - previous).total_seconds() * config.TIME_SCALE
        return max(0, delay)
        
    async def replay_calls(self):
        """Replay all API calls from the HAR file."""
        try:
            har_processor = await self.load_har_file()
            
            # Get all calls and sort by timestamp
            audio_calls = har_processor.get_audio_calls()
            speaker_calls = har_processor.get_speaker_calls()
            
            all_calls: List[Tuple[datetime, Any]] = [
                (call.timestamp, ('audio', call)) for call in audio_calls
            ] + [
                (call.timestamp, ('speaker', call)) for call in speaker_calls
            ]
            all_calls.sort(key=lambda x: x[0])
            
            # Replay calls in sequence
            previous_time = all_calls[0][0] if all_calls else datetime.now()
            
            for current_time, (call_type, call) in all_calls:
                # Calculate and apply delay
                delay = self._calculate_delay(current_time, previous_time)
                if delay > 0:
                    logger.info(f"Waiting {delay:.2f} seconds before next call")
                    await asyncio.sleep(delay)
                
                # Send the call
                try:
                    if call_type == 'audio':
                        logger.info(f"Sending audio chunk {call.chunk_index}")
                        await self.client.send_audio(call)
                    else:
                        logger.info(f"Sending speakers data for {call.meeting_id}")
                        await self.client.send_speakers(call)
                except Exception as e:
                    logger.error(f"Error during replay: {str(e)}")
                    continue
                
                previous_time = current_time
                
        finally:
            await self.client.close()
            
async def main():
    """Main entry point for the replay script."""
    if not config.USER_TOKEN:
        raise ValueError("USER_TOKEN must be set in environment variables")
        
    replay = ApiReplay('api_calls.json')
    await replay.replay_calls()
    
if __name__ == '__main__':
    asyncio.run(main()) 