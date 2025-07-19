# Test Files

This directory contains all test files for the AI Companion project.

## Python Test Files

### Audio & VAD Tests
- `test_enhanced_vad.py` - Enhanced Voice Activity Detection tests
- `test_enhanced_vad_minimal.py` - Minimal VAD implementation tests
- `test_direct_enhanced_vad.py` - Direct Enhanced VAD tests
- `test_enhanced_pipeline.py` - Enhanced audio pipeline tests
- `test_silero.py` - Silero VAD model tests
- `test_var_and_diarization.py` - Voice Activity Recognition and diarization tests

### Chat & LLM Tests
- `test_chat.py` - Chat system tests
- `test_llm_simple.py` - Simple LLM handler tests
- `test_embedded_llm_memory.py` - Embedded LLM with memory tests

### Avatar & Live2D Tests
- `test_avatar_emotions.py` - Avatar emotion system tests

### System Tests
- `test_webapp.py` - Web application tests
- `test_caching_fix.py` - Caching system fix tests
- `test_quick_cache.py` - Quick cache tests
- `test_config_only.py` - Configuration-only tests

## HTML Test Files

### Live2D Tests
- `test_live2d.html` - Basic Live2D integration test
- `test_live2d_debug.html` - Live2D debugging interface
- `test_live2d_simple.html` - Simple Live2D test page
- `test_cubism_live2d.html` - Cubism framework Live2D test

## Running Tests

To run Python tests:
```bash
cd /home/nyx/ai2d_chat
python -m pytest tests/
```

To run specific tests:
```bash
python tests/test_enhanced_vad.py
```

To view HTML tests, serve them through the Flask app or open directly in a browser.
