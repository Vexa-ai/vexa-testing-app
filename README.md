# Testing Application

## Overview

The Testing Application is a critical component for end-to-end testing of the real-time meeting transcription system. It simulates a Chrome extension that captures and streams audio from virtual meetings (Google Meet, Zoom, Teams) to the transcription pipeline.

## Current State and Objectives

### Current State
- The application is being developed to generate synthetic test data based on real API call patterns
- Template data is loaded from HAR files containing recorded API calls
- Currently debugging issues with loading and processing template data:
  - Successfully loading HAR JSON data
  - Processing 3514 entries (814 audio, 896 speaker)
  - Encountering issues with extracting valid audio-speaker patterns

### Current Objectives
1. Debug Template Data Loading:
   - Fix issues with extracting content from HAR entries
   - Properly parse audio and speaker data
   - Establish valid audio-speaker patterns
2. Implement Data Validation:
   - Verify content structure in HAR entries
   - Validate audio chunk sequences
   - Ensure proper speaker state transitions

## System Architecture

The system consists of three main microservices:

### 1. Dashboard (Engine)
- Central service for user management and transcript storage
- Handles user authentication and token management
- Stores transcripts in PostgreSQL with speaker mapping
- Provides API endpoints for transcript retrieval and sharing
- Manages access control for transcripts

### 2. Audio Service
- Receives audio streams and speaker data from extensions
- Validates user tokens against Dashboard
- Processes audio chunks for transcription
- Maps transcripts to speakers based on timing
- Posts processed transcripts back to Dashboard

### 3. Testing Application (This Service)
- Simulates Chrome extension behavior
- Replays recorded API calls for testing
- Validates end-to-end data flow
- Measures system performance
- Generates synthetic test data based on patterns

## Data Flow

1. User Registration:
   ```
   Extension -> Dashboard:
   POST /auth/submit_token
   - Registers user and gets authentication token
   ```

2. Audio Streaming:
   ```
   Extension -> Audio Service:
   PUT /extension/audio
   - Streams audio chunks with auth token
   PUT /extension/speakers
   - Updates speaker activity data
   ```

3. Transcript Processing:
   ```
   Audio Service -> Dashboard:
   POST /api/transcripts/segments/{content_id}
   - Posts processed transcripts with speaker mapping
   ```

4. Transcript Retrieval:
   ```
   Extension -> Dashboard:
   GET /api/transcripts/segments/{content_id}
   - Retrieves transcripts with access control
   ```

## Components

### Authentication Module (`src/auth.py`)
- Handles user registration through Dashboard API
- Manages authentication tokens
- Validates token access

### Audio Replay Module (`src/replay.py`)
- Replays recorded API calls from HAR files
- Uses authentication token for streaming
- Tracks meeting IDs and timing

### Synthetic Data Generator (`src/synthetic.py`)
- Generates test data based on real patterns
- Creates various test scenarios
- Validates generated data integrity
- Currently being debugged for template loading

### Test Runner (`src/test_runner.py`)
- Coordinates test execution flow
- Measures processing latency
- Validates transcript availability

## Configuration

Environment variables required:

```
# Dashboard API
DASHBOARD_API_URL=https://main_dmitry.dev.vexa.ai

# Audio Service
STREAMQUEUE_API_URL=http://localhost:8001

# Authentication
USER_TOKEN=<auth_token>
SERVICE_TOKEN=<service_token>

# Test Settings
MAX_TRANSCRIPT_WAIT_TIME=30  # seconds
TRANSCRIPT_POLL_INTERVAL=2   # seconds
```

## Usage

1. Set up environment:
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Configure environment variables
   cp .env.example .env
   # Edit .env with your settings
   ```

2. Run tests:
   ```bash
   python main.py
   ```

## Monitoring

The application tracks several metrics:

1. Timing Measurements:
   - Audio streaming duration
   - Time to first transcript
   - Total processing latency

2. Success Criteria:
   - User registration success
   - Audio chunk delivery
   - Transcript availability
   - Content accuracy

## Development

### Adding New Tests

1. Record API calls:
   - Use browser dev tools to capture HAR file
   - Save to `api_calls.json`

2. Implement test cases:
   ```python
   async def test_transcript_flow():
       # Register user
       auth_client = AuthClient(DASHBOARD_API_URL)
       token = await auth_client.register_user()
       
       # Stream audio
       replay = ApiReplay('api_calls.json')
       await replay.replay_calls()
       
       # Verify transcripts
       dashboard_client = DashboardClient(token)
       transcripts = await dashboard_client.wait_for_transcripts(
           meeting_id,
           max_wait_time=30
       )
   ```

## Advanced Testing Scenarios

### 1. Multi-User Meeting Testing
- Multiple users streaming audio from same meeting
- Concurrent speaker detection and mapping
- Audio segment selection and processing validation
- Speaker overlap handling

### 2. Scale Testing
- Multiple concurrent meetings
- High volume of audio streams
- System performance under load
- Resource utilization monitoring

### 3. Edge Cases
```
a) Silent Periods:
   - Meetings with extended silence
   - Validation of speaker detection after silence
   - Proper handling of audio gaps

b) Meeting Continuity:
   - Multi-day meetings
   - Connection breaks and resumptions
   - Long-term session management
   - Timestamp consistency across breaks

c) Speaker Patterns:
   - Rapid speaker switches
   - Multiple simultaneous speakers
   - Speaker identification consistency
```

## Data Manipulation Framework

### 1. Source Data
- Original `api_calls.json` contains baseline meeting data
- Two speakers, single user configuration
- Reference for timing and data structure
- Currently being debugged for content extraction

### 2. Data Transformation
```python
class DataTransformer:
    def __init__(self, source_file: str):
        self.source_data = self.load_json(source_file)
        
    def create_multi_user_meeting(self, num_users: int):
        """Generate multi-user version of meeting"""
        
    def add_silence_period(self, duration_sec: int):
        """Insert silence period in meeting"""
        
    def split_meeting(self, gap_hours: int):
        """Split meeting into parts with time gap"""
```

### 3. Test Scenarios Generation
```python
class TestScenarioGenerator:
    def generate_concurrent_meetings(self, base_data, count: int):
        """Create multiple concurrent meetings"""
        
    def generate_extended_meeting(self, base_data, duration_hours: int):
        """Create long-running meeting with patterns"""
        
    def generate_edge_cases(self, base_data):
        """Generate various edge cases"""
```

## Performance Metrics

### 1. System Load Metrics
- CPU utilization per service
- Memory usage patterns
- Network bandwidth consumption
- Redis queue lengths

### 2. Processing Metrics
- Audio chunk processing time
- Speaker detection latency
- Transcription turnaround time
- System throughput (meetings/hour)

### 3. Quality Metrics
- Speaker detection accuracy
- Transcription accuracy
- System response under load
- Error rates and types

## Test Data Management

### 1. Data Generation
```bash
# Generate test scenarios
python -m src.tools.generate_scenarios \
    --source api_calls.json \
    --output test_data/ \
    --scenarios concurrent,extended,edge

# Run specific test suite
python -m src.test_runner \
    --scenario concurrent_meetings \
    --scale 10
```

### 2. Data Validation
- Verify timing consistency
- Validate audio chunk integrity
- Check speaker metadata correctness
- Ensure meeting continuity

## Error Handling

The application implements comprehensive error handling:

1. Authentication Errors:
   - Invalid tokens
   - Registration failures
   - Access denied

2. Streaming Errors:
   - Connection failures
   - Invalid audio data
   - Speaker mapping issues

3. Validation Errors:
   - Missing transcripts
   - Incorrect speaker mapping
   - Timing mismatches

## Current Debugging Focus

### Template Data Loading
1. HAR File Processing:
   - Successfully loading JSON structure
   - Identifying audio and speaker entries
   - Extracting content from entries

2. Content Parsing:
   - Validating content structure
   - Handling response body data
   - Processing audio chunks and speaker data

3. Pattern Generation:
   - Creating audio-speaker patterns
   - Validating pattern integrity
   - Ensuring proper timing alignment

### Next Steps
1. Fix content extraction from HAR entries
2. Implement proper response body parsing
3. Validate and create audio-speaker patterns
4. Add comprehensive logging for debugging
5. Implement data validation checks

