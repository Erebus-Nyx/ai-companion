# LLM API Reference
*AI Companion Project - Enhanced LLM API Documentation with Personality System*

## Overview

This document provides comprehensive API reference for the Enhanced LLM Handler, including the new **personality and emotional intelligence features** implemented on June 10, 2025.

## 🎭 **Enhanced Features**

### New Personality Capabilities
- **Emotional Expression**: Responses include emotion tags (*excited*, *empathetic*, *curious*)
- **Proactive Behavior**: AI asks follow-up questions and drives conversations
- **Relationship Building**: Dynamic bonding system with progressive interaction levels
- **Personalization**: Name usage and memory-based personal references
- **Emotional Intelligence**: Context-appropriate emotional reactions

### `EnhancedLLMHandler`

Main class for LLM operations with memory and personality integration.

#### Constructor

```python
EnhancedLLMHandler(config_path: str = "config.yaml", db_manager: Optional[DBManager] = None)
```

**Parameters:**
- `config_path` (str): Path to configuration file
- `db_manager` (DBManager, optional): Database manager instance

**Example:**
```python
from models.enhanced_llm_handler import EnhancedLLMHandler
from database.db_manager import DBManager

db_manager = DBManager()
handler = EnhancedLLMHandler(db_manager=db_manager)
```

#### Methods

##### `initialize_model(force_reload: bool = False) -> bool`

Initialize the LLM model with optimal settings.

**Parameters:**
- `force_reload` (bool): Force model reinitialization

**Returns:**
- `bool`: True if successful, False otherwise

**Example:**
```python
success = handler.initialize_model()
if success:
    print("Model ready")
else:
    print("Model initialization failed")
```

##### `generate_response(user_input: str, user_id: str = "default_user", streaming: bool = False, session_id: str = "default") -> Union[str, Generator[str, None, None]]`

Generate AI response with **enhanced personality**, memory and emotional context.

**🎭 Enhanced Features:**
- **Emotional Intelligence**: Automatically detects user mood and responds appropriately
- **Proactive Engagement**: Includes follow-up questions and conversation steering
- **Personality Expression**: Uses dynamic emotion tags and expressive language
- **Relationship Awareness**: Adapts response style based on bonding level

**Parameters:**
- `user_input` (str): User's message
- `user_id` (str): Unique user identifier
- `streaming` (bool): Enable streaming responses
- `session_id` (str): Session identifier for context

**Returns:**
- `str`: Complete response with emotion tags and personality (if streaming=False)
- `Generator[str, None, None]`: Token generator (if streaming=True)

**Enhanced Response Examples:**
```python
# Supportive response to stress
response = handler.generate_response(
    user_input="I'm having a tough day at work",
    user_id="user123"
)
# Output: "*empathetically* I'm sorry you're going through that. Would you like to talk about it? *supportive*"

# Celebratory response to good news
response = handler.generate_response(
    user_input="I got promoted!",
    user_id="user123"
)
# Output: "*excitedly* That's AMAZING news! Congratulations! *curious* What was the promotion for?"

# Engaging response to casual greeting
response = handler.generate_response(
    user_input="Hello!",
    user_id="user123"
)
# Output: "*warmly* Hi there! *curious* How are you doing today? What brings you here?"
```

##### `get_model_status() -> Dict[str, Any]`

Get current model status and information.

**Returns:**
- `Dict[str, Any]`: Status information

**Example:**
```python
status = handler.get_model_status()
print(f"Model loaded: {status['model_loaded']}")
print(f"Model path: {status['model_path']}")
print(f"Context length: {status['context_length']}")
```

##### `get_performance_stats() -> Dict[str, Any]`

Get performance statistics including cache metrics.

**Returns:**
- `Dict[str, Any]`: Performance statistics

**Example:**
```python
stats = handler.get_performance_stats()
print(f"Total requests: {stats['total_requests']}")
print(f"Cache hits: {stats['cache_hits']}")
print(f"Hit rate: {stats['cache_hit_rate']:.2%}")
```

##### `clear_cache(user_id: Optional[str] = None) -> int`

Clear response cache for user or globally.

**Parameters:**
- `user_id` (str, optional): Clear cache for specific user only

**Returns:**
- `int`: Number of cache entries cleared

**Example:**
```python
# Clear all cache
cleared = handler.clear_cache()

# Clear user-specific cache
cleared = handler.clear_cache(user_id="user123")
print(f"Cleared {cleared} cache entries")
```

#### Properties

##### `model_loaded: bool`
Read-only property indicating if model is loaded.

##### `max_tokens: int`
Maximum tokens to generate (default: 512).

##### `temperature: float`
Sampling temperature (default: 0.7).

##### `top_p: float`
Nucleus sampling parameter (default: 0.9).

##### `context_length: int`
Maximum context window size (default: 2048).

##### `enable_caching: bool`
Enable/disable response caching (default: True).

## REST API Endpoints

### Chat Endpoints

#### `POST /api/chat`

Basic chat endpoint for LLM interactions.

**Request:**
```json
{
    "message": "Hello, how are you?"
}
```

**Response:**
```json
{
    "response": "I'm doing well, thank you! How can I help you today?",
    "personality": {
        "friendliness": 0.8,
        "curiosity": 0.7
    },
    "timestamp": 1623456789.123
}
```

**Example:**
```javascript
fetch('/api/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message: 'Hello!'})
})
.then(response => response.json())
.then(data => console.log(data.response));
```

#### `POST /api/v1/chat`

Versioned chat endpoint (recommended for new integrations).

**Request/Response:** Same as `/api/chat`

**Example:**
```python
import requests

response = requests.post(
    'http://localhost:13443/api/v1/chat',
    json={'message': 'What is AI?'}
)
data = response.json()
print(data['response'])
```

### Memory Endpoints

#### `GET /api/v1/memory`

Inspect user memories for debugging.

**Parameters:**
- `user_id` (optional): User ID (default: "default_user")

**Response:**
```json
{
    "memories": [
        {
            "id": 1,
            "memory_type": "preference",
            "key_topic": "food",
            "value_content": "loves pizza",
            "importance_score": 0.7,
            "created_at": "2025-06-10T10:30:00",
            "access_count": 5
        }
    ],
    "count": 1
}
```

**Example:**
```bash
curl "http://localhost:13443/api/v1/memory?user_id=user123"
```

#### `GET /api/v1/memory/clusters`

Inspect memory clusters for debugging.

**Parameters:**
- `user_id` (optional): User ID (default: "default_user")

**Response:**
```json
{
    "clusters": [
        {
            "id": 1,
            "cluster_name": "work_preferences",
            "cluster_description": "User's work-related preferences",
            "memory_ids": [1, 3, 7],
            "importance_score": 0.8
        }
    ],
    "count": 1
}
```

### System Endpoints

#### `GET /status`

Get application status including LLM initialization.

**Response:**
```json
{
    "is_initializing": false,
    "initialization_progress": 100,
    "initialization_status": "Ready!",
    "system_info": {
        "tier": "medium",
        "cpu_count": 8,
        "ram_gb": 16
    }
}
```

#### `GET /api/personality`

Get current personality state.

**Response:**
```json
{
    "friendliness": 0.8,
    "curiosity": 0.7,
    "openness": 0.6,
    "emotional_stability": 0.9,
    "conscientiousness": 0.5
}
```

## WebSocket Events

### Client → Server Events

#### `chat_message`

Send chat message to AI.

**Data:**
```json
{
    "message": "Hello, how are you?"
}
```

**Example:**
```javascript
socket.emit('chat_message', {
    message: 'What is machine learning?'
});
```

#### `send_message`

Alternative chat message event.

**Data:** Same as `chat_message`

### Server → Client Events

#### `ai_response`

Receive AI response with **enhanced personality metadata**.

**Enhanced Data Structure:**
```json
{
    "user_input": "I'm feeling stressed about work",
    "response": "*empathetically* I'm sorry you're feeling that way. *supportive* Would you like to talk about what's causing the stress?",
    "timestamp": 1749587731.488,
    "personality_state": {
        "bonding_level": 2.5,
        "dominant_traits": [
            ["empathy", 0.82],
            ["friendliness", 0.8],
            ["curiosity", 0.7]
        ],
        "emotional_state": "caring",
        "energy_level": 1.0,
        "mood_stability": 0.7
    }
}
```

**New Personality Fields:**
- `bonding_level`: Current relationship strength (1.0-10.0)
- `dominant_traits`: Top 3 personality traits with values
- `emotional_state`: Current AI emotional state
- `energy_level`: AI's current energy/enthusiasm level
- `mood_stability`: Consistency of emotional responses

**Example:**
```javascript
socket.on('ai_response', (data) => {
    console.log('User:', data.user_input);
    console.log('AI:', data.response);
    
    // New personality features
    console.log('Bonding Level:', data.personality_state.bonding_level);
    console.log('Emotional State:', data.personality_state.emotional_state);
    console.log('Top Traits:', data.personality_state.dominant_traits);
});
```

#### `status_update`

Receive system status updates.

**Data:**
```json
{
    "is_initializing": false,
    "initialization_progress": 100,
    "connected_clients": 3
}
```

#### `error`

Receive error notifications.

**Data:**
```json
{
    "message": "LLM model not available"
}
```

## Data Structures

### `ConversationContext`

Container for conversation state and context.

```python
@dataclass
class ConversationContext:
    messages: List[Dict[str, str]]           # Recent conversation
    personality_traits: Dict[str, float]     # User personality
    user_memories: List[Dict[str, Any]]      # Relevant memories
    bonding_progress: Dict[str, Any]         # Relationship state
    avatar_state: Dict[str, Any]             # Avatar emotional state
    max_context_length: int = 4096           # Context limit
```

### `MemoryItem`

Individual memory record structure.

```python
@dataclass
class MemoryItem:
    id: Optional[int]           # Database ID
    memory_type: str           # Type: 'fact', 'preference', etc.
    key_topic: str             # Topic/category
    value_content: str         # Memory content
    importance_score: float    # Importance (0.0-1.0)
    created_at: datetime       # Creation timestamp
    last_accessed: datetime    # Last access time
    access_count: int          # Access frequency
```

## Configuration

### Model Configuration

```yaml
# config.yaml
llm:
  model_size: "small"          # tiny, base, small, medium, large
  max_tokens: 512              # Maximum response length
  temperature: 0.7             # Creativity (0.0-1.0)
  top_p: 0.9                  # Nucleus sampling
  context_length: 2048         # Context window
  enable_caching: true         # Response caching
  cache_ttl_hours: 24         # Cache lifetime
```

### System Optimization

```yaml
# config.yaml
optimization:
  auto_detect_hardware: true   # Automatic hardware detection
  force_cpu: false            # Force CPU-only mode
  n_threads: 0                # Thread count (0 = auto)
  use_mmap: true              # Memory mapping
  use_mlock: false            # Memory locking
```

## Error Codes

### HTTP Status Codes

- `200` - Success
- `400` - Bad Request (missing message)
- `500` - Internal Server Error
- `503` - Service Unavailable (initializing)

### Error Messages

```json
{
    "error": "System is initializing"           // 503
}
{
    "error": "No message provided"              // 400
}
{
    "error": "LLM not available"               // 503
}
{
    "error": "Database not available"          // 503
}
```

## Performance Guidelines

### Request Optimization

1. **Use Caching**: Enable response caching for production
2. **Session Management**: Use consistent session IDs
3. **Context Length**: Keep conversations reasonable length
4. **Batch Requests**: Group related requests when possible

### Memory Management

1. **Memory Cleanup**: Periodically clean old memories
2. **Importance Scoring**: Let system auto-score importance
3. **Cluster Management**: Monitor memory clustering
4. **Cache Management**: Monitor cache hit rates

### Hardware Optimization

1. **Model Selection**: Use appropriate model size for hardware
2. **GPU Acceleration**: Enable CUDA when available
3. **Thread Tuning**: Optimize thread count for CPU
4. **Memory Mapping**: Enable for better performance

## Example Integrations

### Basic Python Client

```python
import requests

class LLMClient:
    def __init__(self, base_url="http://localhost:13443"):
        self.base_url = base_url
    
    def chat(self, message):
        response = requests.post(
            f"{self.base_url}/api/v1/chat",
            json={"message": message}
        )
        return response.json()["response"]

# Usage
client = LLMClient()
response = client.chat("Hello!")
print(response)
```

### JavaScript/Node.js Client

```javascript
const io = require('socket.io-client');

class LLMClient {
    constructor(url = 'http://localhost:13443') {
        this.socket = io(url);
        this.setupEvents();
    }
    
    setupEvents() {
        this.socket.on('ai_response', (data) => {
            console.log('AI:', data.response);
        });
    }
    
    sendMessage(message) {
        this.socket.emit('chat_message', {message});
    }
}

// Usage
const client = new LLMClient();
client.sendMessage('Hello!');
```

---

For more information, see:
- [LLM Integration Guide](LLM_INTEGRATION_GUIDE.md)
- [LLM Status Report](LLM_STATUS_REPORT.md)
- [Enhanced VAD Documentation](ENHANCED_VAD_README.md)
