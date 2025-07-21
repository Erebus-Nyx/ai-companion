# AI Companion Project v0.5.0a

🎉 **NEW in v0.5.0a: RAG System & Dynamic Personality!** 🎉

This project is now in **alpha** with production-ready features and comprehensive integration however due to still being in development,  may contain bugs that break functionality. 

## 📚 **Key Documentation**
- **[📋 TODO.md](TODO.md)** - Current development status, priorities, and roadmap
- **[🏗️ ARCHITECTURE_SUMMARY.md](docs/ARCHITECTURE_SUMMARY.md)** - Comprehensive system architecture and implementation details
- **[🧠 RAG_SYSTEM_SUMMARY_v0.5.0a.md](docs/RAG_SYSTEM_SUMMARY_v0.5.0a.md)** - RAG implementation and semantic search capabilities
- **[🎭 AUTONOMOUS_AVATAR_SYSTEM_v0.5.0a.md](docs/AUTONOMOUS_AVATAR_SYSTEM_v0.5.0a.md)** - Dynamic personality and autonomous conversation system
- **[💬 CHAT_SYSTEM_SUMMARY_v0.5.0a.md](docs/CHAT_SYSTEM_SUMMARY_v0.5.0a.md)** - Real-time chat and multi-modal communication

## 🎉 Enhanced Personality, RAG System & Complete Live2D Integration!

🧠 **NEW: RAG System** - Semantic search and intelligent memory retrieval using ChromaDB and sentence-transformers!  
🎭 **NEW: Dynamic Personality System** - Contextual engagement, mood-based interactions, and truly autonomous avatars!  
💬 **Enhanced Chat System** - Multi-modal communication with voice, text, and real-time WebSocket integration!  
🎨 **Complete Live2D System** - Interactive animated avatars with advanced features including mouse dragging, smart scaling, visual debugging, and comprehensive UI integration!

📚 **See [ENHANCED_VAD_README.md](docs/ENHANCED_VAD_README.md) for complete enhanced VAD documentation**  
📚 **See [LLM_PERSONALITY_COMPLETION_REPORT.md](docs/LLM_PERSONALITY_COMPLETION_REPORT.md) for personality enhancement details**
📚 **See [EMOTION_TO_lIVE2D_INTEGRATION_README.md](docs/EMOTION_TO_lIVE2D_INTEGRATION_README.md) for complete integration of live2d and emotion documentation**
📚 **See [EMOTIONAL_TTS_INTEGRATION_REPORT.md](docs/EMOTIONAL_TTS_INTEGRATION_REPORT.md) for emotion integration with TTS details**  

## Project Scope & Vision

### Core Concept
Develop an AI-powered virtual companion application that provides an immersive, conversational experience through a local, self-contained system. The application creates a personal bond between the user and an animated avatar character that evolves and remembers interactions over time.

### Key Features

**🧠 RAG (Retrieval-Augmented Generation) System:**
- ✅ **Semantic Search**: ChromaDB vector database for intelligent conversation retrieval
- ✅ **Local Processing**: sentence-transformers embedding generation (no external APIs)
- ✅ **Context Enhancement**: RAG-powered memory system with traditional fallback
- ✅ **User Privacy**: All processing happens locally with encrypted storage
- ✅ **API Integration**: Dedicated endpoints for search, context, and synchronization
- ✅ **Performance Optimized**: Sub-second search across thousands of conversations

**🎭 Dynamic Personality & Autonomous Interaction:**
- ✅ **Contextual Engagement**: Dynamic personality traits based on mood, topics, and relationships
- ✅ **Autonomous Conversations**: Avatar-initiated interactions with smart conversation starters
- ✅ **Relationship Progression**: 5-level bonding system (Stranger → Companion)
- ✅ **Mood State Management**: Complex emotional states affecting behavior and responses
- ✅ **Proactive Behavior**: AI actively asks questions and drives meaningful conversations
- ✅ **Multi-Avatar Coordination**: Independent personalities with shared awareness
- ✅ **Emotional Intelligence**: Empathy detection, supportive responses, and celebration sharing

**🌐 Web-Based Interface:**
- ✅ **Flask Web Application**: Production-ready server with modular blueprint routing
- ✅ **Real-time Communication**: WebSocket-based interface for instant messaging
- ✅ **Interactive Live2D Avatars**: Complete avatar system with mouse interaction and controls
- ✅ **Professional UI**: Responsive design with Vue.js-ready components
- ✅ **Multi-Avatar Support**: Independent avatar conversations with personality switching
- ✅ **Debug Interface**: Comprehensive testing and diagnostic tools
- ✅ **API Integration**: RESTful endpoints for all system components
- ✅ **Mobile Responsive**: Optimized for desktop, tablet, and mobile devices

**Enhanced Audio Processing:**
- ✅ **Advanced VAD**: ML-based voice activity detection with Silero VAD and both pyannote segmentation and speaker diarization.
- ✅ **Faster-whisper STT**: 4-10x faster speech-to-text processing
- ✅ **Multiple Performance Modes**: Lightweight, balanced, and high-accuracy
- ✅ **Smart Fallback**: Graceful degradation to basic VAD if needed
- ✅ **Noise Handling**: Superior background noise filtering and false wake-word reduction

**Multi-Modal Interaction:**
- ✅ **Enhanced Voice Activation**: Advanced wake word detection with customizable words
- ✅ **Optimized Speech-to-Text**: Fast, accurate voice input processing
- 🔄 Text-based chat with real-time message exchange between multiple avatars
- 🔄 Text-to-Speech (TTS) output for avatar responses with unique character settings

**Local AI Processing:**
- ✅ **Embedded LLM**: llama.cpp integration for local conversation generation
- ✅ **Intelligent Memory System**: SQLite-based conversation memory with clustering and retrieval
- ✅ **Response Caching**: MD5-based caching for improved performance
- ✅ **Session Continuity**: Conversation context preservation across sessions
- ✅ **Enhanced Personality System**: Emotional intelligence and proactive interactions
- ✅ **No external API dependencies** - internet required for initial install but is fully offline capable
- ✅ **Automatic System Detection**: Hardware detection and model optimization
- ✅ **RAG Integration**: Semantic search for long-term memory retention
- 🔄 Integrated Kokoro TTS for natural speech synthesis (pending)

**💬 Enhanced Chat & Communication System:**
- ✅ **Real-time WebSocket Communication**: Instant messaging with live updates
- ✅ **Multi-modal Input/Output**: Seamless voice and text interaction
- ✅ **Context-Aware Responses**: Memory and RAG-enhanced conversation context
- ✅ **Performance Optimization**: Response caching and efficient processing
- ✅ **Multi-Avatar Support**: Independent conversations with multiple avatars
- ✅ **Conversation History**: Comprehensive chat history with search capabilities

**🎭 Enhanced Personality & Emotional Intelligence:**
- ✅ **Emotional Expression**: Dynamic emotion tags in responses (*excited*, *empathetic*, *curious*)
- ✅ **Proactive Behavior**: AI actively asks questions and drives conversations
- ✅ **Relationship Building**: Progressive bonding system with dynamic interaction levels
- ✅ **Personalization**: Name usage and memory-based personal references
- ✅ **Empathy & Support**: Context-appropriate emotional reactions to user mood
- ✅ **Advanced Memory Management**: Automatic importance scoring and context-aware retrieval
- ✅ **Conversation Summarization**: Intelligent topic extraction and memory clustering
- ✅ **Enhanced Database Schema**: Extended SQLite with memory clusters and LLM caching
- ✅ **RAG Implementation**: Semantic memory search with ChromaDB and sentence-transformers
- ✅ **Local Directory Structure**: Proper user data isolation (~/.local/share/ai2d_chat/)
- 🔄 Memory and emotions unique to each avatar (ability to backup and restore to different model)
- 🔄 Interaction with multiple avatars who have different personalities simultaneously
- 🔄 Avatars can interact with each other without dependance on user input.
- 🔄 Tamagotchi-inspired bonding mechanics and character development

**🎨 Live2D Avatar System:**
- ✅ **Dual Runtime Architecture**: Complete support for all Live2D formats
  - ✅ **Cubism 2.x Support**: Legacy .moc models via Live2D v2 Bundle
  - ✅ **Cubism 3/4/5 Support**: Modern .moc3 models via Cubism 5 Core
  - ✅ **Backward Compatibility**: Unified system handles all model generations
- ✅ **PIXI.js 6.5.10 Integration**: Optimized renderer with proper EventEmitter compatibility
- ✅ **Clean Architecture**: Organized file structure in dist/ folder
  - ✅ **PIXI.js**: Local installation (460KB) in dist/pixi-6.5.10.min.js
  - ✅ **Live2D v2 Bundle**: Complete framework (474KB) in dist/live2d_bundle.js
  - ✅ **Cubism 5 Core**: Latest SDK (207KB) in dist/CubismSdkForWeb-5-r.4/Core/
- ✅ **Flask API Integration**: Backend endpoints for model management and motion data
- ✅ **Professional Canvas**: Responsive design with proper aspect ratio handling
- ✅ **Future-Proof Design**: Ready for new Cubism 5 features and enhancements
- 🔄 TTS-synchronized mouth movements
- 🔄 Dynamic expression changes based on AI emotional state
- 🔄 Integration of interaction and mouse control with model

**Cross-Platform Deployment:**
- Global installation via pipx package manager
- Automatic hardware detection and model selection
- Optimized for Raspberry Pi 5 with touchscreen support
- Scalable across Windows, Linux, and macOS platforms

### Target Experience
Users will feel like they're having genuine conversations with a living character who remembers their preferences, interests, and shared experiences. The avatar serves as both a visual representation of the AI's responses and an evolving companion that grows more personalized over time.

### Technical Architecture
- **Frontend:** Responsive web UI with WebSocket real-time communication
- **Backend:** Python-based server with embedded AI models
- **Storage:** Local SQLite database for conversation and personality data
- **Audio:** Real-time voice processing with wake word detection
- **Deployment:** Self-contained application with automatic dependency management


## Installation

### Quick Start with Enhanced VAD

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Test Enhanced VAD Configuration**:
   ```bash
   python3 test_config_only.py
   ```

3. **Run Enhanced VAD Demo**:
   ```bash
   python3 enhanced_vad_example.py
   ```

### Standard Installation

To install the AI Companion application, follow these steps:

1. Ensure you have Python installed on your system.
2. Use `pipx` to install the application globally:
   ```
   pipx install .
   ```
3. The application will automatically detect your system configuration and download the appropriate models.

### Manual Installation

If you prefer manual setup:

```bash
# Install Python dependencies
poetry install

# Setup Live2D Viewer Web (optional)
python scripts/setup_live2d.py

# Initialize databases
python -c "from src.database.live2d_models_separated import initialize_live2d_database; initialize_live2d_database()"
```

## Running the Application

```bash
# Activate virtual environment
poetry shell

# Start the AI Companion
python src/app.py
```

Access the application at `http://localhost:5000`

## Usage

### Enhanced VAD Integration

The AI live2d chat now features advanced audio processing:

```python
from src.audio import create_audio_pipeline_from_config

# Create enhanced audio pipeline
pipeline = create_audio_pipeline_from_config("config.yaml")

# Setup callbacks
pipeline.add_event_callback('transcription_ready', on_speech_transcribed)
pipeline.add_event_callback('wake_word_detected', on_wake_word)

# Start processing
pipeline.start()
```

### Standard Usage

1. Launch the application:
   ```
   python src/main.py
   ```
2. Open your web browser and navigate to `http://localhost:13773` to access the web UI.
3. Interact with the avatar through text or voice input.

## Live2D Integration

The AI Companion uses [Live2D Viewer Web](https://github.com/guansss/live2d-viewer-web) as the foundation for avatar interaction.

### Adding Live2D Models

1. Place Live2D model folders in `models/live2d/`
2. Models should contain `.model3.json` files and associated assets
3. The system will automatically detect and make them available

### Live2D Features

- **Interactive Avatar** - Mouse dragging, zoom controls, hit area detection
- **Motion System** - Built-in motion and expression management
- **Lipsync Integration** - Synchronized mouth movement with TTS
- **Professional UI** - Vue.js + Vuetify interface with model editor

## Configuration

Edit `config.json` to customize settings:

```json
{
  "live2d": {
    "enabled": true,
    "auto_setup": true,
    "integration_mode": "embedded"
  },
  "ai": {
    "model_path": "models/llm",
    "memory_enabled": true
  }
}
```

### Enhanced VAD Settings

The enhanced VAD system is configured in `config.yaml`:

```yaml
voice_detection:
  enhanced_vad:
    enabled: true
    mode: "lightweight"  # lightweight, balanced, high_accuracy
    fallback_to_basic: true
    vad_model: "pyannote/segmentation-3.0"
    stt_model: "small"
    # ... additional settings
```

### General Settings

The application settings can be modified in the `config.yaml` file. This includes model paths and user preferences.

## Dependencies

### Enhanced VAD Dependencies

The enhanced VAD system requires additional dependencies:
- `faster-whisper>=0.10.0` - Optimized speech-to-text
- `pyannote.audio>=3.1.0` - ML-based voice activity detection
- `pyannote.core>=5.0.0` - Core audio processing
- `pyannote.database>=5.0.0` - Audio database management
- `pyannote.metrics>=3.2.0` - Performance metrics

### Standard Dependencies

The required dependencies for the project are listed in the `requirements.txt` file. Ensure all dependencies are installed before running the application.

## Enhanced VAD Performance

| Mode | Speed | Accuracy | Memory | Use Case |
|------|-------|----------|---------|----------|
| Lightweight | Fastest | Good | 244MB | Real-time, low-resource |
| Balanced | Medium | Better | 769MB | General purpose |
| High Accuracy | Slower | Highest | 1550MB | Maximum quality |

## Project Structure

```
src/
├── audio/
│   ├── enhanced_vad.py              # ✅ Core enhanced VAD implementation
│   ├── enhanced_audio_pipeline.py   # ✅ Integration wrapper
│   ├── config_loader.py            # ✅ Configuration management
│   ├── audio_pipeline.py           # Basic audio pipeline
│   ├── voice_detection.py          # WebRTC VAD (fallback)
│   └── speech_to_text.py           # Multi-engine STT
├── database/                        # Data persistence
│   └── live2d_models_separated.py  # ✅ Live2D model management
├── models/                          # AI model handlers
├── utils/                          # Utilities
└── web/                            # Web interface
    ├── static/
    │   ├── assets/                  # ✅ 21 Live2D models with motions/expressions
    │   ├── css/
    │   │   └── live2d_test.css      # ✅ Live2D interface styling
    │   ├── js/
    │   │   ├── live2d_config.js     # ✅ Live2D configuration
    │   │   ├── live2d_core.js       # ✅ Core Live2D functionality
    │   │   ├── live2d_model_manager.js # ✅ Model loading and management
    │   │   ├── live2d_motion_manager.js # ✅ Motion and expression handling
    │   │   ├── live2d_ui_controller.js # ✅ UI controls and interactions
    │   │   ├── live2d_simple_fix.js # ✅ PIXI v8 compatibility fixes
    │   │   └── live2d_*.js          # ✅ Modular Live2D system (8 modules)
    │   └── live2d_pixi_test.html    # ✅ Live2D testing interface
    └── templates/
```

## Testing

### Enhanced VAD Tests

Run the enhanced VAD tests:

```bash
# Configuration validation
python3 test_config_only.py

# Full integration test (requires dependencies)
python3 test_enhanced_vad.py

# Integration example
python3 enhanced_vad_example.py
```

### Live2D Integration Tests

Test the complete Live2D avatar system:

```bash
# Start Flask backend
cd src && python app.py

# Open Live2D test interface
# Navigate to: http://localhost:19443/static/live2d_pixi.html
```

**Live2D Test Features:**
- ✅ **Complete Production System**: All Live2D functionality implemented and working
- ✅ **21 Live2D Models**: Full model collection with motion/expression data
- ✅ **Mouse Interaction**: Drag models with boundary constraints
- ✅ **Smart Scaling**: Professional canvas sizing with 25-50px margins and 75% height
- ✅ **Visual Debugging**: Canvas frame, model frame, and hit area visualization toggles
- ✅ **Motion/Expression Loading**: Automated loading of all model animations
- ✅ **UI Integration**: Comprehensive controls with zoom, toggles, and model selection
- ✅ **Flask API Integration**: Backend endpoints for model management
- ✅ **Dual Architecture**: Support for both Cubism 2.x and modern models
- ✅ **Professional Canvas**: Responsive design with proper aspect ratio handling
- 🎯 **Ready for Integration**: Lipsync and emotion mapping can now be implemented

## Contributing
Contributions to the AI Companion project are welcome! Please fork the repository and submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.

## Acknowledgments
- Thanks to the contributors and the open-source community for their support and resources.
