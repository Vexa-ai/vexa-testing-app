"""Module for generating synthetic test data based on real API call patterns."""

import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, NamedTuple
import logging
from dataclasses import dataclass
from copy import deepcopy

from .models import AudioCall, SpeakersCall, HarProcessor

logger = logging.getLogger(__name__)

class AudioSpeakerPattern(NamedTuple):
    """A pattern of synchronized audio and speaker data from real recordings."""
    audio_chunk: bytes
    chunk_index: int
    speaker_data: Dict[str, Any]
    relative_timestamp: float  # seconds from start
    duration_sec: float

@dataclass
class Speaker:
    """Speaker in a meeting (not necessarily a user)."""
    name: str
    speaking_patterns: List[Tuple[float, float]]  # List of (start_sec, end_sec) speaking periods

@dataclass
class SyntheticUser:
    """User configuration for synthetic data (client/participant)."""
    user_id: str = str(uuid.uuid4())
    connection_id: str = str(uuid.uuid4())

@dataclass
class SyntheticMeeting:
    """Configuration for a synthetic meeting."""
    meeting_id: str = str(uuid.uuid4())
    duration_minutes: int = 30
    num_users: int = 2  # Number of clients/participants
    speakers: List[Speaker] = None  # Will be populated from patterns
    chunk_duration_sec: float = 1.0
    speaker_update_interval_sec: float = 0.5
    start_time: datetime = datetime.now()

class SyntheticDataGenerator:
    """Generates synthetic test data based on real API call patterns."""
    
    def __init__(self, template_file: str):
        """Initialize generator with template data."""
        self.template_file = template_file
        self.audio_speaker_patterns: List[AudioSpeakerPattern] = []
        self.speaker_patterns: Dict[str, List[Tuple[float, float]]] = {}  # speaker_name -> speaking periods
        self._load_template_data()
        
    def _load_template_data(self):
        """Load template data from HAR file"""
        try:
            logger.info("Starting to load template data...")
            with open(self.template_file, 'r') as f:
                logger.info("Reading HAR file...")
                har_data = json.load(f)
                logger.info("Successfully loaded HAR JSON data")

            current_pattern = None
            relative_time = 0.0
            entries_processed = 0
            audio_entries = 0
            speaker_entries = 0
            patterns_created = 0
            audio_parse_failures = 0
            speaker_parse_failures = 0

            # Sample a few entries for detailed inspection
            sample_audio = None
            sample_speaker = None
            samples_collected = 0

            logger.info("Processing HAR entries...")
            for entry in har_data.get('log', {}).get('entries', []):
                entries_processed += 1
                try:
                    # Extract call type from URL
                    url = entry.get('request', {}).get('url', '')
                    if not url:
                        continue

                    call_type = None
                    if 'audio' in url:
                        call_type = 'audio'
                        audio_entries += 1
                        # Collect a sample audio entry
                        if not sample_audio and samples_collected < 2:
                            sample_audio = entry
                            samples_collected += 1
                            logger.info(f"Sample audio URL: {url}")
                            response = entry.get('response', {})
                            content = response.get('content', {})
                            logger.info(f"Audio content: {content}")
                            logger.info(f"Audio content text: {content.get('text', '')}")
                            if 'text' not in content:
                                logger.warning(f"No text field in audio content. Available fields: {list(content.keys())}")
                    elif 'speakers' in url:
                        call_type = 'speaker'
                        speaker_entries += 1
                        # Collect a sample speaker entry
                        if not sample_speaker and samples_collected < 2:
                            sample_speaker = entry
                            samples_collected += 1
                            logger.info(f"Sample speaker URL: {url}")
                            response = entry.get('response', {})
                            content = response.get('content', {})
                            logger.info(f"Speaker content: {content}")
                            logger.info(f"Speaker content text: {content.get('text', '')}")
                            if 'text' not in content:
                                logger.warning(f"No text field in speaker content. Available fields: {list(content.keys())}")

                    if not call_type:
                        continue

                    # Get response body
                    response = entry.get('response', {})
                    content = response.get('content', {})
                    if not content:
                        logger.debug(f"No content for {call_type} entry")
                        continue
                    if not content.get('text'):
                        logger.debug(f"No text in content for {call_type} entry")
                        continue

                    if call_type == 'audio':
                        logger.debug("Processing audio entry...")
                        # Start new pattern with audio data
                        if current_pattern and current_pattern.get('speakers'):
                            logger.debug(f"Saving completed pattern with speakers: {list(current_pattern['speakers'].keys())}")
                            self.audio_speaker_patterns.append(AudioSpeakerPattern(
                                audio_chunk=current_pattern['audio_chunk'],
                                chunk_index=current_pattern['chunk_index'],
                                speaker_data=current_pattern['speakers'],
                                relative_timestamp=current_pattern['relative_timestamp'],
                                duration_sec=current_pattern['duration_sec']
                            ))
                            patterns_created += 1

                        # Parse audio data
                        try:
                            audio_text = content['text']
                            logger.debug(f"Audio text type: {type(audio_text)}, length: {len(audio_text)}")
                            audio_data = json.loads(audio_text)
                            logger.debug(f"Audio data keys: {list(audio_data.keys())}")
                            
                            if 'audio_chunk' not in audio_data:
                                logger.warning("No audio_chunk in audio data")
                                audio_parse_failures += 1
                                continue
                                
                            current_pattern = {
                                'audio_chunk': audio_data['audio_chunk'],
                                'chunk_index': audio_data.get('chunk_index', 0),
                                'relative_timestamp': relative_time,
                                'duration_sec': 0.5,  # Default duration
                                'speakers': {}
                            }
                            logger.debug(f"Created new pattern with chunk index {current_pattern['chunk_index']}")
                            relative_time += current_pattern['duration_sec']
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse audio data: {e}")
                            audio_parse_failures += 1
                            continue
                        except Exception as e:
                            logger.warning(f"Error processing audio data: {str(e)}")
                            audio_parse_failures += 1
                            continue

                    elif call_type == 'speaker' and current_pattern:
                        logger.debug("Processing speaker entry...")
                        # Add speaker data to current pattern
                        try:
                            speaker_text = content['text']
                            logger.debug(f"Speaker text type: {type(speaker_text)}, length: {len(speaker_text)}")
                            
                            # Try to decode if it's bytes
                            if isinstance(speaker_text, bytes):
                                speaker_text = speaker_text.decode('utf-8')
                            
                            speaker_data = json.loads(speaker_text)
                            logger.debug(f"Speaker data: {speaker_data}")

                            # Process speaker data
                            for speaker_entry in speaker_data:
                                if len(speaker_entry) >= 2:
                                    speaker_name = speaker_entry[0]
                                    meta_bits = speaker_entry[1]
                                    logger.debug(f"Processing speaker {speaker_name} with meta_bits: {meta_bits}")
                                    
                                    # Calculate speaking state from meta bits
                                    is_speaking = sum(1 for b in meta_bits if b == '1') / max(len(meta_bits), 1) > 0.5
                                    
                                    if is_speaking:
                                        logger.debug(f"Found active speaker: {speaker_name}")
                                        current_pattern['speakers'][speaker_name] = {
                                            'speaker_name': speaker_name,
                                            'meta': meta_bits,
                                            'is_speaking': is_speaking
                                        }
                                        
                                        # Update speaker patterns
                                        if speaker_name not in self.speaker_patterns:
                                            self.speaker_patterns[speaker_name] = []
                                        self.speaker_patterns[speaker_name].append(
                                            (relative_time, relative_time + current_pattern['duration_sec'])
                                        )

                        except Exception as e:
                            logger.warning(f"Failed to process speaker data: {e}")
                            speaker_parse_failures += 1
                            continue

                except Exception as e:
                    logger.warning(f"Failed to process entry: {e}")
                    continue

            logger.info(f"Processed {entries_processed} entries ({audio_entries} audio, {speaker_entries} speaker)")
            logger.info(f"Audio parse failures: {audio_parse_failures}, Speaker parse failures: {speaker_parse_failures}")
            logger.info(f"Created {patterns_created} patterns during processing")

            # Save last pattern if it exists and has both audio and speakers
            if current_pattern and current_pattern.get('speakers'):
                logger.debug("Saving final pattern")
                self.audio_speaker_patterns.append(AudioSpeakerPattern(
                    audio_chunk=current_pattern['audio_chunk'],
                    chunk_index=current_pattern['chunk_index'],
                    speaker_data=current_pattern['speakers'],
                    relative_timestamp=current_pattern['relative_timestamp'],
                    duration_sec=current_pattern['duration_sec']
                ))
                patterns_created += 1

            if not self.audio_speaker_patterns:
                raise ValueError("No valid audio-speaker patterns found in template data")

            logger.info(f"Successfully loaded {len(self.audio_speaker_patterns)} audio-speaker patterns")
            logger.info(f"Found speakers: {list(self.speaker_patterns.keys())}")

        except Exception as e:
            logger.error(f"Failed to load template data: {str(e)}")
            raise
            
    def _create_synthetic_speakers(self, duration_minutes: int) -> List[Speaker]:
        """Create synthetic speakers based on real patterns."""
        speakers = []
        total_duration_sec = duration_minutes * 60
        
        # For each real speaker pattern
        for speaker_name, speaking_periods in self.speaker_patterns.items():
            # Create new synthetic speaker
            synthetic_periods = []
            pattern_duration = max(end for _, end in speaking_periods)
            
            # Repeat pattern to fill duration
            num_repeats = int(total_duration_sec / pattern_duration) + 1
            for i in range(num_repeats):
                offset = i * pattern_duration
                for start, end in speaking_periods:
                    if offset + start < total_duration_sec:
                        synthetic_periods.append(
                            (offset + start, min(total_duration_sec, offset + end))
                        )
            
            speakers.append(Speaker(
                name=f"Speaker_{len(speakers)+1}",  # New unique name
                speaking_patterns=synthetic_periods
            ))
            
        return speakers
        
    def generate_meeting(self, config: SyntheticMeeting) -> List[Dict[str, Any]]:
        """Generate synthetic meeting data."""
        synthetic_calls = []
        
        # Create users (clients/participants)
        users = [SyntheticUser() for _ in range(config.num_users)]
        
        # Create or use provided speakers
        if not config.speakers:
            config.speakers = self._create_synthetic_speakers(config.duration_minutes)
        
        # Calculate total chunks needed
        total_chunks = int(config.duration_minutes * 60 / config.chunk_duration_sec)
        chunks_per_user = total_chunks // config.num_users
        
        current_time = config.start_time
        chunk_index = 0
        
        # Generate interleaved audio and speaker data
        for user in users:
            for i in range(chunks_per_user):
                # Find matching pattern for current time
                relative_time = i * config.chunk_duration_sec
                pattern = None
                for p in self.audio_speaker_patterns:
                    if abs(p.relative_timestamp - relative_time) < config.chunk_duration_sec:
                        pattern = p
                        break
                
                if not pattern:
                    pattern = self.audio_speaker_patterns[i % len(self.audio_speaker_patterns)]
                
                # Add audio chunk
                audio_call = {
                    'request': {
                        'method': 'PUT',
                        'url': '/extension/audio',
                        'queryString': [
                            {'name': 'i', 'value': str(chunk_index)},
                            {'name': 'connection_id', 'value': user.connection_id},
                            {'name': 'meeting_id', 'value': config.meeting_id}
                        ],
                        'headers': [],
                        'postData': {
                            'text': pattern.audio_chunk.decode('latin1')
                        }
                    },
                    'startedDateTime': current_time.isoformat()
                }
                synthetic_calls.append(audio_call)
                
                # Add speaker data for each active speaker
                if i % int(config.speaker_update_interval_sec / config.chunk_duration_sec) == 0:
                    for speaker in config.speakers:
                        # Check if speaker is active at this time
                        is_speaking = any(
                            start <= relative_time <= end 
                            for start, end in speaker.speaking_patterns
                        )
                        
                        if is_speaking:
                            # Use template speaker data but modify fields
                            speaker_data = deepcopy(next(iter(pattern.speaker_data.values())))
                            speaker_data.update({
                                'speaker_name': speaker.name,
                                'user_id': user.user_id,  # Associate with current user
                                'meeting_id': config.meeting_id,
                                'user_timestamp': current_time.isoformat()
                            })
                            
                            speaker_call = {
                                'request': {
                                    'method': 'PUT',
                                    'url': '/extension/speakers',
                                    'queryString': [
                                        {'name': 'connection_id', 'value': user.connection_id},
                                        {'name': 'meeting_id', 'value': config.meeting_id}
                                    ],
                                    'headers': [],
                                    'postData': {
                                        'text': json.dumps(speaker_data)
                                    }
                                },
                                'startedDateTime': current_time.isoformat()
                            }
                            synthetic_calls.append(speaker_call)
                
                current_time += timedelta(seconds=config.chunk_duration_sec)
                chunk_index += 1
                
        return synthetic_calls

    def validate_generated_data(self, synthetic_calls: List[Dict[str, Any]]) -> bool:
        """Validate generated synthetic data."""
        try:
            # Sort calls by timestamp
            sorted_calls = sorted(
                synthetic_calls,
                key=lambda x: datetime.fromisoformat(x['startedDateTime'].rstrip('Z'))
            )
            
            # Track state for validation
            audio_chunks_by_connection = {}
            speaker_states = {}
            current_speakers = set()
            
            for call in sorted_calls:
                timestamp = datetime.fromisoformat(call['startedDateTime'].rstrip('Z'))
                url = call['request']['url']
                query = {q['name']: q['value'] for q in call['request']['queryString']}
                
                if '/extension/audio' in url:
                    # Validate audio chunk sequence
                    connection_id = query['connection_id']
                    chunk_index = int(query['i'])
                    
                    if connection_id not in audio_chunks_by_connection:
                        audio_chunks_by_connection[connection_id] = []
                    
                    # Check chunk sequence
                    if audio_chunks_by_connection[connection_id]:
                        last_index = audio_chunks_by_connection[connection_id][-1]
                        if chunk_index != last_index + 1:
                            logger.error(f"Non-sequential chunk index for connection {connection_id}")
                            return False
                    elif chunk_index != 0:
                        logger.error(f"First chunk index not 0 for connection {connection_id}")
                        return False
                        
                    audio_chunks_by_connection[connection_id].append(chunk_index)
                    
                elif '/extension/speakers' in url:
                    # Validate speaker data
                    connection_id = query['connection_id']
                    speaker_data = json.loads(call['request']['postData']['text'])
                    speaker_name = speaker_data['speaker_name']
                    
                    # Check speaker state transitions
                    is_speaking = sum(1 for b in speaker_data['meta'] if b == '1') / len(speaker_data['meta']) > 0.5
                    
                    if is_speaking:
                        current_speakers.add(speaker_name)
                        if len(current_speakers) > 3:  # Arbitrary limit for simultaneous speakers
                            logger.warning(f"Too many simultaneous speakers: {current_speakers}")
                    else:
                        current_speakers.discard(speaker_name)
                    
                    # Track speaker state
                    if connection_id not in speaker_states:
                        speaker_states[connection_id] = {}
                    speaker_states[connection_id][timestamp] = speaker_data
            
            logger.info("Validation passed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            return False

    def generate_test_scenario(self, scenario_config: Dict[str, Any]) -> str:
        """Generate complete test scenario and save to file.
        
        Args:
            scenario_config: Dictionary containing test scenario parameters:
                - meetings: List[SyntheticMeeting] - Meeting configurations
                - output_file: str - Path to save generated HAR file
                
        Returns:
            Path to generated HAR file
        """
        har_data = {
            'log': {
                'version': '1.2',
                'creator': {'name': 'Synthetic Test Generator', 'version': '1.0'},
                'entries': []
            }
        }
        
        # Generate data for each meeting
        for meeting_config in scenario_config['meetings']:
            synthetic_calls = self.generate_meeting(meeting_config)
            har_data['log']['entries'].extend(synthetic_calls)
            
        # Sort all entries by timestamp
        har_data['log']['entries'].sort(
            key=lambda x: datetime.fromisoformat(x['startedDateTime'].rstrip('Z'))
        )
        
        # Save to file
        output_file = scenario_config['output_file']
        with open(output_file, 'w') as f:
            json.dump(har_data, f, indent=2)
            
        logger.info(f"Generated synthetic test data saved to {output_file}")
        return output_file
        
def create_concurrent_meetings_scenario(
    base_duration_minutes: int = 30,
    num_meetings: int = 3,
    users_per_meeting: int = 2,
    output_file: str = 'synthetic_concurrent.json'
) -> str:
    """Create a scenario with multiple concurrent meetings.
    
    Args:
        base_duration_minutes: Base duration for each meeting
        num_meetings: Number of concurrent meetings
        users_per_meeting: Number of users per meeting
        output_file: Path to save generated HAR file
        
    Returns:
        Path to generated HAR file
    """
    # Create staggered meeting start times
    start_time = datetime.now()
    meetings = []
    
    for i in range(num_meetings):
        meeting = SyntheticMeeting(
            duration_minutes=base_duration_minutes,
            num_users=users_per_meeting,
            start_time=start_time + timedelta(minutes=i * 5)  # Stagger starts by 5 minutes
        )
        meetings.append(meeting)
    
    scenario_config = {
        'meetings': meetings,
        'output_file': output_file
    }
    
    generator = SyntheticDataGenerator('api_calls.json')
    return generator.generate_test_scenario(scenario_config)
    
def create_extended_meeting_scenario(
    duration_hours: int = 24,
    num_users: int = 2,
    gap_hours: Optional[int] = None,
    output_file: str = 'synthetic_extended.json'
) -> str:
    """Create a scenario with an extended meeting duration.
    
    Args:
        duration_hours: Total meeting duration in hours
        num_users: Number of users in the meeting
        gap_hours: Optional gap duration to simulate meeting break
        output_file: Path to save generated HAR file
        
    Returns:
        Path to generated HAR file
    """
    start_time = datetime.now()
    meetings = []
    
    if gap_hours:
        # Split into two sessions
        first_duration = duration_hours // 2
        second_duration = duration_hours - first_duration
        
        # First session
        meetings.append(SyntheticMeeting(
            duration_minutes=first_duration * 60,
            num_users=num_users,
            start_time=start_time
        ))
        
        # Second session after gap
        meetings.append(SyntheticMeeting(
            duration_minutes=second_duration * 60,
            num_users=num_users,
            start_time=start_time + timedelta(hours=first_duration + gap_hours),
            meeting_id=meetings[0].meeting_id  # Use same meeting ID
        ))
    else:
        # Single long session
        meetings.append(SyntheticMeeting(
            duration_minutes=duration_hours * 60,
            num_users=num_users,
            start_time=start_time
        ))
    
    scenario_config = {
        'meetings': meetings,
        'output_file': output_file
    }
    
    generator = SyntheticDataGenerator('api_calls.json')
    return generator.generate_test_scenario(scenario_config) 