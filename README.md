# Voice Chat Assistant Backend

## Overview
This repository contains a Django REST API backend for a voice chat assistant. It provides endpoints for:
- Health check
- Audio transcription
- Text chat with OpenAI
- Combined voice chat (transcribe audio and get a chat reply)

The service uses OpenAI APIs when configured. If an OpenAI API key is not available, transcription falls back to the SpeechRecognition library where possible.

## Tech Stack
- Django 5.2
- Django REST Framework
- drf-yasg for Swagger/OpenAPI docs
- SpeechRecognition for local fallback transcription
- OpenAI Python SDK (>=1.x)

## Environment Setup

### 1) Prerequisites
- Python 3.10+ recommended
- pip
- (Optional) virtualenv

### 2) Clone and install dependencies
```
cd voice-chat-assistant-8601-8610/voice_chat_backend
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3) Configure environment variables
Create a file named .env inside voice_chat_backend/ and set the variables described below. You can base it on the example shown here.

Example .env (reference only, place this inside voice_chat_backend/.env):
```
# App runtime
DEBUG=True

# OpenAI configuration
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
OPENAI_TRANSCRIPTION_MODEL=whisper-1

# Audio upload limits and allowed types
MAX_AUDIO_FILE_MB=10
ALLOWED_AUDIO_MIME_TYPES=audio/wav,audio/x-wav,audio/mpeg,audio/mp3

# Debugging
DEBUG_TRANSCRIPTS=False
```

Notes:
- If OPENAI_API_KEY is empty or not set, OpenAI features won’t be used. Chat replies will return an informative message and transcription will use SpeechRecognition where possible.
- OPENAI_MODEL defaults to gpt-4o-mini.
- OPENAI_TRANSCRIPTION_MODEL defaults to whisper-1.
- MAX_AUDIO_FILE_MB defaults to 10 MB.
- ALLOWED_AUDIO_MIME_TYPES defaults to wav and mp3 variants.

Environment variables are loaded in config/settings.py via python-dotenv if .env exists.

### 4) Run database migrations (SQLite default)
```
python manage.py migrate
```

### 5) Start the API server (port 3001)
By default Django runs on 8000. To run on port 3001:
```
python manage.py runserver 0.0.0.0:3001
```

The API base URL in this README assumes:
- Local: http://localhost:3001

## API Documentation
- Swagger UI: http://localhost:3001/docs
- Redoc: http://localhost:3001/redoc

These routes are configured dynamically to work behind proxies and will present the live OpenAPI documentation.

## Endpoints

### Health Check
- Method: GET
- URL: /api/health/
- Response: 200 OK with {"message": "Server is up!"}

Example:
```
curl -X GET http://localhost:3001/api/health/
```

### Transcribe Audio
- Method: POST
- URL: /api/v1/transcribe/
- Content-Type: multipart/form-data
- Form fields:
  - audio: file (required) — supported common audio formats: WAV and MP3 (see ALLOWED_AUDIO_MIME_TYPES)
- Behavior:
  - If OPENAI_API_KEY is set, the service attempts to transcribe with OpenAI (model defined by OPENAI_TRANSCRIPTION_MODEL).
  - If OPENAI_API_KEY is not set, the service falls back to SpeechRecognition where possible.
  - File size and MIME type are validated against MAX_AUDIO_FILE_MB and ALLOWED_AUDIO_MIME_TYPES in settings.
  - If DEBUG_TRANSCRIPTS is True, a debug flag is added to the response.

Example curl (multipart upload):
```
curl -X POST http://localhost:3001/api/v1/transcribe/ \
  -H "Accept: application/json" \
  -F "audio=@/path/to/sample.wav;type=audio/wav"
```

Possible responses:
- 200 OK:
```
{
  "ok": true,
  "transcript": "Hello world"
}
```
- 400 Bad Request (validation):
```
{
  "ok": false,
  "error": {
    "audio": ["Unsupported audio type 'audio/ogg'. Allowed: audio/wav, audio/x-wav, audio/mpeg, audio/mp3"]
  }
}
```
- 500 Server Error:
```
{ "ok": false, "error": "Transcription failed ..." }
```

Supported formats and size limits:
- Allowed MIME types by default: audio/wav, audio/x-wav, audio/mpeg, audio/mp3
- Max file size by default: 10 MB (configurable via MAX_AUDIO_FILE_MB)
- Note: Other formats (e.g., OGG, M4A) are not accepted by default to avoid additional dependencies (like ffmpeg). You can add them by extending ALLOWED_AUDIO_MIME_TYPES.

Fallback behavior when OPENAI_API_KEY is missing:
- Transcription: Falls back to SpeechRecognition (may have accuracy/format limitations and may require compatible audio content).
- Chat: Will return a message indicating OpenAI is not configured.

### Chat
- Method: POST
- URL: /api/v1/chat/
- Content-Type: application/json
- Body:
  - message (string, required)
  - context (string, optional)
- Behavior:
  - Uses OpenAI Chat Completions if OPENAI_API_KEY is set.
  - If no API key is set, reply will indicate that OpenAI is not configured.

Example curl:
```
curl -X POST http://localhost:3001/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello! Can you help me?",
    "context": "You are a helpful assistant."
  }'
```

Example success response:
```
{
  "ok": true,
  "reply": "Hi! How can I help you today?"
}
```

Example when no OPENAI_API_KEY is set:
```
{
  "ok": true,
  "reply": "OpenAI is not configured. Please set OPENAI_API_KEY to enable chat replies."
}
```

### Voice Chat (Transcribe + Chat)
- Method: POST
- URL: /api/v1/voice-chat/
- Content-Type: multipart/form-data
- Form fields:
  - audio: file (required) — supported types and size as per Transcribe Audio endpoint
- Behavior:
  - Transcribes the uploaded audio then uses the transcript as the chat message.
  - If transcription fails, the request returns an error.
  - If OPENAI_API_KEY is missing, chat reply will contain the informative message about missing configuration.

Example curl:
```
curl -X POST http://localhost:3001/api/v1/voice-chat/ \
  -H "Accept: application/json" \
  -F "audio=@/path/to/sample.mp3;type=audio/mpeg"
```

Example success response:
```
{
  "ok": true,
  "transcript": "What is the weather today?",
  "reply": "The weather looks sunny with a high of 75°F."
}
```

## Configuration Details

### Environment Variables
- OPENAI_API_KEY
  - Description: API key for OpenAI. If empty/missing, chat returns a message indicating OpenAI is not configured and transcription falls back to SpeechRecognition.
  - Default: "" (empty)
- OPENAI_MODEL
  - Description: Model for chat completions.
  - Default: gpt-4o-mini
- OPENAI_TRANSCRIPTION_MODEL
  - Description: Model for OpenAI transcription.
  - Default: whisper-1
- MAX_AUDIO_FILE_MB
  - Description: Maximum allowed audio file size in MB.
  - Default: 10
- ALLOWED_AUDIO_MIME_TYPES
  - Description: Comma-separated list of allowed audio MIME types.
  - Default: audio/wav,audio/x-wav,audio/mpeg,audio/mp3
- DEBUG_TRANSCRIPTS
  - Description: When True, transcription responses include a "debug": true flag.
  - Default: False
- DEBUG
  - Description: Django debug flag.
  - Default: True for local development.

### Limitations and Notes
- Only WAV and MP3 are allowed by default. Extend ALLOWED_AUDIO_MIME_TYPES if you need more formats and ensure required system dependencies are installed.
- Large files over MAX_AUDIO_FILE_MB will be rejected.
- SpeechRecognition fallback may not match the quality or features of OpenAI transcription and may have compatibility limits with certain audio encodings.

## Run Tests
```
python manage.py test
```

## Project Structure (key parts)
- voice_chat_backend/config/settings.py — environment variables and Django config
- voice_chat_backend/config/urls.py — mounts /api and API documentation routes
- voice_chat_backend/api/urls.py — API endpoints under /api/
- voice_chat_backend/api/views.py — endpoint implementations
- voice_chat_backend/api/serializers.py — request validations
- voice_chat_backend/api/services/chat.py — chat integration with OpenAI
- voice_chat_backend/api/utils/audio.py — audio temp file handling
- voice_chat_backend/requirements.txt — Python dependencies

## License
This project is intended for demonstration and internal development purposes.

