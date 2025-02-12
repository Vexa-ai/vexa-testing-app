import asyncio
import json
import logging
import os
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
        self.output_dir = "output_audio"
        os.makedirs(self.output_dir, exist_ok=True)
        
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

    def _write_chunk_to_file(self, connection_id: str, chunk_data: bytes, chunk_index: int) -> None:
        """Write audio chunk to a webm file."""
        file_path = os.path.join(self.output_dir, f"{connection_id}.webm")
        try:
            with open(file_path, "ab") as f:
                f.write(chunk_data)
            logger.info(f"Wrote chunk {chunk_index} to {file_path}")
        except Exception as e:
            logger.error(f"Failed to write chunk {chunk_index} to {file_path}: {str(e)}")

    def _validate_audio_chunks(self, audio_calls: List[AudioCall]) -> None:
        """Validate audio chunks sequence and log detailed information."""
        if not audio_calls:
            logger.error("No audio calls found in the HAR file")
            return

        # Group chunks by connection_id to handle multiple streams
        chunks_by_connection = {}
        for call in audio_calls:
            if call.connection_id not in chunks_by_connection:
                chunks_by_connection[call.connection_id] = []
            chunks_by_connection[call.connection_id].append(call)

        # Validate each connection's chunks
        for connection_id, chunks in chunks_by_connection.items():
            sorted_chunks = sorted(chunks, key=lambda x: x.chunk_index)
            first_chunk = sorted_chunks[0]
            
            logger.info(f"Connection {connection_id}:")
            logger.info(f"  First chunk index: {first_chunk.chunk_index}")
            logger.info(f"  Total chunks: {len(chunks)}")
            logger.info(f"  Chunk indices: {[c.chunk_index for c in sorted_chunks]}")
            
            # Strict validation for first chunk
            if first_chunk.chunk_index != 0:
                raise ValueError(
                    f"First chunk index must be 0, got {first_chunk.chunk_index} "
                    f"for connection {connection_id}"
                )

            # Check for gaps in sequence
            expected_indices = set(range(len(chunks)))
            actual_indices = set(c.chunk_index for c in chunks)
            missing_indices = expected_indices - actual_indices
            if missing_indices:
                logger.error(f"Missing chunk indices for connection {connection_id}: {missing_indices}")
        
    async def replay_calls(self):
        """Replay all API calls from the HAR file."""
        try:
            har_processor = await self.load_har_file()
            
            # Get all calls in their original order
            all_calls = []
            for entry in har_processor.parser.pages[0].entries:
                if '/extension/audio' in entry.url:
                    call = AudioCall.from_har_entry(entry.raw_entry)
                    all_calls.append((call.timestamp, ('audio', call)))
                    logger.info(f"Found audio call - connection: {call.connection_id}, index: {call.chunk_index}, timestamp: {call.timestamp}")
                elif '/extension/speakers' in entry.url:
                    call = SpeakersCall.from_har_entry(entry.raw_entry)
                    all_calls.append((call.timestamp, ('speaker', call)))
                    logger.info(f"Found speaker call - connection: {call.connection_id}, timestamp: {call.timestamp}")

            if not all_calls:
                logger.warning("No calls found to replay")
                return

            # Collect audio calls for validation only
            audio_calls = [call for _, (type_, call) in all_calls if type_ == 'audio']
            
            # Validate audio chunks but don't change the order
            try:
                self._validate_audio_chunks(audio_calls)
            except ValueError as e:
                logger.error(f"Chunk validation failed: {str(e)}")
                return

            # Log the sequence we're going to replay
            logger.info("Call sequence for replay:")
            for time, (call_type, call) in all_calls:
                if call_type == 'audio':
                    logger.info(f"Will send audio chunk {call.chunk_index} for connection {call.connection_id} at {time}")
                else:
                    logger.info(f"Will send speakers data for connection {call.connection_id} at {time}")

            # Track sent chunks for verification
            sent_chunks = set()
            
            # Clean up any existing webm files
            for file in os.listdir(self.output_dir):
                if file.endswith('.webm'):
                    os.remove(os.path.join(self.output_dir, file))
            
            # Replay calls in original sequence
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
                        total_chunks = len([c for _, (t, c) in all_calls if t == 'audio' and c.connection_id == call.connection_id])
                        chunk_info = f"chunk {call.chunk_index}/{total_chunks-1}"
                        logger.info(f"Sending {chunk_info} for connection {call.connection_id} at {current_time}")
                        
                        # Write chunk to file before sending
                        if hasattr(call, 'body') and call.body:
                            self._write_chunk_to_file(call.connection_id, call.body, call.chunk_index)
                        else:
                            logger.warning(f"No audio data in chunk {call.chunk_index} for connection {call.connection_id}")
                        
                        await self.client.send_audio(call)
                        sent_chunks.add((call.connection_id, call.chunk_index))
                    else:
                        logger.info(f"Sending speakers data for {call.meeting_id}")
                        await self.client.send_speakers(call)
                except Exception as e:
                    logger.error(f"Error during replay: {str(e)}")
                    continue
                
                previous_time = current_time

            # Group audio calls by connection for final verification
            chunks_by_connection = {}
            for call in audio_calls:
                if call.connection_id not in chunks_by_connection:
                    chunks_by_connection[call.connection_id] = []
                chunks_by_connection[call.connection_id].append(call)
            
            # Verify all chunks were sent and written
            logger.info("Verifying sent chunks:")
            for connection_id, chunks in chunks_by_connection.items():
                expected_indices = set(range(len(chunks)))
                sent_indices = {idx for conn_id, idx in sent_chunks if conn_id == connection_id}
                missing_indices = expected_indices - sent_indices
                
                webm_path = os.path.join(self.output_dir, f"{connection_id}.webm")
                if os.path.exists(webm_path):
                    file_size = os.path.getsize(webm_path)
                    logger.info(f"Generated webm file for {connection_id}: {file_size} bytes")
                
                if missing_indices:
                    logger.error(f"Connection {connection_id}: Failed to send chunks {missing_indices}")
                else:
                    logger.info(f"Connection {connection_id}: Successfully sent all {len(chunks)} chunks in original sequence")
                
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