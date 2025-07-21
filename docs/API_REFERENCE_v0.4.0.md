# AI Companion API Documentation v0.5.0a

## Overview

The AI Companion API provides RESTful endpoints and WebSocket communication for interacting with an AI live2d chat featuring Live2D visual avatars, voice processing, advanced conversational AI, and RAG (Retrieval-Augmented Generation) capabilities.

**Base URL**: `http://localhost:19080`  
**API Version**: `1.0.0`  
**Application Version**: `0.5.0a`

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
  "version": "0.5.0a",
  "api_version": "1.0.0", 
  "title": "AI Companion",
  "description": "An interactive AI live2d chat with Live2D visual avatar...",
  "components": {
    "live2d": "0.5.0a",
    "vad": "0.5.0a", 
    "tts": "0.5.0a",
    "llm": "0.5.0a",
    "personality": "0.5.0a",
    "memory": "0.5.0a",
    "rag": "0.5.0a"
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

### RAG (Retrieval-Augmented Generation)

#### GET /api/rag/status
Get RAG system status and configuration.

**Response:**
```json
{
  "enabled": true,
  "vector_database": {
    "type": "chroma",
    "collection_name": "ai2d_chat_knowledge",
    "total_documents": 156
  },
  "embedding_model": "all-MiniLM-L6-v2",
  "last_sync": "2025-07-21T10:30:00Z"
}
```

#### POST /api/rag/search
Perform semantic search across conversation history.

**Request Body:**
```json
{
  "query": "machine learning discussions",
  "user_id": "user123",
  "limit": 5,
  "similarity_threshold": 0.7
}
```

**Response:**
```json
{
  "results": [
    {
      "similarity_score": 0.92,
      "conversation_id": 123,
      "user_message": "What do you think about machine learning?",
      "assistant_message": "Machine learning is fascinating! It's about...",
      "timestamp": "2025-07-20T15:30:00Z",
      "metadata": {
        "model_id": "haru",
        "emotion": "excited"
      }
    }
  ],
  "query_time": 0.045
}
```

#### POST /api/rag/context
Get relevant context for a user query.

**Request Body:**
```json
{
  "query": "tell me about our previous AI discussions",
  "user_id": "user123",
  "max_length": 2000
}
```

**Response:**
```json
{
  "context": "=== Relevant Context ===\nPrevious discussion about AI...",
  "sources_count": 3,
  "context_length": 1456
}
```

#### POST /api/rag/sync
Synchronize existing conversations with vector database.

**Request Body:**
```json
{
  "user_id": "user123",
  "force_resync": false
}
```

**Response:**
```json
{
  "synced_conversations": 42,
  "total_documents": 156,
  "sync_time": 2.34
}
```

## WebSocket Events

Connect to: `ws://localhost:19443/socket.io/`

### Client Events

- `connect` - Establish connection
- `chat_message` - Send chat message
- `audio_data` - Send audio data for processing

### Server Events

- `chat_response` - Receive AI responses with enhanced metadata
- `motion_trigger` - Live2D motion updates
- `audio_status` - Audio processing status
- `system_status` - System health updates
- `rag_update` - RAG system status changes
- `avatar_mood_change` - Avatar personality/mood updates

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

### v0.5.0a (Current)
- **NEW: RAG System Integration** - Semantic search and enhanced memory
- **Enhanced Autonomous Avatars** - Dynamic personality and contextual engagement
- **Improved Chat System** - Multi-modal communication with voice/text
- **Local Directory Structure** - Proper user data isolation (~/.local/share/ai2d_chat/)
- **Enhanced Memory System** - RAG integration with fallback to traditional search
- **Configuration Management** - Comprehensive config system with local/production modes

### v0.4.0
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
