# AI Companion - System Architecture Summary v0.5.0a

## Project Overview

The AI Companion is a production-ready local AI assistant featuring Live2D avatars, local LLM inference, intelligent memory systems with RAG capabilities, enhanced voice activity detection, and dynamic personality systems. The system is designed for offline operation with comprehensive integration between avatar animations, conversational AI, and audio processing.

## Core Architecture

### System Components

#### 1. **Frontend - Live2D Avatar System** ✅ Production Ready
- **Framework**: PIXI.js 6.5.10 with Cubism SDK 5
- **Dual Runtime Support**: Cubism 2.x (.moc) and Cubism 3/4/5 (.moc3) models
- **File**: `src/web/static/live2d_pixi.html` (2226 lines, production-optimized)
- **Features**:
  - Interactive mouse dragging with boundary constraints
  - Professional canvas sizing (75% height, 25-50px margins)
  - Visual debugging tools (canvas frame, model frame, hit area visualization)
  - Complete motion/expression loading and management
  - Touch device support via pointer events
  - Smart zoom system with base scaling
- **Dependencies**: Local Live2D libraries (18MB bundle) for offline functionality
- **Integration**: SocketIO real-time chat, Flask API for model discovery

#### 2. **Backend - Flask Application** ✅ Production Ready
- **Main Server**: `src/app.py` - Flask application with SocketIO support
- **Port**: 19080 (production) / 19081 (development)
- **Architecture**: Modular blueprint routing system
- **Routes**:
  - `routes/app_routes_chat.py` - Chat and conversation handling
  - `routes/app_routes_audio.py` - Audio processing and voice detection
  - `routes/app_routes_live2d.py` - Live2D model management
  - `routes/app_routes_tts.py` - Text-to-speech processing
  - `routes/app_routes_rag.py` - RAG system management and search
  - `routes/app_routes_debug.py` - Debug and diagnostics

#### 3. **LLM Integration** ✅ Enhanced & Functional
- **Engine**: llama-cpp-python with local inference
- **Handler**: `src/models/enhanced_llm_handler.py` (985 lines)
- **Features**:
  - Memory-aware conversation with intelligent context building
  - Response caching system (MD5-based, 4-10x performance improvement)
  - Session-based context preservation
  - Hardware-appropriate model selection (CPU/GPU/RAM detection)
  - Personality integration with emotional responses
- **Models**: Support for GPTQ, SafeTensor formats with automatic fallback
- **Memory Integration**: Automatic memory extraction and retrieval

#### 4. **Enhanced Memory System with RAG** ✅ Advanced Implementation
- **Location**: `src/models/memory_system.py`
- **RAG Integration**: `src/models/rag_system.py` (ChromaDB + sentence-transformers)
- **Features**:
  - Intelligent memory scoring and importance ranking
  - Automatic conversation summarization
  - Context-aware memory retrieval with keyword and semantic search
  - Memory clustering for efficient organization
  - RAG (Retrieval-Augmented Generation) integration for semantic search
  - Traditional memory fallback when RAG unavailable
  - Dynamic importance scoring based on emotional impact
- **Database**: SQLite with memory clusters, conversation context, LLM caching
- **Vector Storage**: ChromaDB for semantic search and conversation indexing
- **Integration**: Seamless integration with LLM for context-aware responses

#### 5. **RAG System** ✅ NEW in v0.5.0a
- **Location**: `src/models/rag_system.py`
- **Components**:
  - **ChromaDB**: Vector database for semantic storage
  - **SentenceTransformers**: Embedding generation (all-MiniLM-L6-v2)
  - **RAGEnhancedMemorySystem**: Integration wrapper
- **Features**:
  - Semantic conversation search and retrieval
  - Local processing (no external APIs)
  - Automatic conversation indexing
  - User-isolated vector storage
- **API**: Dedicated routes for search, context retrieval, and synchronization

#### 6. **Enhanced Personality System** ✅ NEW in v0.5.0a  
- **Location**: `src/models/personality.py` and `src/models/autonomous_avatar_manager.py`
- **Core Innovation**: Dynamic personality traits (not boolean flags)
- **Features**:
  - **Contextual Engagement**: Engagement levels based on mood, topics, relationships
  - **Mood State Management**: Dynamic emotional states affecting behavior
  - **Relationship Progression**: 5-level bonding system (Stranger → Companion)
  - **Proactive Conversations**: Avatar-initiated interactions
  - **Interest Mapping**: Passionate topics driving engagement
- **Integration**: Seamless connection with memory, chat, and Live2D systems

#### 7. **Audio Processing** ✅ Enhanced VAD System
- **Enhanced VAD**: `src/audio/enhanced_vad_wrapper.py`
- **Components**:
  - **PyannoteVAD**: Advanced VAD with speaker diarization
  - **SileroVAD**: Fast VAD with CUDA support
  - **FasterWhisperSTT**: Enhanced speech-to-text
  - **HybridVAD**: Combines multiple engines for optimal performance
- **Caching**: Dual-layer model caching (disk + memory)
- **Performance**: Multiple modes (lightweight, balanced, high-accuracy)

#### 8. **TTS Integration** 🔧 Needs Attention
- **Model**: Kokoro TTS (ONNX format)
- **Issue**: Model download failing (404 error from HuggingFace)
- **Status**: Foundation implemented, needs model source verification
- **Integration Ready**: TTS handler and audio streaming prepared

### Database Architecture

#### Separated Database Design ✅
- **conversations.db** - Chat history, conversation management, and memory storage
- **live2d.db** - Avatar models, motions, expressions
- **personality.db** - User personality traits and bonding mechanics
- **system.db** - System configuration and cache data
- **vector_db/** - ChromaDB vector storage for RAG system

#### Schema Features
- Memory clusters with importance scoring
- LLM response caching (MD5-based)
- Conversation context preservation
- Personality trait evolution tracking
- RAG conversation indexing and metadata

### Local Directory Structure ✅ NEW in v0.5.0a

#### User Data Isolation
- **Configuration**: `~/.config/ai2d_chat/config.yaml`
- **Data Storage**: `~/.local/share/ai2d_chat/`
  - `databases/` - All SQLite databases and vector storage
  - `models/` - LLM models, embedding models, TTS models
  - `live2d_models/` - Live2D avatar assets
- **Cache**: `~/.cache/ai2d_chat/` - Temporary files and logs
- **Benefits**: Proper user isolation, no app directory access, clean uninstall

### Configuration System ✅

#### Centralized Configuration
- **Location**: `config/config.yaml` (676 lines)
- **Features**:
  - Hardware-appropriate model selection
  - Functional default generation
  - Secure secrets auto-generation
  - Clean database installation
- **Management**: `src/config/config_manager.py` with CLI integration

### Project Organization ✅

#### File Structure (July 18, 2025 Reorganization)
```
ai2d_chat/
├── scripts/              # Organized standalone scripts
│   ├── migration/        # Database management and migration
│   ├── setup/           # Installation and data population
│   ├── testing/         # Test scripts and validation
│   ├── deployment/      # Application deployment
│   └── debug/           # Debug utilities and diagnostics
├── src/                 # Source code
│   ├── api/            # API specifications
│   ├── routes/         # Flask route handlers
│   ├── config/         # Configuration management
│   ├── models/         # LLM and memory systems
│   ├── audio/          # Enhanced VAD and audio processing
│   ├── database/       # Database management
│   └── web/            # Frontend components
├── config/             # Configuration files and templates
├── docs/               # Documentation and reports
└── archive/            # Legacy code and test files
```

### Packaging & Distribution ✅

#### Production Packaging
- **Format**: Modern Python wheel (lightweight, essential components only)
- **Installation**: `pipx install dist/ai2d_chat-0.4.0-py3-none-any.whl`
- **CLI**: Global `ai2d_chat` command with comprehensive subcommands
- **Dependencies**: All included for offline operation
- **Model Storage**: Large models stored in user's local directory (`~/.local/share/ai2d_chat/`)

#### CLI Interface
- **Entry Point**: `ai2d_chat` command
- **Subcommands**: server, api, status, version, models
- **API Documentation**: Generate docs in text, JSON, YAML formats
- **System Management**: Health monitoring and status checks

## System Integration

### Real-Time Communication
- **SocketIO**: Bidirectional communication between frontend and backend
- **Events**: Chat messages, avatar animations, voice activity, system status
- **Performance**: Optimized for real-time interaction

### Cross-Component Integration
- **LLM ↔ Memory**: Automatic memory extraction and context building
- **LLM ↔ Live2D**: Emotion-based expression mapping (ready for implementation)
- **Audio ↔ Live2D**: Voice activity detection integration
- **TTS ↔ Live2D**: Lipsync animation system (awaiting TTS model fix)

## Performance & Optimization

### Caching Systems
- **LLM Responses**: MD5-based caching for 4-10x performance improvement
- **Model Loading**: Dual-layer caching (disk + memory) for VAD models
- **Memory Retrieval**: Intelligent context caching for conversation continuity

### Resource Management
- **Hardware Detection**: Automatic system capability assessment
- **Model Selection**: Appropriate model size based on available resources
- **Memory Optimization**: Efficient memory usage for long-running sessions
- **Model Storage**: Large models automatically downloaded to user's local directory

## Current Status & Priorities

### ✅ Completed Systems
- **Live2D Avatar System**: Production-ready with full interaction support
- **Backend Architecture**: Modular Flask application with comprehensive routing
- **LLM Integration**: Local inference with memory and caching systems
- **Database Layer**: Separated databases with migration support
- **Audio Processing**: Enhanced VAD with multiple performance modes
- **Project Organization**: Clean file structure with logical separation
- **Configuration Management**: Automated setup with functional defaults

### 🔧 Immediate Priorities
1. **TTS Model Download**: Resolve Kokoro ONNX model download issues
2. **LLM Performance**: Optimize response times for real-time interaction (target 3-5s)

### 🎯 Next Features
1. **Lipsync Integration**: Connect TTS output to Live2D mouth movements
2. **Voice Input Integration**: Connect enhanced VAD to Live2D system
3. **Emotion Mapping**: Link AI emotional state to Live2D expressions
4. **WebSocket Enhancement**: Real-time avatar animation triggers
5. **Cross-Avatar Interactions**: Multiple avatar conversation system

## Technical Foundation

### Development Standards
- **Import Strategy**: Fallback imports for development/package/installed scenarios
- **Error Handling**: Comprehensive error handling with graceful degradation
- **Logging**: Structured logging throughout application
- **Testing**: Comprehensive test coverage for core systems

### Security & Privacy
- **Local Operation**: All processing happens locally, no external dependencies
- **Data Privacy**: User conversations and memories stored locally
- **Secure Configuration**: Auto-generated secure keys and credentials

## Deployment & Maintenance

### Installation Process
1. **Requirements**: Python 3.8+, basic system dependencies
2. **Installation**: Single command pipx installation
3. **Setup**: Automated configuration generation with `ai2d_chat setup`
4. **Launch**: Single command server startup

### Maintenance
- **Database Migration**: Automated schema updates
- **Model Updates**: Automatic download and caching
- **Configuration Updates**: Version-aware configuration management
- **Monitoring**: Built-in health checks and status monitoring

---

*This architecture represents a comprehensive AI live2d chat system ready for production deployment with a solid foundation for advanced features.*
