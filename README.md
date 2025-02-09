# Mock Extension

This tool allows replaying captured API calls from a Chrome extension to test the StreamQueue API service. It simulates the behavior of the actual Chrome extension by replaying audio chunks and speaker data.

## Setup

1. Create a `.env` file in the root directory with the following configuration:
```env
# Streamqueue API configuration
STREAMQUEUE_URL=http://localhost:8008
USER_TOKEN=dima_token
SERVICE_TOKEN=dima_token

# Default values for replay
DEFAULT_MEETING_ID=mock-meeting
DEFAULT_CONNECTION_ID=  # Leave empty to auto-generate

# Replay timing configuration
PRESERVE_TIMING=false  # Set to false to send requests as fast as possible
TIME_SCALE=1.0  # Use values < 1.0 to speed up, > 1.0 to slow down
```

2. Place your captured API calls in `api_calls.json` in the root directory. This file should contain the recorded audio chunks and speaker data from a real extension session.

## How It Works

The mock extension performs the following operations in sequence:

1. **Cache Flushing**
   - Flushes the main Redis cache to clear any existing audio/speaker data
   - Flushes the admin Redis cache to clear any existing user tokens

2. **User Setup**
   - Adds a user token to Redis for authentication
   - This token will be used for all extension-related API calls

3. **Data Replay**
   - Reads the `api_calls.json` file
   - Replays each audio chunk and speaker data entry in sequence
   - Maintains the original connection IDs and meeting IDs
   - Can preserve original timing between calls or run at maximum speed

4. **Verification**
   - Checks the final state of connections in Redis
   - Reports the number of chunks stored for each connection

## Usage

Run the mock extension:
```bash
python main.py
```

The script will:
1. Validate environment variables
2. Clean up any existing data
3. Set up authentication
4. Replay all API calls
5. Report the final state

## API Endpoints Used

- `POST /api/v1/tools/flush-cache` - Flush main Redis cache
- `POST /api/v1/tools/flush-admin-cache` - Flush admin Redis cache
- `POST /api/v1/users/add-token` - Add user token for authentication
- `PUT /api/v1/extension/audio` - Send audio chunks
- `PUT /api/v1/extension/speakers` - Send speaker data
- `GET /api/v1/connections/list` - Get list of active connections

## Authentication

The tool uses two types of authentication:
- Service token for admin operations (flush cache, add user token)
- User token for extension operations (send audio/speaker data)

Both tokens should be configured in the `.env` file.

## Timing Control

You can control the replay timing using environment variables:
- `PRESERVE_TIMING=true` - Maintain original delays between calls
- `PRESERVE_TIMING=false` - Send requests as fast as possible
- `TIME_SCALE` - Adjust replay speed (e.g., 0.5 for 2x speed) 