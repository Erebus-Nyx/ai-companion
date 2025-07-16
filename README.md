# AI Companion Project

## 🎉 Enhanced VAD, Embedded LLM, Personality System & Live2D Integration in Progress!

**Latest Update**: Full embedded llama.cpp integration with advanced SQLite memory system, enhanced emotional personality, AND Live2D avatar integration development with PIXI.js v8! This provides local LLM inference with intelligent conversation memory, caching, personality-aware responses, emotional intelligence, proactive interaction capabilities, and interactive animated avatars (currently debugging compatibility issues).

🎭 **NEW: Enhanced Personality System** - The AI now features emotional expression, proactive conversations, relationship building, and personalized interactions!  
🎨 **IN PROGRESS: Live2D Avatar Integration** - Interactive animated avatars with 21 models, motion controls, and PIXI.js v8 compatibility (debugging EventEmitter and model loading issues)!

📚 **See [ENHANCED_VAD_README.md](docs/ENHANCED_VAD_README.md) for complete enhanced VAD documentation**  
📚 **See [LLM_PERSONALITY_COMPLETION_REPORT.md](docs/LLM_PERSONALITY_COMPLETION_REPORT.md) for personality enhancement details**

## Project Scope & Vision

### Core Concept
Develop an AI-powered virtual companion application that provides an immersive, conversational experience through a local, self-contained system. The application creates a personal bond between the user and an animated avatar character that evolves and remembers interactions over time.

### Key Features
**Enhanced Audio Processing:**
- ✅ **Advanced VAD**: ML-based voice activity detection with pyannote.audio
- ✅ **Faster-whisper STT**: 4-10x faster speech-to-text processing
- ✅ **Multiple Performance Modes**: Lightweight, balanced, and high-accuracy
- ✅ **Smart Fallback**: Graceful degradation to basic VAD if needed
- ✅ **Noise Handling**: Superior background noise filtering and false wake-word reduction

**Web-Based Interface:**
- Horizontally split viewport design
- Left panel: Animated female avatar with expressive animations and personality
- Right panel: Chat interface with conversation history and text input field

**Multi-Modal Interaction:**
- Text-based chat with real-time message exchange
- ✅ **Enhanced Voice Activation**: Advanced wake word detection with customizable words
- Text-to-Speech (TTS) output for avatar responses
- ✅ **Optimized Speech-to-Text**: Fast, accurate voice input processing

**Local AI Processing:**
- ✅ **Embedded LLM**: llama.cpp integration for local conversation generation
- ✅ **Intelligent Memory System**: SQLite-based conversation memory with clustering and retrieval
- ✅ **Response Caching**: MD5-based caching for improved performance
- ✅ **Session Continuity**: Conversation context preservation across sessions
- ✅ **Enhanced Personality System**: Emotional intelligence and proactive interactions
- Integrated Kokoro TTS for natural speech synthesis (pending)
- No external API dependencies - fully offline capable
- ✅ **Automatic System Detection**: Hardware detection and model optimization

**🎭 Enhanced Personality & Emotional Intelligence:**
- ✅ **Emotional Expression**: Dynamic emotion tags in responses (*excited*, *empathetic*, *curious*)
- ✅ **Proactive Behavior**: AI actively asks questions and drives conversations
- ✅ **Relationship Building**: Progressive bonding system with dynamic interaction levels
- ✅ **Personalization**: Name usage and memory-based personal references
- ✅ **Empathy & Support**: Context-appropriate emotional reactions to user mood
- ✅ **Advanced Memory Management**: Automatic importance scoring and context-aware retrieval
- ✅ **Conversation Summarization**: Intelligent topic extraction and memory clustering
- ✅ **Enhanced Database Schema**: Extended SQLite with memory clusters and LLM caching
- Long-term memory retention for meaningful relationship building
- Tamagotchi-inspired bonding mechanics and character development (pending)

**🎨 Live2D Avatar Integration:**
- ✅ **PIXI.js v8 Integration**: Modern renderer with EventEmitter compatibility layer
- ✅ **21 Live2D Models**: Comprehensive model collection with motion/expression data
- ✅ **Modular Architecture**: 8 JavaScript modules for organized Live2D functionality
- ✅ **Interactive Controls**: Settings panel with model selection, motion triggers, and expressions
- ✅ **Flask API Integration**: Backend endpoints for model management and motion data
- ✅ **Responsive UI**: Panel collapse/expand with CSS transitions and canvas scaling
- 🔄 **PIXI v8 Compatibility**: EventEmitter polyfill implementation (debugging in progress)
- 🔄 **Model Loading**: Live2D model class detection and instantiation (debugging in progress)  
- 🔄 **Canvas Rendering**: PIXI application and model display framework (requires rebuild)
- 🔄 **Lipsync Integration**: TTS-synchronized mouth movements (pending model loading fix)
- 🔄 **Emotion Mapping**: Dynamic expression changes based on AI emotional state (pending model loading fix)

**Current Live2D Status:**
- 🔧 **Issues Being Resolved**: EventEmitter compatibility with cubism4.min.js, model class detection, core library initialization
- 🎯 **Next Steps**: Rebuild canvas framework and model loading system from Live2D Viewer Web foundation

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

## Usage

### Enhanced VAD Integration

The AI companion now features advanced audio processing:

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

## Configuration

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

Test the Live2D avatar system:

```bash
# Start Flask backend
cd src && python app.py

# Open Live2D test interface
# Navigate to: http://localhost:13443/static/live2d_pixi_test.html
```

**Live2D Test Features:**
- ✅ Model API endpoints (21 models available)
- ✅ Settings panel with responsive controls
- ✅ Panel collapse/expand functionality
- ✅ Flask backend integration
- 🔄 **Current Issues**: EventEmitter compatibility, model class detection, canvas rendering
- 🔧 **Known Problems**: 
  - `cubism4.min.js` EventEmitter errors
  - `PIXI.live2d` missing model classes
  - Core library initialization failures
- 🎯 **Resolution Plan**: Rebuild using Live2D Viewer Web foundation architecture

## Contributing
Contributions to the AI Companion project are welcome! Please fork the repository and submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.

## Acknowledgments
- Thanks to the contributors and the open-source community for their support and resources.
