# AI Companion API Documentation v0.4.0

## Overview

The AI Companion API provides RESTful endpoints and WebSocket communication for interacting with an AI live2d chat featuring Live2D visual avatars, voice processing, and advanced conversational AI.

**Base URL**: `http://localhost:19443`  
**API Version**: `1.0.0`  
**Application Version**: `0.4.0`

## Quick Start

```bash
# Start the server
ai2d_chat server

# View API documentation
ai2d_chat api

# Check system status  
ai2d_chat status

# Get detailed version info
ai2d_chat version
```

## Authentication

Currently, no authentication is required for local deployment. All endpoints are accessible without credentials.

## Rate Limits

- **Chat**: 10 requests/minute
- **TTS**: 5 requests/minute  
- **Audio Upload**: 20 MB max file size

## Core Endpoints

### System Information

#### GET /api/system/version
Get detailed version information.

**Response:**
```json
{
  "version": "0.4.0",
  "api_version": "1.0.0", 
  "title": "AI Companion",
  "description": "An interactive AI live2d chat with Live2D visual avatar...",
  "components": {
    "live2d": "0.4.0",
    "vad": "0.4.0", 
    "tts": "0.4.0",
    "llm": "0.4.0"
  }
}
```

#### GET /api/system/status
Get system health and status information.

**Response:**
```json
{
  "status": "running",
  "uptime": 1234.56,
  "memory_usage": {...},
  "models_loaded": ["model1", "model2"]
}
```

### Chat System

#### POST /api/chat
Send a message to the AI live2d chat.

**Request Body:**
```json
{
  "message": "Hello, how are you?",
  "conversation_id": "optional-conversation-id"
}
```

**Response:**
```json
{
  "reply": "I'm doing great! How can I help you today?",
  "conversation_id": "generated-or-provided-id",
  "emotion": "happy",
  "timestamp": "2025-07-17T12:00:00Z"
}
```

### Text-to-Speech

#### POST /api/tts
Convert text to speech with emotional inflection.

**Request Body:**
```json
{
  "text": "Hello world!",
  "emotion": "excited",
  "voice": "default"
}
```

**Response:**
```json
{
  "audio_url": "/api/audio/generated/abc123.wav",
  "duration": 2.5
}
```

### Live2D Integration

#### GET /api/live2d/models
List available Live2D models.

**Response:**
```json
{
  "models": [
    {
      "name": "Hiyori",
      "path": "/models/Hiyori/",
      "motions": ["idle", "greeting", "goodbye"],
      "expressions": ["normal", "happy", "sad"]
    }
  ],
  "count": 1
}
```

#### POST /api/live2d/load
Load a specific Live2D model.

**Request Body:**
```json
{
  "model_name": "Hiyori"
}
```

#### POST /api/live2d/motion
Trigger a Live2D animation.

**Request Body:**
```json
{
  "motion_group": "idle",
  "motion_index": 0,
  "priority": 2
}
```

#### POST /api/live2d/expression
Set a Live2D facial expression.

**Request Body:**
```json
{
  "expression_id": "happy"
}
```

### Audio Processing

#### POST /api/audio/record
Control audio recording.

**Request Body:**
```json
{
  "action": "start"  // or "stop"
}
```

#### POST /api/audio/upload
Upload audio file for speech-to-text processing.

**Request Body:** Multipart form data with audio file

**Response:**
```json
{
  "transcript": "Hello world",
  "confidence": 0.95
}
```

## WebSocket Events

Connect to: `ws://localhost:19443/socket.io/`

### Client Events

- `connect` - Establish connection
- `chat_message` - Send chat message
- `audio_data` - Send audio data for processing

### Server Events

- `chat_response` - Receive AI responses
- `motion_trigger` - Live2D motion updates
- `audio_status` - Audio processing status
- `system_status` - System health updates

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Error description",
  "code": "ERROR_CODE",
  "timestamp": "2025-07-17T12:00:00Z"
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad Request
- `404` - Not Found
- `500` - Internal Server Error

## CLI Usage

```bash
# Start server with custom options
ai2d_chat server --port 8080 --dev

# View API documentation in different formats
ai2d_chat api --format json
ai2d_chat api --format yaml

# Monitor system
ai2d_chat status
```

## Version History

### v0.4.0 (Current)
- Enhanced CLI interface with comprehensive API documentation
- Improved version management and component tracking
- Updated Live2D integration with motion system
- Enhanced TTS with emotional processing

### v0.3.0
- Added WebSocket support for real-time communication
- Implemented enhanced VAD (Voice Activity Detection)
- Integrated local LLM processing

### v0.2.0
- Initial Live2D integration
- Basic chat and TTS functionality
- Core API structure

## Support

For issues and feature requests, visit: https://github.com/Erebus-Nyx/ai2d_chat/issues
