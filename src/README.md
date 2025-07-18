# Source Code Organization

This directory contains the organized source code for the AI Companion project.

## Directory Structure

### Core Application Files
- `__init__.py` - Package initialization
- `__version__.py` - Version information
- `app.py` - Main Flask application
- `app_globals.py` - Global application state
- `cli.py` - Command-line interface
- `main.py` - Application entry point
- `socketio_handlers.py` - WebSocket event handlers

### `/api/`
API specifications and documentation:
- `api_spec.py` - Main OpenAPI specification
- `api_spec_fixed.py` - Fixed API specification
- `api_spec_old.py` - Legacy API specification

### `/config/`
Configuration management and templates:
- `config_manager.py` - Configuration management system
- `config_template.yaml` - Configuration template
- `production_config.py` - Production configuration
- `.secrets.template` - Secrets template

### `/routes/`
Flask route handlers by functionality:
- `app_routes_audio.py` - Audio processing routes
- `app_routes_chat.py` - Chat functionality routes
- `app_routes_debug.py` - Debug and diagnostic routes
- `app_routes_live2d.py` - Live2D avatar routes
- `app_routes_system.py` - System management routes
- `app_routes_tts.py` - Text-to-speech routes

### `/audio/`
Audio processing components:
- Audio handlers and processors
- Voice activity detection
- Speech recognition components

### `/databases/`
Database management:
- Database schemas and managers
- Migration utilities
- Data models

### `/models/`
AI model handlers:
- LLM integration
- TTS model handlers
- Audio model processors

### `/utils/`
Utility functions and helpers:
- `live2d_model_installer.py` - Live2D model installation
- `model_downloader.py` - Model downloading utilities
- `system_detector.py` - System capability detection

### `/web/`
Web interface components:
- Frontend templates
- Static assets
- JavaScript components

## Organization Principles

### **Separation of Concerns**
- API specifications in `/api/`
- Route handlers in `/routes/`
- Configuration in `/config/`
- Core business logic in domain-specific directories

### **Clear Dependencies**
- Core app files import from organized subdirectories
- Fallback imports handle both development and installed package scenarios
- Module-specific functionality isolated in dedicated directories

### **Maintainability**
- Related functionality grouped together
- Clear naming conventions
- Documentation for each major component

## Import Strategy

The codebase uses a fallback import strategy to handle:
1. **Development Mode**: Direct imports from subdirectories
2. **Package Mode**: Relative imports with dot notation
3. **Installed Package**: Absolute imports with full paths

Example:
```python
try:
    from routes.app_routes_live2d import live2d_bp
except ImportError:
    try:
        from .routes.app_routes_live2d import live2d_bp
    except ImportError:
        live2d_bp = Blueprint('live2d', __name__)  # Fallback
```
