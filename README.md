# Mock Extension

This mock extension simulates the behavior of the Chrome extension by sending API calls to the Streamqueue service. It focuses specifically on the extension endpoints and uses UserTokenAuth for authentication.

## Purpose
- Simulate Chrome extension behavior for testing and development
- Send predefined API calls from `api_calls.json` to Streamqueue
- Focus on extension-specific endpoints only

## Endpoints Covered

### 1. Token Validation
- Endpoint: `GET /v1/extension/check-token`
- Purpose: Validates the user token
- Response: Returns whether the token is valid

### 2. Audio Processing
- Endpoint: `PUT /v1/extension/audio`
- Purpose: Sends audio chunks to the server
- Parameters:
  - `i`: Chunk number (integer)
  - `connection_id`: Unique connection identifier
  - `source`: Source type (default: GOOGLE_MEET)
  - `meeting_id`: Optional meeting identifier
  - `ts`: Optional user timestamp
- Body: Audio data in hex format

### 3. Speakers Data
- Endpoint: `PUT /v1/extension/speakers`
- Purpose: Sends speaker activity data
- Parameters:
  - `connection_id`: Unique connection identifier
  - `meeting_id`: Optional meeting identifier
  - `ts`: Optional user timestamp
- Body: JSON array of speaker data

## Authentication
- Uses UserTokenAuth only
- Token must be included in requests

## Data Flow
1. Read API calls from `api_calls.json`
2. Process and validate the calls
3. Send to appropriate Streamqueue endpoints
4. Handle responses

## Questions/Considerations
1. Format of `api_calls.json`:
   - How are the API calls structured?
   - What timing/sequence information is included?
   - Are there specific test scenarios defined?

2. Authentication Details:
   - How is the UserToken obtained/managed?
   - Token refresh mechanism if needed?

3. Data Handling:
   - Format of audio chunks in the mock data
   - Structure of speaker data
   - Handling of timestamps and sequencing

4. Error Scenarios:
   - How to handle failed requests
   - Retry mechanisms if needed
   - Error reporting format 