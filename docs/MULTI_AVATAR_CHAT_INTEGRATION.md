# Multi-Avatar Chat Integration

## Overview
Enhanced the chat system to support multiple active Live2D avatars with avatar identification and cross-referencing with database information.

## Features Implemented

### 1. Frontend Multi-Avatar Chat Manager (`chat.js`)
- **AvatarChatManager Class**: Central management for multi-avatar chat functionality
- **Active Avatar Tracking**: Monitors which avatars are currently loaded and visible
- **Database Integration**: Loads avatar information from the backend API
- **Smart Avatar Selection**: Round-robin selection for multi-avatar conversations
- **Message Attribution**: Each chat message is attributed to a specific avatar
- **Chat History**: Maintains conversation history with avatar context

### 2. Backend Multi-Avatar API (`app_routes_chat.py`)
- **Enhanced Chat Endpoint**: Accepts avatar context and active avatar information
- **Avatar Database Lookup**: Cross-references with Live2D models database
- **Contextual Responses**: Builds prompts with avatar-specific information
- **Multi-Avatar Awareness**: Handles multiple active avatars in conversations

### 3. Database Extensions (`live2d_models_separated.py`)
- **get_model_info()**: Comprehensive model information retrieval
- **Motion and Expression Data**: Organized avatar capabilities
- **Chat Integration Helper**: Convenience functions for chat system

### 4. Visual Enhancements (`app.css`)
- **Avatar-Specific Styling**: Color-coded chat messages per avatar
- **Dynamic Chat Title**: Shows active avatar count and names
- **Avatar Name Display**: Clear identification of speaking avatar

### 5. HTML Integration (`live2d_pixi.html`)
- **Unified Chat System**: Delegates to enhanced chat.js functionality
- **Fallback Support**: Legacy chat mode for compatibility
- **Input ID Correction**: Consistent element naming

## Architecture

```
User Input → Chat.js (AvatarChatManager) → Backend API → Database Lookup
                ↓                              ↓              ↓
         Avatar Selection              Avatar Context    Model Info
                ↓                              ↓              ↓
         Frontend Display ← Enhanced Response ← LLM Generation
```

## Key Components

### AvatarChatManager
- Tracks active avatars from Live2D system
- Manages avatar selection for responses
- Maintains conversation history with attribution
- Handles database cross-referencing

### Enhanced Chat API
- Receives: user message, avatar_id, active_avatars, conversation_context
- Returns: response with avatar attribution and emotion data
- Integrates: avatar descriptions and motion capabilities

### Database Integration
- Retrieves avatar metadata (name, description, motions, expressions)
- Provides avatar-specific context for LLM responses
- Supports future personality system integration

## Usage

### Single Avatar Mode
- Automatically detected when only one avatar is active
- Behaves like traditional chat with avatar attribution

### Multi-Avatar Mode
- Activated when multiple avatars are loaded
- Round-robin selection (extendable for personality-based selection)
- Chat title shows active avatar count and names

### Avatar Identification
- Each message shows which avatar is speaking
- Color-coded messages per avatar (6 predefined avatars supported)
- Database-driven avatar information display

## Future Enhancements
- Personality-based avatar selection (when personality system is rebuilt)
- Emotion-driven motion triggering per avatar
- Conversation threading per avatar
- Avatar-specific memory systems

## API Endpoints

### `/api/chat` (Enhanced)
```json
POST {
    "message": "user message",
    "avatar_id": "haruka",
    "avatar_name": "Haruka", 
    "active_avatars": [...],
    "conversation_context": [...]
}
```

### `/api/live2d/models/detailed`
```json
GET → [
    {
        "model_name": "haruka",
        "description": "...",
        "motions": {...},
        "expressions": {...},
        "motion_count": 12
    }
]
```

## Configuration
- No additional configuration required
- Automatically detects active avatars from Live2D system
- Gracefully falls back to single-chat mode when no avatars active

## Compatibility
- Maintains backward compatibility with existing chat system
- Progressive enhancement - works with or without Live2D avatars
- Fallback mechanisms for API failures
