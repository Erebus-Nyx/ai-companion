# LLM Integration Guide
*AI Companion Project - Enhanced LLM Implementation with Personality System*

## Overview

This guide covers the integration and usage of the **Enhanced LLM Handler** in the AI Companion project. The system provides local LLM inference with **advanced personality integration**, memory awareness, **emotional intelligence**, and intelligent caching.

## 🎭 **NEW: Enhanced Personality Features**

### Emotional & Interactive AI
The LLM system now includes:
- **Emotional Expression**: Dynamic emotion tags in responses (*excited*, *empathetic*, *curious*)
- **Proactive Behavior**: AI actively asks questions and drives conversations
- **Relationship Building**: Progressive bonding system with dynamic interaction levels
- **Personalization**: Name usage and memory-based personal references
- **Emotional Intelligence**: Context-appropriate emotional reactions

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                Enhanced LLM System                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ LLM Handler │  │ Memory Sys  │  │ Personality System  │  │
│  │             │  │             │  │                     │  │
│  │ + Caching   │  │ + Context   │  │ + Trait Evolution   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    SQLite Database                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │Conversations│  │   Memories  │  │    LLM Cache        │  │
│  │   + Context │  │ + Clusters  │  │ + MD5 Hashing       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Installation & Setup

### 1. Dependencies

Ensure the following dependencies are installed:

```bash
pip install llama-cpp-python
pip install sqlite3  # Usually included with Python
```

For GPU acceleration (optional):
```bash
pip install llama-cpp-python[cuda]  # For NVIDIA GPUs
```

### 2. Model Download

Models are automatically downloaded on first use:

```python
from models.enhanced_llm_handler import EnhancedLLMHandler

# Initialize handler - will auto-download appropriate model
handler = EnhancedLLMHandler()
success = handler.initialize_model()
```

### 3. Database Setup

The database is automatically initialized:

```python
from database.db_manager import DBManager

# Creates all necessary tables
db_manager = DBManager("ai_companion.db")
```

## Usage

### Basic Usage

```python
from models.enhanced_llm_handler import EnhancedLLMHandler
from database.db_manager import DBManager

# Initialize components
db_manager = DBManager()
llm_handler = EnhancedLLMHandler(db_manager=db_manager)

# Initialize model
if llm_handler.initialize_model():
    # Generate response
    response = llm_handler.generate_response(
        user_input="Hello, how are you?",
        user_id="user123"
    )
    print(f"AI: {response}")
```

### Advanced Usage with Sessions

```python
# Use session-based conversations
session_id = "conversation_001"

response = llm_handler.generate_response(
    user_input="I love pizza",
    user_id="user123",
    session_id=session_id
)

# Follow-up in same session
response2 = llm_handler.generate_response(
    user_input="What's my favorite food?",
    user_id="user123",
    session_id=session_id
)
# Will remember pizza from previous context
```

### Streaming Responses

```python
# Get streaming response for real-time display
response_generator = llm_handler.generate_response(
    user_input="Tell me a story",
    user_id="user123",
    streaming=True
)

for chunk in response_generator:
    print(chunk, end="", flush=True)
```

## API Integration

### REST API Endpoints

#### POST /api/chat
Basic chat endpoint:
```javascript
fetch('/api/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message: 'Hello!'})
})
.then(response => response.json())
.then(data => console.log(data.response));
```

#### POST /api/v1/chat
Versioned endpoint (recommended):
```javascript
fetch('/api/v1/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message: 'Hello!'})
})
.then(response => response.json())
.then(data => console.log(data.response));
```

### WebSocket Integration

```javascript
const socket = io();

// Send message
socket.emit('chat_message', {message: 'Hello!'});

// Receive response
socket.on('ai_response', (data) => {
    console.log('AI:', data.response);
    console.log('Personality:', data.personality_state);
});
```

## Memory System Integration

### Automatic Memory Creation

The system automatically extracts and stores important information:

```python
# This conversation will automatically create memories
response = llm_handler.generate_response(
    user_input="I work as a software engineer and love Python",
    user_id="user123"
)

# Memories created:
# - Type: 'fact', Content: 'works as a software engineer'
# - Type: 'preference', Content: 'loves Python programming'
```

### Manual Memory Management

```python
from models.memory_system import MemorySystem

memory_system = MemorySystem(db_manager)

# Add specific memory
memory_id = memory_system.add_memory(
    user_id="user123",
    memory_type="preference",
    content="Prefers morning conversations",
    topic="communication",
    importance="medium"
)

# Retrieve relevant memories
memories = memory_system.get_relevant_memories(
    user_id="user123",
    query="when should we talk?",
    limit=5
)
```

## Personality System Integration

### Automatic Personality Updates

```python
# Personality traits are automatically updated based on conversations
from models.personality import PersonalitySystem

personality_system = PersonalitySystem(db_manager)

# Process user input - automatically updates traits
personality_system.update_traits("I really enjoy learning new things!")

# Get current personality
traits = personality_system.get_personality_summary()
print(traits)  # {'curiosity': 0.8, 'openness': 0.7, ...}
```

### Manual Personality Management

```python
# Directly update specific traits
db_manager.update_personality_trait(
    user_id="user123",
    trait_name="friendliness",
    trait_value=0.9
)

# Get full personality profile
profile = db_manager.get_personality_profile("user123")
```

## Configuration

### Model Configuration

```python
# Configure model parameters
handler = EnhancedLLMHandler(config_path="custom_config.yaml")

# Override default settings
handler.max_tokens = 256
handler.temperature = 0.8
handler.top_p = 0.95
```

### Cache Configuration

```python
# Configure caching behavior
handler.enable_caching = True
handler.cache_ttl_hours = 48  # Cache for 48 hours

# Clear cache manually
handler._clear_expired_cache()
```

### System Optimization

```python
# Get system-specific optimizations
from utils.system_detector import SystemDetector

detector = SystemDetector()
system_info = detector.get_system_info()
optimization_flags = detector.get_optimization_flags()

print(f"System tier: {system_info['tier']}")
print(f"Recommended threads: {optimization_flags['n_threads']}")
```

## Error Handling

### Graceful Degradation

```python
try:
    response = llm_handler.generate_response(user_input, user_id)
except Exception as e:
    # Fallback response
    response = "I'm sorry, I'm having trouble right now. Please try again."
    logger.error(f"LLM error: {e}")
```

### Model Initialization Errors

```python
if not llm_handler.initialize_model():
    # Handle initialization failure
    print("LLM not available - using fallback responses")
    # Implement fallback logic
```

## Performance Optimization

### Model Selection

The system automatically selects appropriate models based on system capabilities:

- **Low-end systems**: tiny/base models (~1-2GB RAM)
- **Mid-range systems**: small/medium models (~4-8GB RAM)  
- **High-end systems**: large models (~16GB+ RAM)

### Caching Strategy

- **Input Hashing**: MD5 hashing for fast cache lookups
- **TTL Management**: Automatic cache expiration
- **Memory Efficiency**: Compressed cache storage

### Threading Optimization

- **CPU Threads**: Automatically configured based on CPU cores
- **GPU Layers**: Dynamic GPU offloading when available
- **Memory Mapping**: Efficient model loading strategies

## Monitoring & Debugging

### Status Monitoring

```python
# Get model status
status = handler.get_model_status()
print(f"Model loaded: {status['model_loaded']}")
print(f"Model path: {status['model_path']}")

# Get performance stats
stats = handler.get_performance_stats()
print(f"Cache hit rate: {stats['cache_hit_rate']}")
```

### Debug Logging

```python
import logging

# Enable debug logging
logging.getLogger('models.enhanced_llm_handler').setLevel(logging.DEBUG)

# View detailed operation logs
handler.generate_response("test", "user123")
```

### Memory Inspection

```python
# Inspect user memories via API
curl "http://localhost:13443/api/v1/memory?user_id=user123"

# Inspect memory clusters
curl "http://localhost:13443/api/v1/memory/clusters?user_id=user123"
```

## Best Practices

### 1. Session Management
- Use consistent session IDs for related conversations
- Keep sessions reasonable in length (50-100 messages)
- Clear old sessions periodically

### 2. Memory Management
- Let the system auto-create memories for natural conversations
- Use manual memory creation for important facts
- Periodically clean up old, low-importance memories

### 3. Performance
- Enable caching for production use
- Monitor cache hit rates
- Use appropriate model sizes for your hardware

### 4. Error Handling
- Always handle model initialization failures
- Implement fallback responses
- Log errors for debugging

## Troubleshooting

### Common Issues

1. **Model Download Fails**
   ```python
   # Manually download models
   from utils.model_downloader import ModelDownloader
   downloader = ModelDownloader()
   success = downloader.download_model("llm", "small")
   ```

2. **Memory Issues**
   ```python
   # Use smaller model
   handler.model_size = "tiny"
   handler.initialize_model(force_reload=True)
   ```

3. **Slow Responses**
   ```python
   # Reduce context length
   handler.context_length = 1024
   handler.max_tokens = 128
   ```

4. **Cache Issues**
   ```python
   # Clear cache
   handler.enable_caching = False
   # Or clear manually
   db_manager.cursor.execute("DELETE FROM llm_cache")
   ```

## Integration Examples

See the following files for complete integration examples:
- `src/app.py` - Flask web application integration
- `test_embedded_llm_memory.py` - Comprehensive testing
- `enhanced_vad_example.py` - Audio integration example

---

For more information, see:
- [LLM Status Report](LLM_STATUS_REPORT.md)
- [API Reference](LLM_API_REFERENCE.md)
- [Enhanced VAD Integration](ENHANCED_VAD_README.md)

## 🎭 Enhanced Personality Usage

### Emotional Response Examples

```python
# The AI will now respond with emotions and proactivity
handler = EnhancedLLMHandler()

# Happy/Excited response
response = handler.generate_response("I got promoted today!", user_id="user123")
# Expected: "*excitedly* That's AMAZING news! Congratulations! What was the promotion for?"

# Supportive/Empathetic response  
response = handler.generate_response("I'm feeling really stressed", user_id="user123")
# Expected: "*empathetically* I'm sorry you're feeling that way. Would you like to talk about it?"

# Curious/Engaging response
response = handler.generate_response("Hello", user_id="user123")
# Expected: "*warmly* Hi there! *curious* How are you doing today? What's on your mind?"
```

### Personality Configuration

```python
# Enhanced personality settings (automatically applied)
handler.temperature = 0.8  # Increased for more creative/emotional responses
handler.max_tokens = 256   # Balanced response length
handler.personality_mode = "enhanced"  # Enables emotion tags and proactive behavior
```

### Bonding System Usage

```python
# Check bonding progression
personality_data = handler.get_personality_context(user_id="user123")
bond_level = personality_data['bonding_progress']['bond_level']

if bond_level < 2:
    # Early relationship - focus on getting to know user
    print("Building initial connection...")
elif bond_level < 5:
    # Growing friendship - deeper conversations
    print("Developing friendship...")
else:
    # Close relationship - intimate support and understanding
    print("Close relationship established...")
```
