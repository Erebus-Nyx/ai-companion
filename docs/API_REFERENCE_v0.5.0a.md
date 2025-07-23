# AI Companion API Reference v0.5.0a

**Version**: 0.5.0a  
**Updated**: July 22, 2025

## Overview

The AI Companion API provides comprehensive endpoints for chat functionality, Live2D avatar management, audio processing, user management, system monitoring, and the new RAG (Retrieval-Augmented Generation) system with dynamic personality features.

## Authentication

Currently, the API uses session-based authentication. Future versions will implement token-based authentication for enhanced security.

## Base Routes

### Core Application Routes
- `GET /` - Main application interface
- `GET /live2d` - Live2D avatar interface
- `GET /live2d_models/<path:filename>` - Static Live2D model files
- `GET /api/docs` - API documentation
- `GET /docs` - Documentation interface
- `GET /api/status` - Basic application status

## API Endpoints

### 1. Chat System (`/api/chat`)

#### Send Chat Message
```http
POST /api/chat
Content-Type: application/json

{
  "message": "Hello, how are you?",
  "user_id": "user123",
  "character_id": "char456"
}
```

**Response:**
```json
{
  "success": true,
  "response": "I'm doing well, thank you for asking!",
  "emotion": "happy",
  "timestamp": "2025-07-22T10:30:00Z",
  "conversation_id": "conv789"
}
```

#### Get Chat History
```http
GET /api/chat/history?user_id=user123&limit=50&offset=0
```

**Response:**
```json
{
  "success": true,
  "messages": [
    {
      "id": 1,
      "user_message": "Hello",
      "ai_response": "Hi there!",
      "timestamp": "2025-07-22T10:30:00Z",
      "emotion": "neutral"
    }
  ],
  "total": 150,
  "has_more": true
}
```

#### Get User Chat Summary
```http
GET /api/chat/users/<user_id>/summary
```

#### V1 Chat Endpoint (Alternative)
```http
POST /api/v1/chat
```

#### Get Personality Configuration
```http
GET /api/personality
```

### 2. RAG System (`/api/rag`) - New in v0.5.0a

#### Get RAG Status
```http
GET /api/rag/status
```

**Response:**
```json
{
  "status": "active",
  "vector_db_size": 1524,
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "last_sync": "2025-07-22T10:00:00Z"
}
```

#### Semantic Search
```http
POST /api/rag/search
Content-Type: application/json

{
  "query": "Tell me about our previous conversations about AI",
  "user_id": "user123",
  "limit": 10
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "content": "We discussed AI capabilities...",
      "score": 0.89,
      "timestamp": "2025-07-20T15:30:00Z",
      "conversation_id": "conv456"
    }
  ]
}
```

#### Get Enhanced Context
```http
POST /api/rag/context
Content-Type: application/json

{
  "message": "What did we talk about yesterday?",
  "user_id": "user123",
  "context_limit": 5
}
```

#### Add Conversation to RAG
```http
POST /api/rag/add_conversation
Content-Type: application/json

{
  "user_id": "user123",
  "user_message": "Hello",
  "ai_response": "Hi there!",
  "metadata": {
    "emotion": "happy",
    "topic": "greeting"
  }
}
```

#### Sync RAG Database
```http
POST /api/rag/sync
Content-Type: application/json

{
  "user_id": "user123",
  "force_rebuild": false
}
```

#### Initialize RAG System
```http
POST /api/rag/initialize
Content-Type: application/json

{
  "rebuild_database": false
}
```

### 3. Live2D Avatar System (`/api/live2d`)

#### Get System Status
```http
GET /api/live2d/system_status
```

#### Run Comprehensive Test
```http
GET /api/live2d/comprehensive_test
```

#### Debug Path Information
```http
GET /api/live2d/debug_paths
```

#### List Available Models
```http
GET /api/live2d/models
```

**Response:**
```json
{
  "success": true,
  "models": [
    {
      "name": "Hiyori",
      "path": "/live2d_models/Hiyori/",
      "version": "cubism3",
      "has_expressions": true,
      "has_motions": true
    }
  ]
}
```

#### Get Detailed Model Information
```http
GET /api/live2d/models/detailed
```

#### Get Model Expressions
```http
GET /api/live2d/model/<model_name>/expressions
```

#### Get Model Motions
```http
GET /api/live2d/model/<model_name>/motions
GET /api/live2d/motions/<model_name>
```

#### Check Animation Compatibility
```http
GET /api/live2d/model/<model_name>/animation_compatibility
```

#### Get Model Textures
```http
GET /api/live2d/textures/<model_name>
GET /textures/<model_name>
```

#### Model Preview
```http
GET /api/live2d/preview/<model_name>
POST /api/live2d/preview/<model_name>
GET /api/live2d/preview/<model_name>/check
```

#### Debug Model Information
```http
GET /debug/model/<model_name>
```

### 4. Audio System (`/api/audio`)

#### Start Audio Processing
```http
POST /api/audio/start
Content-Type: application/json

{
  "mode": "enhanced",
  "user_id": "user123"
}
```

#### Stop Audio Processing
```http
POST /api/audio/stop
```

#### Get Audio Status
```http
GET /api/audio/status
```

**Response:**
```json
{
  "status": "active",
  "mode": "enhanced",
  "processing": true,
  "vad_active": true
}
```

### 5. Text-to-Speech (`/api/tts`)

#### Basic TTS
```http
POST /api/tts
Content-Type: application/json

{
  "text": "Hello, how are you today?",
  "voice": "default"
}
```

#### Emotional TTS - New in v0.5.0a
```http
POST /api/tts/emotional
Content-Type: application/json

{
  "text": "I'm so excited to see you!",
  "emotion": "excited",
  "intensity": 0.8,
  "voice": "default"
}
```

**Response:**
```json
{
  "success": true,
  "audio_url": "/api/audio/output/tts_12345.wav",
  "duration": 3.2,
  "emotion_applied": "excited"
}
```

### 6. User Management (`/api/users`)

#### List Users
```http
GET /api/users?limit=20&offset=0
```

#### Get Current User
```http
GET /api/users/current
```

#### Get User Profile
```http
GET /api/users/<user_id>/profile
```

#### Update User Profile
```http
PUT /api/users/<user_id>/profile
Content-Type: application/json

{
  "name": "John Doe",
  "preferences": {
    "theme": "dark",
    "language": "en"
  }
}
```

#### Create User
```http
POST /api/users
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "profile": {
    "name": "New User"
  }
}
```

#### Activate User
```http
POST /api/users/<user_id>/activate
```

#### Set Current User
```http
POST /api/users/set-current
Content-Type: application/json

{
  "user_id": "user123"
}
```

#### User Logout
```http
POST /api/users/logout
```

### 7. Character Management (`/api/characters`)

#### List Characters
```http
GET /api/characters
```

#### Get Character Details
```http
GET /api/characters/<character_id>
```

#### Update Character
```http
PUT /api/characters/<character_id>
Content-Type: application/json

{
  "name": "Updated Character",
  "personality": {
    "traits": ["friendly", "helpful"]
  }
}
```

#### Delete Character
```http
DELETE /api/characters/<character_id>
```

#### Upload Character Icon
```http
POST /api/characters/<character_id>/icon
Content-Type: multipart/form-data

{
  "icon": [file]
}
```

### 8. System Information (`/api/system`)

#### Get Version
```http
GET /api/system/version
```

**Response:**
```json
{
  "version": "0.5.0a",
  "title": "AI Companion",
  "description": "An interactive AI live2d chat with Live2D visual avatar, voice capabilities, and advanced AI integration"
}
```

#### Get System Status
```http
GET /api/system/status
```

**Response:**
```json
{
  "status": "healthy",
  "uptime": 3600,
  "memory_usage": "45%",
  "cpu_usage": "12%",
  "active_connections": 5
}
```

#### Health Check
```http
GET /api/system/health
```

#### Get Configuration
```http
GET /api/system/config
```

#### Get System Information
```http
GET /api/system/info
```

### 9. Logging System (`/api/logs`) - Enhanced in v0.5.0a

#### Get Log Viewer
```http
GET /api/logs
```

#### Submit Frontend Logs
```http
POST /api/logs/frontend
Content-Type: application/json

{
  "level": "error",
  "message": "JavaScript error occurred",
  "timestamp": "2025-07-22T10:30:00Z",
  "user_id": "user123"
}
```

#### Download Logs
```http
GET /api/logs/download/<log_type>
```

#### Get Logging Status
```http
GET /api/logs/status
```

**Response:**
```json
{
  "status": "active",
  "log_files": [
    {
      "type": "chat_activity",
      "size": "2.5MB",
      "last_modified": "2025-07-22T10:30:00Z"
    }
  ],
  "retention_policy": "5 files max"
}
```

### 10. Autonomous System (`/api/autonomous`) - New in v0.5.0a

#### Get Autonomous Status
```http
GET /api/autonomous/status
```

**Response:**
```json
{
  "enabled": true,
  "conversation_mode": "proactive",
  "engagement_level": 0.7,
  "last_interaction": "2025-07-22T10:25:00Z"
}
```

#### Enable Autonomous Mode
```http
POST /api/autonomous/enable
Content-Type: application/json

{
  "mode": "proactive",
  "engagement_threshold": 0.6
}
```

#### Disable Autonomous Mode
```http
POST /api/autonomous/disable
```

### 11. Debug Endpoints

#### Get Personality (Debug)
```http
GET /get_personality
```

## WebSocket Events

The application uses Socket.IO for real-time communication:

### Client → Server Events
- `connect` - Client connection established
- `message` - Send chat message
- `chat_message` - Alternative chat message event
- `join_room` - Join user-specific room
- `typing_start` - User started typing
- `typing_stop` - User stopped typing

### Server → Client Events
- `response` - AI response to chat message
- `emotion_change` - Avatar emotion update
- `system_message` - System notifications
- `typing_indicator` - Show/hide typing indicator
- `autonomous_message` - AI-initiated conversation

## Error Responses

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error description",
  "code": "ERROR_CODE",
  "timestamp": "2025-07-22T10:30:00Z"
}
```

### Common Error Codes
- `INVALID_REQUEST` - Malformed request data
- `USER_NOT_FOUND` - Specified user doesn't exist
- `CHARACTER_NOT_FOUND` - Specified character doesn't exist
- `MODEL_NOT_FOUND` - Live2D model not found
- `AUDIO_ERROR` - Audio processing error
- `RAG_ERROR` - RAG system error
- `SYSTEM_ERROR` - Internal system error

## Rate Limiting

API endpoints are rate-limited to prevent abuse:
- Chat endpoints: 60 requests/minute per user
- TTS endpoints: 30 requests/minute per user
- System endpoints: 120 requests/minute per IP
- RAG search: 100 requests/minute per user

## New Features in v0.5.0a

### RAG System Integration
- Semantic search across conversation history
- Context-aware responses using vector database
- ChromaDB with sentence-transformers embedding
- User-specific conversation indexing

### Dynamic Personality System
- Contextual engagement calculation
- Mood-based response adaptation
- Relationship progression tracking
- Interest-driven conversation topics

### Enhanced Logging
- Timestamped log files with retention policy
- Frontend error reporting
- Chat activity logging
- System performance monitoring

### Autonomous Conversation
- AI-initiated interactions
- Proactive conversation starters
- Memory-based topic suggestions
- Emotional intelligence responses

## Migration from v0.4.0

### Breaking Changes
- New RAG endpoints require user_id parameter
- Personality system responses include engagement metrics
- Enhanced logging format with additional metadata

### New Required Parameters
- `user_id` now required for most chat operations
- RAG endpoints require explicit user context
- TTS emotional endpoints need emotion parameters

### Deprecated Endpoints
- Old personality endpoints replaced with enhanced versions
- Legacy chat formats deprecated in favor of RAG-enhanced responses

## Development and Testing

### Local Development
```bash
# Start development server
python -m ai2d_chat.cli setup --clean
python -m ai2d_chat.server_cli

# Run with enhanced logging
python -m ai2d_chat.server_cli --debug
```

### API Testing
```bash
# Test basic chat
curl -X POST http://localhost:19443/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "user_id": "test_user"}'

# Test RAG search
curl -X POST http://localhost:19443/api/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "previous conversations", "user_id": "test_user"}'
```

---

**Last Updated**: July 22, 2025  
**API Version**: v0.5.0a  
**Documentation Version**: 1.0.0
